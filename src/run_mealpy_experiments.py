from __future__ import annotations

import argparse
import sys
from pathlib import Path

from algorithms.mealpy_algorithm import build_mealpy_suite, run_mealpy_hypersphere
from reporting.mealpy_result_files import save_mealpy_suite


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run MealPy experiments for the Hypersphere benchmark."
    )
    parser.add_argument("--dimensions", type=int, default=3)
    parser.add_argument("--lower-bound", type=float, default=-5.0)
    parser.add_argument("--upper-bound", type=float, default=5.0)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--population", type=int, default=80)
    parser.add_argument("--w", type=float, default=0.7)
    parser.add_argument("--c1", type=float, default=1.5)
    parser.add_argument("--c2", type=float, default=1.5)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--no-weight-sweep",
        action="store_true",
        help="Skip the inertia weight sweep.",
    )
    parser.add_argument(
        "--no-coeff-sweep",
        action="store_true",
        help="Skip the c1/c2 coefficient sweep.",
    )
    parser.add_argument(
        "--no-pop-sweep",
        action="store_true",
        help="Skip the population size sweep.",
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
    configs = build_mealpy_suite(
        dimensions=args.dimensions,
        lower_bound=args.lower_bound,
        upper_bound=args.upper_bound,
        epochs=args.epochs,
        pop_size=args.population,
        w=args.w,
        c1=args.c1,
        c2=args.c2,
        seed=args.seed,
        include_weight_sweep=not args.no_weight_sweep,
        include_coeff_sweep=not args.no_coeff_sweep,
        include_population_sweep=not args.no_pop_sweep,
    )

    print(f"Running {len(configs)} MealPy configurations...")
    results = []
    for index, config in enumerate(configs, start=1):
        label = (
            f"{config.algorithm} | pop={config.pop_size} | "
            f"w={config.w} | c1={config.c1} | c2={config.c2}"
        )
        print(f"[{index:02d}/{len(configs):02d}] {label}")
        try:
            results.append(run_mealpy_hypersphere(config))
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1

    artifacts = save_mealpy_suite(results, args.results_dir)
    print("")
    print(f"Saved suite: {relative_path(artifacts.suite_directory)}")
    print(f"Summary CSV: {relative_path(artifacts.summary_csv)}")
    print(f"Summary MD : {relative_path(artifacts.summary_markdown)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
