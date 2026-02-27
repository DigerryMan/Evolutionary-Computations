"""Output display widget - shows execution results or errors."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPlainTextEdit
import json


class OutputDisplayWidget(QWidget):
    """Widget for displaying function execution results."""

    def __init__(self, parent=None):
        """Initialize the output display widget."""
        super().__init__(parent)

        # Setup layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title label
        self.title_label = QLabel("Result:")
        layout.addWidget(self.title_label)

        # Output text area
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(100)
        layout.addWidget(self.output_text)

        # Set default styling
        self.clear_output()

    def display_result(self, success: bool, value=None):
        """Display the result of function execution.

        Args:
            success: Whether the function executed successfully
            value: The return value or error message
        """
        if success:
            self._display_value(value)
        else:
            self._display_error(str(value))

    def _display_value(self, value):
        """Display a successful return value."""
        self.title_label.setText("Result:")
        self.title_label.setStyleSheet("color: green; font-weight: bold;")
        self.output_text.setStyleSheet("background-color: #e8f5e9;")

        # Format value based on type
        if isinstance(value, bool):
            display_str = "True" if value else "False"
        elif isinstance(value, (int, float)):
            display_str = str(value)
        elif isinstance(value, str):
            display_str = value
        elif isinstance(value, list):
            display_str = self._format_list(value)
        elif isinstance(value, dict):
            display_str = json.dumps(value, indent=2)
        else:
            display_str = repr(value)

        self.output_text.setPlainText(display_str)

    def _display_error(self, error_msg: str):
        """Display an error message."""
        self.title_label.setText("Error:")
        self.title_label.setStyleSheet("color: red; font-weight: bold;")
        self.output_text.setStyleSheet("background-color: #ffebee;")
        self.output_text.setPlainText(error_msg)

    def _format_list(self, lst: list) -> str:
        """Format a list for display."""
        if not lst:
            return "[]"

        # Check if all elements are simple types
        if all(isinstance(x, (int, float, str, bool)) for x in lst):
            return "[\n" + "\n".join(f"  {repr(x)}" for x in lst) + "\n]"
        else:
            return json.dumps(lst, indent=2)

    def clear_output(self):
        """Clear the output display."""
        self.title_label.setText("Result:")
        self.title_label.setStyleSheet("color: gray;")
        self.output_text.setStyleSheet("background-color: #f5f5f5;")
        self.output_text.setPlainText(
            "(Select a function and click Execute to see results)"
        )
