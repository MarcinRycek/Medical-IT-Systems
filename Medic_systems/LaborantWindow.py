import psycopg2
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFrame, QTextEdit,
                               QListWidgetItem, QHBoxLayout, QListWidget)
from PySide6.QtCore import Qt, QSize
from BaseWindow import BaseWindow, conn_str, DIALOG_STYLE


# --- OKNO EDYCJI WYNIKU ---
class EditResultWindow(QDialog):
    def __init__(self, test_id, test_name, parent=None):
        super().__init__(parent)
        self.test_id = test_id
        self.setWindowTitle(f"Wynik")
        self.resize(500, 350)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        layout.addWidget(QLabel(f"BADANIE: {test_name}", styleSheet="font-size: 16px; color: #2980B9;"))
        layout.addWidget(QLabel("Wpisz wynik badania:"))

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Wpisz tutaj parametry...")
        layout.addWidget(self.desc_edit)

        btn = QPushButton("ZAPISZ I ZAKOŃCZ")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # --- ZMIANA: Dodano efekt HOVER ---
        btn.setStyleSheet("""
            QPushButton { background-color: #27AE60; color: white; font-weight: bold; border-radius: 5px; padding: 10px; border: none; }
            QPushButton:hover { background-color: #2ECC71; }
        """)
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        text = self.desc_edit.toPlainText().strip()
        if not text: return

        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("UPDATE lab_tests SET description = %s WHERE id = %s", (text, self.test_id))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Sukces", "Wynik zapisany.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))


# --- GŁÓWNE OKNO LABORANTA ---
class LaborantWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Laborant")
        self.build_lab_ui()

    def build_lab_ui(self):
        self.setup_sidebar()

        self.main_v_layout.addWidget(QLabel("BADANIA DO WYKONANIA",
                                            styleSheet="color: #E67E22; font-size: 20px; font-weight: bold; margin-bottom: 10px;"))
        self.main_v_layout.addWidget(self.create_header_bar("PESEL"))

        self.list_todo = QListWidget()
        self.list_todo.setStyleSheet("background: transparent; border: none;")
        self.list_todo.itemClicked.connect(self.handle_click)
        self.main_v_layout.addWidget(self.list_todo)

        self.refresh_list()

    def setup_sidebar(self):
        name = "LABORANT"
        if self.connection:
            try:
                c = self.connection.cursor()
                c.execute("SELECT login FROM users WHERE id=%s", (self.user_id,))
                r = c.fetchone()
                if r: name = r[0].upper()
            except:
                pass

        self.setup_info_widget(f"TECH. {name}", f"ID: {self.user_id}")

        self.side_layout.addSpacing(20)

        # --- ZMIANA: Dodano style HOVER do przycisków ---
        btn_style = """
            QPushButton { background-color: #E67E22; color: white; border-radius: 6px; font-weight: bold; padding: 15px; text-align: left; padding-left: 20px; border: none; }
            QPushButton:hover { background-color: #D35400; }
        """

        b1 = self.add_button("WPROWADŹ WYNIKI")
        b1.setStyleSheet(btn_style)
        b1.clicked.connect(self.open_edit_result)

        self.side_layout.addSpacing(10)

        b2 = self.add_button("ZOBACZ KARTĘ")
        # Nadajemy styl również tutaj, aby był spójny
        b2.setStyleSheet("""
            QPushButton { background-color: #34495E; color: white; border-radius: 6px; font-weight: bold; padding: 15px; text-align: left; padding-left: 20px; border: none; }
            QPushButton:hover { background-color: #415B76; }
        """)
        b2.clicked.connect(self._show_visit_details)

        self.side_layout.addStretch()

        wyloguj = self.add_button("WYLOGUJ")
        wyloguj.setStyleSheet("""
            QPushButton { background-color: #C0392B; color: white; border-radius: 6px; padding: 15px; font-weight: bold; font-size: 13px; text-align: left; padding-left: 20px; border: none;} 
            QPushButton:hover { background-color: #E74C3C; }
        """)
        wyloguj.clicked.connect(self._show_logout_window)

    def refresh_list(self):
        self.list_todo.clear()
        self.current_selected_frame = None
        self.current_selected_data = None

        if not self.connection: return

        try:
            with self.connection.cursor() as cursor:
                query = """
                    SELECT t.id, v.visit_date, t.title, v.pesel, v.id
                    FROM lab_tests t
                    JOIN visits v ON t.visit_id = v.id
                    WHERE t.description IS NULL
                    ORDER BY v.visit_date ASC
                """
                cursor.execute(query)
                self.fill_list(self.list_todo, cursor.fetchall())

        except Exception as e:
            print(f"SQL Error: {e}")

    def fill_list(self, widget, rows):
        bg_colors = ["#FFFFFF", "#F8F9F9"]

        for i, row in enumerate(rows):
            item = QListWidgetItem()
            date_str = row[1].strftime("%Y-%m-%d")

            item_data = (date_str, f"Badanie: {row[2]}", str(row[3]), row[0], row[4])
            item.setData(Qt.ItemDataRole.UserRole, item_data)

            frame = QFrame()
            frame.setProperty("visit_id", row[4])
            frame.setFixedHeight(60)
            frame.setStyleSheet(
                f"background-color: {bg_colors[i % 2]}; border-bottom: 1px solid #E0E0E0; border-left: 5px solid #E67E22;")

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(15, 0, 15, 0)

            lbl_date = QLabel(date_str)
            lbl_date.setFixedWidth(140)
            lbl_date.setStyleSheet("color: #555; font-weight: bold; border:none;")
            hl.addWidget(lbl_date)

            lbl_title = QLabel(row[2].upper())
            lbl_title.setStyleSheet("color: #2C3E50; font-weight: bold; font-size: 13px; border:none;")
            hl.addWidget(lbl_title, stretch=1)

            lbl_pesel = QLabel(str(row[3]))
            lbl_pesel.setFixedWidth(150)
            lbl_pesel.setStyleSheet("color: #555; border:none;")
            hl.addWidget(lbl_pesel)

            widget.addItem(item)
            item.setSizeHint(QSize(0, 60))
            widget.setItemWidget(item, frame)

    def handle_click(self, item):
        for i in range(self.list_todo.count()):
            w = self.list_todo.itemWidget(self.list_todo.item(i))
            if w: w.setStyleSheet(
                "background-color: #FFFFFF; border-bottom: 1px solid #E0E0E0; border-left: 5px solid #E67E22;")

        self.current_selected_frame = self.list_todo.itemWidget(item)
        self.current_selected_data = item.data(Qt.ItemDataRole.UserRole)

        if self.current_selected_frame:
            self.current_selected_frame.setStyleSheet(
                "background-color: #EBF5FB; border-bottom: 1px solid #AED6F1; border-left: 5px solid #3498DB;")

    def open_edit_result(self):
        if not self.current_selected_data:
            QMessageBox.warning(self, "Uwaga", "Najpierw wybierz badanie z listy.")
            return

        test_id = self.current_selected_data[3]
        test_title = self.current_selected_data[1]

        if EditResultWindow(test_id, test_title, self).exec():
            self.refresh_list()