"""Genetic algorithm with binary chromosome encoding."""

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Literal


# ─── Chromosome ───────────────────────────────────────────────────────────────

@dataclass
class Chromosome:
    """Binary-encoded chromosome representing one real number in [a, b]."""

    bits: list[int]
    a: float
    b: float

    @property
    def length(self) -> int:
        return len(self.bits)

    def decode(self) -> float:
        """Decode binary string to a real value in [a, b]."""
        decimal = int("".join(map(str, self.bits)), 2) if self.bits else 0
        max_val = (1 << self.length) - 1
        if max_val == 0:
            return self.a
        return self.a + decimal * (self.b - self.a) / max_val

    @classmethod
    def random(cls, length: int, a: float, b: float) -> "Chromosome":
        return cls(bits=[random.randint(0, 1) for _ in range(length)], a=a, b=b)

    def copy(self) -> "Chromosome":
        return Chromosome(bits=self.bits[:], a=self.a, b=self.b)


def chromosome_length(a: float, b: float, precision: int) -> int:
    """Return minimum bit length to represent [a,b] with given decimal precision."""
    n = math.ceil(math.log2((b - a) * (10 ** precision) + 1))
    return max(2, min(n, 64))


# ─── Selection ────────────────────────────────────────────────────────────────

def select_best(
    population: list[Chromosome], fitnesses: list[float], n: int
) -> list[Chromosome]:
    """Truncation selection: return the n best individuals."""
    order = sorted(range(len(population)), key=lambda i: fitnesses[i])
    return [population[i].copy() for i in order[:n]]


def select_roulette(
    population: list[Chromosome], fitnesses: list[float], n: int
) -> list[Chromosome]:
    """Roulette-wheel (fitness-proportionate) selection for minimisation."""
    max_f = max(fitnesses)
    # invert so smaller fitness → larger weight
    weights = [max_f - f + 1e-10 for f in fitnesses]
    total = sum(weights)
    probs = [w / total for w in weights]

    selected: list[Chromosome] = []
    for _ in range(n):
        r = random.random()
        cumulative = 0.0
        chosen = population[-1]
        for i, p in enumerate(probs):
            cumulative += p
            if r <= cumulative:
                chosen = population[i]
                break
        selected.append(chosen.copy())
    return selected


def select_tournament(
    population: list[Chromosome],
    fitnesses: list[float],
    n: int,
    tournament_size: int = 3,
) -> list[Chromosome]:
    """Tournament selection: run n tournaments of given size."""
    k = min(tournament_size, len(population))
    selected: list[Chromosome] = []
    for _ in range(n):
        participants = random.sample(range(len(population)), k)
        winner = min(participants, key=lambda i: fitnesses[i])
        selected.append(population[winner].copy())
    return selected


# ─── Crossover ────────────────────────────────────────────────────────────────

def crossover_single_point(
    p1: Chromosome, p2: Chromosome
) -> tuple[Chromosome, Chromosome]:
    pt = random.randint(1, p1.length - 1)
    c1 = Chromosome(bits=p1.bits[:pt] + p2.bits[pt:], a=p1.a, b=p1.b)
    c2 = Chromosome(bits=p2.bits[:pt] + p1.bits[pt:], a=p1.a, b=p1.b)
    return c1, c2


def crossover_two_point(
    p1: Chromosome, p2: Chromosome
) -> tuple[Chromosome, Chromosome]:
    if p1.length < 3:
        return crossover_single_point(p1, p2)
    a, b = sorted(random.sample(range(1, p1.length), 2))
    bits1 = p1.bits[:a] + p2.bits[a:b] + p1.bits[b:]
    bits2 = p2.bits[:a] + p1.bits[a:b] + p2.bits[b:]
    return Chromosome(bits=bits1, a=p1.a, b=p1.b), Chromosome(bits=bits2, a=p1.a, b=p1.b)


