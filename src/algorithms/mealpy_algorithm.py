from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass, field
from typing import Callable, Literal, Sequence

import benchmark_functions as bf
import numpy

Algorithm = Literal["pso"]


@dataclass(frozen=True)
class MealpyConfig:
    algorithm: Algorithm = "pso"
    dimensions: int = 3
    lower_bound: float = -5.0
    upper_bound: float = 5.0
    epochs: int = 100
    pop_size: int = 80
    w: float = 0.7
    c1: float = 1.5
    c2: float = 1.5
    seed: int | None = None


@dataclass
class MealpyGenerationStats:
    epoch: int
    best_objective: float
    average_objective: float | None = None
    std_objective: float | None = None
    min_objective: float | None = None
    max_objective: float | None = None


@dataclass
class MealpyRunResult:
    config: MealpyConfig
    best_vector: list[float]
    best_objective: float
    best_fitness: float
    history: list[MealpyGenerationStats] = field(default_factory=list)


def validate_mealpy_config(config: MealpyConfig) -> None:
    if config.upper_bound <= config.lower_bound:
        raise ValueError("upper_bound must be greater than lower_bound")
    if config.dimensions < 1:
        raise ValueError("dimensions must be at least 1")
    if config.epochs < 1:
        raise ValueError("epochs must be at least 1")
    if config.pop_size < 2:
        raise ValueError("pop_size must be at least 2")
    if config.algorithm != "pso":
        raise ValueError("unsupported algorithm")


def make_hypersphere_objective(dimensions: int) -> Callable[[Sequence[float]], float]:
    function = bf.Hypersphere(n_dimensions=dimensions)

    def objective(vector: Sequence[float]) -> float:
        return float(function(vector))

    return objective


def _import_pso():
    try:
        from mealpy import PSO
    except ImportError:
        from mealpy.swarm_based import PSO
    return PSO


def _filter_kwargs(callable_obj, kwargs: dict) -> dict:
    try:
        signature = inspect.signature(callable_obj)
    except (TypeError, ValueError):
        return kwargs

    if any(
        param.kind == inspect.Parameter.VAR_KEYWORD
        for param in signature.parameters.values()
    ):
        return kwargs

    return {key: value for key, value in kwargs.items() if key in signature.parameters}


def _build_pso_model(config: MealpyConfig):
    pso_module = _import_pso()
    pso_class = getattr(pso_module, "OriginalPSO", None)
    if pso_class is None:
        pso_class = getattr(pso_module, "BasePSO", None)

    if pso_class is None:
        raise RuntimeError("MealPy PSO class not found")

    parameters = {
        "epoch": config.epochs,
        "pop_size": config.pop_size,
        "w": config.w,
        "c1": config.c1,
        "c2": config.c2,
    }

    filtered = _filter_kwargs(pso_class, parameters)
    if config.seed is not None:
        try:
            signature = inspect.signature(pso_class)
        except (TypeError, ValueError):
            signature = None

        if signature is not None:
            if "seed" in signature.parameters:
                filtered["seed"] = config.seed
            elif "random_seed" in signature.parameters:
                filtered["random_seed"] = config.seed

    return pso_class(**filtered)


def _build_problem(
    config: MealpyConfig, objective: Callable[[Sequence[float]], float]
) -> dict:
    lower_bounds = [config.lower_bound] * config.dimensions
    upper_bounds = [config.upper_bound] * config.dimensions

    try:
        from mealpy import FloatVar
    except ImportError:
        return {
            "fit_func": objective,
            "lb": lower_bounds,
            "ub": upper_bounds,
            "minmax": "min",
        }

    bounds = FloatVar(lb=lower_bounds, ub=upper_bounds)
    return {
        "obj_func": objective,
        "bounds": bounds,
        "minmax": "min",
    }


def _to_float_list(values: Sequence[float]) -> list[float]:
    return [float(value) for value in values]


def _extract_solution_from_agent(agent) -> list[float] | None:
    for attr in ("solution", "position", "pos", "x", "vector"):
        if hasattr(agent, attr):
            raw = getattr(agent, attr)
            if raw is not None:
                return _to_float_list(raw)
    return None


def _extract_fitness_from_agent(agent) -> float | None:
    for attr in ("fitness", "fit", "cost"):
        if hasattr(agent, attr):
            value = getattr(agent, attr)
            if value is not None:
                return float(value)

    target = getattr(agent, "target", None)
    if target is not None:
        if hasattr(target, "fitness"):
            return float(target.fitness)
        if hasattr(target, "cost"):
            return float(target.cost)

    return None


def _extract_best_result(best, model, objective):
    if isinstance(best, (tuple, list)) and len(best) >= 2:
        return _to_float_list(best[0]), float(best[1])

    solution = _extract_solution_from_agent(best)
    fitness = _extract_fitness_from_agent(best)

    if solution is None:
        fallback = getattr(model, "g_best", None) or getattr(model, "best", None)
        if fallback is not None:
            solution = _extract_solution_from_agent(fallback)
            if fitness is None:
                fitness = _extract_fitness_from_agent(fallback)

    if solution is None:
        raise RuntimeError("Unable to extract best solution from MealPy result")

    if fitness is None:
        fitness = float(objective(solution))

    return solution, fitness


