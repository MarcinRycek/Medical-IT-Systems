import psycopg2
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFrame,
                               QListWidgetItem, QHBoxLayout)
from PySide6.QtCore import Qt, QSize
from BaseWindow import BaseWindow, conn_str


# --- OKNO ZLECANIA BADANIA (Styl: Czarny tekst) ---
class AddLabTestWindow(QDialog):
    def __init__(self, visit_id, parent=None):
        super().__init__(parent)
        self.visit_id = visit_id
        self.setWindowTitle("Zleć Badanie")
        self.resize(400, 250)

        self.setStyleSheet("""
            QDialog { background-color: #F0F0F0; }
            QLabel { color: black; }
            QLineEdit { color: black; background-color: white; border: 1px solid #AAA; padding: 5px; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        layout.addWidget(QLabel("<h2>Nowe Zlecenie</h2>"))
        layout.addWidget(QLabel("Nazwa badania (np. Morfologia, RTG):"))

        self.title_in = QLineEdit()
        self.title_in.setPlaceholderText("Wpisz nazwę badania...")
        layout.addWidget(self.title_in)

        info_lbl = QLabel("Opis/Wyniki zostaną uzupełnione przez Laboranta.")
        info_lbl.setStyleSheet("color: #555; font-style: italic; font-size: 11px;")
        layout.addWidget(info_lbl)

        layout.addStretch()

        btn = QPushButton("ZLEĆ BADANIE")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("background-color: #2F9ADF; color: white; font-weight: bold; border: 1px solid #1F8ACF;")
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


# --- OKNO DODAWANIA WIZYTY (Styl: Czarny tekst) ---
class AddVisitWindow(QDialog):
    def __init__(self, doctor_id, parent=None):
        super().__init__(parent)
        self.doctor_id = doctor_id
        self.setWindowTitle("Dodaj Nową Wizytę")
        self.resize(400, 400)

        self.setStyleSheet("""
            QDialog { background-color: #F0F0F0; }
            QLabel { color: black; font-size: 13px; font-weight: bold; }
            QLineEdit { color: black; background-color: white; border: 1px solid #AAA; padding: 5px; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        header = QLabel("<h2>Nowa Wizyta</h2>")
        header.setStyleSheet("color: black; border: none;")
        layout.addWidget(header)

        self.date_in = QLineEdit()
        self.date_in.setPlaceholderText("YYYY-MM-DD HH:MM")
        self.date_in.setText(datetime.now().strftime("%Y-%m-%d %H:%M"))

        self.title_in = QLineEdit()
        self.title_in.setPlaceholderText("Np. Konsultacja")

        self.pesel_in = QLineEdit()
        self.pesel_in.setPlaceholderText("PESEL Pacjenta")

        layout.addWidget(QLabel("Data:"))
        layout.addWidget(self.date_in)

        layout.addWidget(QLabel("Tytuł:"))
        layout.addWidget(self.title_in)

        layout.addWidget(QLabel("Pacjent (PESEL):"))
        layout.addWidget(self.pesel_in)

        layout.addStretch()

        btn = QPushButton("ZATWIERDŹ")
        btn.setFixedHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("background-color: #2F9ADF; color: white; font-weight: bold; border: 1px solid #1F8ACF;")
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        date_text = self.date_in.text().strip()
        title = self.title_in.text().strip()
        pesel = self.pesel_in.text().strip()

        if not date_text or not title or not pesel:
            QMessageBox.warning(self, "Błąd", "Wypełnij wszystkie pola.")
            return

        if len(pesel) != 11 or not pesel.isdigit():
            QMessageBox.warning(self, "Błąd", "PESEL musi mieć 11 cyfr.")
            return

        try:
            valid_date = datetime.strptime(date_text, "%Y-%m-%d %H:%M")
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Zły format daty. Wymagany: RRRR-MM-DD GG:MM")
            return

        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO visits (visit_date, title, pesel, doctor_id) VALUES (%s, %s, %s, %s)",
                           (valid_date, title, pesel, self.doctor_id))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Sukces", "Wizyta dodana.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))


