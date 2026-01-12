import psycopg2
import bcrypt
from PySide6.QtWidgets import (QWidget, QLineEdit, QPushButton, QVBoxLayout,
                               QMessageBox, QLabel, QComboBox)
from PySide6.QtCore import Qt

conn_str = "postgresql://neondb_owner:npg_yKUJZNj2ShD0@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech/logowanie_db?sslmode=require&channel_binding=require"


class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MedEX-POL - Rejestracja")
        self.resize(350, 500)

        # --- STYLESHEET ---
        # Ten sam kolor tła (#ACF87A) i kontrastowe pola
        self.setStyleSheet("""
            QWidget {
                background-color: #ACF87A;
                font-family: 'Segoe UI', sans-serif;
                color: #000000;
            }

            /* Pola tekstowe i Lista rozwijana */
            QLineEdit, QComboBox {
                background-color: #FFFFFF;
                color: #000000;  /* Czarny tekst */
                border: 2px solid #555555;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #0055AA;
            }

            /* Naprawa widoku listy w QComboBox */
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #000000;
                selection-background-color: #2F9ADF;
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
                background-color: #E0E0E0;
            }

            /* Etykiety */
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #222222;
            }
            QLabel#header {
                font-size: 24px;
                margin-bottom: 15px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(40, 20, 40, 20)

        header = QLabel("Utwórz konto", objectName="header")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Pola formularza
        layout.addWidget(QLabel("PESEL (11 cyfr):"))
        self.pesel_box = QLineEdit(self)
        self.pesel_box.setPlaceholderText("Wpisz PESEL")
        self.pesel_box.setMaxLength(11)
        layout.addWidget(self.pesel_box)

        layout.addWidget(QLabel("Login:"))
        self.login_box = QLineEdit(self)
        self.login_box.setPlaceholderText("Wpisz login")
        layout.addWidget(self.login_box)

        layout.addWidget(QLabel("Hasło:"))
        self.password_box = QLineEdit(self)
        self.password_box.setPlaceholderText("Wpisz hasło")
        self.password_box.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_box)

        layout.addWidget(QLabel("Rola:"))
        self.role_combo = QComboBox(self)
        self.role_combo.addItems(["Pacjent", "Lekarz", "Laborant"])
        layout.addWidget(self.role_combo)

        layout.addSpacing(20)

        # Przyciski
        reg_btn = QPushButton("ZAREJESTRUJ SIĘ")
        reg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reg_btn.clicked.connect(self.register_user)
        layout.addWidget(reg_btn)

        back_btn = QPushButton("Wróć")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.show_login)
        layout.addWidget(back_btn)

        layout.addStretch()

    def show_login(self):
        from LoginWindow import LoginWindow
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def register_user(self):
        pesel = self.pesel_box.text().strip()
        login = self.login_box.text().strip()
        password = self.password_box.text().strip()
        role = self.role_combo.currentText()

        if not pesel or not login or not password:
            QMessageBox.warning(self, "Błąd", "Wypełnij wszystkie pola!")
            return

        if len(pesel) != 11 or not pesel.isdigit():
            QMessageBox.warning(self, "Błąd", "PESEL musi składać się z 11 cyfr.")
            return

        conn = None
        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM users WHERE login = %s", (login,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Błąd", "Taki login jest już zajęty!")
                return

            cursor.execute("SELECT id FROM users WHERE id = %s", (pesel,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Błąd", "Użytkownik o takim numerze PESEL już istnieje!")
                return

            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            cursor.execute(
                "INSERT INTO users (id, login, password, role) VALUES (%s, %s, %s, %s)",
                (pesel, login, hashed, role)
            )

            conn.commit()

            QMessageBox.information(self, "Sukces", "Konto utworzone pomyślnie!\nZaloguj się teraz.")
            self.show_login()

        except Exception as e:
            if conn: conn.rollback()
            QMessageBox.critical(self, "Błąd Bazy", f"Wystąpił błąd podczas rejestracji: {e}")

        finally:
            if conn:
                cursor.close()
                conn.close()