def _extract_best_series(history) -> list[float]:
    for attr in (
        "list_global_best_fit",
        "list_best_fit",
        "list_global_best_fitness",
    ):
        if hasattr(history, attr):
            return [float(value) for value in getattr(history, attr)]

    for attr in ("list_global_best", "list_best", "list_current_best"):
        if hasattr(history, attr):
            candidates = getattr(history, attr)
            values: list[float] = []
            for agent in candidates:
                fitness = _extract_fitness_from_agent(agent)
                if fitness is not None:
                    values.append(float(fitness))
            if values:
                return values

    return []


def _extract_population_series(history) -> list[list] | None:
    for attr in ("list_population", "list_populations", "list_pop"):
        if hasattr(history, attr):
            populations = getattr(history, attr)
            if populations:
                return list(populations)
    return None


def _extract_population_fitness(
    population: Sequence,
    objective: Callable[[Sequence[float]], float],
) -> list[float]:
    values: list[float] = []
    for agent in population:
        fitness = _extract_fitness_from_agent(agent)
        if fitness is None:
            solution = _extract_solution_from_agent(agent)
            if solution is None:
                continue
            fitness = float(objective(solution))
        values.append(float(fitness))
    return values


def _extract_history(
    model,
    objective: Callable[[Sequence[float]], float],
) -> list[MealpyGenerationStats]:
    history = getattr(model, "history", None)
    if history is None:
        return []

    best_series = _extract_best_series(history)
    populations = _extract_population_series(history)

    if not best_series and populations:
        for population in populations:
            values = _extract_population_fitness(population, objective)
            best_series.append(min(values) if values else float("nan"))

    if not best_series:
        return []

    stats: list[MealpyGenerationStats] = []
    for index, best_value in enumerate(best_series, start=1):
        average = std = min_value = max_value = None
        if populations and index - 1 < len(populations):
            values = _extract_population_fitness(populations[index - 1], objective)
            if values:
                array = numpy.array(values, dtype=float)
                average = float(array.mean())
                std = float(array.std())
                min_value = float(array.min())
                max_value = float(array.max())

        stats.append(
            MealpyGenerationStats(
                epoch=index,
                best_objective=float(best_value),
                average_objective=average,
                std_objective=std,
                min_objective=min_value,
                max_objective=max_value,
            )
        )

    return stats


def run_mealpy_hypersphere(
    config: MealpyConfig,
    logger: logging.Logger | None = None,
) -> MealpyRunResult:
    try:
        import mealpy  # noqa: F401
    except ImportError as error:
        raise RuntimeError(
            "MealPy is not installed. Install project dependencies before running "
            "MealPy experiments."
        ) from error

    validate_mealpy_config(config)
    objective = make_hypersphere_objective(config.dimensions)
    problem = _build_problem(config, objective)

    model = _build_pso_model(config)
    if logger is not None:
        logger.info(
            "MealPy run: algorithm=%s pop=%s epochs=%s",
            config.algorithm,
            config.pop_size,
            config.epochs,
        )

    best = model.solve(problem)
    best_vector, best_fitness = _extract_best_result(best, model, objective)
    best_objective = float(objective(best_vector))

    history = _extract_history(model, objective)
    if not history:
        history = [
            MealpyGenerationStats(
                epoch=1,
                best_objective=best_objective,
            )
        ]

    return MealpyRunResult(
        config=config,
        best_vector=best_vector,
        best_objective=best_objective,
        best_fitness=best_fitness,
        history=history,
    )


def _add_unique(
    configs: list[MealpyConfig],
    seen: set[tuple],
    config: MealpyConfig,
) -> None:
    key = (
        config.algorithm,
        config.dimensions,
        config.lower_bound,
        config.upper_bound,
        config.epochs,
        config.pop_size,
        config.w,
        config.c1,
        config.c2,
        config.seed,
    )
    if key in seen:
        return
    seen.add(key)
    configs.append(config)


def build_mealpy_suite(
    *,
    dimensions: int = 3,
    lower_bound: float = -5.0,
    upper_bound: float = 5.0,
    epochs: int = 100,
    pop_size: int = 80,
    w: float = 0.7,
    c1: float = 1.5,
    c2: float = 1.5,
    seed: int | None = None,
    include_weight_sweep: bool = True,
    include_coeff_sweep: bool = True,
    include_population_sweep: bool = True,
) -> list[MealpyConfig]:
    base = MealpyConfig(
        dimensions=dimensions,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        epochs=epochs,
        pop_size=pop_size,
        w=w,
        c1=c1,
        c2=c2,
        seed=seed,
    )

    configs: list[MealpyConfig] = []
    seen: set[tuple] = set()
    _add_unique(configs, seen, base)

    if include_weight_sweep:
        for candidate in (0.4, 0.7, 0.9):
            _add_unique(
                configs,
                seen,
                MealpyConfig(
                    dimensions=dimensions,
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                    epochs=epochs,
                    pop_size=pop_size,
                    w=candidate,
                    c1=c1,
                    c2=c2,
                    seed=seed,
                ),
            )

    if include_coeff_sweep:
        for candidate in (1.2, 1.8, 2.4):
            _add_unique(
                configs,
                seen,
                MealpyConfig(
                    dimensions=dimensions,
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                    epochs=epochs,
                    pop_size=pop_size,
                    w=w,
                    c1=candidate,
                    c2=candidate,
                    seed=seed,
                ),
            )

    if include_population_sweep:
        for candidate in (40, 80, 120):
            _add_unique(
                configs,
                seen,
                MealpyConfig(
                    dimensions=dimensions,
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                    epochs=epochs,
                    pop_size=candidate,
                    w=w,
                    c1=c1,
                    c2=c2,
                    seed=seed,
                ),
            )

    return configs
