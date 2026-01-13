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
        self.init_ui()

    def setup_sidebar_widgets(self):
        self.setup_info_widget("PANEL LABORANTA", f"ID: {self.user_id}")

    def setup_extra_buttons(self):
        self.add_button("ODŚWIEŻ LISTĘ").clicked.connect(self.reset_to_pending)
        self.add_button("WPISZ WYNIKI").clicked.connect(self.open_fill_result)

    def reset_to_pending(self):
        self.refresh_list()

    def get_sql_query(self):
        # Zapytanie BEZ parametrów (%s)
        return """
            SELECT t.id, v.visit_date, t.title, v.pesel 
            FROM lab_tests t
            JOIN visits v ON t.visit_id = v.id
            WHERE t.description IS NULL OR t.description = ''
            ORDER BY v.visit_date DESC
        """

    # --- NADPISUJEMY REFRESH_LIST ABY NAPRAWIĆ BŁĄD PARAMETRÓW ---
    def refresh_list(self):
        self.current_selected_frame = None
        self.current_selected_data = None
        self.lista_wizyt.clear()

        query = self.get_sql_query()
        if not query or not self.connection: return

        try:
            with self.connection.cursor() as cursor:
                # TU JEST ZMIANA: Wykonujemy execute(query) BEZ (self.user_id,)
                # ponieważ nasze zapytanie nie ma "%s"
                cursor.execute(query)
                rows = cursor.fetchall()
                self.add_list_items(rows)
        except Exception as e:
            print(f"SQL Error: {e}")
            QMessageBox.warning(self, "Błąd SQL", str(e))

    def open_fill_result(self):
        if not self.current_selected_frame:
            QMessageBox.warning(self, "Uwaga", "Wybierz badanie z listy, aby wpisać wynik.")
            return

        test_id = self.current_selected_frame.property("test_id")
        test_title = self.current_selected_frame.property("test_title")

        if not test_id:
            QMessageBox.critical(self, "Błąd", "Nie można zidentyfikować badania.")
            return

        if FillLabResultWindow(test_id, test_title, self).exec():
            self.refresh_list()

    def add_list_items(self, data_rows):
        styles = ["background-color: #FFFFFF;", "background-color: #E8E8E8;"]

        for i, (tid, data, tytul, pesel) in enumerate(data_rows):
            data_str = data.strftime("%Y-%m-%d") if data else ""
            pesel_str = str(pesel)

            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, f"BADANIE: {tytul}", pesel_str))

            frame = QFrame()
            frame.setFixedHeight(60)
            frame.setStyleSheet(styles[i % 2] + "border-bottom: 1px solid #AAA; color: black;")

            frame.setProperty("test_id", tid)
            frame.setProperty("test_title", tytul)

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(10, 0, 10, 0)

            labels = [data_str, tytul.upper(), pesel_str]
            for j, txt in enumerate(labels):
                lbl = QLabel(txt)
                lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

                if j == 1:
                    lbl.setStyleSheet("border: none; color: #2F9ADF; font-weight: bold; font-size: 13px;")
                else:
                    lbl.setStyleSheet("border: none; color: black; font-size: 12px;")

                hl.addWidget(lbl, stretch=1 if j == 1 else 0)
                if j < 2: hl.addSpacing(20)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, 60))
            self.lista_wizyt.setItemWidget(list_item, frame)