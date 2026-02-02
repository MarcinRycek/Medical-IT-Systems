import random
import re
import psycopg2
from functools import partial
from datetime import datetime, timedelta, time, date

# Pobieranie lokalnej strefy czasowej
try:
    LOCAL_TZ = datetime.now().astimezone().tzinfo
except:
    LOCAL_TZ = None

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFrame, QPushButton,
                               QMessageBox, QListWidgetItem, QHBoxLayout, QScrollArea,
                               QWidget, QLineEdit, QComboBox, QCalendarWidget,
                               QGridLayout, QTableView, QTextEdit, QListWidget)
from PySide6.QtCore import Qt, QSize, QDate
from PySide6.QtGui import QBrush, QColor, QPalette, QTextCharFormat
from BaseWindow import BaseWindow, conn_str, DIALOG_STYLE


class BookVisitWindow(QDialog):
    def __init__(self, patient_pesel, parent=None):
        super().__init__(parent)
        self.patient_pesel = patient_pesel
        self.selected_time = None
        self.setWindowTitle("Umów Wizytę")
        self.resize(520, 780)

        # --- STYLE ---
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

            QComboBox QAbstractItemView {
                background-color: white;
                color: #2C3E50;
                selection-background-color: #95A5A6;
                selection-color: white;
            }

            /* --- KALENDARZ --- */
            QCalendarWidget QWidget#qt_calendar_navigationbar { 
                background-color: #34495E; 
                color: white;
                font-weight: bold;
            }
            QCalendarWidget QToolButton {
                color: white;
                icon-size: 25px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #2C3E50;
                background-color: white;
                selection-background-color: #95A5A6; /* Szary po kliknięciu */
                selection-color: white;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("1. Wybierz Lekarza:"))
        self.doctor_combo = QComboBox()
        # Po zmianie lekarza odświeżamy kolory w kalendarzu
        self.doctor_combo.currentIndexChanged.connect(self.on_doctor_changed)
        layout.addWidget(self.doctor_combo)

        layout.addWidget(QLabel("2. Wybierz Datę (Pn-Pt):"))
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setMinimumDate(QDate.currentDate())
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

        # Kliknięcie w kalendarz
        self.calendar.selectionChanged.connect(self.refresh_time_slots)
        self._last_selected_qdate = None
        layout.addWidget(self.calendar)

        self.lbl_hours = QLabel("3. Wybierz Godzinę:")
        layout.addWidget(self.lbl_hours)

        self.time_slots_area = QScrollArea()
        self.time_slots_area.setWidgetResizable(True)
        self.time_slots_area.setFixedHeight(180)
        self.time_slots_area.setFrameShape(QFrame.Shape.NoFrame)
        self.time_slots_content = QWidget()
        self.time_slots_layout = QGridLayout(self.time_slots_content)
        self.time_slots_area.setWidget(self.time_slots_content)
        layout.addWidget(self.time_slots_area)

        layout.addWidget(QLabel("4. Cel wizyty:"))
        self.title_in = QLineEdit()
        self.title_in.setPlaceholderText("Np. Ból gardła")
        layout.addWidget(self.title_in)

        self.save_btn = QPushButton("POTWIERDŹ REZERWACJĘ")
        self.save_btn.setFixedHeight(50)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #27AE60; color: white; font-weight: bold; border-radius: 6px; border:none; }
            QPushButton:hover { background-color: #2ECC71; }
        """)
        self.save_btn.clicked.connect(self.save)
        layout.addWidget(self.save_btn)

        self.load_doctors()
        # Inicjalne malowanie kalendarza dla pierwszego lekarza
        self.on_doctor_changed()

    def _db_connect(self):
        try:
            c = psycopg2.connect(conn_str)
            with c.cursor() as cur:
                cur.execute("SET TIME ZONE 'Europe/Warsaw'")
            c.commit()
            return c
        except Exception as e:
            print(f"DB Error: {e}")
            return None

    def load_doctors(self):
        conn = self._db_connect()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("SELECT login, id FROM users WHERE role IN ('Lekarz', 'lekarz', 'doctor')")
            doctors = cur.fetchall()
            conn.close()
            # Blokujemy sygnały podczas ładowania, żeby nie odpalać refresh x razy
            self.doctor_combo.blockSignals(True)
            for login, doc_id in doctors:
                self.doctor_combo.addItem(f"Dr {login}", doc_id)
            self.doctor_combo.blockSignals(False)
        except Exception as e:
            print(e)

    def on_doctor_changed(self):
        """Obsługa zmiany lekarza: koloruje dni i odświeża sloty."""
        self.highlight_unavailable_days()
        self.refresh_time_slots()

    def highlight_unavailable_days(self):
        """Koloruje dni, w które lekarz NIE pracuje, na jasnoczerwono."""
        # 1. Reset formatowania
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())

        doc_id = self.doctor_combo.currentData()
        if not doc_id: return

        working_days = set()

        conn = self._db_connect()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT day_of_week FROM doctor_schedules WHERE doctor_id=%s", (doc_id,))
                rows = cur.fetchall()
                for r in rows:
                    working_days.add(r[0])  # 0=Pon, 6=Nd (format bazy)
                conn.close()
            except:
                pass

        # Jeśli lekarz nie ma ustawionego grafiku, zakładamy że nie pracuje wcale (pusty zbiór)
        # Format dla dni wolnych (czerwony)
        fmt_unavailable = QTextCharFormat()
        fmt_unavailable.setBackground(QBrush(QColor("#FDEDEC")))  # Bardzo jasny czerwony
        fmt_unavailable.setForeground(QBrush(QColor("#C0392B")))  # Ciemniejszy czerwony tekst

        # 2. Iterujemy przez najbliższe 60 dni i kolorujemy
        today = QDate.currentDate()
        for i in range(60):
            check_date = today.addDays(i)
            # PySide dayOfWeek: 1=Pon...7=Nd
            # Baza day_of_week: 0=Pon...6=Nd
            db_day = check_date.dayOfWeek() - 1

            if db_day not in working_days:
                self.calendar.setDateTextFormat(check_date, fmt_unavailable)

    def _apply_selected_date_gray(self):
        """Nadaje wybranej dacie szary kolor (nadpisując czerwony jeśli trzeba)."""
        qdate = self.calendar.selectedDate()

        # Format szary (aktywny wybór)
        fmt_selected = QTextCharFormat()
        fmt_selected.setBackground(QBrush(QColor("#95A5A6")))
        fmt_selected.setForeground(QBrush(QColor("white")))

        # Jeśli zmieniliśmy datę, musimy przywrócić format "starej" daty
        # (czy była czerwona czy biała)
        if getattr(self, "_last_selected_qdate", None) and self._last_selected_qdate != qdate:
            # Najprościej: ponownie uruchomić logikę kolorowania dla całego kalendarza,
            # to przywróci czerwone tło tam gdzie trzeba.
            self.highlight_unavailable_days()

        self.calendar.setDateTextFormat(qdate, fmt_selected)
        self._last_selected_qdate = qdate

    def refresh_time_slots(self, *_):
        # Najpierw kolorujemy wybraną datę
        self._apply_selected_date_gray()

        # Czyszczenie slotów
        for i in reversed(range(self.time_slots_layout.count())):
            w = self.time_slots_layout.itemAt(i).widget()
            if w: w.setParent(None)

        self.selected_time = None
        self.save_btn.setText("Wybierz godzinę")
        self.save_btn.setEnabled(False)

        doc_id = self.doctor_combo.currentData()
        if not doc_id: return

        q_date = self.calendar.selectedDate()
        sel_date = date(q_date.year(), q_date.month(), q_date.day())

        # Obsługa grafiku Admina
        day_of_week = sel_date.weekday()
        start_h, end_h = 8, 18
        is_working_day = True

        taken = []
        conn = self._db_connect()
        if conn:
            try:
                cur = conn.cursor()

                # 1. Grafik
                cur.execute("SELECT start_time, end_time FROM doctor_schedules WHERE doctor_id=%s AND day_of_week=%s",
                            (doc_id, day_of_week))
                schedule = cur.fetchone()
                if schedule:
                    start_h = schedule[0].hour
                    end_h = schedule[1].hour
                else:
                    # Sprawdź czy lekarz w ogóle ma grafik
                    cur.execute("SELECT 1 FROM doctor_schedules WHERE doctor_id=%s LIMIT 1", (doc_id,))
                    if cur.fetchone():
                        is_working_day = False  # Ma grafik, ale nie dziś

                # 2. Zajęte
                cur.execute(
                    "SELECT EXTRACT(HOUR FROM visit_date), EXTRACT(MINUTE FROM visit_date) FROM visits WHERE doctor_id=%s AND DATE(visit_date)=%s",
                    (doc_id, sel_date))
                for h, m in cur.fetchall(): taken.append(f"{int(h):02d}:{int(m):02d}")

                conn.close()
            except Exception as e:
                print(e)

        if not is_working_day:
            self.lbl_hours.setText("Lekarz nie przyjmuje w tym dniu.")
            return

        self.lbl_hours.setText(f"3. Wybierz Godzinę ({start_h}:00 - {end_h}:00):")

        row, col = 0, 0
        now = datetime.now()

        for h in range(start_h, end_h):
            for m in [0, 30]:
                ts = f"{h:02d}:{m:02d}"
                btn = QPushButton(ts)
                btn.setCheckable(True)
                btn.setFixedSize(70, 35)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)

                is_past = False
                if sel_date == now.date() and datetime.combine(sel_date, time(h, m)) < now: is_past = True
                if sel_date < now.date(): is_past = True

                if ts in taken or is_past:
                    btn.setEnabled(False)
                    btn.setStyleSheet("background: #BDC3C7; border:none; color: #888; border-radius: 4px;")
                else:
                    btn.setStyleSheet("""
                        QPushButton { background: #3498DB; color: white; border:none; border-radius: 4px; font-weight: bold;} 
                        QPushButton:checked { background: #2C3E50; border: 2px solid #F39C12; }
                        QPushButton:hover:!checked { background-color: #5DADE2; }
                    """)
                    btn.clicked.connect(partial(self.clk_time, btn, ts))

                self.time_slots_layout.addWidget(btn, row, col)
                col += 1
                if col > 3:
                    col = 0
                    row += 1

    def clk_time(self, btn, ts):
        for i in range(self.time_slots_layout.count()):
            w = self.time_slots_layout.itemAt(i).widget()
            if w and w != btn: w.setChecked(False)

        if btn.isChecked():
            self.selected_time = ts
            self.save_btn.setText(f"UMÓW: {self.calendar.selectedDate().toString('dd.MM.yyyy')} - {ts}")
            self.save_btn.setEnabled(True)
        else:
            self.selected_time = None
            self.save_btn.setEnabled(False)

    def save(self):
        title = self.title_in.text().strip()
        if not title: return
        doc_id = self.doctor_combo.currentData()
        if not doc_id or not self.selected_time: return

        q_date = self.calendar.selectedDate()
        d_str = f"{q_date.year()}-{q_date.month():02d}-{q_date.day():02d} {self.selected_time}"

        try:
            vd_naive = datetime.strptime(d_str, "%Y-%m-%d %H:%M")
            conn = self._db_connect()
            cur = conn.cursor()

            cur.execute("SELECT 1 FROM visits WHERE doctor_id=%s AND visit_date=%s LIMIT 1", (doc_id, vd_naive))
            if cur.fetchone():
                conn.close()
                QMessageBox.warning(self, "Zajęte", "Ten termin został już zajęty. Wybierz inny.")
                self.refresh_time_slots()
                return

            cur.execute(
                "INSERT INTO visits (visit_date, title, pesel, doctor_id) VALUES (%s, %s, %s, %s)",
                (vd_naive, title, self.patient_pesel, doc_id)
            )
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sukces", "Wizyta umówiona.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))


class PatientWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Pacjent")
        self.code_label = None
        self.init_ui()

    def init_ui(self):
        self.setup_info_widget("PACJENT", f"PESEL: {self.user_id}")

        b = self.add_button("UMÓW WIZYTĘ")
        b.setStyleSheet("""
            QPushButton { background: #27AE60; color: white; font-weight:bold; padding: 15px; text-align: left; border-radius: 6px; border:none; }
            QPushButton:hover { background-color: #2ECC71; }
        """)
        b.clicked.connect(self.open_book)

        self.side_layout.addSpacing(20)

        code = self.fetch_code()
        f = QFrame()
        f.setFixedSize(240, 140)
        f.setStyleSheet("background: #34495E; border: 2px dashed #555; border-radius: 10px;")
        vl = QVBoxLayout(f)
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(QLabel("KOD DLA LEKARZA", styleSheet="color:#ccc; font-size:10px; border:none;"))
        self.code_label = QLabel(str(code) if code else "---",
                                 styleSheet="color:orange; font-size:28px; font-weight:bold; border:none;")
        vl.addWidget(self.code_label)
        b_gen = QPushButton("GENERUJ")
        b_gen.setCursor(Qt.CursorShape.PointingHandCursor)
        b_gen.setStyleSheet("""
            QPushButton { background: #2980B9; color: white; border:none; padding: 5px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #5DADE2; }
        """)
        b_gen.clicked.connect(self.gen_code)
        vl.addWidget(b_gen)
        self.side_layout.addWidget(f, alignment=Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addStretch()

        wyloguj = self.add_button("WYLOGUJ")
        wyloguj.setStyleSheet("""
            QPushButton { background-color: #C0392B; color: white; border-radius: 6px; padding: 15px; font-weight: bold; font-size: 13px; text-align: left; padding-left: 20px; border: none;} 
            QPushButton:hover { background-color: #E74C3C; }
        """)
        wyloguj.clicked.connect(self._show_logout_window)

        self.main_v_layout.addWidget(QLabel("NADCHODZĄCE WIZYTY",
                                            styleSheet="font-size: 20px; font-weight: bold; color: #3498DB; margin-bottom: 5px; margin-top: 10px;"))
        self.main_v_layout.addWidget(self.create_header_bar("LEKARZ"))

        self.list_upcoming = QListWidget()
        self.list_upcoming.setFrameShape(QFrame.Shape.NoFrame)
        self.list_upcoming.setStyleSheet("background: transparent; border: none;")
        self.list_upcoming.itemClicked.connect(lambda i: self.handle_click(i, self.list_upcoming))
        self.main_v_layout.addWidget(self.list_upcoming)

        self.main_v_layout.addWidget(QLabel("HISTORIA WIZYT",
                                            styleSheet="font-size: 20px; font-weight: bold; color: #7F8C8D; margin-bottom: 5px; margin-top: 20px;"))
        self.main_v_layout.addWidget(self.create_header_bar("LEKARZ"))

        self.list_history = QListWidget()
        self.list_history.setFrameShape(QFrame.Shape.NoFrame)
        self.list_history.setStyleSheet("background: transparent; border: none;")
        self.list_history.itemClicked.connect(lambda i: self.handle_click(i, self.list_history))
        self.main_v_layout.addWidget(self.list_history)

        self.main_v_layout.addSpacing(10)
        btn_det = QPushButton("ZOBACZ KARTĘ WIZYTY")
        btn_det.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_det.setFixedHeight(45)
        btn_det.setStyleSheet("""
            QPushButton { background: #34495E; color: white; font-weight: bold; border-radius: 6px; border:none; }
            QPushButton:hover { background-color: #415B76; }
        """)
        btn_det.clicked.connect(self._show_visit_details)
        self.main_v_layout.addWidget(btn_det)

        self.refresh_list()

    def _db_connect(self):
        try:
            c = psycopg2.connect(conn_str)
            return c
        except:
            return None

    def _normalize_visit_dt(self, value):
        if not value: return None
        tz = LOCAL_TZ
        if isinstance(value, datetime):
            if value.tzinfo is None and tz: return value.replace(tzinfo=tz)
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace(" ", "T"))
            except:
                try:
                    return datetime.strptime(value.split('.')[0], "%Y-%m-%d %H:%M:%S")
                except:
                    return None
        return None

    def refresh_list(self):
        self.list_upcoming.clear()
        self.list_history.clear()
        self.current_selected_frame = None
        self.current_selected_data = None

        conn = self._db_connect()
        if not conn: return

        now = datetime.now()
        if LOCAL_TZ:
            now = now.astimezone(LOCAL_TZ)
        else:
            now = now.replace(tzinfo=None)

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT v.id, v.visit_date, v.title, u.login, v.recommendations 
                FROM visits v
                JOIN users u ON u.id = v.doctor_id
                WHERE v.pesel = %s
                ORDER BY v.visit_date ASC
            """, (self.user_id,))
            rows = cur.fetchall()

            for row in rows:
                vd = self._normalize_visit_dt(row[1])
                if not vd: continue

                vd_naive = vd.replace(tzinfo=None)
                now_naive = now.replace(tzinfo=None)

                fixed_row = (row[0], vd, row[2], row[3], row[4])

                if vd_naive >= now_naive:
                    self.fill_item(self.list_upcoming, fixed_row, is_future=True)
                else:
                    self.fill_item(self.list_history, fixed_row, is_future=False)
            conn.close()
        except Exception as e:
            print(e)

    def fill_item(self, widget, row, is_future):
        it = QListWidgetItem()
        d_str = row[1].strftime("%Y-%m-%d %H:%M") if isinstance(row[1], (datetime, date)) else str(row[1])
        it.setData(Qt.ItemDataRole.UserRole, (d_str, row[2], f"Dr {row[3]}", row[4]))

        f = QFrame()
        f.setProperty("visit_id", row[0])
        f.setFixedHeight(60)
        border_col = "#3498DB" if is_future else "#95A5A6"

        f.setStyleSheet(f"""
            QFrame {{ background-color: #FFFFFF; border-bottom: 1px solid #E0E0E0; border-left: 5px solid {border_col}; }}
        """)

        hl = QHBoxLayout(f)
        hl.setContentsMargins(10, 0, 10, 0)
        lbl_date = QLabel(d_str)
        lbl_date.setFixedWidth(140)
        lbl_date.setStyleSheet("font-weight:bold; color:#555; border:none;")
        hl.addWidget(lbl_date)

        lbl_title = QLabel(row[2])
        lbl_title.setStyleSheet("color:#2C3E50; font-weight:500; font-size:13px; border:none;")
        hl.addWidget(lbl_title, stretch=1)

        lbl_doc = QLabel(f"Dr {row[3]}")
        lbl_doc.setFixedWidth(150)
        lbl_doc.setStyleSheet("color:#555; border:none;")
        hl.addWidget(lbl_doc)

        widget.addItem(it)
        it.setSizeHint(QSize(0, 60))
        widget.setItemWidget(it, f)

    def handle_click(self, item, source_list):
        other_list = self.list_history if source_list == self.list_upcoming else self.list_upcoming
        other_list.clearSelection()

        for i in range(other_list.count()):
            w = other_list.itemWidget(other_list.item(i))
            if w:
                col = "#3498DB" if other_list == self.list_upcoming else "#95A5A6"
                w.setStyleSheet(
                    f"background-color: #FFFFFF; border-bottom: 1px solid #E0E0E0; border-left: 5px solid {col};")

        col_active = "#3498DB" if source_list == self.list_upcoming else "#95A5A6"
        for i in range(source_list.count()):
            w = source_list.itemWidget(source_list.item(i))
            if w:
                w.setStyleSheet(
                    f"background-color: #FFFFFF; border-bottom: 1px solid #E0E0E0; border-left: 5px solid {col_active};")

        self.current_selected_frame = source_list.itemWidget(item)
        self.current_selected_data = item.data(Qt.ItemDataRole.UserRole)

        if self.current_selected_frame:
            self.current_selected_frame.setStyleSheet(
                f"background-color: #EBF5FB; border-bottom: 1px solid #AED6F1; border-left: 5px solid {col_active};")

    def fetch_code(self):
        conn = self._db_connect()
        if not conn: return None
        try:
            cur = conn.cursor()
            cur.execute("SELECT code FROM patient_codes WHERE pesel=%s AND expiration_time>%s",
                        (self.user_id, datetime.now()))
            r = cur.fetchone()
            conn.close()
            return r[0] if r else None
        except:
            return None

    def gen_code(self):
        conn = self._db_connect()
        if not conn: return
        code = str(random.randint(100000, 999999))
        exp = datetime.now() + timedelta(minutes=15)
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM patient_codes WHERE pesel=%s", (self.user_id,))
            if cur.fetchone():
                cur.execute("UPDATE patient_codes SET code=%s, expiration_time=%s WHERE pesel=%s",
                            (code, exp, self.user_id))
            else:
                cur.execute("INSERT INTO patient_codes (pesel, code, expiration_time) VALUES (%s, %s, %s)",
                            (self.user_id, code, exp))
            conn.commit()
            self.code_label.setText(code)
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Err", str(e))

    def open_book(self):
        if BookVisitWindow(self.user_id, self).exec():
            self.refresh_list()