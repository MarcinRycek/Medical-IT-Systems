import psycopg2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                               QPushButton, QListWidget, QListWidgetItem,
                               QDialog, QMessageBox, QScrollArea)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette, qRgb

conn_str = "postgresql://neondb_owner:npg_yKUJZNj2ShD0@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech/logowanie_db?sslmode=require&channel_binding=require"

# Wspólny styl dla komunikatów
MSG_BOX_STYLE = """
    QMessageBox {
        background-color: #FFFFFF;
        color: #000000;
    }
    QMessageBox QLabel {
        color: #000000;
        background-color: transparent;
    }
    QMessageBox QPushButton {
        background-color: #F0F0F0;
        color: #000000;
        border: 1px solid #888888;
        border-radius: 5px;
        padding: 5px 15px;
    }
    QMessageBox QPushButton:hover {
        background-color: #E0E0E0;
    }
"""


class VisitDetailsWindow(QDialog):
    def __init__(self, data_wizyty, tytul_wizyty, lekarz, lab_results=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Karta Wizyty")
        self.resize(550, 600)
        self.setStyleSheet("background-color: #F8F9FA;" + MSG_BOX_STYLE)

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


class LogoutWindow(QDialog):
    def __init__(self, parent=None, on_logged_out=None):
        super().__init__(parent)
        self.setWindowTitle("Wylogowanie")
        self.resize(350, 180)
        self.setStyleSheet("background-color: white;" + MSG_BOX_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        lbl = QLabel("Czy na pewno chcesz się wylogować?", self)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #333; font-weight: 500;")
        layout.addWidget(lbl)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        cancel_button = QPushButton("ANULUJ", self)
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button.setStyleSheet(
            "QPushButton { background-color: #ECF0F1; color: #333; border: none; padding: 10px; border-radius: 4px; font-weight: bold;} QPushButton:hover { background-color: #D0D3D4; }")
        cancel_button.clicked.connect(self.reject)

        logout_button = QPushButton("WYLOGUJ", self)
        logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_button.setStyleSheet(
            "QPushButton { background-color: #E74C3C; color: white; border: none; padding: 10px; border-radius: 4px; font-weight: bold;} QPushButton:hover { background-color: #C0392B; }")
        logout_button.clicked.connect(self._logout)

        btn_layout.addWidget(cancel_button)
        btn_layout.addWidget(logout_button)
        layout.addLayout(btn_layout)
        self.on_logged_out = on_logged_out

    def _logout(self):
        self.accept()
        if self.on_logged_out:
            self.on_logged_out()


class BaseWindow(QWidget):
    def __init__(self, user_id, role_title):
        super().__init__()
        self.user_id = user_id
        self.role_title = role_title

        self.setWindowTitle(f"MedEX-POL - Panel: {self.role_title}")
        self.resize(1200, 800)

        # --- APLIKUJEMY STYL KOMUNIKATÓW NA CAŁE OKNO ---
        self.setStyleSheet(MSG_BOX_STYLE)

        self.current_selected_frame = None
        self.current_selected_data = None
        self.connection = self.connect_to_database()

        self.main_h_layout = QHBoxLayout(self)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)

        self.side_panel = QFrame(self)
        self.side_panel.setFixedWidth(280)
        self.side_panel.setStyleSheet("background-color: #2C3E50; border: none;")

        self.side_layout = QVBoxLayout(self.side_panel)
        self.side_layout.setSpacing(15)
        self.side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.side_layout.setContentsMargins(20, 40, 20, 20)

        self.main_content_frame = QFrame(self)
        self.main_content_frame.setStyleSheet("background-color: #ECF0F1;")
        self.main_v_layout = QVBoxLayout(self.main_content_frame)
        self.main_v_layout.setContentsMargins(30, 30, 30, 30)
        self.main_v_layout.setSpacing(0)

        self.list_header_lbl = QLabel(f"LISTA WIZYT", self.main_content_frame)
        self.list_header_lbl.setStyleSheet("color: #2C3E50; font-size: 24px; font-weight: bold; margin-bottom: 15px;")
        self.main_v_layout.addWidget(self.list_header_lbl)

        self.lista_wizyt = QListWidget(self.main_content_frame)
        self.lista_wizyt.setFrameShape(QFrame.Shape.NoFrame)
        self.lista_wizyt.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.lista_wizyt.setStyleSheet(
            "QListWidget { background-color: transparent; outline: none; } QScrollBar:vertical { width: 10px; background: #ECF0F1; } QScrollBar::handle:vertical { background: #BDC3C7; border-radius: 5px; }")
        self.lista_wizyt.itemClicked.connect(self._handle_item_clicked)

    def connect_to_database(self):
        try:
            return psycopg2.connect(conn_str)
        except Exception as e:
            print(f"Błąd połączenia z bazą: {e}")
            return None

    def init_ui(self):
        self.setup_sidebar_widgets()
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #34495E;")
        self.side_layout.addWidget(line)
        self.side_layout.addSpacing(10)

        zobacz_btn = self.add_button("ZOBACZ KARTĘ")
        zobacz_btn.clicked.connect(self._show_visit_details)

        self.setup_extra_buttons()
        self.side_layout.addStretch(1)

        wyloguj_btn = self.add_button("WYLOGUJ")
        wyloguj_btn.setStyleSheet(
            "QPushButton { background-color: #C0392B; color: white; border-radius: 6px; padding: 15px; font-weight: bold; font-size: 13px; text-align: left; padding-left: 20px; border: none;} QPushButton:hover { background-color: #E74C3C; }")
        wyloguj_btn.clicked.connect(self._show_logout_window)

        third_col = "LEKARZ" if self.role_title == "Pacjent" else "PESEL"
        header = self.create_header_bar(self.main_content_frame, third_col)
        self.main_v_layout.addWidget(header)
        self.main_v_layout.addWidget(self.lista_wizyt)

        self.main_h_layout.addWidget(self.side_panel)
        self.main_h_layout.addWidget(self.main_content_frame)
        self.setLayout(self.main_h_layout)

        self.refresh_list()

    def setup_sidebar_widgets(self):
        pass

    def setup_extra_buttons(self):
        pass

    def get_sql_query(self):
        return ""

    def refresh_list(self):
        self.current_selected_frame = None
        self.current_selected_data = None
        self.lista_wizyt.clear()
        query = self.get_sql_query()
        if not query or not self.connection: return
        try:
            with self.connection.cursor() as cursor:
                if "%s" in query:
                    cursor.execute(query, (self.user_id,))
                else:
                    cursor.execute(query)
                rows = cursor.fetchall()
                self.add_list_items(rows)
        except Exception as e:
            print(f"SQL Error: {e}")

    def add_list_items(self, data_rows):
        styles = ["background-color: #FFFFFF;", "background-color: #F8F9F9;"]
        WIDTH_DATE = 140
        WIDTH_PERSON = 150
        for i, (data, tytul, osoba) in enumerate(data_rows):
            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""
            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, tytul, str(osoba)))

            frame = QFrame()
            frame.setFixedHeight(65)
            frame.setStyleSheet(f"{styles[i % 2]} border-bottom: 1px solid #E0E0E0; color: #2C3E50;")

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(15, 0, 15, 0)

            lbl_date = QLabel(data_str)
            lbl_date.setFixedWidth(WIDTH_DATE)
            lbl_date.setStyleSheet("border: none; color: #555; font-weight: bold;")
            hl.addWidget(lbl_date)

            lbl_title = QLabel(tytul)
            lbl_title.setStyleSheet("border: none; color: #2C3E50; font-size: 14px; font-weight: 500;")
            hl.addWidget(lbl_title, stretch=1)

            lbl_person = QLabel(str(osoba))
            lbl_person.setFixedWidth(WIDTH_PERSON)
            lbl_person.setStyleSheet("border: none; color: #555;")
            hl.addWidget(lbl_person)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, 65))
            self.lista_wizyt.setItemWidget(list_item, frame)

    def _handle_item_clicked(self, item):
        for i in range(self.lista_wizyt.count()):
            it = self.lista_wizyt.item(i)
            wid = self.lista_wizyt.itemWidget(it)
            if wid:
                bg = "#FFFFFF" if i % 2 == 0 else "#F8F9F9"
                wid.setStyleSheet(f"background-color: {bg}; border-bottom: 1px solid #E0E0E0; color: #2C3E50;")

        selected_frame = self.lista_wizyt.itemWidget(item)
        if selected_frame:
            selected_frame.setStyleSheet(
                "background-color: #EBF5FB; border-bottom: 1px solid #AED6F1; border-left: 5px solid #3498DB; color: #2C3E50;")
            self.current_selected_frame = selected_frame
            self.current_selected_data = item.data(Qt.ItemDataRole.UserRole)

    def _show_visit_details(self):
        if not self.current_selected_data:
            QMessageBox.warning(self, "Uwaga", "Wybierz wizytę z listy.")
            return
        d, t, o = self.current_selected_data
        VisitDetailsWindow(d, t, o, lab_results=None, parent=self).exec()

    def _show_logout_window(self):
        from LoginWindow import LoginWindow
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def add_button(self, text):
        btn = QPushButton(text, self)
        btn.setFixedHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background-color: #34495E; color: white; border-radius: 6px; font-weight: bold; font-size: 13px; text-align: left; padding-left: 20px; border: none;} QPushButton:hover { background-color: #415B76; }")
        self.side_layout.addWidget(btn)
        return btn

    def create_header_bar(self, parent, col3_text):
        f = QFrame(parent)
        f.setFixedHeight(45)
        f.setStyleSheet("background-color: #34495E; border-top-left-radius: 6px; border-top-right-radius: 6px;")
        hl = QHBoxLayout(f)
        hl.setContentsMargins(15, 0, 15, 0)

        style = "color: white; font-weight: bold; font-size: 12px; border: none;"

        l1 = QLabel("DATA")
        l1.setFixedWidth(140)
        l1.setStyleSheet(style)
        hl.addWidget(l1)

        l2 = QLabel("TYTUŁ / OPIS")
        l2.setStyleSheet(style)
        hl.addWidget(l2, stretch=1)

        l3 = QLabel(col3_text)
        l3.setFixedWidth(150)
        l3.setStyleSheet(style)
        hl.addWidget(l3)

        f.setLayout(hl)
        return f

    def setup_info_widget(self, title, subtitle):
        f = QFrame(self)
        f.setFixedHeight(90)
        f.setStyleSheet("background-color: #243442; border-radius: 8px;")
        l = QVBoxLayout(f)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.setSpacing(5)

        l1 = QLabel(title, f)
        l1.setStyleSheet("color: #3498DB; font-size: 14px; font-weight: 800; border: none;")
        l2 = QLabel(subtitle, f)
        l2.setStyleSheet("color: #BDC3C7; font-size: 12px; border: none;")

        l.addWidget(l1)
        l.addWidget(l2)
        self.side_layout.addWidget(f)