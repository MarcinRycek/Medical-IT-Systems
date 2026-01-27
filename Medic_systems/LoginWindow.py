import psycopg2
import bcrypt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from DoctorWindow import DoctorWindow
from LaborantWindow import LaborantWindow
from PatientWindow import PatientWindow
from BaseWindow import conn_str


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MedEX-POL - Logowanie")
        self.resize(500, 600)

        # Styl z naprawionym QMessageBox
        self.setStyleSheet("""
            QWidget { background-color: #ECF0F1; }

            QMessageBox {
                background-color: #FFFFFF;
                color: #000000;
            }
            QMessageBox QLabel {
                color: #000000;
                background-color: transparent;
            }
            QMessageBox QPushButton {
                background-color: #F0F0F0;
                color: #000000;
                border: 1px solid #888888;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QMessageBox QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.login_card = QFrame()
        self.login_card.setFixedSize(380, 450)
        self.login_card.setStyleSheet("""
            QFrame { background-color: white; border-radius: 10px; border: 1px solid #BDC3C7; }
        """)

        card_layout = QVBoxLayout(self.login_card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Witaj w MedEX")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2C3E50; font-size: 26px; font-weight: bold; border: none;")

        subtitle = QLabel("System Obsługi Medycznej")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7F8C8D; font-size: 14px; margin-bottom: 20px; border: none;")

        # --- NAPRAWA WYGLĄDU PÓL (Wyraźny tekst, brak ucinania) ---
        input_style = """
            QLineEdit { 
                background-color: #F8F9F9; 
                border: 1px solid #BDC3C7; 
                border-radius: 5px; 
                padding-left: 10px; /* Tylko z lewej, góra/dół automatycznie */
                height: 45px;       /* Stała wysokość */
                font-size: 14px; 
                color: #2C3E50; 
            }
            QLineEdit:focus { 
                border: 2px solid #3498DB; 
                background-color: white; 
            }
        """

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Login / PESEL")
        self.login_input.setStyleSheet(input_style)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Hasło")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(input_style)
        self.password_input.returnPressed.connect(self.handle_login)

        self.login_btn = QPushButton("ZALOGUJ SIĘ")
        self.login_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.login_btn.setFixedHeight(50)
        self.login_btn.setStyleSheet("""
            QPushButton { background-color: #3498DB; color: white; font-size: 14px; font-weight: bold; border-radius: 5px; border: none; margin-top: 10px; }
            QPushButton:hover { background-color: #2980B9; }
        """)
        self.login_btn.clicked.connect(self.handle_login)

        self.register_btn = QPushButton("Nie masz konta? Zarejestruj się")
        self.register_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.register_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #7F8C8D; border: none; margin-top: 5px; }
            QPushButton:hover { color: #3498DB; text-decoration: underline; }
        """)
        self.register_btn.clicked.connect(self.open_register)

        footer = QLabel("© 2026 MedEX-POL sp. z o.o.")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #BDC3C7; font-size: 11px; margin-top: 20px; border: none;")

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self.login_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.login_btn)
        card_layout.addWidget(self.register_btn)
        card_layout.addWidget(footer)
        card_layout.addStretch()

        main_layout.addWidget(self.login_card)

    def handle_login(self):
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Błąd", "Podaj login i hasło!")
            return

        try:
            conn = psycopg2.connect(conn_str)
            with conn.cursor() as cur:
                cur.execute("SELECT id, role, password FROM users WHERE login = %s", (login,))
                user = cur.fetchone()

                if user:
                    user_id, role, db_hash = user
                    try:
                        if bcrypt.checkpw(password.encode('utf-8'),
                                          db_hash.encode('utf-8') if isinstance(db_hash, str) else db_hash):
                            self.open_dashboard(role, user_id)
                        else:
                            QMessageBox.warning(self, "Błąd", "Nieprawidłowe hasło!")
                    except ValueError:
                        if password == db_hash:
                            self.open_dashboard(role, user_id)
                        else:
                            QMessageBox.warning(self, "Błąd", "Nieprawidłowe hasło.")
                else:
                    if len(login) == 11 and login.isdigit():
                        self.open_dashboard("patient", login)
                    else:
                        QMessageBox.warning(self, "Błąd", "Nie znaleziono użytkownika.")
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Błąd Serwera", f"Błąd bazy danych:\n{e}")

    def open_dashboard(self, role, user_id):
        self.hide()
        role = role.lower().strip()

        try:
            if role in ["doctor", "lekarz", "doktor"]:
                self.dashboard = DoctorWindow(user_id)
            elif role == "laborant":
                self.dashboard = LaborantWindow(user_id)
            elif role in ["patient", "pacjent"]:
                self.dashboard = PatientWindow(user_id)
            else:
                self.show()
                QMessageBox.critical(self, "Błąd", f"Nieznana rola: '{role}'")
                return

            self.dashboard.show()
        except Exception as e:
            self.show()
            QMessageBox.critical(self, "Błąd Aplikacji",
                                 f"Nie udało się otworzyć okna dla roli {role}.\nSzczegóły: {e}")

    def open_register(self):
        from RegisterWindow import RegisterWindow
        self.close()
        self.reg_window = RegisterWindow()
        self.reg_window.show()