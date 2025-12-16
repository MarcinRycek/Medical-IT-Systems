import psycopg2
import bcrypt
from PySide6.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QListWidget, QMessageBox
from PySide6.QtGui import QColor, QPalette, qRgb
import sys

conn_str = "postgresql://neondb_owner:npg_yKUJZNj2ShD0@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech/logowanie_db?sslmode=require&channel_binding=require"

class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MedEX-POL Rejestracja")
        self.set_palette()

        self.pesel_box_register = QLineEdit('', self)
        self.pesel_box_register.setPlaceholderText("Pesel")
        self.login_box_register = QLineEdit('', self)
        self.login_box_register.setPlaceholderText("Login")
        self.password_box_register = QLineEdit('', self)
        self.password_box_register.setPlaceholderText("Hasło")
        self.password_box_register.setEchoMode(QLineEdit.Password)

        self.role_box = QListWidget(self)
        self.role_box.addItem("Pacjent")
        self.role_box.addItem("Lekarz")
        self.role_box.addItem("Laborant")

        Register_button_2 = QPushButton("Zarejestruj się", self)
        Register_button_2.clicked.connect(self.register_user)

        Back_button = QPushButton("Wróć", self)
        Back_button.clicked.connect(self.show_login)

        self.pesel_box_register.setFixedWidth(200)
        self.login_box_register.setFixedWidth(200)
        self.password_box_register.setFixedWidth(200)
        Register_button_2.setFixedWidth(200)
        Back_button.setFixedWidth(200)

        layout_register = QVBoxLayout(self)

        layout_register.addWidget(self.pesel_box_register)
        layout_register.addWidget(self.login_box_register)
        layout_register.addWidget(self.password_box_register)
        layout_register.addWidget(self.role_box)
        layout_register.addWidget(Register_button_2)
        layout_register.addWidget(Back_button)

        layout_register.setStretch(0, 0)
        layout_register.setStretch(1, 0)
        layout_register.setStretch(2, 0)
        layout_register.setStretch(3, 0)
        layout_register.setStretch(4, 0)
        layout_register.setStretch(5, 0)

        self.setLayout(layout_register)

        self.setFixedSize(220, 200)

    def set_palette(self):
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(qRgb(172, 248, 122)))
        self.setPalette(palette)

    def show_login(self):
        from LoginWindow import LoginWindow
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def register_user(self):
        pesel = self.pesel_box_register.text()
        login = self.login_box_register.text()
        password = self.password_box_register.text()
        role = self.role_box.currentItem().text()

        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM users WHERE login = %s", (login,))
            if cursor.fetchone():
                self.show_error_popup("Taki login już istnieje!")
                return

            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            cursor.execute(
                "INSERT INTO users (id, login, password, role) VALUES (%s, %s, %s, %s)",
                (pesel, login, hashed, role)
            )

            conn.commit()

            self.login_user(login, password)

        except Exception as e:
            self.show_error_popup(f"Błąd podczas rejestracji: {e}")

        finally:
            if 'conn' in locals():
                cursor.close()
                conn.close()

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

    def show_success_popup(self, message):
        QMessageBox.information(self, "Sukces", message, QMessageBox.Ok)

    def show_error_popup(self, message):
        QMessageBox.critical(self, "Błąd", message, QMessageBox.Ok)

    def open_main_window(self, user_id):
        from MainWindow import MainWindow
        self.close()
        self.main_window = MainWindow(user_id)
        self.main_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = RegisterWindow()
    window.show()

    app.exec()
