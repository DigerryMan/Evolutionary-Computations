from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from algorithms.mealpy_algorithm import MealpyGenerationStats, MealpyRunResult


@dataclass
class SavedMealpyRunArtifacts:
    run_directory: Path
    summary_file: Path
    history_file: Path
    plot_file: Path


@dataclass
class SavedMealpySuiteArtifacts:
    suite_directory: Path
    summary_csv: Path
    summary_markdown: Path
    run_artifacts: list[SavedMealpyRunArtifacts]


def save_mealpy_run(
    result: MealpyRunResult,
    root_dir: Path | None = None,
    run_name: str | None = None,
) -> SavedMealpyRunArtifacts:
    results_root = get_mealpy_results_root(root_dir)
    if run_name is None:
        run_name = datetime.now().strftime("mealpy_hypersphere_%Y%m%d_%H%M%S_%f")

    run_directory = results_root / run_name
    run_directory.mkdir(parents=True, exist_ok=False)

    summary_file = run_directory / "summary.json"
    history_file = run_directory / "history.csv"
    plot_file = run_directory / "objective_history.svg"

    summary = {
        "function": "Hypersphere",
        "library": "MealPy",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "config": asdict(result.config),
        "result": {
            "best_objective": result.best_objective,
            "best_fitness": result.best_fitness,
            "best_vector": result.best_vector,
        },
        "artifacts": {
            "summary": summary_file.name,
            "history_csv": history_file.name,
            "objective_history_svg": plot_file.name,
        },
    }

    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_mealpy_history_csv(history_file, result.history)
    plot_file.write_text(build_mealpy_history_svg(result.history), encoding="utf-8")

    return SavedMealpyRunArtifacts(run_directory, summary_file, history_file, plot_file)


def get_mealpy_results_root(root_dir: Path | None = None) -> Path:
    if root_dir is not None:
        results_root = root_dir
    else:
        results_root = Path(__file__).resolve().parents[2] / "results"

    results_root.mkdir(parents=True, exist_ok=True)
    return results_root


def save_mealpy_suite(
    results: list[MealpyRunResult],
    root_dir: Path | None = None,
) -> SavedMealpySuiteArtifacts:
    results_root = get_mealpy_results_root(root_dir)
    suite_directory = results_root / datetime.now().strftime(
        "mealpy_suite_%Y%m%d_%H%M%S_%f"
    )
    suite_directory.mkdir(parents=True, exist_ok=False)

    run_artifacts: list[SavedMealpyRunArtifacts] = []
    for index, result in enumerate(results, start=1):
        config = result.config
        run_name = (
            f"{index:03d}_{config.algorithm}_"
            f"w{_format_value(config.w)}_"
            f"c1{_format_value(config.c1)}_"
            f"c2{_format_value(config.c2)}_"
            f"pop{config.pop_size}"
        )
        run_artifacts.append(save_mealpy_run(result, suite_directory, run_name))

    summary_csv = suite_directory / "suite_summary.csv"
    summary_markdown = suite_directory / "suite_summary.md"
    write_mealpy_suite_csv(summary_csv, results, run_artifacts)
    write_mealpy_suite_markdown(summary_markdown, results, run_artifacts)

    return SavedMealpySuiteArtifacts(
        suite_directory=suite_directory,
        summary_csv=summary_csv,
        summary_markdown=summary_markdown,
        run_artifacts=run_artifacts,
    )


def _format_value(value: float) -> str:
    text = f"{value:.3g}"
    return text.replace(".", "p")


def write_mealpy_history_csv(
    history_file: Path,
    history: list[MealpyGenerationStats],
) -> None:
    with history_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "epoch",
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
                    row.epoch,
                    f"{row.best_objective:.16g}",
                    f"{row.average_objective:.16g}"
                    if row.average_objective is not None
                    else "",
                    f"{row.std_objective:.16g}" if row.std_objective is not None else "",
                    f"{row.min_objective:.16g}" if row.min_objective is not None else "",
                    f"{row.max_objective:.16g}" if row.max_objective is not None else "",
                ]
            )


