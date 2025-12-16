import psycopg2
import bcrypt
from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from PySide6.QtGui import QColor, QPalette, qRgb

conn_str = "postgresql://neondb_owner:npg_yKUJZNj2ShD0@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech/logowanie_db?sslmode=require&channel_binding=require"


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MedEX-POL Logowanie")
        self.set_palette()

        self.login_box = QLineEdit('', self)
        self.login_box.setPlaceholderText("Login")
        self.password_box = QLineEdit('', self)
        self.password_box.setPlaceholderText("Hasło")
        self.password_box.setEchoMode(QLineEdit.Password)

        Login_button = QPushButton("Zaloguj się", self)
        Login_button.clicked.connect(self.login_user)

        Register_button = QPushButton("Zarejestruj się", self)
        Register_button.clicked.connect(self.show_register)

        self.login_box.setFixedWidth(200)
        self.password_box.setFixedWidth(200)
        Login_button.setFixedWidth(200)
        Register_button.setFixedWidth(200)

        layout_login = QVBoxLayout(self)
        layout_login.addWidget(self.login_box)
        layout_login.addWidget(self.password_box)
        layout_login.addWidget(Login_button)
        layout_login.addWidget(Register_button)

        layout_login.setStretch(0, 0)
        layout_login.setStretch(1, 0)
        layout_login.setStretch(2, 0)
        layout_login.setStretch(3, 0)

        self.setLayout(layout_login)

        self.setFixedSize(230, 170)

    def set_palette(self):
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(qRgb(172, 248, 122)))
        self.setPalette(palette)

    def show_register(self):
        from RegisterWindow import RegisterWindow
        self.close()
        self.register_window = RegisterWindow()
        self.register_window.show()

    def login_user(self):
        try:
            self.conn = psycopg2.connect(conn_str)
            cursor = self.conn.cursor()

            cursor.execute("SELECT id, password, role FROM users WHERE login = %s", (self.login_box.text(),))
            result = cursor.fetchone()

            if result is None:
                self.show_error_popup("Nie znaleziono takiego użytkownika.")
                return

            user_id, password_hash, role = result

            if bcrypt.checkpw(self.password_box.text().encode("utf-8"), password_hash.encode("utf-8")):
                self.show_success_popup()
                self.open_main_window(user_id)
            else:
                self.show_error_popup("Niepoprawne hasło.")

        except Exception as e:
            self.show_error_popup(f"Błąd połączenia lub logowania: {e}")

        finally:
            if 'conn' in locals():
                cursor.close()
                self.conn.close()

    def show_success_popup(self):
        QMessageBox.information(self, "Zalogowano Pomyślnie!", f"Dzień dobry, {self.login_box.text()}!", QMessageBox.Ok)

    def show_error_popup(self, message):
        QMessageBox.critical(self, "Błąd", message, QMessageBox.Ok)

    def open_main_window(self,user_id):
        from MainWindow import MainWindow
        self.close()
        self.main_window = MainWindow(user_id)
        self.main_window.show()