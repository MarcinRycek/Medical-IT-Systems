import psycopg2
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFrame, QTextEdit,
                               QListWidgetItem, QHBoxLayout, QListWidget)
from PySide6.QtCore import Qt, QSize
# Importujemy style i bazę z BaseWindow
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
        super().__init__(user_id, "Lekarz")
        self.code_input = None

        # Przebudowujemy interfejs, aby mieć dwie listy zamiast jednej
        self.setup_doctor_ui()
        self.init_ui()  # To wywoła setup_sidebar_widgets i refresh_list

    def setup_doctor_ui(self):
        """Nadpisuje domyślny layout BaseWindow, tworząc dwie sekcje."""
        # Czyścimy domyślny layout z BaseWindow (usuwamy pojedynczą listę)
        if self.main_v_layout:
            # Usuwamy stare widgety z layoutu
            while self.main_v_layout.count():
                item = self.main_v_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        # --- SEKCJA 1: DZISIAJ ---
        lbl_today = QLabel("WIZYTY DZISIAJ", self.main_content_frame)
        lbl_today.setStyleSheet(
            "color: #E74C3C; font-size: 18px; font-weight: bold; margin-bottom: 5px; margin-top: 10px;")
        self.main_v_layout.addWidget(lbl_today)

        # Nagłówek tabeli
        header_today = self.create_header_bar(self.main_content_frame, "PESEL")
        self.main_v_layout.addWidget(header_today)

        # Lista Dzisiaj
        self.list_today = QListWidget()
        self.list_today.setFrameShape(QFrame.Shape.NoFrame)
        self.list_today.setStyleSheet("background-color: transparent;")
        self.list_today.itemClicked.connect(lambda item: self.handle_list_click(item, "today"))
        self.main_v_layout.addWidget(self.list_today)

        # --- SEKCJA 2: PRZYSZŁOŚĆ ---
        lbl_future = QLabel("NADCHODZĄCE WIZYTY", self.main_content_frame)
        lbl_future.setStyleSheet(
            "color: #3498DB; font-size: 18px; font-weight: bold; margin-bottom: 5px; margin-top: 20px;")
        self.main_v_layout.addWidget(lbl_future)

        # Nagłówek tabeli
        header_future = self.create_header_bar(self.main_content_frame, "PESEL")
        self.main_v_layout.addWidget(header_future)

        # Lista Przyszłość
        self.list_future = QListWidget()
        self.list_future.setFrameShape(QFrame.Shape.NoFrame)
        self.list_future.setStyleSheet("background-color: transparent;")
        self.list_future.itemClicked.connect(lambda item: self.handle_list_click(item, "future"))
        self.main_v_layout.addWidget(self.list_future)

    def setup_sidebar_widgets(self):
        self.setup_info_widget("DR. MEDYCYNY", f"ID: {self.user_id}")

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
        self.refresh_list()

    def refresh_list(self):
        """Pobiera dane i dzieli na dwie listy (Dzisiaj / Przyszłość)."""
        self.current_selected_frame = None
        self.current_selected_data = None
        self.list_today.clear()
        self.list_future.clear()

        if not self.connection: return

        try:
            with self.connection.cursor() as cursor:
                # --- ZAPYTANIE 1: WIZYTY DZISIEJSZE ---
                # Używamy date(visit_date) = CURRENT_DATE
                query_today = """
                    SELECT id, visit_date, title, pesel, recommendations
                    FROM visits 
                    WHERE doctor_id = %s AND date(visit_date) = CURRENT_DATE
                    ORDER BY visit_date ASC
                """
                cursor.execute(query_today, (self.user_id,))
                rows_today = cursor.fetchall()
                self.populate_list(self.list_today, rows_today)

                # --- ZAPYTANIE 2: WIZYTY PRZYSZŁE ---
                # Używamy date(visit_date) > CURRENT_DATE
                query_future = """
                    SELECT id, visit_date, title, pesel, recommendations
                    FROM visits 
                    WHERE doctor_id = %s AND date(visit_date) > CURRENT_DATE
                    ORDER BY visit_date ASC
                """
                cursor.execute(query_future, (self.user_id,))
                rows_future = cursor.fetchall()
                self.populate_list(self.list_future, rows_future)

        except Exception as e:
            print(f"SQL Error: {e}")

    def populate_list(self, target_list_widget, data_rows):
        """Pomocnicza funkcja do wypełniania konkretnej listy."""
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
        """Obsługuje kliknięcie w jedną z list i czyści zaznaczenie w drugiej."""

        # Określamy która lista jest aktywna, a która ma być wyczyszczona
        if source == "today":
            active_list = self.list_today
            other_list = self.list_future
        else:
            active_list = self.list_future
            other_list = self.list_today

        # Czyścimy wybór w drugiej liście (wizualnie i logicznie)
        other_list.clearSelection()
        other_list.setCurrentItem(None)

        # Resetujemy style w "innej" liście
        for i in range(other_list.count()):
            it = other_list.item(i)
            wid = other_list.itemWidget(it)
            if wid:
                bg = "#FFFFFF" if i % 2 == 0 else "#F8F9F9"
                wid.setStyleSheet(f"background-color: {bg}; border-bottom: 1px solid #E0E0E0; color: #2C3E50;")

        # --- LOGIKA ZAZNACZENIA W AKTYWNEJ LIŚCIE ---
        # Resetujemy style w aktywnej liście (poza wybranym)
        for i in range(active_list.count()):
            it = active_list.item(i)
            wid = active_list.itemWidget(it)
            if wid:
                bg = "#FFFFFF" if i % 2 == 0 else "#F8F9F9"
                wid.setStyleSheet(f"background-color: {bg}; border-bottom: 1px solid #E0E0E0; color: #2C3E50;")

        # Podświetlamy kliknięty
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

        if not visit_id:
            return

        if AddRecommendationWindow(visit_id, current_recs, self).exec():
            self.refresh_list()

    def open_add_lab_test(self):
        if not self.current_selected_frame:
            QMessageBox.warning(self, "Uwaga", "Najpierw wybierz wizytę z listy.")
            return

        visit_id = self.current_selected_frame.property("visit_id")
        if not visit_id: return

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

                # Czyścimy obie listy, bo ładujemy historię pacjenta (wszystkie wizyty w jednej liście)
                # W trybie podglądu pacjenta używamy list_today jako głównej listy historii
                self.list_today.clear()
                self.list_future.clear()

                # Zmieniamy nagłówek pierwszej listy na "HISTORIA PACJENTA"
                # (Trudno zmienić label, bo jest lokalny w setup_doctor_ui,
                # ale po prostu wrzucimy wszystko do pierwszej listy)

                cursor.execute(
                    "SELECT id, visit_date, title, pesel, recommendations FROM visits WHERE pesel = %s ORDER BY visit_date DESC",
                    (pesel,))
                rows = cursor.fetchall()

                self.populate_list(self.list_today, rows)

                QMessageBox.information(self, "Sukces", f"Załadowano historię pacjenta: {pesel}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))