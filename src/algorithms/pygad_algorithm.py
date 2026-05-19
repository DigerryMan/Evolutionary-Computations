from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Literal, Sequence

import benchmark_functions as bf
import numpy

Representation = Literal["binary", "real"]
SelectionMethod = Literal["tournament", "rws", "random"]
CrossoverMethod = Literal[
    "single_point",
    "two_points",
    "uniform",
    "custom_single_point",
]
MutationMethod = Literal["random", "swap", "gaussian"]

TESTED_SELECTION_METHODS: tuple[SelectionMethod, ...] = (
    "tournament",
    "rws",
    "random",
)
TESTED_CROSSOVER_METHODS: tuple[CrossoverMethod, ...] = (
    "single_point",
    "two_points",
    "uniform",
)
TESTED_MUTATION_METHODS: tuple[MutationMethod, ...] = ("random", "swap")


@dataclass(frozen=True)
class PyGADConfig:
    dimensions: int = 3
    bits_per_dimension: int = 20
    lower_bound: float = -5.0
    upper_bound: float = 5.0
    representation: Representation = "binary"
    num_generations: int = 100
    sol_per_pop: int = 80
    num_parents_mating: int = 50
    mutation_num_genes: int = 1
    parent_selection_type: SelectionMethod = "tournament"
    crossover_type: CrossoverMethod = "single_point"
    mutation_type: MutationMethod = "random"
    keep_elitism: int = 1
    k_tournament: int = 3
    gaussian_sigma_ratio: float = 0.1
    epsilon: float = 1e-12
    random_seed: int | None = None
    parallel_processing: tuple[Literal["thread", "process"], int] | None = (
        "thread",
        4,
    )

    @property
    def num_genes(self) -> int:
        if self.representation == "binary":
            return self.dimensions * self.bits_per_dimension
        return self.dimensions


@dataclass
class PyGADGenerationStats:
    generation: int
    best_objective: float
    average_objective: float
    std_objective: float
    min_objective: float
    max_objective: float


@dataclass
class PyGADRunResult:
    config: PyGADConfig
    best_solution: list[float]
    best_vector: list[float]
    best_objective: float
    best_fitness: float
    history: list[PyGADGenerationStats] = field(default_factory=list)


def validate_pygad_config(config: PyGADConfig) -> None:
    if config.upper_bound <= config.lower_bound:
        raise ValueError("upper_bound must be greater than lower_bound")
    if config.dimensions < 1:
        raise ValueError("dimensions must be at least 1")
    if config.bits_per_dimension < 1:
        raise ValueError("bits_per_dimension must be at least 1")
    if config.num_generations < 1:
        raise ValueError("num_generations must be at least 1")
    if config.sol_per_pop < 2:
        raise ValueError("sol_per_pop must be at least 2")
    if not 1 <= config.num_parents_mating <= config.sol_per_pop:
        raise ValueError("num_parents_mating must fit within the population")
    if not 1 <= config.mutation_num_genes <= config.num_genes:
        raise ValueError("mutation_num_genes must fit within the chromosome")
    if config.parent_selection_type not in TESTED_SELECTION_METHODS:
        raise ValueError("unsupported parent_selection_type")
    if config.crossover_type not in {
        *TESTED_CROSSOVER_METHODS,
        "custom_single_point",
    }:
        raise ValueError("unsupported crossover_type")
    if config.mutation_type not in {"random", "swap", "gaussian"}:
        raise ValueError("unsupported mutation_type")
    if config.representation == "binary" and config.mutation_type == "gaussian":
        raise ValueError("gaussian mutation is available only for real encoding")


def make_hypersphere_objective(dimensions: int) -> Callable[[Sequence[float]], float]:
    function = bf.Hypersphere(n_dimensions=dimensions)

    def objective(vector: Sequence[float]) -> float:
        return float(function(vector))

    return objective


def decode_binary_solution(
    solution: Sequence[float], config: PyGADConfig
) -> list[float]:
    values: list[float] = []
    max_value = (1 << config.bits_per_dimension) - 1

    for dimension in range(config.dimensions):
        start = dimension * config.bits_per_dimension
        end = start + config.bits_per_dimension
        raw_bits = solution[start:end]
        bits = [1 if int(round(bit)) else 0 for bit in raw_bits]
        decimal = int("".join(str(bit) for bit in bits), 2)
        value = (
            config.lower_bound
            + decimal * (config.upper_bound - config.lower_bound) / max_value
        )
        values.append(value)

    return values


def decode_real_solution(solution: Sequence[float], config: PyGADConfig) -> list[float]:
    return [
        min(config.upper_bound, max(config.lower_bound, float(value)))
        for value in solution[: config.dimensions]
    ]


