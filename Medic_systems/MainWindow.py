from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Main Window")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout(self)

        self.create_top_bar(layout)

        label = QLabel("Witaj w głównym oknie aplikacji!", self)
        layout.addWidget(label)

        self.setLayout(layout)

    def create_top_bar(self, layout):
        top_bar = QFrame(self)
        top_bar.setFrameShape(QFrame.StyledPanel)
        top_bar.setFrameShadow(QFrame.Raised)

        top_bar.setStyleSheet("background-color: #4CAF50;")

        top_bar.setFixedHeight(5)

        layout.addWidget(top_bar)
