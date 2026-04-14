import math
import random
from dataclasses import dataclass, field
from typing import Callable, Literal


@dataclass
class Chromosome:
    bits: list[int]
    a: float
    b: float
    bits_per_dimension: int
    dimensions: int = 1

    @property
    def length(self) -> int:
        return len(self.bits)

    def clone(self) -> "Chromosome":
        return Chromosome(
            self.bits[:],
            self.a,
            self.b,
            self.bits_per_dimension,
            self.dimensions,
        )

    def with_bits(self, bits: list[int]) -> "Chromosome":
        return Chromosome(
            bits,
            self.a,
            self.b,
            self.bits_per_dimension,
            self.dimensions,
        )

    def decode(self) -> list[float]:
        values: list[float] = []
        max_value = (1 << self.bits_per_dimension) - 1

        for i in range(self.dimensions):
            start = i * self.bits_per_dimension
            end = start + self.bits_per_dimension
            part = self.bits[start:end]
            decimal = int("".join(str(bit) for bit in part), 2) if part else 0

            if max_value == 0:
                values.append(self.a)
            else:
                value = self.a + decimal * (self.b - self.a) / max_value
                values.append(value)

        return values

    @classmethod
    def random(
        cls, bits_per_dimension: int, a: float, b: float, dimensions: int = 1
    ) -> "Chromosome":
        return cls(
            [random.randint(0, 1) for _ in range(bits_per_dimension * dimensions)],
            a,
            b,
            bits_per_dimension,
            dimensions,
        )


def chromosome_length(a: float, b: float, precision: int) -> int:
    value = math.ceil(math.log2((b - a) * (10**precision) + 1))
    return max(2, min(value, 64))


def select_best(
    population: list[Chromosome], fitnesses: list[float], n: int
) -> list[Chromosome]:
    order = sorted(range(len(population)), key=fitnesses.__getitem__)
    return [population[i].clone() for i in order[:n]]


def select_roulette(
    population: list[Chromosome], fitnesses: list[float], n: int
) -> list[Chromosome]:
    max_fitness = max(fitnesses)
    weights = [max_fitness - fitness + 1e-10 for fitness in fitnesses]
    total = sum(weights)
    probabilities = [weight / total for weight in weights]

    selected: list[Chromosome] = []
    for _ in range(n):
        draw = random.random()
        cumulative = 0.0
        chosen = population[-1]

        for i, probability in enumerate(probabilities):
            cumulative += probability
            if draw <= cumulative:
                chosen = population[i]
                break

        selected.append(chosen.clone())

    return selected


def select_tournament(
    population: list[Chromosome],
    fitnesses: list[float],
    n: int,
    tournament_size: int = 3,
) -> list[Chromosome]:
    size = min(tournament_size, len(population))
    selected: list[Chromosome] = []

    for _ in range(n):
        players = random.sample(range(len(population)), size)
        winner = min(players, key=fitnesses.__getitem__)
        selected.append(population[winner].clone())

    return selected


def crossover_single_point(
    first: Chromosome, second: Chromosome
) -> tuple[Chromosome, Chromosome]:
    point = random.randint(1, first.length - 1)
    child1 = first.with_bits(first.bits[:point] + second.bits[point:])
    child2 = second.with_bits(second.bits[:point] + first.bits[point:])
    return child1, child2


def crossover_two_point(
    first: Chromosome, second: Chromosome
) -> tuple[Chromosome, Chromosome]:
    if first.length < 3:
        return crossover_single_point(first, second)

    left, right = sorted(random.sample(range(1, first.length), 2))
    child1 = first.with_bits(
        first.bits[:left] + second.bits[left:right] + first.bits[right:]
    )
    child2 = second.with_bits(
        second.bits[:left] + first.bits[left:right] + second.bits[right:]
    )
    return child1, child2


def crossover_uniform(
    first: Chromosome, second: Chromosome
) -> tuple[Chromosome, Chromosome]:
    mask = [random.randint(0, 1) for _ in range(first.length)]
    child1 = first.with_bits(
        [first.bits[i] if mask[i] else second.bits[i] for i in range(first.length)]
    )
    child2 = second.with_bits(
        [second.bits[i] if mask[i] else first.bits[i] for i in range(first.length)]
    )
    return child1, child2


def crossover_granular(
    first: Chromosome, second: Chromosome, grain_size: int = 2
) -> tuple[Chromosome, Chromosome]:
    bits1: list[int] = []
    bits2: list[int] = []
    swap = bool(random.randint(0, 1))

    for start in range(0, first.length, grain_size):
        end = min(start + grain_size, first.length)
        if swap:
            bits1.extend(second.bits[start:end])
            bits2.extend(first.bits[start:end])
        else:
            bits1.extend(first.bits[start:end])
            bits2.extend(second.bits[start:end])
        swap = not swap

    return first.with_bits(bits1), second.with_bits(bits2)


def apply_crossover(
    first: Chromosome, second: Chromosome, method: str, grain_size: int
) -> tuple[Chromosome, Chromosome]:
    if method == "single_point":
        return crossover_single_point(first, second)
    if method == "two_point":
        return crossover_two_point(first, second)
    if method == "uniform":
        return crossover_uniform(first, second)
    return crossover_granular(first, second, grain_size)


