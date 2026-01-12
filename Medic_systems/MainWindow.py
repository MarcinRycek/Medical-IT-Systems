import psycopg2
import random
from datetime import datetime, timedelta  # <--- NOWY WYMAGANY IMPORT
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                               QPushButton, QListWidget, QListWidgetItem,
                               QDialog, QMessageBox, QLineEdit)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette, qRgb


# --- OKNO SZCZEGÓŁÓW WIZYTY ---
class VisitDetailsWindow(QDialog):
    def __init__(self, data_wizyty, tytul_wizyty, lekarz, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Szczegóły Wizyty: {tytul_wizyty}")
        self.setGeometry(300, 300, 600, 400)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"<h2>Szczegóły Wizyty</h2>", self))
        layout.addWidget(QLabel(f"<b>Data:</b> {data_wizyty}", self))
        layout.addWidget(QLabel(f"<b>Tytuł:</b> {tytul_wizyty}", self))
        layout.addWidget(QLabel(f"<b>Doktor/Laborant:</b> {lekarz}", self))
        close_button = QPushButton("Zamknij", self)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)


# --- OKNO DODAWANIA WIZYTY (Tylko dla lekarza) ---
class AddVisitWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dodaj Nową Wizytę")
        self.setGeometry(300, 300, 600, 400)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<h2>Dodaj Nową Wizytę</h2>", self))
        layout.addWidget(QLabel(f"<b>Wprowadź dane wizyty:</b>", self))

        self.date_input = QLineEdit(self)
        self.date_input.setPlaceholderText("RRRR-MM-DD GG:MM")
        self.title_input = QLineEdit(self)
        self.doctor_input = QLineEdit(self)

        layout.addWidget(QLabel("Data:", self))
        layout.addWidget(self.date_input)
        layout.addWidget(QLabel("Tytuł:", self))
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("ID Doktora/Laboranta:", self))
        layout.addWidget(self.doctor_input)

        add_button = QPushButton("Dodaj Wizytę", self)
        add_button.clicked.connect(self._add_visit)
        layout.addWidget(add_button, alignment=Qt.AlignmentFlag.AlignRight)

        close_button = QPushButton("Zamknij", self)
        close_button.clicked.connect(self.reject)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

    def _add_visit(self):
        QMessageBox.information(self, "Dodaj Wizytę", "Funkcja w przygotowaniu (placeholder).")
        self.accept()


# --- OKNO WYLOGOWANIA ---
class LogoutWindow(QDialog):
    def __init__(self, parent=None, on_logged_out=None):
        super().__init__(parent)
        self.setWindowTitle("Wylogowanie")
        self.setGeometry(300, 300, 600, 400)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Potwierdzenie Wylogowania</h2>", self))
        layout.addWidget(QLabel("<b>Czy na pewno chcesz się wylogować?</b>", self))

        logout_button = QPushButton("Wyloguj", self)
        logout_button.clicked.connect(self._logout)
        layout.addWidget(logout_button, alignment=Qt.AlignmentFlag.AlignRight)

        cancel_button = QPushButton("Anuluj", self)
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.on_logged_out = on_logged_out

    def _logout(self):
        QMessageBox.information(self, "Wylogowanie", "Zostałeś wylogowany.")
        self.accept()
        if self.on_logged_out:
            self.on_logged_out()


