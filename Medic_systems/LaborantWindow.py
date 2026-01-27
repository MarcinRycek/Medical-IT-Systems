import psycopg2
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFrame, QTextEdit,
                               QListWidgetItem, QHBoxLayout)
from PySide6.QtCore import Qt, QSize
from BaseWindow import BaseWindow, conn_str


# --- OKNO WPISYWANIA WYNIKÓW ---
class FillLabResultWindow(QDialog):
    def __init__(self, test_id, test_title, parent=None):
        super().__init__(parent)
        self.test_id = test_id
        self.setWindowTitle(f"Wynik badania: {test_title}")
        self.resize(500, 450)

        # Stylizacja
        self.setStyleSheet("""
            QDialog { background-color: #F8F9FA; }
            QLabel { color: #2C3E50; font-size: 13px; font-weight: bold; }
            QTextEdit { 
                background-color: white; 
                color: #2C3E50; 
                border: 1px solid #BDC3C7; 
                border-radius: 4px; 
                padding: 10px;
                font-size: 13px;
            }
            QTextEdit:focus { border: 2px solid #3498DB; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        header = QLabel("Wprowadzanie Wyników")
        header.setStyleSheet("color: #2C3E50; font-size: 18px; border: none; margin-bottom: 5px;")
        layout.addWidget(header)

        info_lbl = QLabel(f"BADANIE: {test_title}")
        info_lbl.setStyleSheet(
            "font-size: 14px; color: #2980B9; border-bottom: 1px solid #BDC3C7; padding-bottom: 10px;")
        layout.addWidget(info_lbl)

        layout.addWidget(QLabel("Opis wyników / Parametry:"))

        self.result_edit = QTextEdit()
        self.result_edit.setPlaceholderText("Wpisz tutaj szczegółowe wyniki badania...")
        layout.addWidget(self.result_edit)

        btn = QPushButton("ZAPISZ WYNIK")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(50)
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
        description = self.result_edit.toPlainText().strip()

        if not description:
            QMessageBox.warning(self, "Błąd", "Pole wyników nie może być puste.")
            return

        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()

            # Aktualizujemy rekord w tabeli lab_tests
            cursor.execute("UPDATE lab_tests SET description = %s WHERE id = %s",
                           (description, self.test_id))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sukces", "Wynik badania został zapisany.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd Bazy", str(e))


# --- GŁÓWNE OKNO LABORANTA ---
class LaborantWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Laborant")
        self.init_ui()

    def setup_sidebar_widgets(self):
        self.setup_info_widget("LABORATORIUM", f"ID: {self.user_id}")

        info_frame = QFrame(self)
        info_frame.setStyleSheet("""
            QFrame { background-color: #34495E; border: 1px solid #415B76; border-radius: 8px; }
            QLabel { color: #ECF0F1; }
        """)
        layout = QVBoxLayout(info_frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)

        lbl = QLabel("STATUS PRACY:", info_frame)
        lbl.setStyleSheet("color: #BDC3C7; font-size: 10px; font-weight: bold; border: none;")

        lbl2 = QLabel("WSZYSTKIE\nZLECENIA", info_frame)
        lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl2.setStyleSheet("color: #2ECC71; font-weight: 800; font-size: 14px; border: none;")

        layout.addWidget(lbl)
        layout.addWidget(lbl2)
        self.side_layout.addWidget(info_frame)

    def setup_extra_buttons(self):
        self.add_button("ODŚWIEŻ LISTĘ").clicked.connect(self.reset_to_pending)
        self.add_button("WPISZ WYNIKI").clicked.connect(self.open_fill_result)

    def reset_to_pending(self):
        self.refresh_list()

    def get_sql_query(self):
        # Pobieramy 4 kolumny: ID testu, Data wizyty, Tytuł testu, PESEL
        # Łączymy tabele lab_tests i visits
        return """
            SELECT t.id, v.visit_date, t.title, v.pesel 
            FROM lab_tests t
            JOIN visits v ON t.visit_id = v.id
            WHERE t.description IS NULL OR t.description = ''
            ORDER BY v.visit_date DESC
        """

    def refresh_list(self):
        self.current_selected_frame = None
        self.current_selected_data = None
        self.lista_wizyt.clear()

        query = self.get_sql_query()
        if not query or not self.connection: return

        try:
            with self.connection.cursor() as cursor:
                # Laborant widzi wszystko, nie filtrujemy po ID użytkownika, więc bez parametrów
                cursor.execute(query)
                rows = cursor.fetchall()
                self.add_list_items(rows)
        except Exception as e:
            print(f"SQL Error: {e}")
            QMessageBox.warning(self, "Błąd SQL", str(e))

    # --- TO JEST FUNKCJA, KTÓREJ BRAKOWAŁO ---
    def add_list_items(self, data_rows):
        styles = ["background-color: #FFFFFF;", "background-color: #F8F9F9;"]

        WIDTH_DATE = 140
        WIDTH_PERSON = 150

        # Rozpakowujemy 4 wartości: TestID, Data, Tytuł, PESEL
        for i, (tid, data, tytul, pesel) in enumerate(data_rows):
            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""
            pesel_str = str(pesel)

            list_item = QListWidgetItem()
            # Dane dla okna szczegółów (kompatybilność)
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, f"BADANIE: {tytul}", pesel_str))

            frame = QFrame()
            frame.setFixedHeight(65)
            frame.setStyleSheet(f"{styles[i % 2]} border-bottom: 1px solid #E0E0E0; color: #2C3E50;")

            # --- ZAPAMIĘTUJEMY ID BADANIA (do edycji) ---
            frame.setProperty("test_id", tid)
            frame.setProperty("test_title", tytul)

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(15, 0, 15, 0)

            # Wyświetlamy 3 kolumny (ID jest ukryte)

            # 1. Data
            lbl_date = QLabel(data_str)
            lbl_date.setFixedWidth(WIDTH_DATE)
            lbl_date.setStyleSheet("border: none; color: #555; font-weight: bold;")
            hl.addWidget(lbl_date)

            # 2. Tytuł badania (Kolor niebieski dla wyróżnienia)
            lbl_title = QLabel(tytul.upper())
            lbl_title.setStyleSheet("border: none; color: #2980B9; font-size: 13px; font-weight: bold;")
            hl.addWidget(lbl_title, stretch=1)

            # 3. PESEL
            lbl_pesel = QLabel(pesel_str)
            lbl_pesel.setFixedWidth(WIDTH_PERSON)
            lbl_pesel.setStyleSheet("border: none; color: #555;")
            hl.addWidget(lbl_pesel)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, 65))
            self.lista_wizyt.setItemWidget(list_item, frame)

    def open_fill_result(self):
        if not self.current_selected_frame:
            QMessageBox.warning(self, "Uwaga", "Wybierz badanie z listy, aby wpisać wynik.")
            return

        # Pobieramy ukryte ID badania
        test_id = self.current_selected_frame.property("test_id")
        test_title = self.current_selected_frame.property("test_title")

        if not test_id:
            QMessageBox.critical(self, "Błąd", "Nie można zidentyfikować badania.")
            return

        # Otwieramy okno edycji
        if FillLabResultWindow(test_id, test_title, self).exec():
            # Po pomyślnym zapisie odświeżamy listę -> wykonane badanie zniknie z listy "Do zrobienia"
            self.refresh_list()