import csv
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from algorithms.genetic_algorithm import GAConfig, GAResult


@dataclass
class SavedRunArtifacts:
    run_directory: Path
    summary_file: Path
    history_file: Path
    plot_file: Path


def save_hypersphere_run(
    config: GAConfig,
    result: GAResult,
    elapsed_seconds: float,
    root_dir: Path | None = None,
) -> SavedRunArtifacts:
    results_root = get_results_root(root_dir)
    run_name = datetime.now().strftime("hypersphere_%Y%m%d_%H%M%S_%f")
    run_directory = results_root / run_name
    run_directory.mkdir(parents=True, exist_ok=False)

    summary_file = run_directory / "summary.json"
    history_file = run_directory / "history.csv"
    plot_file = run_directory / "fitness_history.svg"

    summary = {
        "function": "Hypersphere",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": elapsed_seconds,
        "config": asdict(config),
        "result": {
            "best_fitness": result.best_fitness,
            "best_vector": result.best_chromosome.decode(),
            "best_bits": "".join(str(bit) for bit in result.best_chromosome.bits),
            "bits_per_dimension": result.best_chromosome.bits_per_dimension,
            "total_bits": result.best_chromosome.length,
        },
        "artifacts": {
            "summary": summary_file.name,
            "history_csv": history_file.name,
            "fitness_plot_svg": plot_file.name,
        },
    }

    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_history_csv(history_file, result.history)
    generate_history_plot_from_csv(history_file, plot_file)

    return SavedRunArtifacts(run_directory, summary_file, history_file, plot_file)


def generate_history_plot_from_csv(history_file: Path, output_file: Path) -> None:
    history: list[float] = []

    with history_file.open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            history.append(float(row["best_fitness"]))

    output_file.write_text(build_history_svg(history), encoding="utf-8")


def get_results_root(root_dir: Path | None = None) -> Path:
    if root_dir is not None:
        results_root = root_dir
    else:
        results_root = Path(__file__).resolve().parents[2] / "results"

    results_root.mkdir(parents=True, exist_ok=True)
    return results_root


def write_history_csv(history_file: Path, history: list[float]) -> None:
    with history_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["epoch", "best_fitness"])
        for epoch, fitness in enumerate(history, start=1):
            writer.writerow([epoch, f"{fitness:.16g}"])


def build_history_svg(history: list[float]) -> str:
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

    low = min(history)
    high = max(history)
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

    points = " ".join(
        f"{x_pos(index):.2f},{y_pos(value):.2f}" for index, value in enumerate(history)
    )

    rows: list[str] = []
    for tick in range(6):
        ratio = tick / 5
        y = top + ratio * plot_height
        label = high - ratio * (high - low)
        rows.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" y2="{y:.2f}" '
            'stroke="#d0d7de" stroke-width="1" />'
        )
        rows.append(
            f'<text x="{left - 12}" y="{y + 4:.2f}" text-anchor="end" '
            f'fill="#3d4955" font-size="12">{label:.6g}</text>'
        )

    columns: list[str] = []
    for index in sorted({0, len(history) // 2, len(history) - 1}):
        x = x_pos(index)
        columns.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{height - bottom}" '
            'stroke="#e6ebf0" stroke-width="1" />'
        )
        columns.append(
            f'<text x="{x:.2f}" y="{height - bottom + 24}" text-anchor="middle" '
            f'fill="#3d4955" font-size="12">{index + 1}</text>'
        )

    last_x = x_pos(len(history) - 1)
    last_y = y_pos(history[-1])

    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff" />',
            f'<text x="{width / 2:.2f}" y="30" text-anchor="middle" font-size="24" fill="#1f2933">Hypersphere fitness history</text>',
            f'<text x="{width / 2:.2f}" y="{height - 18}" text-anchor="middle" font-size="14" fill="#52606d">Epoch</text>',
            f'<text x="24" y="{height / 2:.2f}" text-anchor="middle" font-size="14" fill="#52606d" transform="rotate(-90 24 {height / 2:.2f})">Best fitness</text>',
            *rows,
            *columns,
            f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#52606d" stroke-width="2" />',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#52606d" stroke-width="2" />',
            f'<polyline fill="none" stroke="#0b84f3" stroke-width="3" points="{points}" />',
            f'<circle cx="{last_x:.2f}" cy="{last_y:.2f}" r="5" fill="#d94841" stroke="#ffffff" stroke-width="2" />',
            f'<text x="{last_x:.2f}" y="{last_y - 12:.2f}" text-anchor="middle" font-size="12" fill="#7b341e">{history[-1]:.6g}</text>',
            "</svg>",
        ]
    )
