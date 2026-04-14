from PyQt6.QtWidgets import QMainWindow

from gui.widgets.ga_widget import GAWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Evolutionary Computations - Hypersphere")
        self.setGeometry(100, 100, 1200, 700)
        self.ga_widget = GAWidget()
        self.setCentralWidget(self.ga_widget)
