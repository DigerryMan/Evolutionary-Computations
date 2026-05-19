from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from algorithms.pygad_algorithm import PyGADGenerationStats, PyGADRunResult


@dataclass
class SavedPyGADRunArtifacts:
    run_directory: Path
    summary_file: Path
    history_file: Path
    plot_file: Path


@dataclass
class SavedPyGADSuiteArtifacts:
    suite_directory: Path
    summary_csv: Path
    summary_markdown: Path
    run_artifacts: list[SavedPyGADRunArtifacts]


def save_pygad_run(
    result: PyGADRunResult,
    root_dir: Path | None = None,
    run_name: str | None = None,
) -> SavedPyGADRunArtifacts:
    results_root = get_pygad_results_root(root_dir)
    if run_name is None:
        run_name = datetime.now().strftime("pygad_hypersphere_%Y%m%d_%H%M%S_%f")

    run_directory = results_root / run_name
    run_directory.mkdir(parents=True, exist_ok=False)

    summary_file = run_directory / "summary.json"
    history_file = run_directory / "history.csv"
    plot_file = run_directory / "objective_stats.svg"

    summary = {
        "function": "Hypersphere",
        "library": "PyGAD",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "config": asdict(result.config),
        "result": {
            "best_objective": result.best_objective,
            "best_fitness": result.best_fitness,
            "best_vector": result.best_vector,
            "best_solution": result.best_solution,
        },
        "artifacts": {
            "summary": summary_file.name,
            "history_csv": history_file.name,
            "objective_stats_svg": plot_file.name,
        },
    }

    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_pygad_history_csv(history_file, result.history)
    plot_file.write_text(build_pygad_stats_svg(result.history), encoding="utf-8")

    return SavedPyGADRunArtifacts(run_directory, summary_file, history_file, plot_file)


def get_pygad_results_root(root_dir: Path | None = None) -> Path:
    if root_dir is not None:
        results_root = root_dir
    else:
        results_root = Path(__file__).resolve().parents[2] / "results"

    results_root.mkdir(parents=True, exist_ok=True)
    return results_root


def save_pygad_suite(
    results: list[PyGADRunResult],
    root_dir: Path | None = None,
) -> SavedPyGADSuiteArtifacts:
    results_root = get_pygad_results_root(root_dir)
    suite_directory = results_root / datetime.now().strftime(
        "pygad_suite_%Y%m%d_%H%M%S_%f"
    )
    suite_directory.mkdir(parents=True, exist_ok=False)

    run_artifacts: list[SavedPyGADRunArtifacts] = []
    for index, result in enumerate(results, start=1):
        config = result.config
        run_name = (
            f"{index:03d}_{config.representation}_"
            f"{config.parent_selection_type}_{config.crossover_type}_"
            f"{config.mutation_type}"
        )
        run_artifacts.append(save_pygad_run(result, suite_directory, run_name))

    summary_csv = suite_directory / "suite_summary.csv"
    summary_markdown = suite_directory / "suite_summary.md"
    write_pygad_suite_csv(summary_csv, results, run_artifacts)
    write_pygad_suite_markdown(summary_markdown, results, run_artifacts)

    return SavedPyGADSuiteArtifacts(
        suite_directory=suite_directory,
        summary_csv=summary_csv,
        summary_markdown=summary_markdown,
        run_artifacts=run_artifacts,
    )


def write_pygad_history_csv(
    history_file: Path,
    history: list[PyGADGenerationStats],
) -> None:
    with history_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "generation",
                "best_objective",
                "average_objective",
                "std_objective",
                "min_objective",
                "max_objective",
            ]
        )
        for row in history:
            writer.writerow(
                [
                    row.generation,
                    f"{row.best_objective:.16g}",
                    f"{row.average_objective:.16g}",
                    f"{row.std_objective:.16g}",
                    f"{row.min_objective:.16g}",
                    f"{row.max_objective:.16g}",
                ]
            )


def write_pygad_suite_csv(
    summary_file: Path,
    results: list[PyGADRunResult],
    artifacts: list[SavedPyGADRunArtifacts],
) -> None:
    with summary_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "representation",
                "selection",
                "crossover",
                "mutation",
                "best_objective",
                "last_average_objective",
                "last_std_objective",
                "run_directory",
            ]
        )
        for result, artifact in sorted(
            zip(results, artifacts, strict=True),
            key=lambda item: item[0].best_objective,
        ):
            last = result.history[-1] if result.history else None
            writer.writerow(
                [
                    result.config.representation,
                    result.config.parent_selection_type,
                    result.config.crossover_type,
                    result.config.mutation_type,
                    f"{result.best_objective:.16g}",
                    f"{last.average_objective:.16g}" if last else "",
                    f"{last.std_objective:.16g}" if last else "",
                    artifact.run_directory.name,
                ]
            )


