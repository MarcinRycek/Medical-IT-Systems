import psycopg2
from datetime import datetime, date, time
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFrame, QTextEdit,
                               QListWidgetItem, QHBoxLayout, QListWidget)
from PySide6.QtCore import Qt, QSize
from BaseWindow import BaseWindow, conn_str, DIALOG_STYLE

# --- STYL LOKALNY ---
LOCAL_DIALOG_STYLE = """
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
    QMessageBox { background-color: white; color: black; }
    QMessageBox QLabel { color: black; }
    QMessageBox QPushButton { background-color: #F0F0F0; color: black; border: 1px solid #888; }
"""


# --- OKNO ZLECANIA BADANIA ---
class AddLabTestWindow(QDialog):
    def __init__(self, visit_id, parent=None):
        super().__init__(parent)
        self.visit_id = visit_id
        self.setWindowTitle("Zleć Badanie")
        self.resize(400, 280)
        self.setStyleSheet(LOCAL_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

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
        btn.setStyleSheet("""
            QPushButton { background-color: #3498DB; color: white; font-weight: bold; border-radius: 5px; border: none; } 
            QPushButton:hover { background-color: #5DADE2; }
        """)
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


# --- OKNO DODAWANIA ZALECEŃ ---
class AddRecommendationWindow(QDialog):
    def __init__(self, visit_id, current_recs, parent=None):
        super().__init__(parent)
        self.visit_id = visit_id
        self.setWindowTitle("Zalecenia Lekarskie")
        self.resize(500, 450)
        self.setStyleSheet(LOCAL_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        header = QLabel("Zalecenia i Przebieg Wizyty")
        header.setStyleSheet("color: #2C3E50; font-size: 18px; border: none;")
        layout.addWidget(header)

        layout.addWidget(QLabel("Treść zaleceń (Leki, diagnoza, uwagi):"))
        self.rec_edit = QTextEdit()
        if current_recs:
            self.rec_edit.setText(current_recs)
        else:
            self.rec_edit.setPlaceholderText("Wpisz diagnozę i zalecenia dla pacjenta...")

        layout.addWidget(self.rec_edit)

        btn = QPushButton("ZAPISZ ZALECENIA")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background-color: #27AE60; color: white; font-weight: bold; border-radius: 5px; border: none; } 
            QPushButton:hover { background-color: #2ECC71; }
        """)
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        text = self.rec_edit.toPlainText().strip()
        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("UPDATE visits SET recommendations = %s WHERE id = %s",
                           (text, self.visit_id))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Sukces", "Zalecenia zostały zapisane.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd Bazy", str(e))


# --- GŁÓWNE OKNO LEKARZA ---
class DoctorWindow(BaseWindow):
    def __init__(self, user_id):
        # 1. Init BaseWindow (tylko szkielet)
        super().__init__(user_id, "Lekarz")
        self.code_input = None

        # 2. Ręczne budowanie UI
        self.init_ui()

    def init_ui(self):
        """Buduje interfejs lekarza."""
        # A. Pasek boczny
        self.setup_sidebar_widgets()

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #34495E;")
        self.side_layout.addWidget(line)
        self.side_layout.addSpacing(10)

        # Przyciski
        zobacz_btn = self.add_button("ZOBACZ KARTĘ")
        zobacz_btn.clicked.connect(self._show_visit_details)

        self.setup_extra_buttons()
        self.side_layout.addStretch(1)

        wyloguj_btn = self.add_button("WYLOGUJ")
        wyloguj_btn.setStyleSheet("""
            QPushButton { background-color: #C0392B; color: white; border-radius: 6px; padding: 15px; font-weight: bold; font-size: 13px; text-align: left; padding-left: 20px; border: none;} 
            QPushButton:hover { background-color: #E74C3C; }
        """)
        wyloguj_btn.clicked.connect(self._show_logout_window)

        # B. Tabele (Główna treść)
        self.setup_doctor_tables()

        # C. Layout
        # BaseWindow już dodaje side_panel i main_content_frame do main_h_layout.
        # Ponowne dodawanie tych samych widgetów potrafi powodować problemy z układem/rozmiarem.

        # D. Dane (Pobierz wizyty)
        self.refresh_list()

    def get_doctor_login(self):
        if not self.connection: return "MEDYCYNY"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT login FROM users WHERE id = %s", (self.user_id,))
                res = cursor.fetchone()
                return res[0].upper() if res else "MEDYCYNY"
        except:
            return "MEDYCYNY"

    def setup_doctor_tables(self):
        # 1. PACJENT (Ukryta na start)
        self.lbl_patient = QLabel("KARTA PACJENTA", self.main_content_frame)
        self.lbl_patient.setStyleSheet("color: #8E44AD; font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        self.lbl_patient.setVisible(False)
        self.main_v_layout.addWidget(self.lbl_patient)

        self.header_patient = self.create_header_bar("PESEL")
        self.header_patient.setVisible(False)
        self.main_v_layout.addWidget(self.header_patient)

        self.list_patient = QListWidget()
        self.list_patient.setFrameShape(QFrame.Shape.NoFrame)
        self.list_patient.setStyleSheet("background-color: transparent;")
        self.list_patient.itemClicked.connect(lambda item: self.handle_list_click(item, "patient"))
        self.list_patient.setVisible(False)
        self.main_v_layout.addWidget(self.list_patient)

        # 2. DZISIAJ
        lbl_today = QLabel("WIZYTY DZISIAJ", self.main_content_frame)
        lbl_today.setStyleSheet(
            "color: #E74C3C; font-size: 18px; font-weight: bold; margin-bottom: 5px; margin-top: 15px;")
        self.main_v_layout.addWidget(lbl_today)

        header_today = self.create_header_bar("PESEL")
        self.main_v_layout.addWidget(header_today)

        self.list_today = QListWidget()
        self.list_today.setMinimumHeight(150)  # Zabezpieczenie przed znikaniem
        self.list_today.setFrameShape(QFrame.Shape.NoFrame)
        self.list_today.setStyleSheet("background-color: transparent;")
        self.list_today.itemClicked.connect(lambda item: self.handle_list_click(item, "today"))
        self.main_v_layout.addWidget(self.list_today)

        # 3. PRZYSZŁOŚĆ
        lbl_future = QLabel("NADCHODZĄCE WIZYTY", self.main_content_frame)
        lbl_future.setStyleSheet(
            "color: #3498DB; font-size: 18px; font-weight: bold; margin-bottom: 5px; margin-top: 15px;")
        self.main_v_layout.addWidget(lbl_future)

        header_future = self.create_header_bar("PESEL")
        self.main_v_layout.addWidget(header_future)

        self.list_future = QListWidget()
        self.list_future.setMinimumHeight(150)  # Zabezpieczenie przed znikaniem
        self.list_future.setFrameShape(QFrame.Shape.NoFrame)
        self.list_future.setStyleSheet("background-color: transparent;")
        self.list_future.itemClicked.connect(lambda item: self.handle_list_click(item, "future"))
        self.main_v_layout.addWidget(self.list_future)

        # Ważne: Rozciąganie list
        self.main_v_layout.setStretchFactor(self.list_patient, 1)
        self.main_v_layout.setStretchFactor(self.list_today, 1)
        self.main_v_layout.setStretchFactor(self.list_future, 1)

    def setup_sidebar_widgets(self):
        doc_name = self.get_doctor_login()
        self.setup_info_widget(f"DR {doc_name}", f"ID: {self.user_id}")

        search_frame = QFrame(self)
        search_frame.setFixedHeight(160)
        search_frame.setStyleSheet("""
            QFrame { background-color: #34495E; border: 1px solid #415B76; border-radius: 8px; }
            QLabel { color: #ECF0F1; }
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
        self.code_input.setStyleSheet("""
            QLineEdit { 
                background-color: white; 
                color: #2C3E50; 
                border: none; 
                border-radius: 4px; 
                padding: 6px; 
                font-weight: bold;
            }
        """)

        search_btn = QPushButton("POBIERZ KARTĘ", search_frame)
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.setStyleSheet("""
            QPushButton { background-color: #3498DB; color: white; font-weight: bold; padding: 8px; border-radius: 4px; border: none; } 
            QPushButton:hover { background-color: #5DADE2; }
        """)
        search_btn.clicked.connect(self.load_patient_by_code)

        layout.addWidget(lbl)
        layout.addWidget(self.code_input)
        layout.addWidget(search_btn)
        self.side_layout.addWidget(search_frame)

    def setup_extra_buttons(self):
        style = """
            QPushButton { background-color: #34495E; color: white; border-radius: 6px; font-weight: bold; font-size: 13px; text-align: left; padding-left: 20px; border: none;} 
            QPushButton:hover { background-color: #415B76; }
        """
        btn1 = self.add_button("MOJE WIZYTY")
        btn1.setStyleSheet(style)
        btn1.clicked.connect(self.reset_to_my_schedule)

        btn2 = self.add_button("DODAJ ZALECENIA")
        btn2.setStyleSheet(style)
        btn2.clicked.connect(self.open_add_recommendations)

        btn3 = self.add_button("ZLEĆ BADANIE")
        btn3.setStyleSheet(style)
        btn3.clicked.connect(self.open_add_lab_test)

    def reset_to_my_schedule(self):
        """Ukrywa sekcję pacjenta i pokazuje harmonogram lekarza."""
        self.lbl_patient.setVisible(False)
        self.header_patient.setVisible(False)
        self.list_patient.setVisible(False)
        self.list_patient.clear()

        self.refresh_list()

    def refresh_list(self):
        """Pobiera wizyty lekarza i dzieli je na "dzisiaj" oraz "przyszłe".

        Naprawa:
        - obsługa strefy czasowej (Warszawa) oraz porównań datetime aware/naive,
        - odporność na visit_date jako DATE lub TIMESTAMP,
        - opcjonalnie nie pokazujemy wizyt z przeszłych dni.
        """
        self.current_selected_frame = None
        self.current_selected_data = None
        self.list_today.clear()
        self.list_future.clear()

        if not self.connection: return

        tz = self._get_local_tz()
        now_local = datetime.now(tz)
        today_date = now_local.date()

        try:
            with self.connection.cursor() as cursor:
                # Pobieramy WSZYSTKIE wizyty tego lekarza (bez warunku na datę w SQL)
                query = """
                    SELECT id, visit_date, title, pesel, recommendations
                    FROM visits 
                    WHERE doctor_id = %s 
                    ORDER BY visit_date ASC
                """
                cursor.execute(query, (self.user_id,))
                rows = cursor.fetchall()

                # Dzielimy w Pythonie - stabilnie niezależnie od typu w bazie (DATE/TIMESTAMP)
                for row in rows:
                    raw_dt = row[1]
                    visit_local = self._to_local_datetime(raw_dt)
                    if not visit_local:
                        continue

                    v_date = visit_local.date()

                    if v_date < today_date:
                        # Przeszłość ignorujemy w widoku harmonogramu
                        continue

                    if v_date == today_date:
                        self.add_single_item(self.list_today, row, visit_local)
                    else:
                        self.add_single_item(self.list_future, row, visit_local)

            # Placeholdery, żeby lekarz widział, że lista jest pusta (a nie "zniknęła")
            if self.list_today.count() == 0:
                self._add_placeholder(self.list_today, "Brak wizyt na dziś")
            if self.list_future.count() == 0:
                self._add_placeholder(self.list_future, "Brak nadchodzących wizyt")

        except Exception as e:
            print(f"SQL Error: {e}")

    def _get_local_tz(self):
        """Zwraca strefę czasową dla porównań (domyślnie Europa/Warszawa)."""
        try:
            from zoneinfo import ZoneInfo
            return ZoneInfo("Europe/Warsaw")
        except Exception:
            # Fallback: strefa systemowa
            return datetime.now().astimezone().tzinfo

    def _to_local_datetime(self, value):
        """Normalizuje visit_date z bazy do datetime w strefie lokalnej."""
        tz = self._get_local_tz()

        if isinstance(value, datetime):
            # timestamp with time zone -> aware
            if value.tzinfo is not None:
                return value.astimezone(tz)
            # timestamp without time zone -> traktujemy jako lokalny
            return value.replace(tzinfo=tz)

        if isinstance(value, date):
            # Jeżeli w bazie jest DATE, przyjmijmy koniec dnia, żeby "dzisiaj" nie wpadało do przeszłości.
            return datetime.combine(value, time(23, 59, 59)).replace(tzinfo=tz)

        return None

    def _add_placeholder(self, widget, text):
        it = QListWidgetItem(text)
        it.setFlags(Qt.ItemFlag.NoItemFlags)
        it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        it.setForeground(Qt.GlobalColor.gray)
        widget.addItem(it)

    def add_single_item(self, widget, row, visit_local_dt=None):
        """Pomocnicza funkcja dodająca element do listy."""
        count = widget.count()
        bg_color = "#FFFFFF" if count % 2 == 0 else "#F8F9F9"

        raw_dt = row[1]
        if visit_local_dt is None:
            visit_local_dt = self._to_local_datetime(raw_dt)

        # Format daty do UI
        if isinstance(raw_dt, datetime):
            data_str = visit_local_dt.strftime("%Y-%m-%d %H:%M") if visit_local_dt else str(raw_dt)
        else:
            # DATE w bazie (bez godziny)
            data_str = raw_dt.strftime("%Y-%m-%d") if hasattr(raw_dt, "strftime") else str(raw_dt)

        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, (data_str, row[2], str(row[3]), row[4]))

        frame = QFrame()
        frame.setFixedHeight(65)
        frame.setStyleSheet(f"background-color: {bg_color}; border-bottom: 1px solid #E0E0E0; color: #2C3E50;")
        frame.setProperty("visit_id", row[0])

        hl = QHBoxLayout(frame)
        hl.setContentsMargins(15, 0, 15, 0)

        lbl_date = QLabel(data_str)
        lbl_date.setFixedWidth(140)
        lbl_date.setStyleSheet("border: none; color: #555; font-weight: bold;")
        hl.addWidget(lbl_date)

        lbl_title = QLabel(row[2])
        lbl_title.setStyleSheet("border: none; color: #2C3E50; font-size: 14px; font-weight: 500;")
        hl.addWidget(lbl_title, stretch=1)

        lbl_person = QLabel(str(row[3]))
        lbl_person.setFixedWidth(150)
        lbl_person.setStyleSheet("border: none; color: #555;")
        hl.addWidget(lbl_person)

        widget.addItem(item)
        item.setSizeHint(QSize(0, 65))
        widget.setItemWidget(item, frame)

    def load_patient_by_code(self):
        """Po wpisaniu kodu: Ładuje historię pacjenta na górę."""
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

                # Pobieramy historię pacjenta
                query_patient = """
                    SELECT id, visit_date, title, pesel, recommendations 
                    FROM visits 
                    WHERE pesel = %s 
                    ORDER BY visit_date DESC
                """
                cursor.execute(query_patient, (pesel,))
                rows = cursor.fetchall()

                self.list_patient.clear()
                for row in rows:
                    self.add_single_item(self.list_patient, row)

                self.lbl_patient.setText(f"HISTORIA PACJENTA: {pesel}")
                self.lbl_patient.setVisible(True)
                self.header_patient.setVisible(True)
                self.list_patient.setVisible(True)

                QMessageBox.information(self, "Sukces", f"Załadowano historię pacjenta: {pesel}")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def handle_list_click(self, item, source):
        all_lists = {
            "patient": self.list_patient,
            "today": self.list_today,
            "future": self.list_future
        }

        for key, lst in all_lists.items():
            if key != source:
                lst.clearSelection()
                lst.setCurrentItem(None)
                for i in range(lst.count()):
                    it = lst.item(i)
                    wid = lst.itemWidget(it)
                    if wid:
                        bg = "#FFFFFF" if i % 2 == 0 else "#F8F9F9"
                        wid.setStyleSheet(f"background-color: {bg}; border-bottom: 1px solid #E0E0E0; color: #2C3E50;")

        active_list = all_lists[source]

        for i in range(active_list.count()):
            it = active_list.item(i)
            wid = active_list.itemWidget(it)
            if wid:
                bg = "#FFFFFF" if i % 2 == 0 else "#F8F9F9"
                wid.setStyleSheet(f"background-color: {bg}; border-bottom: 1px solid #E0E0E0; color: #2C3E50;")

        selected_frame = active_list.itemWidget(item)
        if selected_frame:
            selected_frame.setStyleSheet(
                "background-color: #EBF5FB; border-bottom: 1px solid #AED6F1; border-left: 5px solid #3498DB; color: #2C3E50;")
            self.current_selected_frame = selected_frame
            self.current_selected_data = item.data(Qt.ItemDataRole.UserRole)

    def open_add_recommendations(self):
        if not self.current_selected_frame:
            QMessageBox.warning(self, "Uwaga", "Najpierw wybierz wizytę z listy.")
            return

        visit_id = self.current_selected_frame.property("visit_id")
        data = self.current_selected_data
        current_recs = data[3] if data and len(data) > 3 else ""

        if not visit_id: return

        if AddRecommendationWindow(visit_id, current_recs, self).exec():
            if self.list_patient.isVisible():
                self.load_patient_by_code()
            else:
                self.refresh_list()

    def open_add_lab_test(self):
        if not self.current_selected_frame:
            QMessageBox.warning(self, "Uwaga", "Najpierw wybierz wizytę z listy.")
            return

        visit_id = self.current_selected_frame.property("visit_id")
        if not visit_id: return

        AddLabTestWindow(visit_id, self).exec()