# --- GŁÓWNE OKNO LEKARZA ---
class DoctorWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Lekarz")
        self.code_input = None
        self.init_ui()

    def setup_sidebar_widgets(self):
        self.setup_info_widget("PANEL LEKARZA", f"ID: {self.user_id}")

        search_frame = QFrame(self)
        search_frame.setFixedHeight(150)
        # Stylizacja panelu bocznego
        search_frame.setStyleSheet("""
            QFrame { background-color: white; border: 2px solid #CCC; }
            QLabel { color: #333; }
            QLineEdit { color: black; background-color: white; border: 1px solid #AAA; }
        """)

        layout = QVBoxLayout(search_frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        lbl = QLabel("DOSTĘP DO PACJENTA", search_frame)
        lbl.setStyleSheet("color: #333; font-weight: bold; font-size: 11px; border: none;")

        self.code_input = QLineEdit(search_frame)
        self.code_input.setPlaceholderText("Kod (6 cyfr)")
        self.code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        search_btn = QPushButton("POBIERZ HISTORIĘ", search_frame)
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.setStyleSheet("""
            QPushButton { background-color: #2F9ADF; color: white; font-weight: bold; padding: 5px; border: none;}
            QPushButton:hover { background-color: #1F8ACF; }
        """)
        search_btn.clicked.connect(self.load_patient_by_code)

        layout.addWidget(lbl)
        layout.addWidget(self.code_input)
        layout.addWidget(search_btn)

        self.side_layout.addWidget(search_frame)

    def setup_extra_buttons(self):
        self.add_button("DODAJ WIZYTĘ").clicked.connect(self.open_add_visit)
        self.add_button("ZLEĆ BADANIE").clicked.connect(self.open_add_lab_test)

    def open_add_visit(self):
        # Dodawanie wizyty (może być dla nowego pacjenta, nie wpływa na widok listy)
        if AddVisitWindow(self.user_id, self).exec():
            # Po dodaniu NIE odświeżamy listy automatycznie na "wszystkie",
            # chyba że chcemy załadować tego konkretnego pacjenta, ale tu zostawiamy puste dla bezpieczeństwa.
            pass

    def open_add_lab_test(self):
        if not self.current_selected_frame:
            QMessageBox.warning(self, "Uwaga", "Najpierw wyszukaj pacjenta i wybierz wizytę z listy.")
            return

        visit_id = self.current_selected_frame.property("visit_id")

        if not visit_id:
            QMessageBox.critical(self, "Błąd", "Nie udało się pobrać ID wizyty.")
            return

        AddLabTestWindow(visit_id, self).exec()

    def get_sql_query(self):
        # --- ZMIANA: Zwracamy pusty string ---
        # Domyślnie lista ma być pusta. Lekarz nie widzi nic, dopóki nie wpisze kodu.
        return ""

    def load_patient_by_code(self):
        code = self.code_input.text().strip()
        if len(code) != 6:
            QMessageBox.warning(self, "Błąd", "Kod musi mieć 6 cyfr.")
            return

        if not self.connection: return

        try:
            with self.connection.cursor() as cursor:
                # 1. Sprawdzamy kod
                cursor.execute("SELECT pesel FROM patient_codes WHERE code = %s AND expiration_time > %s",
                               (code, datetime.now()))
                res = cursor.fetchone()
                if not res:
                    QMessageBox.warning(self, "Błąd", "Kod nieprawidłowy lub wygasł.")
                    return

                pesel = res[0]

                # 2. Pobieramy historię TEGO konkretnego pacjenta
                cursor.execute(
                    "SELECT id, visit_date, title, doctor_id FROM visits WHERE pesel = %s ORDER BY visit_date DESC",
                    (pesel,))
                rows = cursor.fetchall()

                self.lista_wizyt.clear()
                self.add_list_items(rows)

                QMessageBox.information(self, "Sukces", f"Załadowano kartę pacjenta: {pesel}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    # --- NADPISANIE FUNKCJI LISTY ---
    def add_list_items(self, data_rows):
        styles = ["background-color: #FFFFFF;", "background-color: #E8E8E8;"]

        for i, (vid, data, tytul, osoba) in enumerate(data_rows):
            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""
            osoba_str = str(osoba)

            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, tytul, osoba_str))

            frame = QFrame()
            frame.setFixedHeight(60)
            frame.setStyleSheet(styles[i % 2] + "border-bottom: 1px solid #AAA; color: black;")

            # Zapamiętujemy ID wizyty
            frame.setProperty("visit_id", vid)

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(10, 0, 10, 0)

            labels = [data_str, tytul, osoba_str]
            for j, txt in enumerate(labels):
                lbl = QLabel(txt)
                lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                lbl.setStyleSheet("border: none; color: black; font-size: 13px;")
                hl.addWidget(lbl, stretch=1 if j == 1 else 0)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, 60))
            self.lista_wizyt.setItemWidget(list_item, frame)