import psycopg2
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFrame, QTextEdit,
                               QListWidgetItem, QHBoxLayout)
from PySide6.QtCore import Qt, QSize
from BaseWindow import BaseWindow, conn_str


# --- OKNO WPISYWANIA WYNIKÓW (Bez zmian - styl czarny tekst) ---
class FillLabResultWindow(QDialog):
    def __init__(self, test_id, test_title, parent=None):
        super().__init__(parent)
        self.test_id = test_id
        self.setWindowTitle(f"Wynik badania: {test_title}")
        self.resize(500, 400)

        # Stylizacja okna
        self.setStyleSheet("""
            QDialog { background-color: #F0F0F0; }
            QLabel { color: black; font-size: 13px; }
            QTextEdit { 
                background-color: white; 
                color: black; 
                border: 1px solid #AAA; 
                border-radius: 5px; 
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel(f"<h2>Uzupełnij wynik</h2>"))

        info_lbl = QLabel(f"<b>Badanie:</b> {test_title}")
        info_lbl.setStyleSheet("font-size: 14px; color: #333;")
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
                background-color: #2F9ADF; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px; 
                font-size: 14px;
                border: 1px solid #1F8ACF;
            }
            QPushButton:hover { background-color: #1F8ACF; }
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
        # Automatyczne ładowanie nastąpi dzięki init_ui -> refresh_list -> get_sql_query
        self.init_ui()

    def setup_sidebar_widgets(self):
        self.setup_info_widget("PANEL LABORANTA", f"ID: {self.user_id}")

        # Usunąłem ramkę wyszukiwania kodem.
        # Zamiast tego dodajemy informację statyczną.

        info_frame = QFrame(self)
        info_frame.setStyleSheet("""
            QFrame { background-color: white; border: 2px solid #CCC; border-radius: 10px; }
            QLabel { color: #333; }
        """)
        layout = QVBoxLayout(info_frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel("TRYB PRACY:\nWSZYSTKIE ZLECENIA", info_frame)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-weight: bold; font-size: 12px; border: none;")

        layout.addWidget(lbl)
        self.side_layout.addWidget(info_frame)

    def setup_extra_buttons(self):
        # Przycisk do ręcznego odświeżania listy (np. gdy lekarz dodał coś przed chwilą)
        self.add_button("ODŚWIEŻ LISTĘ").clicked.connect(self.refresh_list)

        # Przycisk do wpisywania wyników
        self.add_button("WPISZ WYNIKI").clicked.connect(self.open_fill_result)

    def get_sql_query(self):
        # --- ZMIANA LOGIKI ---
        # Pobieramy WSZYSTKIE badania, które nie mają opisu (description IS NULL lub pusty string)
        # Niezależnie od pacjenta.
        return """
            SELECT t.id, v.visit_date, t.title, v.pesel 
            FROM lab_tests t
            JOIN visits v ON t.visit_id = v.id
            WHERE t.description IS NULL OR t.description = ''
            ORDER BY v.visit_date DESC
        """

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

    # --- NADPISANIE FUNKCJI LISTY (Styl czarny tekst, układ kolumn) ---
    def add_list_items(self, data_rows):
        styles = ["background-color: #FFFFFF;", "background-color: #E8E8E8;"]

        # data_rows: (test_id, data_wizyty, tytul_badania, pesel)
        for i, (tid, data, tytul, pesel) in enumerate(data_rows):
            data_str = data.strftime("%Y-%m-%d") if data else ""
            pesel_str = str(pesel)

            list_item = QListWidgetItem()
            # Dane dla okna szczegółów (kompatybilność z BaseWindow)
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, f"BADANIE: {tytul}", pesel_str))

            frame = QFrame()
            frame.setFixedHeight(60)
            # Styl z czarnym tekstem
            frame.setStyleSheet(styles[i % 2] + "border-bottom: 1px solid #AAA; color: black;")

            # --- ZAPAMIĘTUJEMY ID BADANIA ---
            frame.setProperty("test_id", tid)
            frame.setProperty("test_title", tytul)

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(10, 0, 10, 0)

            # Wyświetlamy: Data | Nazwa Badania | PESEL
            labels = [data_str, tytul.upper(), pesel_str]
            for j, txt in enumerate(labels):
                lbl = QLabel(txt)
                lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

                # Stylizacja środkowej kolumny (tytuł badania)
                if j == 1:
                    lbl.setStyleSheet("border: none; color: #2F9ADF; font-weight: bold; font-size: 13px;")
                else:
                    lbl.setStyleSheet("border: none; color: black; font-size: 12px;")

                hl.addWidget(lbl, stretch=1 if j == 1 else 0)
                if j < 2: hl.addSpacing(20)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, 60))
            self.lista_wizyt.setItemWidget(list_item, frame)