import psycopg2
import bcrypt
from PySide6.QtWidgets import (QWidget, QLineEdit, QPushButton, QVBoxLayout,
                               QMessageBox, QLabel)
from PySide6.QtCore import Qt

conn_str = "postgresql://neondb_owner:npg_yKUJZNj2ShD0@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech/logowanie_db?sslmode=require&channel_binding=require"


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MedEX-POL - Logowanie")
        self.resize(350, 450)

        # --- STYLESHEET (Wygląd) ---
        # Używamy koloru: rgb(172, 248, 122) -> Hex: #ACF87A
        self.setStyleSheet("""
            QWidget {
                background-color: #ACF87A; 
                font-family: 'Segoe UI', sans-serif;
                color: #000000;
            }

            /* Pola tekstowe - Wyraźny tekst */
            QLineEdit {
                background-color: #FFFFFF;  /* Białe tło */
                color: #000000;             /* Czarny tekst (wymuszony) */
                border: 2px solid #555555;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                font-weight: normal;
            }
            QLineEdit:focus {
                border: 2px solid #0055AA;  /* Niebieska ramka po kliknięciu */
            }

            /* Przyciski */
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                border: 2px solid #555555;
                border-radius: 10px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E0E0E0; /* Lekko szary po najechaniu */
            }
            QPushButton:pressed {
                background-color: #CCCCCC;
            }

            /* Specyficzne style dla etykiet */
            QLabel#title {
                font-size: 26px;
                font-weight: bold;
                color: #222222;
                margin-bottom: 5px;
            }
            QLabel#subtitle {
                font-size: 14px;
                color: #444444;
                margin-bottom: 20px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)

        # Nagłówek
        title = QLabel("MedEX-POL", objectName="title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Panel Logowania", objectName="subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Pola tekstowe
        self.login_box = QLineEdit(self)
        self.login_box.setPlaceholderText("Login")

        self.password_box = QLineEdit(self)
        self.password_box.setPlaceholderText("Hasło")
        self.password_box.setEchoMode(QLineEdit.Password)

        # Przyciski
        login_btn = QPushButton("ZALOGUJ SIĘ", objectName="loginBtn")
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.clicked.connect(self.login_user)

        reg_btn = QPushButton("Załóż konto", objectName="regBtn")
        reg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reg_btn.clicked.connect(self.show_register)

        # Dodawanie do layoutu
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.login_box)
        layout.addWidget(self.password_box)
        layout.addSpacing(10)
        layout.addWidget(login_btn)
        layout.addWidget(reg_btn)
        layout.addStretch()

    def show_register(self):
        from RegisterWindow import RegisterWindow
        self.close()
        self.register_window = RegisterWindow()
        self.register_window.show()

    def login_user(self):
        login = self.login_box.text().strip()
        password = self.password_box.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Błąd", "Wpisz login i hasło.")
            return

        conn = None
        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()

            cursor.execute("SELECT id, password, role FROM users WHERE login = %s", (login,))
            result = cursor.fetchone()

            if result is None:
                QMessageBox.critical(self, "Błąd", "Nieprawidłowy login lub hasło.")
                return

            user_id, password_hash, role = result

            if bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
                self.open_main_window(user_id, role)
            else:
                QMessageBox.critical(self, "Błąd", "Nieprawidłowy login lub hasło.")

        except Exception as e:
            QMessageBox.critical(self, "Błąd serwera", f"Nie udało się połączyć: {e}")
        finally:
            if conn: conn.close()

    def open_main_window(self, user_id, role):
        self.close()

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
            QMessageBox.critical(self, "Błąd", f"Nieznana rola użytkownika: {role}")
            return

        self.win.show()