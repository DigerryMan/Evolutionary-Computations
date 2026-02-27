"""Function list widget - displays available functions."""

from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import pyqtSignal

from registry import FunctionRegistry, FunctionMetadata


class FunctionListWidget(QListWidget):
    """Widget displaying a list of available functions."""

    function_selected = pyqtSignal(FunctionMetadata)

    def __init__(self, parent=None):
        """Initialize the function list widget."""
        super().__init__(parent)
        self.functions: dict[str, FunctionMetadata] = self._load_functions()
        self.itemClicked.connect(self._on_function_selected)

    def _load_functions(self) -> dict[str, FunctionMetadata]:
        """Load all functions from registry into the list."""
        self.functions = FunctionRegistry.get_all()

        # Sort by function name for consistent display
        for func_name in sorted(self.functions.keys()):
            metadata = self.functions[func_name]
            # Display: function_name - description
            display_text = f"{metadata.func_name}"
            if metadata.description:
                display_text += f" - {metadata.description}"

            item = QListWidgetItem(display_text)
            item.setData(256, func_name)  # Store function name in item data
            self.addItem(item)

        return self.functions

    def _on_function_selected(self, item: QListWidgetItem):
        """Handle function selection."""
        func_name = item.data(256)
        metadata = self.functions.get(func_name)
        if metadata:
            self.function_selected.emit(metadata)

    def get_selected_function(self) -> FunctionMetadata | None:
        """Get the currently selected function metadata."""
        current_item = self.currentItem()
        if current_item:
            func_name = current_item.data(256)
            return self.functions.get(func_name)
        return None
