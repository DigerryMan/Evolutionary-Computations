"""Main entry point for the evolutionary computations GUI."""

import sys
from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow

# Import functions to trigger registration via decorators
from functions.builtin_functions import *  # noqa: F401, F403


def main():
    """Run the main application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
