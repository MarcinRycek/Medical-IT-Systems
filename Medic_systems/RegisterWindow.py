import psycopg2
import bcrypt
from PySide6.QtWidgets import (QWidget, QLineEdit, QPushButton, QVBoxLayout,
                               QMessageBox, QLabel, QComboBox, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from BaseWindow import conn_str


class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MedEX-POL - Rejestracja")
        self.resize(450, 650)

        self.setStyleSheet("""
            QWidget { background-color: #ECF0F1; font-family: 'Segoe UI', sans-serif; color: #2C3E50; }
            QFrame#RegisterCard { background-color: #FFFFFF; border-radius: 10px; border: 1px solid #BDC3C7; }
            QLineEdit, QComboBox { 
                background-color: #F8F9F9; border: 1px solid #BDC3C7; border-radius: 5px; 
                padding-left: 10px; height: 40px; font-size: 13px; color: #2C3E50; 
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #3498DB; background-color: #FFFFFF; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF; color: #2C3E50; selection-background-color: #3498DB; 
                selection-color: #FFFFFF; border: 1px solid #BDC3C7; outline: 0;
            }
            QPushButton { 
                background-color: #FFFFFF; color: #2C3E50; border: 1px solid #BDC3C7; 
                border-radius: 5px; font-weight: bold; font-size: 14px; padding: 10px;
            }
            QPushButton:hover { background-color: #D6DBDF; }
            QPushButton#RegisterBtn { background-color: #27AE60; color: white; border: none; }
            QPushButton#RegisterBtn:hover { background-color: #2ECC71; }
            QPushButton#BackBtn { background-color: transparent; color: #7F8C8D; border: none; margin-top: 5px; font-size: 12px; } 
            QPushButton#BackBtn:hover { color: #3498DB; text-decoration: underline; }
            QMessageBox { background-color: #FFFFFF; color: #000000; }
            QMessageBox QPushButton { background-color: #F0F0F0; color: #000000; border: 1px solid #888; border-radius: 5px; padding: 5px 15px; }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("RegisterCard")
        card.setFixedSize(380, 600)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(12)

        header = QLabel("Utwórz konto")
        header.setStyleSheet(
            "color: #2C3E50; font-size: 24px; font-weight: bold; border: none; margin-bottom: 5px; background-color: transparent;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(header)

        label_style = "color: #2C3E50; font-weight: bold; font-size: 12px; border: none; margin-top: 5px; background-color: transparent;"

        lbl_role = QLabel("Rola w systemie:")
        lbl_role.setStyleSheet(label_style)
        card_layout.addWidget(lbl_role)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Pacjent", "Lekarz", "Laborant"])
        self.role_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.role_combo.currentTextChanged.connect(self.update_form_ui)
        card_layout.addWidget(self.role_combo)

        self.lbl_id = QLabel("PESEL (11 cyfr):")
        self.lbl_id.setStyleSheet(label_style)
        card_layout.addWidget(self.lbl_id)

        self.id_box = QLineEdit()
        self.id_box.setPlaceholderText("Wpisz numer PESEL")
        self.id_box.setMaxLength(11)
        card_layout.addWidget(self.id_box)

        lbl_login = QLabel("Login:")
        lbl_login.setStyleSheet(label_style)
        card_layout.addWidget(lbl_login)

        self.login_box = QLineEdit()
        self.login_box.setPlaceholderText("Twój login")
        card_layout.addWidget(self.login_box)

        lbl_pass = QLabel("Hasło:")
        lbl_pass.setStyleSheet(label_style)
        card_layout.addWidget(lbl_pass)

        self.password_box = QLineEdit()
        self.password_box.setPlaceholderText("Twoje hasło")
        self.password_box.setEchoMode(QLineEdit.EchoMode.Password)
        card_layout.addWidget(self.password_box)

        card_layout.addSpacing(15)

        reg_btn = QPushButton("ZAREJESTRUJ SIĘ")
        reg_btn.setObjectName("RegisterBtn")
        reg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reg_btn.clicked.connect(self.register_user)
        card_layout.addWidget(reg_btn)

        back_btn = QPushButton("Masz już konto? Zaloguj się")
        back_btn.setObjectName("BackBtn")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.show_login)
        card_layout.addWidget(back_btn)

        card_layout.addStretch()
        layout.addWidget(card)
        self.update_form_ui(self.role_combo.currentText())

    def update_form_ui(self, role):
        self.id_box.clear()
        if role == "Pacjent":
            self.lbl_id.setText("PESEL (11 cyfr):")
            self.id_box.setPlaceholderText("Wpisz numer PESEL")
            self.id_box.setMaxLength(11)
        else:
            self.lbl_id.setText("Numer Uprawnienia / PWZ:")
            self.id_box.setPlaceholderText("Wpisz numer uprawnienia")
            self.id_box.setMaxLength(20)

    def show_login(self):
        from LoginWindow import LoginWindow
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def register_user(self):
        user_id = self.id_box.text().strip()
        login = self.login_box.text().strip()
        password = self.password_box.text().strip()
        role_pl = self.role_combo.currentText()

        role_map = {"Pacjent": "patient", "Lekarz": "doctor", "Laborant": "laborant"}
        db_role = role_map.get(role_pl, "patient")

        if not user_id or not login or not password:
            QMessageBox.warning(self, "Błąd", "Wypełnij wszystkie pola!")
            return

        if role_pl == "Pacjent":
            if len(user_id) != 11 or not user_id.isdigit():
                QMessageBox.warning(self, "Błąd", "PESEL musi składać się z 11 cyfr.")
                return
            is_active = True  # Pacjenci są aktywni od razu
        else:
            if len(user_id) < 5 or not user_id.isdigit():
                QMessageBox.warning(self, "Błąd", "Podaj poprawny Numer Uprawnienia.")
                return
            is_active = False

        conn = None
        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM users WHERE login = %s", (login,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Błąd", "Taki login jest już zajęty!")
                return

            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Błąd", "Użytkownik o takim ID już istnieje!")
                return

            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            cursor.execute(
                "INSERT INTO users (id, login, password, role, is_active) VALUES (%s, %s, %s, %s, %s)",
                (user_id, login, hashed, db_role, is_active)
            )

            conn.commit()

            if is_active:
                QMessageBox.information(self, "Sukces", "Konto utworzone pomyślnie!\nMożesz się zalogować.")
            else:
                QMessageBox.information(self, "Sukces",
                                        "Konto utworzone!\nCzeka na zatwierdzenie przez Administratora.")

            self.show_login()

        except Exception as e:
            if conn: conn.rollback()
            QMessageBox.critical(self, "Błąd Bazy", f"Wystąpił błąd: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()