def mutate_edge(chromosome: Chromosome, probability: float) -> Chromosome:
    bits = chromosome.bits[:]
    for i in range(len(bits)):
        if random.random() < probability:
            bits[i] = random.choice([0, 1])
    return chromosome.with_bits(bits)


def mutate_single_point(chromosome: Chromosome, probability: float) -> Chromosome:
    bits = chromosome.bits[:]
    if random.random() < probability:
        index = random.randint(0, len(bits) - 1)
        bits[index] ^= 1
    return chromosome.with_bits(bits)


def mutate_two_point(chromosome: Chromosome, probability: float) -> Chromosome:
    bits = chromosome.bits[:]
    if random.random() < probability:
        for index in random.sample(range(len(bits)), min(2, len(bits))):
            bits[index] ^= 1
    return chromosome.with_bits(bits)


def invert(chromosome: Chromosome, probability: float) -> Chromosome:
    bits = chromosome.bits[:]
    if random.random() < probability and len(bits) > 2:
        left, right = sorted(random.sample(range(len(bits)), 2))
        bits[left : right + 1] = reversed(bits[left : right + 1])
    return chromosome.with_bits(bits)


MUTATION_METHODS = {
    "edge": mutate_edge,
    "single_point": mutate_single_point,
    "two_point": mutate_two_point,
}


@dataclass
class GAConfig:
    a: float = -10.0
    b: float = 10.0
    dimensions: int = 1
    precision: int = 6
    population_size: int = 50
    epochs: int = 100
    selection_method: Literal["best", "roulette", "tournament"] = "tournament"
    tournament_size: int = 3
    crossover_method: Literal["single_point", "two_point", "uniform", "granular"] = (
        "two_point"
    )
    crossover_prob: float = 0.8
    grain_size: int = 2
    mutation_method: Literal["edge", "single_point", "two_point"] = "single_point"
    mutation_prob: float = 0.01
    inversion_prob: float = 0.05
    elite_size: int = 1
    minimize: bool = True


@dataclass
class GAResult:
    best_chromosome: Chromosome
    best_fitness: float
    history: list[float] = field(default_factory=list)


def run_genetic_algorithm(
    func: Callable[[list[float]], float], config: GAConfig
) -> GAResult:
    if config.b <= config.a:
        raise ValueError("b must be greater than a")
    if config.dimensions < 1:
        raise ValueError("dimensions must be at least 1")

    bits_per_dimension = chromosome_length(config.a, config.b, config.precision)
    mutate = MUTATION_METHODS[config.mutation_method]

    def evaluate(population: list[Chromosome]) -> list[float]:
        values = [func(chromosome.decode()) for chromosome in population]
        if config.minimize:
            return values
        return [-value for value in values]

    def select(
        population: list[Chromosome], fitnesses: list[float], count: int
    ) -> list[Chromosome]:
        if config.selection_method == "best":
            return select_best(population, fitnesses, count)
        if config.selection_method == "roulette":
            return select_roulette(population, fitnesses, count)
        return select_tournament(population, fitnesses, count, config.tournament_size)

    population = [
        Chromosome.random(bits_per_dimension, config.a, config.b, config.dimensions)
        for _ in range(config.population_size)
    ]

    best = population[0].clone()
    best_fitness = float("inf")
    history: list[float] = []

    for _ in range(config.epochs):
        fitnesses = evaluate(population)
        best_index = min(range(len(population)), key=fitnesses.__getitem__)

        if fitnesses[best_index] < best_fitness:
            best_fitness = fitnesses[best_index]
            best = population[best_index].clone()

        history.append(best_fitness if config.minimize else -best_fitness)

        elite_count = min(config.elite_size, len(population))
        order = sorted(range(len(population)), key=fitnesses.__getitem__)
        elite = [population[i].clone() for i in order[:elite_count]]

        needed = len(population) - elite_count
        parents = select(population, fitnesses, max(needed, 2))
        offspring: list[Chromosome] = []
        index = 0

        while len(offspring) < needed:
            first = parents[index % len(parents)]
            second = parents[(index + 1) % len(parents)]

            if random.random() < config.crossover_prob and first.length > 1:
                child1, child2 = apply_crossover(
                    first, second, config.crossover_method, config.grain_size
                )
                offspring.extend([child1, child2])
            else:
                offspring.extend([first.clone(), second.clone()])

            index += 2

        offspring = offspring[:needed]
        offspring = [
            mutate(chromosome, config.mutation_prob) for chromosome in offspring
        ]

        if config.inversion_prob > 0:
            offspring = [
                invert(chromosome, config.inversion_prob) for chromosome in offspring
            ]

        population = elite + offspring

    fitnesses = evaluate(population)
    best_index = min(range(len(population)), key=fitnesses.__getitem__)
    if fitnesses[best_index] < best_fitness:
        best_fitness = fitnesses[best_index]
        best = population[best_index].clone()

    if not config.minimize:
        best_fitness = -best_fitness

    return GAResult(best, best_fitness, history)
