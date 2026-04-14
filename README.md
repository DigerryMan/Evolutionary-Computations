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
