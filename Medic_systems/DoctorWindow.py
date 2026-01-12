from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFrame)
from PySide6.QtCore import Qt
from BaseWindow import BaseWindow


# --- OKNO DODAWANIA WIZYTY ---
class AddVisitWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dodaj Nową Wizytę")
        self.setGeometry(300, 300, 400, 300)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<h2>Dodaj Wizytę</h2>"))
        self.date_in = QLineEdit()
        self.date_in.setPlaceholderText("RRRR-MM-DD GG:MM")
        self.title_in = QLineEdit()
        self.title_in.setPlaceholderText("Tytuł wizyty")
        self.pesel_in = QLineEdit()
        self.pesel_in.setPlaceholderText("PESEL Pacjenta")

        layout.addWidget(QLabel("Data:"))
        layout.addWidget(self.date_in)
        layout.addWidget(QLabel("Tytuł:"))
        layout.addWidget(self.title_in)
        layout.addWidget(QLabel("Pacjent (PESEL):"))
        layout.addWidget(self.pesel_in)

        btn = QPushButton("Zatwierdź")
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        # Tutaj w przyszłości dodasz INSERT INTO visits...
        QMessageBox.information(self, "Info", "Wizyta dodana (placeholder).")
        self.accept()


# --- GŁÓWNE OKNO LEKARZA ---
class DoctorWindow(BaseWindow):
    def __init__(self, user_id):
        # Zmienna przechowująca PESEL pacjenta, jeśli kod został zweryfikowany
        self.searched_pesel = None
        super().__init__(user_id, "Lekarz")
        self.init_ui()

    def setup_sidebar_widgets(self):
        # 1. Info o lekarzu
        self.setup_info_widget("PANEL LEKARZA", f"ID: {self.user_id}")

        # 2. Sekcja weryfikacji kodu pacjenta
        search_frame = QFrame(self)
        search_frame.setFixedSize(250, 140)
        search_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 2px solid #555;
            }
        """)
        layout = QVBoxLayout(search_frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)

        lbl = QLabel("DOSTĘP DO HISTORII", search_frame)
        lbl.setStyleSheet("font-weight: bold; color: #333; font-size: 11px; border: none;")

        self.code_input = QLineEdit(search_frame)
        self.code_input.setPlaceholderText("Wpisz kod pacjenta")
        self.code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_input.setStyleSheet("border: 1px solid #aaa; padding: 5px; border-radius: 5px; color: black;")

        btn_check = QPushButton("Odblokuj dane", search_frame)
        btn_check.setStyleSheet("""
            QPushButton {
                background-color: #2F9ADF; 
                color: white; 
                border-radius: 5px; 
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1F8ACF; }
        """)
        btn_check.clicked.connect(self.verify_patient_code)

        btn_reset = QPushButton("Pokaż mój grafik", search_frame)
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #ddd; 
                color: #333; 
                border-radius: 5px; 
                padding: 5px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #ccc; }
        """)
        btn_reset.clicked.connect(self.reset_view)

        layout.addWidget(lbl)
        layout.addWidget(self.code_input)
        layout.addWidget(btn_check)
        layout.addWidget(btn_reset)

        self.side_layout.addWidget(search_frame, alignment=Qt.AlignmentFlag.AlignCenter)

    def setup_extra_buttons(self):
        btn = self.add_button("dodaj nową wizytę")
        btn.clicked.connect(self.open_add_visit)

    def open_add_visit(self):
        AddVisitWindow(self).exec()

    def verify_patient_code(self):
        """Sprawdza kod w bazie i jeśli poprawny, pobiera PESEL"""
        code = self.code_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Błąd", "Wprowadź kod.")
            return

        if not self.connection:
            return

        try:
            with self.connection.cursor() as cursor:
                # Sprawdź kod I czy czas wygaśnięcia jest w przyszłości (> NOW())
                query = """
                    SELECT pesel 
                    FROM patient_codes 
                    WHERE code = %s AND expiration_time > NOW()
                """
                cursor.execute(query, (code,))
                result = cursor.fetchone()

                if result:
                    self.searched_pesel = result[0]  # Zapisz znaleziony PESEL
                    QMessageBox.information(self, "Sukces",
                                            f"Kod poprawny. Wyświetlam historię pacjenta: {self.searched_pesel}")
                    self.refresh_list()  # Odśwież listę (teraz użyje searched_pesel)
                else:
                    QMessageBox.critical(self, "Błąd", "Kod nieprawidłowy lub wygasł.")

        except Exception as e:
            QMessageBox.critical(self, "Błąd bazy", str(e))

    def reset_view(self):
        """Wraca do widoku własnego grafiku lekarza"""
        self.searched_pesel = None
        self.code_input.clear()
        self.refresh_list()
        QMessageBox.information(self, "Widok", "Powrót do Twojego grafiku wizyt.")

    def refresh_list(self):
        """
        Nadpisujemy funkcję z BaseWindow, aby obsłużyć dwa tryby:
        1. Grafik Lekarza (gdy self.searched_pesel is None)
        2. Historia Pacjenta (gdy self.searched_pesel ma wartość)
        """
        self.lista_wizyt.clear()

        if not self.connection:
            return

        try:
            with self.connection.cursor() as cursor:
                if self.searched_pesel:
                    # TRYB 2: Widok Pacjenta (Wszystkie jego wizyty, kolumna 3 to ID Lekarza)
                    query = """
                        SELECT visit_date, title, doctor_id 
                        FROM visits 
                        WHERE pesel = %s
                    """
                    cursor.execute(query, (self.searched_pesel,))
                else:
                    # TRYB 1: Widok Lekarza (Jego wizyty, kolumna 3 to PESEL Pacjenta)
                    query = """
                        SELECT visit_date, title, pesel 
                        FROM visits 
                        WHERE doctor_id = %s
                    """
                    cursor.execute(query, (self.user_id,))

                rows = cursor.fetchall()
                self.add_list_items(rows)

        except Exception as e:
            print(f"Błąd pobierania danych: {e}")
            QMessageBox.critical(self, "Błąd", f"Nie udało się pobrać danych: {e}")