def write_pygad_suite_markdown(
    summary_file: Path,
    results: list[PyGADRunResult],
    artifacts: list[SavedPyGADRunArtifacts],
) -> None:
    header = (
        "| # | representation | selection | crossover | mutation | best f(x) | "
        "avg last | std last | run |"
    )
    lines = [
        "# PyGAD suite summary",
        "",
        header,
        "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]

    sorted_rows = sorted(
        zip(results, artifacts, strict=True),
        key=lambda item: item[0].best_objective,
    )
    for index, (result, artifact) in enumerate(sorted_rows, start=1):
        last = result.history[-1] if result.history else None
        average = f"{last.average_objective:.6g}" if last else ""
        std = f"{last.std_objective:.6g}" if last else ""
        lines.append(
            "| "
            f"{index} | "
            f"{result.config.representation} | "
            f"{result.config.parent_selection_type} | "
            f"{result.config.crossover_type} | "
            f"{result.config.mutation_type} | "
            f"{result.best_objective:.6g} | "
            f"{average} | "
            f"{std} | "
            f"{artifact.run_directory.name} |"
        )

    summary_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_pygad_stats_svg(history: list[PyGADGenerationStats]) -> str:
    if not history:
        raise ValueError("history is empty")

    width = 1040
    height = 620
    left = 96
    right = 48
    top = 70
    bottom = 88
    plot_width = width - left - right
    plot_height = height - top - bottom

    series = {
        "best f(x)": [row.best_objective for row in history],
        "average": [row.average_objective for row in history],
        "std": [row.std_objective for row in history],
    }
    colors = {
        "best f(x)": "#0b84f3",
        "average": "#d94841",
        "std": "#2f855a",
    }

    values = [value for points in series.values() for value in points]
    low = min(values)
    high = max(values)
    if math.isclose(low, high):
        padding = abs(low) * 0.05 or 1.0
    else:
        padding = (high - low) * 0.1
    low -= padding
    high += padding

    def x_pos(index: int) -> float:
        if len(history) == 1:
            return left + plot_width / 2
        return left + index * plot_width / (len(history) - 1)

    def y_pos(value: float) -> float:
        return top + (high - value) * plot_height / (high - low)

    rows: list[str] = []
    for tick in range(6):
        ratio = tick / 5
        y = top + ratio * plot_height
        label = high - ratio * (high - low)
        rows.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" '
            f'y2="{y:.2f}" stroke="#d0d7de" stroke-width="1" />'
        )
        rows.append(
            f'<text x="{left - 12}" y="{y + 4:.2f}" text-anchor="end" '
            f'fill="#3d4955" font-size="12">{label:.6g}</text>'
        )

    columns: list[str] = []
    for index in sorted({0, len(history) // 2, len(history) - 1}):
        x = x_pos(index)
        generation = history[index].generation
        columns.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" '
            f'y2="{height - bottom}" stroke="#e6ebf0" stroke-width="1" />'
        )
        columns.append(
            f'<text x="{x:.2f}" y="{height - bottom + 24}" '
            f'text-anchor="middle" fill="#3d4955" font-size="12">{generation}</text>'
        )

    polylines: list[str] = []
    for label, points in series.items():
        svg_points = " ".join(
            f"{x_pos(index):.2f},{y_pos(value):.2f}"
            for index, value in enumerate(points)
        )
        polylines.append(
            f'<polyline fill="none" stroke="{colors[label]}" stroke-width="3" '
            f'points="{svg_points}" />'
        )

    legend: list[str] = []
    for index, label in enumerate(series):
        x = left + index * 160
        y = 48
        legend.append(
            f'<line x1="{x}" y1="{y}" x2="{x + 28}" y2="{y}" '
            f'stroke="{colors[label]}" stroke-width="4" />'
        )
        legend.append(
            f'<text x="{x + 36}" y="{y + 4}" fill="#1f2933" '
            f'font-size="13">{label}</text>'
        )

    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff" />',
            f'<text x="{width / 2:.2f}" y="30" text-anchor="middle" '
            'font-size="24" fill="#1f2933">PyGAD objective statistics</text>',
            f'<text x="{width / 2:.2f}" y="{height - 24}" text-anchor="middle" '
            'font-size="14" fill="#52606d">Generation</text>',
            f'<text x="24" y="{height / 2:.2f}" text-anchor="middle" '
            f'font-size="14" fill="#52606d" '
            f'transform="rotate(-90 24 {height / 2:.2f})">Objective value</text>',
            *legend,
            *rows,
            *columns,
            f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" '
            f'y2="{height - bottom}" stroke="#52606d" stroke-width="2" />',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" '
            'stroke="#52606d" stroke-width="2" />',
            *polylines,
            "</svg>",
        ]
    )