def decode_solution(solution: Sequence[float], config: PyGADConfig) -> list[float]:
    if config.representation == "binary":
        return decode_binary_solution(solution, config)
    return decode_real_solution(solution, config)


def evaluate_solution(
    solution: Sequence[float],
    config: PyGADConfig,
    objective: Callable[[Sequence[float]], float],
) -> float:
    return objective(decode_solution(solution, config))


def evaluate_population(
    population: Sequence[Sequence[float]],
    config: PyGADConfig,
    objective: Callable[[Sequence[float]], float],
) -> numpy.ndarray:
    return numpy.array(
        [evaluate_solution(solution, config, objective) for solution in population],
        dtype=float,
    )


def objective_to_fitness(objective_value: float, epsilon: float) -> float:
    return 1.0 / (objective_value + epsilon)


def custom_single_point_crossover(
    parents: numpy.ndarray,
    offspring_size: tuple[int, int],
    ga_instance,
) -> numpy.ndarray:
    offspring = []
    index = 0

    while len(offspring) != offspring_size[0]:
        parent1 = parents[index % parents.shape[0], :].copy()
        parent2 = parents[(index + 1) % parents.shape[0], :].copy()

        if offspring_size[1] > 1:
            split_point = numpy.random.choice(range(1, offspring_size[1]))
            parent1[split_point:] = parent2[split_point:]

        offspring.append(parent1)
        index += 1

    return numpy.array(offspring)


def make_gaussian_mutation(config: PyGADConfig):
    sigma = abs(config.upper_bound - config.lower_bound) * config.gaussian_sigma_ratio

    def mutation_func(offspring: numpy.ndarray, ga_instance) -> numpy.ndarray:
        for chromosome_idx in range(offspring.shape[0]):
            random_gene_idx = numpy.random.choice(range(offspring.shape[1]))
            offspring[chromosome_idx, random_gene_idx] += numpy.random.normal(
                0.0, sigma
            )
            offspring[chromosome_idx, random_gene_idx] = min(
                config.upper_bound,
                max(config.lower_bound, offspring[chromosome_idx, random_gene_idx]),
            )
        return offspring

    return mutation_func


def _build_ga_arguments(
    config: PyGADConfig,
    fitness_func,
    on_generation,
    logger: logging.Logger | None,
) -> dict:
    if config.representation == "binary":
        init_range_low = 0
        init_range_high = 2
        random_mutation_min_val = 0
        random_mutation_max_val = 2
        gene_type = int
        gene_space = [0, 1]
    else:
        init_range_low = config.lower_bound
        init_range_high = config.upper_bound
        random_mutation_min_val = config.lower_bound
        random_mutation_max_val = config.upper_bound
        gene_type = float
        gene_space = [
            {"low": config.lower_bound, "high": config.upper_bound}
            for _ in range(config.dimensions)
        ]

    if config.crossover_type == "custom_single_point":
        crossover_type = custom_single_point_crossover
    else:
        crossover_type = config.crossover_type

    if config.mutation_type == "gaussian":
        mutation_type = make_gaussian_mutation(config)
    else:
        mutation_type = config.mutation_type

    arguments = {
        "num_generations": config.num_generations,
        "sol_per_pop": config.sol_per_pop,
        "num_parents_mating": config.num_parents_mating,
        "num_genes": config.num_genes,
        "fitness_func": fitness_func,
        "init_range_low": init_range_low,
        "init_range_high": init_range_high,
        "gene_type": gene_type,
        "gene_space": gene_space,
        "mutation_num_genes": config.mutation_num_genes,
        "parent_selection_type": config.parent_selection_type,
        "crossover_type": crossover_type,
        "mutation_type": mutation_type,
        "keep_elitism": config.keep_elitism,
        "K_tournament": config.k_tournament,
        "random_mutation_max_val": random_mutation_max_val,
        "random_mutation_min_val": random_mutation_min_val,
        "on_generation": on_generation,
    }

    if logger is not None:
        arguments["logger"] = logger
    if config.parallel_processing is not None:
        arguments["parallel_processing"] = list(config.parallel_processing)
    if config.random_seed is not None:
        arguments["random_seed"] = config.random_seed

    return arguments


