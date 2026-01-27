import psycopg2
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFrame, QTextEdit,
                               QListWidgetItem, QHBoxLayout)
from PySide6.QtCore import Qt, QSize
from BaseWindow import BaseWindow, conn_str

# --- STYLE ---
DIALOG_STYLE = """
    QDialog { background-color: #F8F9FA; }
    QLabel { color: #2C3E50; font-size: 13px; font-weight: bold; }
    QLineEdit, QTextEdit { 
        background-color: white; 
        border: 1px solid #BDC3C7; 
        border-radius: 4px;
        padding: 8px; 
        color: #2C3E50;
        font-size: 13px;
    }
    QLineEdit:focus, QTextEdit:focus { border: 2px solid #3498DB; }

    /* Styl dla komunikatów */
    QMessageBox { background-color: white; color: black; }
    QMessageBox QLabel { color: black; }
"""

BTN_STYLE = """
    QPushButton {
        background-color: #3498DB; 
        color: white; 
        font-weight: bold; 
        border-radius: 5px; 
        font-size: 14px;
        border: none;
    }
    QPushButton:hover { background-color: #2980B9; }
"""


# --- OKNO ZLECANIA BADANIA (Bez zmian) ---
class AddLabTestWindow(QDialog):
    def __init__(self, visit_id, parent=None):
        super().__init__(parent)
        self.visit_id = visit_id
        self.setWindowTitle("Zleć Badanie")
        self.resize(400, 280)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        layout.addWidget(QLabel("Nowe Zlecenie (Laboratorium)"))

        layout.addWidget(QLabel("Nazwa badania (np. Morfologia):"))
        self.title_in = QLineEdit()
        self.title_in.setPlaceholderText("Wpisz nazwę badania...")
        layout.addWidget(self.title_in)

        info_lbl = QLabel("Opis/Wyniki zostaną uzupełnione przez Laboranta.")
        info_lbl.setStyleSheet("color: #7F8C8D; font-style: italic; font-size: 12px; font-weight: normal;")
        layout.addWidget(info_lbl)

        layout.addStretch()

        btn = QPushButton("ZLEĆ BADANIE")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(BTN_STYLE)
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        title = self.title_in.text().strip()
        if not title:
            QMessageBox.warning(self, "Błąd", "Podaj nazwę badania.")
            return

        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO lab_tests (visit_id, title) VALUES (%s, %s)",
                           (self.visit_id, title))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Sukces", "Badanie zostało zlecone.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd Bazy", str(e))


