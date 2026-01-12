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

        self.login_box = QLineEdit(self)
        self.login_box.setPlaceholderText("Login")
        self.password_box = QLineEdit(self)
        self.password_box.setPlaceholderText("Hasło")
        self.password_box.setEchoMode(QLineEdit.Password)

        btn_login = QPushButton("Zaloguj się", self)
        btn_login.clicked.connect(self.login_user)

        btn_reg = QPushButton("Zarejestruj się", self)
        btn_reg.clicked.connect(self.show_register)

        # Layout (skrócony dla czytelności)
        layout = QVBoxLayout(self)
        layout.addWidget(self.login_box)
        layout.addWidget(self.password_box)
        layout.addWidget(btn_login)
        layout.addWidget(btn_reg)
        self.setFixedSize(230, 170)

    def set_palette(self):
        p = self.palette()
        p.setColor(QPalette.ColorRole.Window, QColor(qRgb(172, 248, 122)))
        self.setPalette(p)

    def show_register(self):
        from RegisterWindow import RegisterWindow
        self.close()
        self.reg = RegisterWindow()
        self.reg.show()

    def login_user(self):
        try:
            conn = psycopg2.connect(conn_str)
            cur = conn.cursor()
            cur.execute("SELECT id, password, role FROM users WHERE login = %s", (self.login_box.text(),))
            res = cur.fetchone()
            conn.close()

            if not res:
                QMessageBox.critical(self, "Błąd", "Brak użytkownika.")
                return

            uid, phash, role = res

            # Weryfikacja hasła
            if bcrypt.checkpw(self.password_box.text().encode("utf-8"), phash.encode("utf-8")):
                self.open_main_window(uid, role)
            else:
                QMessageBox.critical(self, "Błąd", "Złe hasło.")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def open_main_window(self, user_id, role):
        self.close()

        # TUTAJ JEST KLUCZOWA ZMIANA - IMPORTUJEMY ODPOWIEDNIE OKNO
        if role == "Pacjent":
            from PatientWindow import PatientWindow
            self.win = PatientWindow(user_id)
        elif role == "Lekarz":
            from DoctorWindow import DoctorWindow
            self.win = DoctorWindow(user_id)
        elif role == "Laborant":
            from LaborantWindow import LaborantWindow
            self.win = LaborantWindow(user_id)
        else:
            QMessageBox.critical(self, "Błąd", f"Nieznana rola: {role}")
            return

        self.win.show()