def crossover_uniform(
    p1: Chromosome, p2: Chromosome
) -> tuple[Chromosome, Chromosome]:
    mask = [random.randint(0, 1) for _ in range(p1.length)]
    bits1 = [p1.bits[i] if mask[i] else p2.bits[i] for i in range(p1.length)]
    bits2 = [p2.bits[i] if mask[i] else p1.bits[i] for i in range(p1.length)]
    return Chromosome(bits=bits1, a=p1.a, b=p1.b), Chromosome(bits=bits2, a=p1.a, b=p1.b)


def crossover_granular(
    p1: Chromosome, p2: Chromosome, grain_size: int = 2
) -> tuple[Chromosome, Chromosome]:
    """Granular crossover: alternately swap fixed-size blocks (grains)."""
    bits1: list[int] = []
    bits2: list[int] = []
    swap = random.randint(0, 1)
    i = 0
    while i < p1.length:
        end = min(i + grain_size, p1.length)
        if swap:
            bits1.extend(p2.bits[i:end])
            bits2.extend(p1.bits[i:end])
        else:
            bits1.extend(p1.bits[i:end])
            bits2.extend(p2.bits[i:end])
        swap ^= 1
        i = end
    return Chromosome(bits=bits1, a=p1.a, b=p1.b), Chromosome(bits=bits2, a=p1.a, b=p1.b)


def _apply_crossover(
    p1: Chromosome, p2: Chromosome, method: str, grain_size: int
) -> tuple[Chromosome, Chromosome]:
    if method == "granular":
        return crossover_granular(p1, p2, grain_size)
    return {
        "single_point": crossover_single_point,
        "two_point": crossover_two_point,
        "uniform": crossover_uniform,
    }[method](p1, p2)


# ─── Mutation ─────────────────────────────────────────────────────────────────

def mutate_edge(chrom: Chromosome, prob: float) -> Chromosome:
    """Edge (boundary) mutation: each bit is replaced by 0 or 1 with prob."""
    bits = chrom.bits[:]
    for i in range(len(bits)):
        if random.random() < prob:
            bits[i] = random.choice([0, 1])
    return Chromosome(bits=bits, a=chrom.a, b=chrom.b)


def mutate_single_point(chrom: Chromosome, prob: float) -> Chromosome:
    """Single-point mutation: flip exactly one random bit with probability prob."""
    bits = chrom.bits[:]
    if random.random() < prob:
        idx = random.randint(0, len(bits) - 1)
        bits[idx] ^= 1
    return Chromosome(bits=bits, a=chrom.a, b=chrom.b)


def mutate_two_point(chrom: Chromosome, prob: float) -> Chromosome:
    """Two-point mutation: flip two distinct random bits with probability prob."""
    bits = chrom.bits[:]
    if random.random() < prob:
        indices = random.sample(range(len(bits)), min(2, len(bits)))
        for idx in indices:
            bits[idx] ^= 1
    return Chromosome(bits=bits, a=chrom.a, b=chrom.b)


_MUTATION_MAP = {
    "edge": mutate_edge,
    "single_point": mutate_single_point,
    "two_point": mutate_two_point,
}


# ─── Inversion ────────────────────────────────────────────────────────────────

def invert(chrom: Chromosome, prob: float) -> Chromosome:
    """Inversion operator: reverse a randomly chosen segment of the chromosome."""
    bits = chrom.bits[:]
    if random.random() < prob and len(bits) > 2:
        lo, hi = sorted(random.sample(range(len(bits)), 2))
        bits[lo : hi + 1] = bits[lo : hi + 1][::-1]
    return Chromosome(bits=bits, a=chrom.a, b=chrom.b)


# ─── Configuration & Result ───────────────────────────────────────────────────

