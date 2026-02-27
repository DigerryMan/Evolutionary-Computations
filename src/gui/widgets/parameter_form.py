"""Parameter form widget - dynamically generates input fields."""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QPushButton,
    QFormLayout,
)
from PyQt6.QtCore import pyqtSignal

from registry import FunctionMetadata, ParameterInfo


class ParameterFormWidget(QWidget):
    """Widget for dynamically generating function parameter input forms."""

    execute_requested = pyqtSignal(dict)  # Emits {param_name: value}

    def __init__(self, parent=None):
        """Initialize the parameter form widget."""
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Form area
        self.form_layout = QFormLayout()
        layout.addLayout(self.form_layout)

        # Execute button
        self.execute_button = QPushButton("Execute")
        self.execute_button.clicked.connect(self._on_execute_clicked)
        self.execute_button.setMinimumHeight(40)
        layout.addWidget(self.execute_button)

        # Storage for current form widgets
        self.input_widgets: dict[str, tuple[ParameterInfo, QWidget]] = {}
        self.current_metadata: FunctionMetadata | None = None

        # Add some vertical space at the end
        layout.addStretch()

    def prep_function_form(self, metadata: FunctionMetadata):
        print(
            f"Loading function: {metadata.func_name} with parameters: {metadata.parameters}"
        )
        self.current_metadata = metadata
        self._clear_form()

        # Title
        title = QLabel(f"Parameters for: {metadata.func_name}")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.form_layout.addRow(title)

        if not metadata.parameters:
            self.form_layout.addRow(QLabel("(No parameters)"))
            return

        for param in metadata.parameters:
            label_text = param.name
            if not param.is_optional:
                label_text += " *"  # Mark required parameters

            label = QLabel(label_text)
            widget = self._create_widget_for_parameter(param)

            self.input_widgets[param.name] = (param, widget)
            self.form_layout.addRow(label, widget)

    def _create_widget_for_parameter(self, param: ParameterInfo) -> QWidget:
        """Create appropriate input widget based on parameter type."""
        if param.param_type is int:
            widget = QSpinBox()
            widget.setMinimum(-2147483648)
            widget.setMaximum(2147483647)
            if param.is_optional and param.default_value is not None:
                widget.setValue(param.default_value)
            return widget

        elif param.param_type is float:
            widget = QDoubleSpinBox()
            widget.setMinimum(-1e9)
            widget.setMaximum(1e9)
            widget.setDecimals(6)
            if param.is_optional and param.default_value is not None:
                widget.setValue(param.default_value)
            return widget

        elif param.param_type is bool:
            widget = QCheckBox()
            if param.is_optional and param.default_value is not None:
                widget.setChecked(param.default_value)
            return widget

        else:  # str or other types - use QLineEdit
            widget = QLineEdit()
            if param.is_optional and param.default_value is not None:
                widget.setText(str(param.default_value))
            elif param.param_type is str:
                widget.setPlaceholderText("Enter text...")
            return widget

    def get_values(self) -> dict:
        """Collect and validate values from form input.

        Returns:
            Dictionary of parameter names to values
        """
        values = {}

        for param_name, (param, widget) in self.input_widgets.items():
            print(
                f"Collecting value for parameter: {param_name} of type {param.param_type}"
            )
            try:
                if isinstance(widget, QSpinBox):
                    values[param_name] = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    values[param_name] = widget.value()
                elif isinstance(widget, QCheckBox):
                    values[param_name] = widget.isChecked()
                elif isinstance(widget, QLineEdit):
                    values[param_name] = widget.text()
                else:
                    raise NotImplementedError(
                        f"Unsupported widget type for parameter: {param_name}"
                    )
            except Exception as e:
                print(
                    f"Error occured while collecting value for parameter {param_name}: {e}"
                )
                raise ValueError(f"Error reading value for {param_name}: {e}")

        return values

    def _on_execute_clicked(self):
        """Handle execute button click."""
        print("Execute clicked")
        if not self.current_metadata:
            print("No function metadata available.")
            return

        try:
            values = self.get_values()
            self.execute_requested.emit(values)
        except ValueError as e:
            print(f"Validation error: {e}")

    def _clear_form(self):
        """Clear all form fields."""
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        self.input_widgets.clear()