# --- NOWE OKNO: DODAWANIE ZALECEŃ LEKARSKICH ---
class AddRecommendationWindow(QDialog):
    def __init__(self, visit_id, current_recs, parent=None):
        super().__init__(parent)
        self.visit_id = visit_id
        self.setWindowTitle("Zalecenia Lekarskie")
        self.resize(500, 450)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        header = QLabel("Zalecenia i Przebieg Wizyty")
        header.setStyleSheet("color: #2C3E50; font-size: 18px; border: none;")
        layout.addWidget(header)

        layout.addWidget(QLabel("Treść zaleceń (Leki, diagnoza, uwagi):"))
        self.rec_edit = QTextEdit()
        # Jeśli są już jakieś zalecenia, wczytaj je
        if current_recs:
            self.rec_edit.setText(current_recs)
        else:
            self.rec_edit.setPlaceholderText("Wpisz diagnozę i zalecenia dla pacjenta...")

        layout.addWidget(self.rec_edit)

        btn = QPushButton("ZAPISZ ZALECENIA")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px; 
                font-size: 14px; 
                border: none;
            }
            QPushButton:hover { background-color: #2ECC71; }
        """)
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        text = self.rec_edit.toPlainText().strip()
        # Pozwalamy zapisać pusty tekst (jeśli lekarz chce wyczyścić zalecenia)

        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()
            # Aktualizujemy tabelę visits
            cursor.execute("UPDATE visits SET recommendations = %s WHERE id = %s",
                           (text, self.visit_id))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Sukces", "Zalecenia zostały zapisane w karcie wizyty.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd Bazy", str(e))


# --- GŁÓWNE OKNO LEKARZA ---
class DoctorWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Lekarz")
        self.code_input = None
        self.init_ui()

    def setup_sidebar_widgets(self):
        self.setup_info_widget("DR. MEDYCYNY", f"ID: {self.user_id}")

        search_frame = QFrame(self)
        search_frame.setFixedHeight(160)
        search_frame.setStyleSheet("""
            QFrame { background-color: #34495E; border: 1px solid #415B76; border-radius: 8px; }
            QLabel { color: #ECF0F1; }
            QLineEdit { 
                color: #2C3E50; background-color: #ECF0F1; border: none; border-radius: 4px; padding: 6px;
            }
        """)

        layout = QVBoxLayout(search_frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        lbl = QLabel("DOSTĘP DO PACJENTA", search_frame)
        lbl.setStyleSheet("font-weight: bold; font-size: 11px; border: none; letter-spacing: 0.5px;")

        self.code_input = QLineEdit(search_frame)
        self.code_input.setPlaceholderText("Kod (6 cyfr)")
        self.code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        search_btn = QPushButton("POBIERZ KARTĘ", search_frame)
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.setStyleSheet("""
            QPushButton { 
                background-color: #3498DB; color: white; font-weight: bold; padding: 8px; border-radius: 4px; border: none;
            }
            QPushButton:hover { background-color: #2980B9; }
        """)
        search_btn.clicked.connect(self.load_patient_by_code)

        layout.addWidget(lbl)
        layout.addWidget(self.code_input)
        layout.addWidget(search_btn)
        self.side_layout.addWidget(search_frame)

    def setup_extra_buttons(self):
        self.add_button("MOJE WIZYTY").clicked.connect(self.reset_to_my_schedule)

        # --- ZMIANA: PRZYCISK DODAWANIA ZALECEŃ ZAMIAST WIZYT ---
        self.add_button("DODAJ ZALECENIA").clicked.connect(self.open_add_recommendations)
        self.add_button("ZLEĆ BADANIE").clicked.connect(self.open_add_lab_test)

    def reset_to_my_schedule(self):
        self.refresh_list()

    def get_sql_query(self):
        # Pobieramy też kolumnę 'recommendations' (jako 5 element, choć add_list_items używa 4)
        # Ale dla bezpieczeństwa trzymamy 4 w select, a recommendations pobierzemy osobno w razie potrzeby
        # lub dołączymy tutaj.
        # W tej wersji pobieramy recommendations, żeby mieć je w `current_selected_data`
        return """
            SELECT id, visit_date, title, pesel, recommendations
            FROM visits 
            WHERE doctor_id = %s AND visit_date >= NOW()
            ORDER BY visit_date ASC
        """

    def add_list_items(self, data_rows):
        styles = ["background-color: #FFFFFF;", "background-color: #F8F9F9;"]
        WIDTH_DATE = 140
        WIDTH_PERSON = 150

        # Teraz data_rows może mieć 5 kolumn (id, date, title, pesel, recommendations)
        for i, row in enumerate(data_rows):
            vid = row[0]
            data = row[1]
            tytul = row[2]
            pesel = row[3]
            # row[4] to zalecenia, jeśli istnieją
            recs = row[4] if len(row) > 4 else ""

            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""
            list_item = QListWidgetItem()

            # Zapisujemy dane (w tym zalecenia) w obiekcie
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, tytul, str(pesel), recs))

            frame = QFrame()
            frame.setFixedHeight(65)
            frame.setStyleSheet(f"{styles[i % 2]} border-bottom: 1px solid #E0E0E0; color: #2C3E50;")

            frame.setProperty("visit_id", vid)

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(15, 0, 15, 0)

            lbl_date = QLabel(data_str)
            lbl_date.setFixedWidth(WIDTH_DATE)
            lbl_date.setStyleSheet("border: none; color: #555; font-weight: bold;")
            hl.addWidget(lbl_date)

            lbl_title = QLabel(tytul)
            lbl_title.setStyleSheet("border: none; color: #2C3E50; font-size: 14px; font-weight: 500;")
            hl.addWidget(lbl_title, stretch=1)

            lbl_person = QLabel(str(pesel))
            lbl_person.setFixedWidth(WIDTH_PERSON)
            lbl_person.setStyleSheet("border: none; color: #555;")
            hl.addWidget(lbl_person)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, 65))
            self.lista_wizyt.setItemWidget(list_item, frame)

    # --- NOWA FUNKCJA OTWIERAJĄCA OKNO ZALECEŃ ---
    def open_add_recommendations(self):
        if not self.current_selected_frame:
            QMessageBox.warning(self, "Uwaga", "Najpierw wybierz wizytę z listy.")
            return

        visit_id = self.current_selected_frame.property("visit_id")

        # Pobieramy aktualne zalecenia z danych elementu listy (zapisaliśmy je tam w add_list_items)
        data = self.current_selected_data
        # data to krotka: (data_str, tytul, pesel, recs)
        current_recs = data[3] if data and len(data) > 3 else ""

        if not visit_id:
            QMessageBox.critical(self, "Błąd", "Brak ID wizyty.")
            return

        # Otwieramy okno
        if AddRecommendationWindow(visit_id, current_recs, self).exec():
            # Po zapisaniu odświeżamy listę, żeby zaktualizować dane
            self.refresh_list()

    def open_add_lab_test(self):
        if not self.current_selected_frame:
            QMessageBox.warning(self, "Uwaga", "Najpierw wybierz wizytę z listy.")
            return

        visit_id = self.current_selected_frame.property("visit_id")
        if not visit_id:
            return

        AddLabTestWindow(visit_id, self).exec()

    def load_patient_by_code(self):
        code = self.code_input.text().strip()
        if len(code) != 6:
            QMessageBox.warning(self, "Błąd", "Kod musi mieć 6 cyfr.")
            return

        if not self.connection: return

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT pesel FROM patient_codes WHERE code = %s AND expiration_time > %s",
                               (code, datetime.now()))
                res = cursor.fetchone()
                if not res:
                    QMessageBox.warning(self, "Błąd", "Kod nieprawidłowy lub wygasł.")
                    return

                pesel = res[0]
                # Pobieramy też zalecenia (recommendations)
                cursor.execute(
                    "SELECT id, visit_date, title, pesel, recommendations FROM visits WHERE pesel = %s ORDER BY visit_date DESC",
                    (pesel,))
                rows = cursor.fetchall()

                self.lista_wizyt.clear()
                self.add_list_items(rows)

                QMessageBox.information(self, "Sukces", f"Załadowano kartę pacjenta: {pesel}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))