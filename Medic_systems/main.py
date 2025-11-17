from PySide6.QtWidgets import QApplication
import sys
from LoginWindow import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = LoginWindow()
    window.show()

    app.exec()
