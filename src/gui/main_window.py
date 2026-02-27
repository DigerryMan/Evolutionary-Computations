"""Main application window."""

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel

from registry import FunctionRegistry
from gui.widgets import FunctionListWidget, ParameterFormWidget, OutputDisplayWidget


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        self.setWindowTitle("Function Registry GUI")
        self.setGeometry(100, 100, 1200, 700)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Left panel: Function list
        left_layout = QVBoxLayout()
        list_title = QLabel("Available Functions:")
        list_title.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_title)

        self.function_list = FunctionListWidget()
        left_layout.addWidget(self.function_list)

        left_panel = QWidget()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(400)

        # Right panel: Parameters and output
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        # Parameter form section
        form_title = QLabel("Function Parameters:")
        form_title.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(form_title)

        self.parameter_form = ParameterFormWidget()
        right_layout.addWidget(self.parameter_form)

        # Output display section
        output_title = QLabel("Execution Result:")
        output_title.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(output_title)

        self.output_display = OutputDisplayWidget()
        right_layout.addWidget(self.output_display)

        right_panel = QWidget()
        right_panel.setLayout(right_layout)

        # Add panels to main layout
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)

        # Connect signals
        self._connect_signals()

        # Load first function if available
        if self.function_list.count() > 0:
            self.function_list.setCurrentRow(0)

    def _connect_signals(self):
        """Connect widget signals to slots."""
        # When a function is selected, load its parameters
        self.function_list.function_selected.connect(self._on_function_selected)

        # When execute is requested, run the function
        self.parameter_form.execute_requested.connect(self._on_execute_requested)

    def _on_function_selected(self, metadata):
        self.parameter_form.prep_function_form(metadata)
        self.output_display.clear_output()

    def _on_execute_requested(self, parameter_values):
        """Handle execute request with collected parameters."""
        metadata = self.parameter_form.current_metadata
        if not metadata:
            return

        # Execute the function through the registry
        success, result = FunctionRegistry.execute(
            metadata.func_name, **parameter_values
        )

        # Display the result
        self.output_display.display_result(success, result)
