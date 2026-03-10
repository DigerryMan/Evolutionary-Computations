"""Genetic Algorithm configuration and execution widget."""

from typing import Literal, cast

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QPushButton,
    QGroupBox,
    QPlainTextEdit,
    QScrollArea,
)
from PyQt6.QtCore import Qt

from registry import FunctionRegistry
from algorithms.genetic_algorithm import GAConfig, run_genetic_algorithm


class GAWidget(QWidget):
    """Widget for configuring and running the Genetic Algorithm."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._populate_function_combo()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area wraps configuration groups
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        # ── Objective function ─────────────────────────────────────────
        func_group = QGroupBox("Objective Function")
        func_layout = QFormLayout(func_group)

        self.func_combo = QComboBox()
        func_layout.addRow("Function:", self.func_combo)

        domain_row = QWidget()
        d_lay = QHBoxLayout(domain_row)
        d_lay.setContentsMargins(0, 0, 0, 0)
        self.a_spin = QDoubleSpinBox()
        self.a_spin.setRange(-1e9, 1e9)
        self.a_spin.setValue(-10.0)
        self.a_spin.setDecimals(4)
        self.b_spin = QDoubleSpinBox()
        self.b_spin.setRange(-1e9, 1e9)
        self.b_spin.setValue(10.0)
        self.b_spin.setDecimals(4)
        d_lay.addWidget(QLabel("a:"))
        d_lay.addWidget(self.a_spin)
        d_lay.addWidget(QLabel("b:"))
        d_lay.addWidget(self.b_spin)
        func_layout.addRow("Domain [a, b]:", domain_row)

        self.minimize_check = QCheckBox("Minimise (uncheck to maximise)")
        self.minimize_check.setChecked(True)
        func_layout.addRow("", self.minimize_check)

        layout.addWidget(func_group)

        # ── Population ────────────────────────────────────────────────
        pop_group = QGroupBox("Population & Encoding")
        pop_layout = QFormLayout(pop_group)

        self.pop_size_spin = QSpinBox()
        self.pop_size_spin.setRange(4, 10000)
        self.pop_size_spin.setValue(50)
        pop_layout.addRow("Population size:", self.pop_size_spin)

        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 100000)
        self.epochs_spin.setValue(100)
        pop_layout.addRow("Number of epochs:", self.epochs_spin)

        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(1, 10)
        self.precision_spin.setValue(6)
        self.precision_spin.setToolTip(
            "Decimal places — determines binary chromosome length"
        )
        pop_layout.addRow("Precision (decimal places):", self.precision_spin)

        layout.addWidget(pop_group)

        # ── Selection ─────────────────────────────────────────────────
        sel_group = QGroupBox("Selection")
        sel_layout = QFormLayout(sel_group)

        self.sel_combo = QComboBox()
        self.sel_combo.addItems(["tournament", "best", "roulette"])
        self.sel_combo.currentTextChanged.connect(self._on_selection_changed)
        sel_layout.addRow("Method:", self.sel_combo)

        self.tournament_label = QLabel("Tournament size:")
        self.tournament_spin = QSpinBox()
        self.tournament_spin.setRange(2, 100)
        self.tournament_spin.setValue(3)
        sel_layout.addRow(self.tournament_label, self.tournament_spin)

        layout.addWidget(sel_group)

        # ── Crossover ─────────────────────────────────────────────────
        cross_group = QGroupBox("Crossover")
        cross_layout = QFormLayout(cross_group)

        self.cross_combo = QComboBox()
        self.cross_combo.addItems(["single_point", "two_point", "uniform", "granular"])
        self.cross_combo.currentTextChanged.connect(self._on_crossover_changed)
        cross_layout.addRow("Method:", self.cross_combo)

        self.cross_prob_spin = QDoubleSpinBox()
        self.cross_prob_spin.setRange(0.0, 1.0)
        self.cross_prob_spin.setSingleStep(0.05)
        self.cross_prob_spin.setDecimals(3)
        self.cross_prob_spin.setValue(0.8)
        cross_layout.addRow("Probability:", self.cross_prob_spin)

        self.grain_label = QLabel("Grain size (bits):")
        self.grain_spin = QSpinBox()
        self.grain_spin.setRange(1, 100)
        self.grain_spin.setValue(2)
        self.grain_label.setVisible(False)
        self.grain_spin.setVisible(False)
        cross_layout.addRow(self.grain_label, self.grain_spin)

        layout.addWidget(cross_group)

        # ── Mutation ──────────────────────────────────────────────────
        mut_group = QGroupBox("Mutation")
        mut_layout = QFormLayout(mut_group)

        self.mut_combo = QComboBox()
        self.mut_combo.addItems(["single_point", "edge", "two_point"])
        mut_layout.addRow("Method:", self.mut_combo)

        self.mut_prob_spin = QDoubleSpinBox()
        self.mut_prob_spin.setRange(0.0, 1.0)
        self.mut_prob_spin.setSingleStep(0.005)
        self.mut_prob_spin.setDecimals(4)
        self.mut_prob_spin.setValue(0.01)
        mut_layout.addRow("Probability:", self.mut_prob_spin)

        layout.addWidget(mut_group)

        # ── Inversion & Elitism ───────────────────────────────────────
        adv_group = QGroupBox("Inversion & Elitism")
        adv_layout = QFormLayout(adv_group)

        self.inv_prob_spin = QDoubleSpinBox()
        self.inv_prob_spin.setRange(0.0, 1.0)
        self.inv_prob_spin.setSingleStep(0.01)
        self.inv_prob_spin.setDecimals(3)
        self.inv_prob_spin.setValue(0.05)
        adv_layout.addRow("Inversion probability:", self.inv_prob_spin)

        self.elite_spin = QSpinBox()
        self.elite_spin.setRange(0, 100)
        self.elite_spin.setValue(1)
        self.elite_spin.setToolTip("Number of best individuals carried unchanged to next epoch")
        adv_layout.addRow("Elite size:", self.elite_spin)

        layout.addWidget(adv_group)

        # ── Run button ────────────────────────────────────────────────
        self.run_button = QPushButton("Run Genetic Algorithm")
        self.run_button.setMinimumHeight(40)
        self.run_button.clicked.connect(self._on_run)
        layout.addWidget(self.run_button)

        # ── Results ───────────────────────────────────────────────────
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)

        self.result_text = QPlainTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(200)
        results_layout.addWidget(self.result_text)

        layout.addWidget(results_group)
        layout.addStretch()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _populate_function_combo(self):
        """Populate the dropdown with single-float-argument functions."""
        self._func_names: list[str] = []
        for name, meta in FunctionRegistry.get_all().items():
            params = [p for p in meta.parameters]
            if len(params) == 1 and params[0].param_type is float:
                self.func_combo.addItem(f"{name}  —  {meta.description}", userData=name)
                self._func_names.append(name)

    def _on_selection_changed(self, method: str):
        visible = method == "tournament"
        self.tournament_label.setVisible(visible)
        self.tournament_spin.setVisible(visible)

    def _on_crossover_changed(self, method: str):
        visible = method == "granular"
        self.grain_label.setVisible(visible)
        self.grain_spin.setVisible(visible)

    def _build_config(self) -> GAConfig:
        return GAConfig(
            a=self.a_spin.value(),
            b=self.b_spin.value(),
            precision=self.precision_spin.value(),
            population_size=self.pop_size_spin.value(),
            epochs=self.epochs_spin.value(),
            selection_method=cast(
                Literal["best", "roulette", "tournament"],
                self.sel_combo.currentText(),
            ),
            tournament_size=self.tournament_spin.value(),
            crossover_method=cast(
                Literal["single_point", "two_point", "uniform", "granular"],
                self.cross_combo.currentText(),
            ),
            crossover_prob=self.cross_prob_spin.value(),
            grain_size=self.grain_spin.value(),
            mutation_method=cast(
                Literal["edge", "single_point", "two_point"],
                self.mut_combo.currentText(),
            ),
            mutation_prob=self.mut_prob_spin.value(),
            inversion_prob=self.inv_prob_spin.value(),
            elite_size=self.elite_spin.value(),
            minimize=self.minimize_check.isChecked(),
        )

    # ── Run ───────────────────────────────────────────────────────────────────

    def _on_run(self):
        func_name: str | None = self.func_combo.currentData()
        if not func_name:
            self.result_text.setPlainText("No single-float function available.")
            return

        meta = FunctionRegistry.get(func_name)
        if meta is None:
            self.result_text.setPlainText(f"Function '{func_name}' not found in registry.")
            return

        param_name = meta.parameters[0].name

        def objective(x: float) -> float:
            _, result = FunctionRegistry.execute(func_name, **{param_name: x})
            return float(result)

        try:
            config = self._build_config()
        except Exception as exc:
            self.result_text.setPlainText(f"Configuration error: {exc}")
            return

        self.run_button.setEnabled(False)
        self.result_text.setPlainText("Running…")

        try:
            result = run_genetic_algorithm(objective, config)
        except Exception as exc:
            self.result_text.setPlainText(f"Error during GA execution:\n{exc}")
            return
        finally:
            self.run_button.setEnabled(True)

        prec = config.precision
        best_x = result.best_chromosome.decode()
        bits_str = "".join(map(str, result.best_chromosome.bits))
        direction = "min" if config.minimize else "max"

        lines = [
            f"Function  : {func_name}",
            f"Domain    : [{config.a}, {config.b}]",
            f"Goal      : {direction}imisation",
            f"Epochs    : {config.epochs}  |  Population: {config.population_size}",
            f"Chromosome: {result.best_chromosome.length} bits",
            "",
            f"Best x    = {best_x:.{prec}f}",
            f"Best f(x) = {result.best_fitness:.{prec}f}",
            f"Binary    : {bits_str}",
            "",
            "─── Fitness history (best per epoch) ───",
        ]

        history = result.history
        # Show at most 100 lines; sample evenly for long runs
        n = len(history)
        if n <= 100:
            indices = range(n)
        else:
            step = n / 100
            indices = [int(i * step) for i in range(100)]
            indices.append(n - 1)

        for i in indices:
            lines.append(f"  Epoch {i + 1:6d}: {history[i]:.{prec}f}")

        self.result_text.setPlainText("\n".join(lines))
