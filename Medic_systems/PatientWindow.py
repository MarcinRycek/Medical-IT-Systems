import random
import psycopg2
from functools import partial
from datetime import datetime, timedelta, time, date
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFrame, QPushButton,
                               QMessageBox, QListWidgetItem, QHBoxLayout, QScrollArea,
                               QWidget, QLineEdit, QComboBox, QCalendarWidget, QGridLayout, QTableView)
from PySide6.QtCore import Qt, QSize, QDate
from BaseWindow import BaseWindow, conn_str


# --- OKNO UMAWIANIA WIZYTY ---
class BookVisitWindow(QDialog):
    def __init__(self, patient_pesel, parent=None):
        super().__init__(parent)
        self.patient_pesel = patient_pesel
        self.selected_time = None
        self.setWindowTitle("Umów Wizytę")
        self.resize(520, 750)

        # --- STYLIZACJA (Poprawiona) ---
        self.setStyleSheet("""
            QDialog { background-color: #F8F9FA; }
            QLabel { color: #2C3E50; font-size: 13px; font-weight: bold; }

            QLineEdit, QComboBox { 
                background-color: white; 
                border: 1px solid #BDC3C7; 
                border-radius: 4px;
                padding: 8px; 
                color: #2C3E50;
            }

            /* KALENDARZ - Wygląd ogólny */
            QCalendarWidget QWidget { 
                alternate-background-color: #E8F6F3; 
                background-color: white;
            }

            /* Przycisk nawigacji (strzałki, miesiąc) */
            QCalendarWidget QToolButton {
                color: black;
                font-weight: bold;
                icon-size: 24px;
                background-color: transparent;
                margin: 5px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #D6EAF8;
                border-radius: 5px;
            }

            /* Ukrycie pól edycji roku (spinbox) dla czystszego wyglądu */
            QCalendarWidget QSpinBox {
                background-color: white;
                color: black;
                selection-background-color: #3498DB;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Rezerwacja Wizyty")
        header.setStyleSheet("color: #2C3E50; font-size: 20px; border: none; font-weight: 800;")
        layout.addWidget(header)

        # 1. WYBÓR LEKARZA
        layout.addWidget(QLabel("1. Wybierz Lekarza:"))
        self.doctor_combo = QComboBox()
        # Podłączymy sygnał dopiero po załadowaniu danych
        layout.addWidget(self.doctor_combo)

        # 2. KALENDARZ
        layout.addWidget(QLabel("2. Wybierz Datę (Pn-Pt):"))
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setMinimumDate(datetime.now().date())
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

        # --- KLUCZOWA POPRAWKA KOLORÓW ---
        # Znajdujemy wewnętrzną tabelę kalendarza i nakładamy styl bezpośrednio na nią
        cal_view = self.calendar.findChild(QTableView, "qt_calendar_calendarview")
        if cal_view:
            cal_view.setStyleSheet("""
                QTableView {
                    background-color: white;
                    selection-background-color: #3498DB; /* WYRAŹNY NIEBIESKI */
                    selection-color: white;              /* BIAŁY TEKST */
                    color: black;
                    outline: 0;
                }
                QTableView::item:hover {
                    background-color: #D6EAF8;
                }
            """)

        self.calendar.clicked.connect(self.on_calendar_clicked)
        layout.addWidget(self.calendar)

        # 3. GODZINY
        self.lbl_hours = QLabel("3. Wybierz Godzinę:")
        layout.addWidget(self.lbl_hours)

        self.time_slots_area = QScrollArea()
        self.time_slots_area.setWidgetResizable(True)
        self.time_slots_area.setFixedHeight(180)
        self.time_slots_area.setFrameShape(QFrame.Shape.NoFrame)

        self.time_slots_content = QWidget()
        self.time_slots_content.setStyleSheet("background-color: transparent;")

        # Inicjalizacja layoutu
        self.time_slots_layout = QGridLayout(self.time_slots_content)
        self.time_slots_layout.setSpacing(10)

        self.time_slots_area.setWidget(self.time_slots_content)
        layout.addWidget(self.time_slots_area)

        # 4. CEL WIZYTY
        layout.addWidget(QLabel("4. Cel wizyty / Dolegliwości:"))
        self.title_in = QLineEdit()
        self.title_in.setPlaceholderText("Np. Ból gardła, Kontrola")
        layout.addWidget(self.title_in)

        layout.addStretch()

        # PRZYCISK ZAPISU
        self.save_btn = QPushButton("POTWIERDŹ REZERWACJĘ")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setFixedHeight(50)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB; 
                color: white; 
                font-weight: bold; 
                border-radius: 6px; 
                font-size: 15px;
                border: none;
            }
            QPushButton:hover { background-color: #2980B9; }
            QPushButton:disabled { background-color: #BDC3C7; color: #F0F0F0; }
        """)
        self.save_btn.clicked.connect(self.save)
        layout.addWidget(self.save_btn)

        # Ładujemy dane
        self.load_doctors()
        self.doctor_combo.currentIndexChanged.connect(self.refresh_time_slots)
        self.refresh_time_slots()

    def load_doctors(self):
        try:
            conn = psycopg2.connect(conn_str)
            cur = conn.cursor()
            cur.execute("SELECT login, id FROM users WHERE role IN ('Lekarz', 'lekarz')")
            doctors = cur.fetchall()
            conn.close()

            if not doctors:
                self.doctor_combo.addItem("Brak lekarzy", None)
                self.doctor_combo.setEnabled(False)
            else:
                for login, doc_id in doctors:
                    self.doctor_combo.addItem(f"Dr {login}", doc_id)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd listy lekarzy: {e}")

    def on_calendar_clicked(self, date):
        self.refresh_time_slots()

    def refresh_time_slots(self):
        """Generuje przyciski godzin, blokuje zajęte i weekendy."""
        if not hasattr(self, 'time_slots_layout'): return

        # 1. Czyścimy stare przyciski
        for i in reversed(range(self.time_slots_layout.count())):
            item = self.time_slots_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        self.selected_time = None
        self.update_save_button_state()

        doctor_id = self.doctor_combo.currentData()
        if not doctor_id: return

        q_date = self.calendar.selectedDate()
        selected_date = date(q_date.year(), q_date.month(), q_date.day())

        # --- SPRAWDZENIE WEEKENDU ---
        # 0=Poniedziałek ... 5=Sobota, 6=Niedziela
        if selected_date.weekday() >= 5:
            lbl = QLabel("Lekarz nie przyjmuje w weekendy.\nWybierz dzień od poniedziałku do piątku.")
            lbl.setStyleSheet("color: #E74C3C; font-weight: bold; font-size: 14px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.time_slots_layout.addWidget(lbl, 0, 0, 1, 4)
            self.lbl_hours.setText("3. Wybierz Godzinę (Weekend - Zamknięte):")
            return

        self.lbl_hours.setText("3. Wybierz Godzinę:")

        # Pobieramy zajęte godziny z bazy
        taken_times = []
        try:
            conn = psycopg2.connect(conn_str)
            cur = conn.cursor()
            query = """
                SELECT EXTRACT(HOUR FROM visit_date), EXTRACT(MINUTE FROM visit_date)
                FROM visits 
                WHERE doctor_id = %s AND DATE(visit_date) = %s
            """
            cur.execute(query, (doctor_id, selected_date))
            rows = cur.fetchall()
            conn.close()

            for h, m in rows:
                taken_times.append(f"{int(h):02d}:{int(m):02d}")

        except Exception as e:
            print(f"Błąd pobierania zajętości: {e}")

        # Generujemy godziny
        start_h = 7
        end_h = 19
        row = 0
        col = 0
        current_dt = datetime.now()

        for h in range(start_h, end_h):
            for m in [0, 30]:
                time_str = f"{h:02d}:{m:02d}"

                btn = QPushButton(time_str)
                btn.setCheckable(True)
                btn.setFixedSize(70, 35)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)

                is_taken = time_str in taken_times

                # Blokada przeszłości
                is_past = False
                if selected_date == current_dt.date():
                    slot_time = datetime.combine(selected_date, time(h, m))
                    if slot_time < current_dt:
                        is_past = True

                if selected_date < current_dt.date():
                    is_past = True

                if is_taken:
                    btn.setEnabled(False)
                    btn.setStyleSheet(
                        "background-color: #E74C3C; color: white; border: none; border-radius: 4px; font-weight: bold;")
                    btn.setToolTip("Termin zajęty")
                elif is_past:
                    btn.setEnabled(False)
                    btn.setStyleSheet("background-color: #BDC3C7; color: #888; border: none; border-radius: 4px;")
                    btn.setToolTip("Termin minął")
                else:
                    # Wolny termin
                    btn.setStyleSheet("""
                        QPushButton { 
                            background-color: #27AE60; 
                            color: white; 
                            border: none; 
                            border-radius: 4px; 
                            font-weight: bold;
                        }
                        QPushButton:checked { 
                            background-color: #2C3E50; 
                            border: 2px solid #F1C40F; 
                        }
                        QPushButton:hover:!checked {
                            background-color: #2ECC71;
                        }
                    """)
                    btn.clicked.connect(partial(self.on_time_clicked, btn, time_str))

                self.time_slots_layout.addWidget(btn, row, col)

                col += 1
                if col > 4:  # 5 kolumn
                    col = 0
                    row += 1

    def on_time_clicked(self, clicked_btn, time_str):
        for i in range(self.time_slots_layout.count()):
            item = self.time_slots_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QPushButton) and item.widget() != clicked_btn:
                item.widget().setChecked(False)

        if clicked_btn.isChecked():
            self.selected_time = time_str
        else:
            self.selected_time = None

        self.update_save_button_state()

    def update_save_button_state(self):
        if self.selected_time:
            self.save_btn.setText(f"UMÓW: {self.calendar.selectedDate().toString('dd.MM.yyyy')} - {self.selected_time}")
            self.save_btn.setEnabled(True)
        else:
            self.save_btn.setText("Wybierz godzinę")
            self.save_btn.setEnabled(False)

    def save(self):
        doctor_id = self.doctor_combo.currentData()
        title = self.title_in.text().strip()

        if not title:
            QMessageBox.warning(self, "Brak celu", "Wpisz cel wizyty / dolegliwości.")
            return

        if not self.selected_time:
            QMessageBox.warning(self, "Brak terminu", "Wybierz godzinę z listy.")
            return

        q_date = self.calendar.selectedDate()
        date_str = f"{q_date.year()}-{q_date.month():02d}-{q_date.day():02d} {self.selected_time}"

        try:
            valid_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")

            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM visits WHERE doctor_id = %s AND visit_date = %s",
                           (doctor_id, valid_date))
            if cursor.fetchone():
                conn.close()
                QMessageBox.warning(self, "Błąd", "Ktoś właśnie zajął ten termin! Odświeżam listę.")
                self.refresh_time_slots()
                return

            cursor.execute("INSERT INTO visits (visit_date, title, pesel, doctor_id) VALUES (%s, %s, %s, %s)",
                           (valid_date, title, self.patient_pesel, doctor_id))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sukces", f"Wizyta umówiona na {date_str}")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Błąd Bazy", str(e))


