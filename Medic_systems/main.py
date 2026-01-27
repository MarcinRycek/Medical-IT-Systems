from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
import sys
from LoginWindow import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setFont(QFont("Segoe UI", 10))

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())