def run_pygad_hypersphere(
    config: PyGADConfig,
    logger: logging.Logger | None = None,
) -> PyGADRunResult:
    try:
        import pygad
    except ImportError as error:
        raise RuntimeError(
            "PyGAD is not installed. Install project dependencies before running "
            "PyGAD experiments."
        ) from error

    validate_pygad_config(config)
    objective = make_hypersphere_objective(config.dimensions)
    history: list[PyGADGenerationStats] = []

    def fitness_func(ga_instance, solution, solution_idx):
        objective_value = evaluate_solution(solution, config, objective)
        return objective_to_fitness(objective_value, config.epsilon)

    def on_generation(ga_instance):
        objective_values = evaluate_population(
            ga_instance.population, config, objective
        )
        history.append(
            PyGADGenerationStats(
                generation=int(ga_instance.generations_completed),
                best_objective=float(numpy.min(objective_values)),
                average_objective=float(numpy.average(objective_values)),
                std_objective=float(numpy.std(objective_values)),
                min_objective=float(numpy.min(objective_values)),
                max_objective=float(numpy.max(objective_values)),
            )
        )

        if logger is not None:
            last = history[-1]
            logger.info(
                "generation=%s best=%s avg=%s std=%s",
                last.generation,
                last.best_objective,
                last.average_objective,
                last.std_objective,
            )

    ga_instance = pygad.GA(
        **_build_ga_arguments(config, fitness_func, on_generation, logger)
    )
    ga_instance.run()

    solution, solution_fitness, _ = ga_instance.best_solution()
    best_solution = [float(value) for value in solution]
    best_vector = decode_solution(solution, config)
    best_objective = objective(best_vector)

    return PyGADRunResult(
        config=config,
        best_solution=best_solution,
        best_vector=best_vector,
        best_objective=best_objective,
        best_fitness=float(solution_fitness),
        history=history,
    )


def build_pygad_suite(
    *,
    dimensions: int = 3,
    bits_per_dimension: int = 20,
    lower_bound: float = -5.0,
    upper_bound: float = 5.0,
    num_generations: int = 100,
    sol_per_pop: int = 80,
    num_parents_mating: int = 50,
    mutation_num_genes: int = 1,
    random_seed: int | None = None,
    include_gaussian: bool = True,
    include_custom_crossover: bool = True,
) -> list[PyGADConfig]:
    configs: list[PyGADConfig] = []

    for representation in ("binary", "real"):
        for selection in TESTED_SELECTION_METHODS:
            for crossover in TESTED_CROSSOVER_METHODS:
                for mutation in TESTED_MUTATION_METHODS:
                    configs.append(
                        PyGADConfig(
                            dimensions=dimensions,
                            bits_per_dimension=bits_per_dimension,
                            lower_bound=lower_bound,
                            upper_bound=upper_bound,
                            representation=representation,
                            num_generations=num_generations,
                            sol_per_pop=sol_per_pop,
                            num_parents_mating=num_parents_mating,
                            mutation_num_genes=mutation_num_genes,
                            random_seed=random_seed,
                            parent_selection_type=selection,
                            crossover_type=crossover,
                            mutation_type=mutation,
                        )
                    )

    if include_gaussian:
        for selection in TESTED_SELECTION_METHODS:
            for crossover in TESTED_CROSSOVER_METHODS:
                configs.append(
                    PyGADConfig(
                        dimensions=dimensions,
                        bits_per_dimension=bits_per_dimension,
                        lower_bound=lower_bound,
                        upper_bound=upper_bound,
                        representation="real",
                        num_generations=num_generations,
                        sol_per_pop=sol_per_pop,
                        num_parents_mating=num_parents_mating,
                        mutation_num_genes=mutation_num_genes,
                        random_seed=random_seed,
                        parent_selection_type=selection,
                        crossover_type=crossover,
                        mutation_type="gaussian",
                    )
                )

    if include_custom_crossover:
        configs.extend(
            [
                PyGADConfig(
                    dimensions=dimensions,
                    bits_per_dimension=bits_per_dimension,
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                    representation="binary",
                    num_generations=num_generations,
                    sol_per_pop=sol_per_pop,
                    num_parents_mating=num_parents_mating,
                    mutation_num_genes=mutation_num_genes,
                    random_seed=random_seed,
                    parent_selection_type="tournament",
                    crossover_type="custom_single_point",
                    mutation_type="random",
                ),
                PyGADConfig(
                    dimensions=dimensions,
                    bits_per_dimension=bits_per_dimension,
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                    representation="real",
                    num_generations=num_generations,
                    sol_per_pop=sol_per_pop,
                    num_parents_mating=num_parents_mating,
                    mutation_num_genes=mutation_num_genes,
                    random_seed=random_seed,
                    parent_selection_type="tournament",
                    crossover_type="custom_single_point",
                    mutation_type="gaussian",
                ),
            ]
        )

    return configs
