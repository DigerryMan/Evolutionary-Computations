from pathlib import Path
from time import perf_counter

import benchmark_functions as bf
from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from algorithms.genetic_algorithm import GAConfig, run_genetic_algorithm
from reporting import save_hypersphere_run


class GAWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_root = Path(__file__).resolve().parents[3]
        self.results_root = self.project_root / "results"
        self.empty_svg = QByteArray(
            b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>'
        )
        self.build_ui()
        self.set_defaults()
        self.show_last_plot()

    def build_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer_layout.addWidget(scroll)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        scroll.setWidget(container)

        function_group = QGroupBox("Objective Function")
        function_layout = QFormLayout(function_group)

        self.function_label = QLabel("Hypersphere")
        function_layout.addRow("Function:", self.function_label)

        self.description_label = QLabel("f(x) = x1^2 + x2^2 + ... + xn^2")
        self.description_label.setWordWrap(True)
        function_layout.addRow("Definition:", self.description_label)

        self.dimensions_spin = QSpinBox()
        self.dimensions_spin.setRange(1, 100)
        self.dimensions_spin.setValue(3)
        function_layout.addRow("Dimensions:", self.dimensions_spin)

        domain_row = QWidget()
        domain_layout = QHBoxLayout(domain_row)
        domain_layout.setContentsMargins(0, 0, 0, 0)

        self.a_spin = QDoubleSpinBox()
        self.a_spin.setRange(-1e9, 1e9)
        self.a_spin.setDecimals(4)
        domain_layout.addWidget(QLabel("a:"))
        domain_layout.addWidget(self.a_spin)

        self.b_spin = QDoubleSpinBox()
        self.b_spin.setRange(-1e9, 1e9)
        self.b_spin.setDecimals(4)
        domain_layout.addWidget(QLabel("b:"))
        domain_layout.addWidget(self.b_spin)

        function_layout.addRow("Shared domain [a, b]:", domain_row)

        self.minimize_check = QCheckBox("Minimise")
        self.minimize_check.setChecked(True)
        function_layout.addRow("", self.minimize_check)

        layout.addWidget(function_group)

        population_group = QGroupBox("Population")
        population_layout = QFormLayout(population_group)

        self.pop_size_spin = QSpinBox()
        self.pop_size_spin.setRange(4, 10000)
        self.pop_size_spin.setValue(50)
        population_layout.addRow("Population size:", self.pop_size_spin)

        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 100000)
        self.epochs_spin.setValue(100)
        population_layout.addRow("Epochs:", self.epochs_spin)

        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(1, 10)
        self.precision_spin.setValue(6)
        population_layout.addRow("Precision:", self.precision_spin)

        layout.addWidget(population_group)

        selection_group = QGroupBox("Selection")
        selection_layout = QFormLayout(selection_group)

        self.sel_combo = QComboBox()
        self.sel_combo.addItems(["tournament", "best", "roulette"])
        self.sel_combo.currentTextChanged.connect(self.on_selection_changed)
        selection_layout.addRow("Method:", self.sel_combo)

        self.tournament_label = QLabel("Tournament size:")
        self.tournament_spin = QSpinBox()
        self.tournament_spin.setRange(2, 100)
        self.tournament_spin.setValue(3)
        selection_layout.addRow(self.tournament_label, self.tournament_spin)

        layout.addWidget(selection_group)

        crossover_group = QGroupBox("Crossover")
        crossover_layout = QFormLayout(crossover_group)

        self.cross_combo = QComboBox()
        self.cross_combo.addItems(["single_point", "two_point", "uniform", "granular"])
        self.cross_combo.currentTextChanged.connect(self.on_crossover_changed)
        crossover_layout.addRow("Method:", self.cross_combo)

        self.cross_prob_spin = QDoubleSpinBox()
        self.cross_prob_spin.setRange(0.0, 1.0)
        self.cross_prob_spin.setSingleStep(0.05)
        self.cross_prob_spin.setDecimals(3)
        self.cross_prob_spin.setValue(0.8)
        crossover_layout.addRow("Probability:", self.cross_prob_spin)

        self.grain_label = QLabel("Grain size:")
        self.grain_spin = QSpinBox()
        self.grain_spin.setRange(1, 100)
        self.grain_spin.setValue(2)
        crossover_layout.addRow(self.grain_label, self.grain_spin)

        layout.addWidget(crossover_group)

        mutation_group = QGroupBox("Mutation")
        mutation_layout = QFormLayout(mutation_group)

        self.mut_combo = QComboBox()
        self.mut_combo.addItems(["single_point", "edge", "two_point"])
        mutation_layout.addRow("Method:", self.mut_combo)

        self.mut_prob_spin = QDoubleSpinBox()
        self.mut_prob_spin.setRange(0.0, 1.0)
        self.mut_prob_spin.setSingleStep(0.005)
        self.mut_prob_spin.setDecimals(4)
        self.mut_prob_spin.setValue(0.01)
        mutation_layout.addRow("Probability:", self.mut_prob_spin)

        layout.addWidget(mutation_group)

        other_group = QGroupBox("Other")
        other_layout = QFormLayout(other_group)

        self.inv_prob_spin = QDoubleSpinBox()
        self.inv_prob_spin.setRange(0.0, 1.0)
        self.inv_prob_spin.setSingleStep(0.01)
        self.inv_prob_spin.setDecimals(3)
        self.inv_prob_spin.setValue(0.05)
        other_layout.addRow("Inversion probability:", self.inv_prob_spin)

        self.elite_spin = QSpinBox()
        self.elite_spin.setRange(0, 100)
        self.elite_spin.setValue(1)
        other_layout.addRow("Elite size:", self.elite_spin)

        layout.addWidget(other_group)

        self.run_button = QPushButton("Run Genetic Algorithm")
        self.run_button.setMinimumHeight(40)
        self.run_button.setStyleSheet(
            """
            QPushButton {
                background-color: #b7f7a8;
                color: #103c12;
                border: 1px solid #7bc96f;
                border-radius: 8px;
                font-weight: 600;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #a7ef97;
            }
            QPushButton:pressed {
                background-color: #95df84;
            }
            QPushButton:disabled {
                background-color: #d7efd0;
                color: #6f8a6f;
                border: 1px solid #c4dec0;
            }
            """
        )
        self.run_button.clicked.connect(self.run_algorithm)
        layout.addWidget(self.run_button)

        result_group = QGroupBox("Results")
        result_layout = QVBoxLayout(result_group)

        self.result_text = QPlainTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(220)
        result_layout.addWidget(self.result_text)

        layout.addWidget(result_group)

        plot_group = QGroupBox("Plot Preview")
        plot_layout = QVBoxLayout(plot_group)

        self.plot_status = QLabel()
        self.plot_status.setWordWrap(True)
        plot_layout.addWidget(self.plot_status)

        self.plot_widget = QSvgWidget()
        self.plot_widget.setMinimumHeight(360)
        self.plot_widget.setStyleSheet(
            "background-color: white; border: 1px solid #d0d7de;"
        )
        plot_layout.addWidget(self.plot_widget)

        layout.addWidget(plot_group)
        layout.addStretch()

    def set_defaults(self):
        bounds = bf.Hypersphere(n_dimensions=1).suggested_bounds()
        self.a_spin.setValue(bounds[0][0])
        self.b_spin.setValue(bounds[1][0])
        self.result_text.setPlainText("Ready to optimise the Hypersphere function.")
        self.on_selection_changed(self.sel_combo.currentText())
        self.on_crossover_changed(self.cross_combo.currentText())

    def on_selection_changed(self, method: str):
        visible = method == "tournament"
        self.tournament_label.setVisible(visible)
        self.tournament_spin.setVisible(visible)

    def on_crossover_changed(self, method: str):
        visible = method == "granular"
        self.grain_label.setVisible(visible)
        self.grain_spin.setVisible(visible)

    def make_config(self) -> GAConfig:
        return GAConfig(
            a=self.a_spin.value(),
            b=self.b_spin.value(),
            dimensions=self.dimensions_spin.value(),
            precision=self.precision_spin.value(),
            population_size=self.pop_size_spin.value(),
            epochs=self.epochs_spin.value(),
            selection_method=self.sel_combo.currentText(),
            tournament_size=self.tournament_spin.value(),
            crossover_method=self.cross_combo.currentText(),
            crossover_prob=self.cross_prob_spin.value(),
            grain_size=self.grain_spin.value(),
            mutation_method=self.mut_combo.currentText(),
            mutation_prob=self.mut_prob_spin.value(),
            inversion_prob=self.inv_prob_spin.value(),
            elite_size=self.elite_spin.value(),
            minimize=self.minimize_check.isChecked(),
        )

    def format_vector(self, values: list[float], precision: int) -> str:
        return "[" + ", ".join(f"{value:.{precision}f}" for value in values) + "]"

    def relative_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.project_root))
        except ValueError:
            return str(path)

    def clear_plot(self, text: str):
        self.plot_widget.load(self.empty_svg)
        self.plot_status.setText(text)

    def show_plot(self, path: Path):
        self.plot_widget.load(str(path))
        self.plot_status.setText(f"Previewing: {self.relative_path(path)}")

    def show_last_plot(self):
        if not self.results_root.exists():
            self.clear_plot("No saved plots yet.")
            return

        plots = sorted(self.results_root.glob("hypersphere_*/fitness_history.svg"))
        if not plots:
            self.clear_plot("No saved plots yet.")
            return

        self.show_plot(plots[-1])

    def reference_point(self, config: GAConfig) -> tuple[list[float], float]:
        if config.minimize:
            if config.a <= 0 <= config.b:
                value = 0.0
            else:
                value = config.a if abs(config.a) <= abs(config.b) else config.b
        else:
            value = config.a if abs(config.a) >= abs(config.b) else config.b

        point = [value] * config.dimensions
        fitness = sum(item * item for item in point)
        return point, fitness

    def run_algorithm(self):
        try:
            config = self.make_config()
        except Exception as error:
            self.result_text.setPlainText(f"Configuration error: {error}")
            return

        hypersphere = bf.Hypersphere(n_dimensions=config.dimensions)

        def objective(vector: list[float]) -> float:
            return float(hypersphere(vector))

        self.run_button.setEnabled(False)
        self.result_text.setPlainText("Running...")

        try:
            start = perf_counter()
            result = run_genetic_algorithm(objective, config)
            elapsed = perf_counter() - start
        except Exception as error:
            self.result_text.setPlainText(f"Error during GA execution:\n{error}")
            self.run_button.setEnabled(True)
            return

        self.run_button.setEnabled(True)

        best_vector = result.best_chromosome.decode()
        best_bits = "".join(str(bit) for bit in result.best_chromosome.bits)
        precision = config.precision
        target = "minimisation" if config.minimize else "maximisation"
        reference_point, reference_value = self.reference_point(config)

        artifacts = None
        save_error = None
        try:
            artifacts = save_hypersphere_run(config, result, elapsed)
        except Exception as error:
            save_error = str(error)

        lines = [
            f"Function  : {hypersphere.name()}",
            f"Formula   : f(x) = sum(x_i^2), i = 1..{config.dimensions}",
            f"Domain    : [{config.a}, {config.b}] for each dimension",
            f"Goal      : {target}",
            f"Epochs    : {config.epochs}  |  Population: {config.population_size}",
            (
                "Genome    : "
                f"{result.best_chromosome.bits_per_dimension} bits/dimension"
                f"  |  {result.best_chromosome.length} total bits"
            ),
            f"Time      : {elapsed:.6f} s",
            "",
            f"Best x    = {self.format_vector(best_vector, precision)}",
            f"Best f(x) = {result.best_fitness:.{precision}f}",
            (
                "Reference = "
                f"{reference_value:.{precision}f} at "
                f"{self.format_vector(reference_point, precision)}"
            ),
            f"Binary    : {best_bits}",
            "",
            "Saved artifacts",
        ]

        if artifacts is None:
            self.plot_status.setText(f"Plot preview unavailable: {save_error}")
            lines.append(f"Save error : {save_error}")
        else:
            self.show_plot(artifacts.plot_file)
            lines.extend(
                [
                    f"Run dir   : {self.relative_path(artifacts.run_directory)}",
                    f"Summary   : {self.relative_path(artifacts.summary_file)}",
                    f"History   : {self.relative_path(artifacts.history_file)}",
                    f"Plot      : {self.relative_path(artifacts.plot_file)}",
                ]
            )

        lines.append("")
        lines.append("Fitness history (best per epoch)")

        history = result.history
        if len(history) <= 100:
            indexes = range(len(history))
        else:
            step = len(history) / 100
            indexes = [int(i * step) for i in range(100)] + [len(history) - 1]

        for i in indexes:
            lines.append(f"  Epoch {i + 1:6d}: {history[i]:.{precision}f}")

        self.result_text.setPlainText("\n".join(lines))
