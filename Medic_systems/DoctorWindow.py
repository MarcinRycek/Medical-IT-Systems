import psycopg2
from datetime import datetime, date
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFrame, QTextEdit,
                               QListWidgetItem, QHBoxLayout, QListWidget)
from PySide6.QtCore import Qt, QSize
from BaseWindow import BaseWindow, conn_str, DIALOG_STYLE


# --- OKNO ZLECANIA BADANIA ---
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
        btn.setStyleSheet(
            "QPushButton { background-color: #3498DB; color: white; font-weight: bold; border-radius: 5px; border: none; } QPushButton:hover { background-color: #2980B9; }")
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
        self.setStyleSheet(DIALOG_STYLE)

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
        btn.setStyleSheet(
            "QPushButton { background-color: #27AE60; color: white; font-weight: bold; border-radius: 5px; border: none; } QPushButton:hover { background-color: #2ECC71; }")
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
        # 1. Inicjalizacja bazy i okna (BaseWindow)
        super().__init__(user_id, "Lekarz")
        self.code_input = None

        # 2. Budowa interfejsu (Twoje 3 tabele)
        self.setup_doctor_ui()

        # 3. Ręczne odświeżenie danych
        self.refresh_list()

    def get_doctor_login(self):
        """Pobiera login (nazwisko) lekarza z bazy danych."""
        if not self.connection: return "MEDYCYNY"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT login FROM users WHERE id = %s", (self.user_id,))
                res = cursor.fetchone()
                return res[0].upper() if res else "MEDYCYNY"
        except:
            return "MEDYCYNY"

    def setup_doctor_ui(self):
        """Konfiguruje 3 sekcje i usuwa domyślną listę z BaseWindow."""

        # --- CZYSZCZENIE LAYOUTU (Usuwamy pustą tabelę z BaseWindow) ---
        if self.main_v_layout:
            while self.main_v_layout.count():
                item = self.main_v_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        # === 1. SEKCJA PACJENTA (Domyślnie ukryta) ===
        self.lbl_patient = QLabel("KARTA PACJENTA", self.main_content_frame)
        self.lbl_patient.setStyleSheet("color: #8E44AD; font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        self.lbl_patient.setVisible(False)
        self.main_v_layout.addWidget(self.lbl_patient)

        self.header_patient = self.create_header_bar(self.main_content_frame, "PESEL")
        self.header_patient.setVisible(False)
        self.main_v_layout.addWidget(self.header_patient)

        self.list_patient = QListWidget()
        self.list_patient.setFrameShape(QFrame.Shape.NoFrame)
        self.list_patient.setStyleSheet("background-color: transparent;")
        self.list_patient.itemClicked.connect(lambda item: self.handle_list_click(item, "patient"))
        self.list_patient.setVisible(False)
        self.main_v_layout.addWidget(self.list_patient)

        # === 2. SEKCJA DZISIAJ ===
        lbl_today = QLabel("TWOJE WIZYTY - DZISIAJ", self.main_content_frame)
        lbl_today.setStyleSheet(
            "color: #E74C3C; font-size: 18px; font-weight: bold; margin-bottom: 5px; margin-top: 15px;")
        self.main_v_layout.addWidget(lbl_today)

        header_today = self.create_header_bar(self.main_content_frame, "PESEL")
        self.main_v_layout.addWidget(header_today)

        self.list_today = QListWidget()
        self.list_today.setFrameShape(QFrame.Shape.NoFrame)
        self.list_today.setStyleSheet("background-color: transparent;")
        self.list_today.itemClicked.connect(lambda item: self.handle_list_click(item, "today"))
        self.main_v_layout.addWidget(self.list_today)

        # === 3. SEKCJA PRZYSZŁOŚĆ ===
        lbl_future = QLabel("TWOJE WIZYTY - NADCHODZĄCE", self.main_content_frame)
        lbl_future.setStyleSheet(
            "color: #3498DB; font-size: 18px; font-weight: bold; margin-bottom: 5px; margin-top: 15px;")
        self.main_v_layout.addWidget(lbl_future)

        header_future = self.create_header_bar(self.main_content_frame, "PESEL")
        self.main_v_layout.addWidget(header_future)

        self.list_future = QListWidget()
        self.list_future.setFrameShape(QFrame.Shape.NoFrame)
        self.list_future.setStyleSheet("background-color: transparent;")
        self.list_future.itemClicked.connect(lambda item: self.handle_list_click(item, "future"))
        self.main_v_layout.addWidget(self.list_future)

    def setup_sidebar_widgets(self):
        doc_name = self.get_doctor_login()
        self.setup_info_widget(f"DR {doc_name}", f"ID: {self.user_id}")

        search_frame = QFrame(self)
        search_frame.setFixedHeight(160)
        search_frame.setStyleSheet("""
            QFrame { background-color: #34495E; border: 1px solid #415B76; border-radius: 8px; }
            QLabel { color: #ECF0F1; }
            QLineEdit { color: #2C3E50; background-color: #ECF0F1; border: none; border-radius: 4px; padding: 6px; }
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
        search_btn.setStyleSheet(
            "QPushButton { background-color: #3498DB; color: white; font-weight: bold; padding: 8px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #2980B9; }")
        search_btn.clicked.connect(self.load_patient_by_code)

        layout.addWidget(lbl)
        layout.addWidget(self.code_input)
        layout.addWidget(search_btn)
        self.side_layout.addWidget(search_frame)

    def setup_extra_buttons(self):
        self.add_button("MOJE WIZYTY").clicked.connect(self.reset_to_my_schedule)
        self.add_button("DODAJ ZALECENIA").clicked.connect(self.open_add_recommendations)
        self.add_button("ZLEĆ BADANIE").clicked.connect(self.open_add_lab_test)

    def reset_to_my_schedule(self):
        """Ukrywa sekcję pacjenta i odświeża wizyty lekarza."""
        self.lbl_patient.setVisible(False)
        self.header_patient.setVisible(False)
        self.list_patient.setVisible(False)
        self.list_patient.clear()

        self.refresh_list()

    def refresh_list(self):
        """Odświeża listy lekarza. Używa lokalnej daty Pythona."""
        if not hasattr(self, 'list_today'): return

        self.current_selected_frame = None
        self.current_selected_data = None

        self.list_today.clear()
        self.list_future.clear()

        if not self.connection: return

        # Pobieramy DZISIEJSZĄ datę z komputera (nie z serwera bazy, żeby uniknąć różnic stref czasowych)
        today_date = date.today()
        print(f"DEBUG: Pobieram wizyty dla lekarza ID={self.user_id} na dzień={today_date}")

        try:
            with self.connection.cursor() as cursor:
                # 1. WIZYTY DZISIEJSZE
                # Porównujemy samą datę (rzutowanie ::date w Postgres) z naszą lokalną datą
                query_today = """
                    SELECT id, visit_date, title, pesel, recommendations
                    FROM visits 
                    WHERE doctor_id = %s AND visit_date::date = %s
                    ORDER BY visit_date ASC
                """
                cursor.execute(query_today, (self.user_id, today_date))
                rows_today = cursor.fetchall()
                print(f"DEBUG: Znaleziono {len(rows_today)} wizyt na dzisiaj.")
                self.populate_list(self.list_today, rows_today)

                # 2. WIZYTY PRZYSZŁE
                query_future = """
                    SELECT id, visit_date, title, pesel, recommendations
                    FROM visits 
                    WHERE doctor_id = %s AND visit_date::date > %s
                    ORDER BY visit_date ASC
                """
                cursor.execute(query_future, (self.user_id, today_date))
                rows_future = cursor.fetchall()
                print(f"DEBUG: Znaleziono {len(rows_future)} wizyt przyszłych.")
                self.populate_list(self.list_future, rows_future)

        except Exception as e:
            print(f"SQL Error: {e}")

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

                query_patient = """
                    SELECT id, visit_date, title, pesel, recommendations 
                    FROM visits 
                    WHERE pesel = %s 
                    ORDER BY visit_date DESC
                """
                cursor.execute(query_patient, (pesel,))
                rows = cursor.fetchall()

                self.list_patient.clear()
                self.populate_list(self.list_patient, rows)

                self.lbl_patient.setText(f"HISTORIA PACJENTA: {pesel}")
                self.lbl_patient.setVisible(True)
                self.header_patient.setVisible(True)
                self.list_patient.setVisible(True)

                QMessageBox.information(self, "Sukces", f"Załadowano historię pacjenta: {pesel}")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def populate_list(self, target_list_widget, data_rows):
        styles = ["background-color: #FFFFFF;", "background-color: #F8F9F9;"]
        WIDTH_DATE = 140
        WIDTH_PERSON = 150

        for i, row in enumerate(data_rows):
            vid = row[0]
            data = row[1]
            tytul = row[2]
            pesel = row[3]
            recs = row[4] if len(row) > 4 else ""

            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""
            list_item = QListWidgetItem()
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

            target_list_widget.addItem(list_item)
            list_item.setSizeHint(QSize(0, 65))
            target_list_widget.setItemWidget(list_item, frame)

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