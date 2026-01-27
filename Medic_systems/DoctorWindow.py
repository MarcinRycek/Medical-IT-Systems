import psycopg2
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFrame,
                               QListWidgetItem, QHBoxLayout)
from PySide6.QtCore import Qt, QSize
from BaseWindow import BaseWindow, conn_str

DIALOG_STYLE = """
    QDialog { background-color: #F8F9FA; }
    QLabel { color: #2C3E50; font-size: 13px; font-weight: bold; }
    QLineEdit { 
        background-color: white; 
        border: 1px solid #BDC3C7; 
        border-radius: 4px;
        padding: 8px; 
        color: #2C3E50;
        font-size: 13px;
    }
    QLineEdit:focus { border: 2px solid #3498DB; }
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

        header = QLabel("Nowe Zlecenie")
        header.setStyleSheet("color: #2C3E50; font-size: 18px; border: none; margin-bottom: 10px;")
        layout.addWidget(header)

        layout.addWidget(QLabel("Nazwa badania (np. Morfologia, RTG):"))
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


class AddVisitWindow(QDialog):
    def __init__(self, doctor_id, parent=None):
        super().__init__(parent)
        self.doctor_id = doctor_id
        self.setWindowTitle("Dodaj Nową Wizytę")
        self.resize(400, 450)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(25, 25, 25, 25)

        header = QLabel("Rejestracja Wizyty")
        header.setStyleSheet("color: #2C3E50; font-size: 18px; border: none; margin-bottom: 10px;")
        layout.addWidget(header)

        self.date_in = QLineEdit()
        self.date_in.setPlaceholderText("YYYY-MM-DD HH:MM")
        self.date_in.setText(datetime.now().strftime("%Y-%m-%d %H:%M"))

        self.title_in = QLineEdit()
        self.title_in.setPlaceholderText("Np. Konsultacja, Szczepienie")

        self.code_in = QLineEdit()
        self.code_in.setPlaceholderText("6 cyfr od pacjenta")

        layout.addWidget(QLabel("Data Wizyty:"))
        layout.addWidget(self.date_in)

        layout.addWidget(QLabel("Cel Wizyty / Tytuł:"))
        layout.addWidget(self.title_in)

        layout.addWidget(QLabel("Kod Autoryzacji Pacjenta:"))
        layout.addWidget(self.code_in)

        layout.addStretch()

        btn = QPushButton("ZATWIERDŹ")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(BTN_STYLE)
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        date_text = self.date_in.text().strip()
        title = self.title_in.text().strip()
        code = self.code_in.text().strip()

        if not date_text or not title or not code:
            QMessageBox.warning(self, "Błąd", "Wypełnij wszystkie pola.")
            return
        if len(code) != 6 or not code.isdigit():
            QMessageBox.warning(self, "Błąd", "Kod pacjenta musi składać się z 6 cyfr.")
            return

        try:
            valid_date = datetime.strptime(date_text, "%Y-%m-%d %H:%M")
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Zły format daty. Wymagany: RRRR-MM-DD GG:MM")
            return

        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()

            cursor.execute("SELECT pesel FROM patient_codes WHERE code = %s AND expiration_time > %s",
                           (code, datetime.now()))
            res = cursor.fetchone()

            if not res:
                conn.close()
                QMessageBox.warning(self, "Błąd", "Kod nieprawidłowy lub wygasł.")
                return

            pesel = res[0]
            cursor.execute("INSERT INTO visits (visit_date, title, pesel, doctor_id) VALUES (%s, %s, %s, %s)",
                           (valid_date, title, pesel, self.doctor_id))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Sukces", f"Dodano wizytę dla pacjenta (PESEL: {pesel}).")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd Bazy", str(e))


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
        self.add_button("DODAJ WIZYTĘ").clicked.connect(self.open_add_visit)
        self.add_button("ZLEĆ BADANIE").clicked.connect(self.open_add_lab_test)

    def reset_to_my_schedule(self):
        self.refresh_list()

    def refresh_list(self):
        # Nadpisujemy refresh_list, aby przekazać 2 parametry: ID i DATĘ
        self.current_selected_frame = None
        self.current_selected_data = None
        self.lista_wizyt.clear()

        # Zapytanie korzystające z %s i %s
        query = """
            SELECT id, visit_date, title, pesel 
            FROM visits 
            WHERE doctor_id = %s AND visit_date >= %s
            ORDER BY visit_date ASC
        """

        if not self.connection: return
        try:
            with self.connection.cursor() as cursor:
                # DEBUG: Sprawdź w konsoli, jakie ID jest używane
                print(f"DEBUG: Pobieranie wizyt dla Lekarza ID: {self.user_id}, od daty: {datetime.now()}")

                # Przekazujemy ID lekarza i aktualny czas z Pythona
                cursor.execute(query, (self.user_id, datetime.now()))
                rows = cursor.fetchall()
                self.add_list_items(rows)

                if not rows:
                    print("DEBUG: Brak wizyt spełniających kryteria.")

        except Exception as e:
            print(f"SQL Error: {e}")

    def add_list_items(self, data_rows):
        styles = ["background-color: #FFFFFF;", "background-color: #F8F9F9;"]
        WIDTH_DATE = 140
        WIDTH_PERSON = 150

        for i, (vid, data, tytul, pesel) in enumerate(data_rows):
            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""
            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, tytul, str(pesel)))

            frame = QFrame()
            frame.setFixedHeight(65)
            frame.setStyleSheet(f"{styles[i % 2]} border-bottom: 1px solid #E0E0E0; color: #2C3E50;")
            frame.setProperty("visit_id", vid)

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(15, 0, 15, 0)

            l1 = QLabel(data_str)
            l1.setFixedWidth(WIDTH_DATE)
            l1.setStyleSheet("border: none; color: #555; font-weight: bold;")
            hl.addWidget(l1)

            l2 = QLabel(tytul)
            l2.setStyleSheet("border: none; color: #2C3E50; font-size: 14px; font-weight: 500;")
            hl.addWidget(l2, stretch=1)

            l3 = QLabel(str(pesel))
            l3.setFixedWidth(WIDTH_PERSON)
            l3.setStyleSheet("border: none; color: #555;")
            hl.addWidget(l3)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, 65))
            self.lista_wizyt.setItemWidget(list_item, frame)

    def open_add_visit(self):
        if AddVisitWindow(self.user_id, self).exec():
            self.refresh_list()

    def open_add_lab_test(self):
        if not self.current_selected_frame:
            QMessageBox.warning(self, "Uwaga", "Najpierw wybierz wizytę z listy.")
            return

        visit_id = self.current_selected_frame.property("visit_id")

        if not visit_id:
            QMessageBox.critical(self, "Błąd", "Nie udało się pobrać ID wizyty.")
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
                cursor.execute(
                    "SELECT id, visit_date, title, pesel FROM visits WHERE pesel = %s ORDER BY visit_date DESC",
                    (pesel,))
                rows = cursor.fetchall()

                self.lista_wizyt.clear()
                self.add_list_items(rows)

                QMessageBox.information(self, "Sukces", f"Załadowano kartę pacjenta: {pesel}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))