# --- OKNO SZCZEGÓŁÓW (Bez zmian) ---
class VisitDetailsWindow(QDialog):
    def __init__(self, data_wizyty, tytul_wizyty, lekarz, lab_results=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Karta Wizyty")
        self.resize(550, 600)
        self.setStyleSheet("background-color: #F8F9FA;")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_lbl = QLabel(f"{tytul_wizyty}", self)
        title_lbl.setStyleSheet("color: #2C3E50; font-size: 22px; font-weight: bold; border: none;")
        layout.addWidget(title_lbl)

        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 8px;")
        info_layout = QVBoxLayout(info_frame)

        lbl_date = QLabel(f"DATA WIZYTY:\n{data_wizyty}")
        lbl_date.setStyleSheet("color: #555; font-size: 13px; border: none; font-weight: bold;")
        info_layout.addWidget(lbl_date)
        info_layout.addSpacing(5)
        lbl_doc = QLabel(f"PROWADZĄCY:\n{lekarz}")
        lbl_doc.setStyleSheet("color: #555; font-size: 13px; border: none; font-weight: bold;")
        info_layout.addWidget(lbl_doc)
        layout.addWidget(info_frame)

        if lab_results:
            layout.addSpacing(20)
            header_lbl = QLabel("WYNIKI BADAŃ")
            header_lbl.setStyleSheet(
                "color: #34495E; font-size: 14px; font-weight: bold; border: none; border-bottom: 2px solid #3498DB; padding-bottom: 5px;")
            layout.addWidget(header_lbl)

            results_area = QScrollArea()
            results_area.setWidgetResizable(True)
            results_area.setFrameShape(QFrame.Shape.NoFrame)

            results_content = QWidget()
            results_content.setStyleSheet("background-color: transparent;")
            results_layout = QVBoxLayout(results_content)
            results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            results_layout.setSpacing(10)

            for title, desc in lab_results:
                res_frame = QFrame()
                res_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #D6DBDF; border-radius: 6px;")
                res_l = QVBoxLayout(res_frame)
                res_l.setContentsMargins(15, 15, 15, 15)

                t_lbl = QLabel(title.upper())
                t_lbl.setStyleSheet("font-weight: bold; color: #2980B9; font-size: 14px; border: none;")

                desc_text = desc if desc else "Oczekiwanie na wynik..."
                d_lbl = QLabel(desc_text)
                d_lbl.setWordWrap(True)
                d_lbl.setStyleSheet(f"color: #2C3E50; border: none; margin-top: 5px; font-size: 13px;")

                res_l.addWidget(t_lbl)
                res_l.addWidget(d_lbl)
                results_layout.addWidget(res_frame)

            results_area.setWidget(results_content)
            layout.addWidget(results_area)
        else:
            layout.addStretch()
            layout.addWidget(QLabel("Brak zleconych badań.", alignment=Qt.AlignmentFlag.AlignCenter))
            layout.addStretch()

        close_button = QPushButton("ZAMKNIJ", self)
        close_button.setStyleSheet(
            "QPushButton { background-color: #ECF0F1; color: #2C3E50; border: 1px solid #BDC3C7; padding: 10px 20px; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #D5D8DC; }")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)


