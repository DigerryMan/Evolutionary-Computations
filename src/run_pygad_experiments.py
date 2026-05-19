from __future__ import annotations

import argparse
import sys
from pathlib import Path

from algorithms.pygad_algorithm import build_pygad_suite, run_pygad_hypersphere
from reporting.pygad_result_files import save_pygad_suite


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run PyGAD experiments for the Hypersphere benchmark."
    )
    parser.add_argument("--dimensions", type=int, default=3)
    parser.add_argument("--bits-per-dimension", type=int, default=20)
    parser.add_argument("--lower-bound", type=float, default=-5.0)
    parser.add_argument("--upper-bound", type=float, default=5.0)
    parser.add_argument("--generations", type=int, default=100)
    parser.add_argument("--population", type=int, default=80)
    parser.add_argument("--parents", type=int, default=50)
    parser.add_argument("--mutation-genes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--no-gaussian",
        action="store_true",
        help="Skip the additional real-valued Gaussian mutation runs.",
    )
    parser.add_argument(
        "--no-custom-crossover",
        action="store_true",
        help="Skip the additional custom crossover examples.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help="Optional output directory. Defaults to the project results directory.",
    )
    return parser.parse_args()


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def main() -> int:
    args = parse_args()
    configs = build_pygad_suite(
        dimensions=args.dimensions,
        bits_per_dimension=args.bits_per_dimension,
        lower_bound=args.lower_bound,
        upper_bound=args.upper_bound,
        num_generations=args.generations,
        sol_per_pop=args.population,
        num_parents_mating=args.parents,
        mutation_num_genes=args.mutation_genes,
        random_seed=args.seed,
        include_gaussian=not args.no_gaussian,
        include_custom_crossover=not args.no_custom_crossover,
    )

    print(f"Running {len(configs)} PyGAD configurations...")
    results = []
    for index, config in enumerate(configs, start=1):
        label = (
            f"{config.representation} | {config.parent_selection_type} | "
            f"{config.crossover_type} | {config.mutation_type}"
        )
        print(f"[{index:02d}/{len(configs):02d}] {label}")
        try:
            results.append(run_pygad_hypersphere(config))
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1

    artifacts = save_pygad_suite(results, args.results_dir)
    print("")
    print(f"Saved suite: {relative_path(artifacts.suite_directory)}")
    print(f"Summary CSV: {relative_path(artifacts.summary_csv)}")
    print(f"Summary MD : {relative_path(artifacts.summary_markdown)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