def write_mealpy_suite_csv(
    summary_file: Path,
    results: list[MealpyRunResult],
    artifacts: list[SavedMealpyRunArtifacts],
) -> None:
    with summary_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "algorithm",
                "pop_size",
                "epochs",
                "w",
                "c1",
                "c2",
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
                    result.config.algorithm,
                    result.config.pop_size,
                    result.config.epochs,
                    f"{result.config.w:.6g}",
                    f"{result.config.c1:.6g}",
                    f"{result.config.c2:.6g}",
                    f"{result.best_objective:.16g}",
                    f"{last.average_objective:.16g}"
                    if last and last.average_objective is not None
                    else "",
                    f"{last.std_objective:.16g}"
                    if last and last.std_objective is not None
                    else "",
                    artifact.run_directory.name,
                ]
            )


def write_mealpy_suite_markdown(
    summary_file: Path,
    results: list[MealpyRunResult],
    artifacts: list[SavedMealpyRunArtifacts],
) -> None:
    header = (
        "| # | algorithm | pop | epochs | w | c1 | c2 | best f(x) | "
        "avg last | std last | run |"
    )
    lines = [
        "# MealPy suite summary",
        "",
        header,
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]

    sorted_rows = sorted(
        zip(results, artifacts, strict=True),
        key=lambda item: item[0].best_objective,
    )
    for index, (result, artifact) in enumerate(sorted_rows, start=1):
        last = result.history[-1] if result.history else None
        average = (
            f"{last.average_objective:.6g}"
            if last and last.average_objective is not None
            else ""
        )
        std = (
            f"{last.std_objective:.6g}"
            if last and last.std_objective is not None
            else ""
        )
        lines.append(
            "| "
            f"{index} | "
            f"{result.config.algorithm} | "
            f"{result.config.pop_size} | "
            f"{result.config.epochs} | "
            f"{result.config.w:.3g} | "
            f"{result.config.c1:.3g} | "
            f"{result.config.c2:.3g} | "
            f"{result.best_objective:.6g} | "
            f"{average} | "
            f"{std} | "
            f"{artifact.run_directory.name} |"
        )

    summary_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_mealpy_history_svg(history: list[MealpyGenerationStats]) -> str:
    if not history:
        raise ValueError("history is empty")

    width = 960
    height = 540
    left = 88
    right = 32
    top = 60
    bottom = 72
    plot_width = width - left - right
    plot_height = height - top - bottom

    values = [row.best_objective for row in history]
    low = min(values)
    high = max(values)
    if math.isclose(low, high):
        padding = abs(low) * 0.05 or 1.0
    else:
        padding = (high - low) * 0.1
    low -= padding
    high += padding

    def x_pos(index: int) -> float:
        if len(values) == 1:
            return left + plot_width / 2
        return left + index * plot_width / (len(values) - 1)

    def y_pos(value: float) -> float:
        return top + (high - value) * plot_height / (high - low)

    points = " ".join(
        f"{x_pos(index):.2f},{y_pos(value):.2f}"
        for index, value in enumerate(values)
    )

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
    for index in sorted({0, len(values) // 2, len(values) - 1}):
        x = x_pos(index)
        epoch = history[index].epoch
        columns.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" '
            f'y2="{height - bottom}" stroke="#e6ebf0" stroke-width="1" />'
        )
        columns.append(
            f'<text x="{x:.2f}" y="{height - bottom + 24}" '
            f'text-anchor="middle" fill="#3d4955" font-size="12">{epoch}</text>'
        )

    last_x = x_pos(len(values) - 1)
    last_y = y_pos(values[-1])

    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff" />',
            f'<text x="{width / 2:.2f}" y="30" text-anchor="middle" '
            'font-size="24" fill="#1f2933">MealPy objective history</text>',
            f'<text x="{width / 2:.2f}" y="{height - 18}" text-anchor="middle" '
            'font-size="14" fill="#52606d">Epoch</text>',
            f'<text x="24" y="{height / 2:.2f}" text-anchor="middle" '
            f'font-size="14" fill="#52606d" '
            f'transform="rotate(-90 24 {height / 2:.2f})">Objective value</text>',
            *rows,
            *columns,
            f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" '
            f'y2="{height - bottom}" stroke="#52606d" stroke-width="2" />',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" '
            'stroke="#52606d" stroke-width="2" />',
            f'<polyline fill="none" stroke="#0b84f3" stroke-width="3" '
            f'points="{points}" />',
            f'<circle cx="{last_x:.2f}" cy="{last_y:.2f}" r="5" fill="#d94841" '
            'stroke="#ffffff" stroke-width="2" />',
            f'<text x="{last_x:.2f}" y="{last_y - 12:.2f}" text-anchor="middle" '
            f'font-size="12" fill="#7b341e">{values[-1]:.6g}</text>',
            "</svg>",
        ]
    )