# --- GŁÓWNE OKNO PACJENTA ---
class PatientWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Pacjent")
        self.code_label = None
        self.init_ui()

    def setup_sidebar_widgets(self):
        btn_book = QPushButton("UMÓW WIZYTĘ", self.side_panel)
        btn_book.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_book.setFixedHeight(50)
        btn_book.setStyleSheet("""
            QPushButton { 
                background-color: #27AE60; 
                color: white; 
                border-radius: 6px; 
                padding: 10px; 
                font-weight: bold;
                border: none;
                font-size: 13px;
                text-align: center;
            } 
            QPushButton:hover { background-color: #2ECC71; }
        """)
        btn_book.clicked.connect(self.open_book_visit)
        self.side_layout.addWidget(btn_book)

        self.side_layout.addSpacing(20)

        code = self.fetch_code()
        code_text = str(code) if code else "------"

        frame = QFrame(self)
        frame.setFixedSize(240, 150)
        frame.setStyleSheet("""
            QFrame { background-color: #34495E; border: 2px dashed #5D6D7E; border-radius: 15px; }
        """)

        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        title_lbl = QLabel("KOD DLA LEKARZA", frame)
        title_lbl.setStyleSheet("color: #BDC3C7; font-size: 10px; font-weight: bold; border: none;")
        layout.addWidget(title_lbl)

        self.code_label = QLabel(code_text, frame)
        self.code_label.setStyleSheet(
            "font-size: 32px; font-weight: bold; letter-spacing: 3px; color: #E74C3C; border: none;")
        layout.addWidget(self.code_label)

        btn = QPushButton("GENERUJ NOWY", frame)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background-color: #2980B9; color: white; border-radius: 6px; padding: 6px; font-weight: bold; border: none; font-size: 11px; } 
            QPushButton:hover { background-color: #3498DB; }
        """)
        btn.clicked.connect(self.generate_code)
        layout.addWidget(btn)

        self.side_layout.addWidget(frame, alignment=Qt.AlignmentFlag.AlignCenter)

    def open_book_visit(self):
        if BookVisitWindow(self.user_id, self).exec():
            self.refresh_list()

    def get_sql_query(self):
        return """
            SELECT v.id, v.visit_date, v.title, u.login 
            FROM visits v
            JOIN users u ON u.id = COALESCE(v.doctor_id, v.laborant_id)
            WHERE v.pesel = %s
            ORDER BY v.visit_date DESC
        """

    def add_list_items(self, data_rows):
        styles = ["background-color: #FFFFFF;", "background-color: #F8F9F9;"]
        WIDTH_DATE = 140
        WIDTH_PERSON = 150

        for i, (vid, data, tytul, lekarz) in enumerate(data_rows):
            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""
            lekarz_str = str(lekarz)

            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, tytul, lekarz_str))

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

            l3 = QLabel("Dr " + lekarz_str)
            l3.setFixedWidth(WIDTH_PERSON)
            l3.setStyleSheet("border: none; color: #555;")
            hl.addWidget(l3)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, 65))
            self.lista_wizyt.setItemWidget(list_item, frame)

    def _show_visit_details(self):
        if not self.current_selected_frame:
            QMessageBox.warning(self, "Uwaga", "Wybierz wizytę z listy.")
            return

        d, t, o = self.current_selected_data
        visit_id = self.current_selected_frame.property("visit_id")

        lab_results = []
        if self.connection and visit_id:
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT title, description FROM lab_tests WHERE visit_id = %s", (visit_id,))
                    lab_results = cursor.fetchall()
            except Exception as e:
                print(f"Błąd pobierania badań: {e}")

        VisitDetailsWindow(d, t, o, lab_results=lab_results, parent=self).exec()

    def fetch_code(self):
        if not self.connection: return None
        try:
            with self.connection.cursor() as cur:
                cur.execute("SELECT code FROM patient_codes WHERE pesel = %s AND expiration_time > %s",
                            (self.user_id, datetime.now()))
                res = cur.fetchone()
                return res[0] if res else None
        except:
            return None

    def generate_code(self):
        if not self.connection:
            QMessageBox.critical(self, "Błąd", "Brak połączenia z bazą.")
            return
        new_code = str(random.randint(100000, 999999))
        exp_time = datetime.now() + timedelta(minutes=15)
        try:
            with self.connection.cursor() as cur:
                cur.execute("SELECT 1 FROM patient_codes WHERE pesel = %s", (self.user_id,))
                if cur.fetchone():
                    cur.execute("UPDATE patient_codes SET code=%s, expiration_time=%s WHERE pesel=%s",
                                (new_code, exp_time, self.user_id))
                else:
                    cur.execute("INSERT INTO patient_codes (pesel, code, expiration_time) VALUES (%s, %s, %s)",
                                (self.user_id, new_code, exp_time))
                self.connection.commit()
                self.code_label.setText(new_code)
                QMessageBox.information(self, "Sukces", "Nowy kod wygenerowany (ważny 15 min)!")
        except Exception as e:
            self.connection.rollback()
            QMessageBox.critical(self, "Błąd", str(e))