@dataclass
class GAConfig:
    # Domain
    a: float = -10.0
    b: float = 10.0
    precision: int = 6  # decimal places → determines chromosome length
    # Population
    population_size: int = 50
    epochs: int = 100
    # Selection
    selection_method: Literal["best", "roulette", "tournament"] = "tournament"
    tournament_size: int = 3
    # Crossover
    crossover_method: Literal["single_point", "two_point", "uniform", "granular"] = "two_point"
    crossover_prob: float = 0.8
    grain_size: int = 2
    # Mutation
    mutation_method: Literal["edge", "single_point", "two_point"] = "single_point"
    mutation_prob: float = 0.01
    # Inversion
    inversion_prob: float = 0.05
    # Elitism
    elite_size: int = 1
    # Optimisation direction
    minimize: bool = True


@dataclass
class GAResult:
    best_chromosome: Chromosome
    best_fitness: float
    history: list[float] = field(default_factory=list)  # best fitness value per epoch


# ─── Main loop ────────────────────────────────────────────────────────────────

def run_genetic_algorithm(
    func: Callable[[float], float], config: GAConfig
) -> GAResult:
    """Run genetic algorithm to optimise func over [a, b]."""
    if config.b <= config.a:
        raise ValueError("Domain error: b must be greater than a.")

    bit_len = chromosome_length(config.a, config.b, config.precision)
    n = config.population_size
    mutation_fn = _MUTATION_MAP[config.mutation_method]

    def do_select(pop: list[Chromosome], fits: list[float], count: int) -> list[Chromosome]:
        if config.selection_method == "tournament":
            return select_tournament(pop, fits, count, config.tournament_size)
        if config.selection_method == "roulette":
            return select_roulette(pop, fits, count)
        return select_best(pop, fits, count)

    def evaluate(pop: list[Chromosome]) -> list[float]:
        raw = [func(c.decode()) for c in pop]
        return raw if config.minimize else [-v for v in raw]  # normalise: lower is always better

    # Initialise
    population = [Chromosome.random(bit_len, config.a, config.b) for _ in range(n)]

    best_chromosome: Chromosome | None = None
    best_fitness = float("inf")
    history: list[float] = []

    for _epoch in range(config.epochs):
        fitnesses = evaluate(population)

        # Track global best
        local_best_idx = min(range(n), key=lambda i: fitnesses[i])
        if fitnesses[local_best_idx] < best_fitness:
            best_fitness = fitnesses[local_best_idx]
            best_chromosome = population[local_best_idx].copy()

        # Record best fitness in original scale
        history.append(best_fitness if config.minimize else -best_fitness)

        # Elitism
        elite_count = min(config.elite_size, n)
        elite: list[Chromosome] = []
        if elite_count > 0:
            order = sorted(range(n), key=lambda i: fitnesses[i])
            elite = [population[i].copy() for i in order[:elite_count]]

        # Selection
        n_offspring = n - elite_count
        parents = do_select(population, fitnesses, max(n_offspring, 2))

        # Crossover → offspring
        offspring: list[Chromosome] = []
        idx = 0
        while len(offspring) < n_offspring:
            p1 = parents[idx % len(parents)]
            p2 = parents[(idx + 1) % len(parents)]
            if random.random() < config.crossover_prob and bit_len > 1:
                c1, c2 = _apply_crossover(p1, p2, config.crossover_method, config.grain_size)
                offspring.extend([c1, c2])
            else:
                offspring.extend([p1.copy(), p2.copy()])
            idx += 2
        offspring = offspring[:n_offspring]

        # Mutation
        offspring = [mutation_fn(c, config.mutation_prob) for c in offspring]

        # Inversion
        if config.inversion_prob > 0.0:
            offspring = [invert(c, config.inversion_prob) for c in offspring]

        # Assemble new population
        population = elite + offspring

    # Final evaluation pass
    final_fits = evaluate(population)
    final_best_idx = min(range(n), key=lambda i: final_fits[i])
    if final_fits[final_best_idx] < best_fitness:
        best_fitness = final_fits[final_best_idx]
        best_chromosome = population[final_best_idx].copy()

    return GAResult(
        best_chromosome=best_chromosome,  # type: ignore[arg-type]
        best_fitness=best_fitness if config.minimize else -best_fitness,
        history=history,
    )