# --- GŁÓWNE OKNO APLIKACJI ---
class MainWindow(QWidget):
    def __init__(self, logged_in_user_id, role):
        super().__init__()
        self.logged_in_user_id = logged_in_user_id
        self.role = role

        self.setWindowTitle(f"MedEX-POL - Panel: {self.role}")
        self.setGeometry(100, 100, 1200, 700)
        self.set_palette()

        self.current_selected_frame = None
        self.current_selected_data = None
        self.connection = self.connect_to_database()

        # Główny Layout
        main_h_layout = QHBoxLayout(self)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        # --- PANEL BOCZNY (Lewa strona) ---
        side_panel = QFrame(self)
        side_panel.setFixedWidth(300)
        side_panel.setStyleSheet("background-color: rgb(172, 248, 122);")
        side_layout = QVBoxLayout(side_panel)
        side_layout.setSpacing(40)
        side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        side_layout.setContentsMargins(20, 150, 20, 20)

        # 1. Element warunkowy: KOD PACJENTA (interaktywny) lub INFO O ROLI
        if self.role == "Pacjent":
            self.setup_patient_code_widget(side_layout)
        else:
            self.setup_staff_info_widget(side_layout)

        # 2. Przyciski Menu
        zobacz_wizyte_btn = self.add_button(side_layout, "zobacz szczegóły")
        zobacz_wizyte_btn.clicked.connect(self._show_visit_details)

        if self.role == "Lekarz":
            dodaj_wizyte_btn = self.add_button(side_layout, "dodaj nową wizytę")
            dodaj_wizyte_btn.clicked.connect(self._show_add_visit_window)

        wyloguj_btn = self.add_button(side_layout, "wyloguj")
        wyloguj_btn.clicked.connect(self._show_logout_window)

        side_layout.addStretch(1)

        # --- PANEL GŁÓWNY (Prawa strona) ---
        main_content_frame = QFrame(self)
        main_content_frame.setStyleSheet("background-color: rgb(172, 248, 122);")
        main_v_layout = QVBoxLayout(main_content_frame)
        main_v_layout.setContentsMargins(0, 0, 0, 0)
        main_v_layout.setSpacing(0)

        header_frame = self.create_header_bar(main_content_frame)
        main_v_layout.addWidget(header_frame)

        self.lista_wizyt = QListWidget(main_content_frame)
        self.lista_wizyt.setFrameShape(QFrame.Shape.NoFrame)
        self.lista_wizyt.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.lista_wizyt.setMinimumSize(QSize(100, 100))
        self.lista_wizyt.itemClicked.connect(self._handle_item_clicked)

        self.add_list_items()

        main_v_layout.addWidget(self.lista_wizyt)

        main_h_layout.addWidget(side_panel)
        main_h_layout.addWidget(main_content_frame)
        self.setLayout(main_h_layout)

    def setup_patient_code_widget(self, layout):
        """Wyświetla kod pacjenta oraz przycisk do jego generowania"""
        patient_code = self.fetch_patient_code()
        code_text = str(patient_code) if patient_code else "------"

        code_frame = QFrame(self)
        code_frame.setFixedSize(250, 120)
        code_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 2px solid #CCCCCC;
            }
        """)
        code_layout = QVBoxLayout(code_frame)
        code_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        code_layout.setSpacing(5)

        code_label_title = QLabel("KOD PACJENTA", code_frame)
        code_label_title.setStyleSheet("color: #666666; font-size: 12px; border: none;")

        self.code_label = QLabel(code_text, code_frame)
        self.code_label.setStyleSheet(
            "font-size: 28px; font-weight: bold; letter-spacing: 4px; color: #000000; border: none;")

        generate_btn = QPushButton("Generuj nowy kod", code_frame)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2F9ADF;
                color: white;
                font-size: 11px;
                border-radius: 5px;
                padding: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1F8ACF;
            }
        """)
        generate_btn.clicked.connect(self.generate_new_patient_code)

        code_layout.addWidget(code_label_title, alignment=Qt.AlignmentFlag.AlignCenter)
        code_layout.addWidget(self.code_label, alignment=Qt.AlignmentFlag.AlignCenter)
        code_layout.addWidget(generate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(code_frame, alignment=Qt.AlignmentFlag.AlignCenter)

    def generate_new_patient_code(self):
        """Generuje losowy kod i ustawia czas ważności (NAPRAWIONE)"""
        if not self.connection:
            QMessageBox.critical(self, "Błąd", "Brak połączenia z bazą danych.")
            return

        # 1. Generowanie losowego kodu
        new_code = str(random.randint(100000, 999999))

        # 2. Obliczanie czasu wygaśnięcia (Teraz + 15 minut)
        expiration_time = datetime.now() + timedelta(minutes=15)

        try:
            with self.connection.cursor() as cursor:
                # Sprawdzenie czy użytkownik ma już wpis
                cursor.execute("SELECT 1 FROM patient_codes WHERE pesel = %s", (self.logged_in_user_id,))
                exists = cursor.fetchone()

                if exists:
                    # Aktualizacja kodu I czasu wygaśnięcia
                    cursor.execute("""
                        UPDATE patient_codes 
                        SET code = %s, expiration_time = %s 
                        WHERE pesel = %s
                    """, (new_code, expiration_time, self.logged_in_user_id))
                else:
                    # Wstawienie nowego wiersza z czasem wygaśnięcia
                    cursor.execute("""
                        INSERT INTO patient_codes (pesel, code, expiration_time) 
                        VALUES (%s, %s, %s)
                    """, (self.logged_in_user_id, new_code, expiration_time))

                self.connection.commit()

                self.code_label.setText(new_code)
                QMessageBox.information(self, "Sukces", "Wygenerowano nowy kod pacjenta (ważny 15 min)!")

        except Exception as e:
            self.connection.rollback()
            QMessageBox.critical(self, "Błąd", f"Nie udało się wygenerować kodu: {e}")

    def setup_staff_info_widget(self, layout):
        info_frame = QFrame(self)
        info_frame.setFixedSize(250, 80)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #555555;
                border-radius: 15px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        role_label = QLabel(f"PANEL {self.role.upper()}A", info_frame)
        role_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")

        user_label = QLabel(f"ID: {self.logged_in_user_id}", info_frame)
        user_label.setStyleSheet("color: #DDDDDD; font-size: 12px;")

        info_layout.addWidget(role_label)
        info_layout.addWidget(user_label)
        layout.addWidget(info_frame, alignment=Qt.AlignmentFlag.AlignCenter)

    def fetch_patient_code(self):
        if not self.connection or self.role != "Pacjent":
            return None

        query = "SELECT code FROM patient_codes WHERE pesel = %s LIMIT 1"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (self.logged_in_user_id,))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Error fetching patient code: {e}")
            return None

    def fetch_visits_from_database(self):
        if not self.connection:
            return []

        if self.role == "Pacjent":
            query = """
            SELECT visit_date, title, coalesce(doctor_id, laborant_id)
            FROM visits WHERE pesel = %s
            """
        elif self.role == "Lekarz":
            query = """
            SELECT visit_date, title, pesel 
            FROM visits WHERE doctor_id = %s
            """
        elif self.role == "Laborant":
            query = """
            SELECT visit_date, title, pesel
            FROM visits WHERE laborant_id = %s
            """
        else:
            return []

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (self.logged_in_user_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching data for role {self.role}: {e}")
            return []

    def add_list_items(self):
        styles = ["background-color: #D3D3D3;", "background-color: #C4C4C4;"]
        self.lista_wizyt.clear()

        all_visits_data = self.fetch_visits_from_database()

        for i, (data, tytul, osoba_powiazana) in enumerate(all_visits_data):
            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""
            trzecia_kolumna_tekst = str(osoba_powiazana)

            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, tytul, trzecia_kolumna_tekst))

            frame = QFrame()
            frame.setFixedHeight(70)
            frame.setStyleSheet(styles[i % 2])

            h_layout = QHBoxLayout(frame)
            h_layout.setContentsMargins(10, 0, 10, 0)

            labels_data = [data_str, tytul, trzecia_kolumna_tekst]

            for j, text in enumerate(labels_data):
                label = QLabel(str(text))
                label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                label.setStyleSheet(
                    "background-color: transparent; color: #444444; font-size: 14px; font-weight: bold;")
                h_layout.addWidget(label, stretch=1 if j == 1 else 0)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, frame.height()))
            self.lista_wizyt.setItemWidget(list_item, frame)

    def _handle_item_clicked(self, item):
        if self.current_selected_frame:
            idx = self.lista_wizyt.row(self.lista_wizyt.itemAt(self.current_selected_frame.pos()))
            original_style = "background-color: #D3D3D3;" if idx % 2 == 0 else "background-color: #C4C4C4;"
            self.current_selected_frame.setStyleSheet(original_style)

        selected_frame = self.lista_wizyt.itemWidget(item)
        if selected_frame:
            selected_frame.setStyleSheet("background-color: #2F9ADF;")
            self.current_selected_frame = selected_frame
            self.current_selected_data = item.data(Qt.ItemDataRole.UserRole)

    def _show_add_visit_window(self):
        add_visit_window = AddVisitWindow(self)
        add_visit_window.exec()

    def _show_logout_window(self):
        logout_window = LogoutWindow(self, self._handle_logged_out)
        logout_window.exec()

    def _handle_logged_out(self):
        from LoginWindow import LoginWindow
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def _show_visit_details(self):
        if not self.current_selected_data:
            QMessageBox.warning(self, "Błąd", "Proszę wybrać wizytę z listy.")
            return

        data, tytul, osoba = self.current_selected_data
        details_window = VisitDetailsWindow(
            data_wizyty=data,
            tytul_wizyty=tytul,
            lekarz=osoba,
            parent=self
        )
        details_window.exec()

    def set_palette(self):
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(qRgb(172, 248, 122)))
        self.setPalette(palette)

    def add_button(self, layout, text):
        button = QPushButton(text.upper(), self)
        button.setFixedSize(QSize(250, 70))
        button.setStyleSheet("""
            QPushButton {
                background-color: #555555; 
                color: white; 
                font-size: 16px;
                border: none;
                border-radius: 10px; 
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        return button

    def create_header_bar(self, parent):
        header_frame = QFrame(parent)
        header_frame.setFixedHeight(40)
        header_frame.setStyleSheet("background-color: #808080;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 0, 10, 0)

        trzecia_kolumna = "DOKTOR:" if self.role == "Pacjent" else "PACJENT (PESEL):"

        headers = ["DATA", "OPIS:", trzecia_kolumna]
        for i, text in enumerate(headers):
            label = QLabel(text, header_frame)
            label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet("background-color: #808080;font-weight: bold; color: #FFFFFF; font-size: 14px;")
            header_layout.addWidget(label, stretch=1 if i == 1 else 0)

        header_frame.setLayout(header_layout)
        return header_frame

    def connect_to_database(self):
        conn_str = "postgresql://neondb_owner:npg_yKUJZNj2ShD0@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech/logowanie_db?sslmode=require&channel_binding=require"
        try:
            connection = psycopg2.connect(conn_str)
            return connection
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            return None