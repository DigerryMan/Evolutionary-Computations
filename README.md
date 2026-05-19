# Evolutionary Computations

This project currently focuses on a genetic algorithm GUI for the
`Hypersphere` benchmark function.

## How to Run

1. Clone the repository.
2. Run the `main.py` file:

   ```bash
   uv run .\src\main.py
   ```

The application opens directly in the genetic algorithm view.
The objective function is fixed to `Hypersphere`, and you can configure:

- number of dimensions,
- shared domain `[a, b]`,
- population size and number of epochs,
- selection, crossover, mutation, inversion, and elitism parameters.

Each run is saved automatically in the `results/` directory.
For every run the application creates:

- `summary.json` with configuration, timing, and the best solution,
- `history.csv` with the best fitness for each epoch,
- `fitness_history.svg` generated from the saved CSV history.

The GUI also shows a plot preview panel. It loads the latest saved SVG plot on
startup and refreshes it after each new run.

## Run formatter
```bash
uv run ruff format
uv run ruff check
```

## Run PyGAD experiments

Project 3 adds a PyGAD-based experiment runner for the same `Hypersphere`
benchmark. It tests binary and real-valued representations across tournament,
roulette-wheel, and random selection; single-point, two-point, and uniform
crossover; random and swap mutation. It also includes extra runs for a custom
single-point crossover and Gaussian mutation.

```bash
uv run .\src\run_pygad_experiments.py
```

The script saves a timestamped `results/pygad_suite_*` directory. Each run
contains `summary.json`, `history.csv`, and `objective_stats.svg`. The suite
directory also contains `suite_summary.csv` and `suite_summary.md`.

## Run MealPy experiments

Project 4 adds a MealPy-based experiment runner for the same `Hypersphere`
benchmark. It runs PSO sweeps across inertia weight, c1/c2 coefficients, and
population sizes.

```bash
uv run .\src\run_mealpy_experiments.py
```

The script saves a timestamped `results/mealpy_suite_*` directory. Each run
contains `summary.json`, `history.csv`, and `objective_history.svg`. The suite
directory also contains `suite_summary.csv` and `suite_summary.md`.
