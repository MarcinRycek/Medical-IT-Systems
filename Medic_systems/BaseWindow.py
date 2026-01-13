import psycopg2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                               QPushButton, QListWidget, QListWidgetItem,
                               QDialog, QMessageBox, QScrollArea)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette, qRgb

conn_str = "postgresql://neondb_owner:npg_yKUJZNj2ShD0@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech/logowanie_db?sslmode=require&channel_binding=require"


# --- OKNO SZCZEGÓŁÓW WIZYTY ---
class VisitDetailsWindow(QDialog):
    def __init__(self, data_wizyty, tytul_wizyty, lekarz, lab_results=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Szczegóły Wizyty")
        self.resize(500, 550)
        self.setStyleSheet("background-color: #F0F0F0;")

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        title_lbl = QLabel(f"<h2>{tytul_wizyty}</h2>", self)
        title_lbl.setStyleSheet("color: black; border: none;")
        layout.addWidget(title_lbl)

        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: white; border: 1px solid #999;")
        info_layout = QVBoxLayout(info_frame)

        lbl_date = QLabel(f"<b>Data:</b> {data_wizyty}")
        lbl_date.setStyleSheet("color: black; font-size: 13px; border: none;")
        info_layout.addWidget(lbl_date)

        lbl_doc = QLabel(f"<b>Prowadzący:</b> {lekarz}")
        lbl_doc.setStyleSheet("color: black; font-size: 13px; border: none;")
        info_layout.addWidget(lbl_doc)

        layout.addWidget(info_frame)

        if lab_results:
            layout.addSpacing(15)
            layout.addWidget(QLabel("<h3>WYNIKI BADAŃ:</h3>"))

            results_area = QScrollArea()
            results_area.setWidgetResizable(True)
            results_area.setFrameShape(QFrame.Shape.Box)

            results_content = QWidget()
            results_content.setStyleSheet("background-color: #DDD;")
            results_layout = QVBoxLayout(results_content)
            results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            results_layout.setSpacing(10)

            for title, desc in lab_results:
                res_frame = QFrame()
                res_frame.setStyleSheet("""
                    QFrame {
                        background-color: #FFFFFF; 
                        border: 1px solid #888;    
                    }
                """)
                res_l = QVBoxLayout(res_frame)
                res_l.setContentsMargins(10, 10, 10, 10)

                t_lbl = QLabel(title.upper())
                t_lbl.setStyleSheet("font-weight: bold; color: #000; font-size: 13px; border: none;")

                desc_text = desc if desc else "Oczekiwanie na wynik..."
                d_lbl = QLabel(desc_text)
                d_lbl.setWordWrap(True)
                d_lbl.setStyleSheet("color: black; border: none; margin-top: 5px; font-size: 12px;")

                res_l.addWidget(t_lbl)
                res_l.addWidget(d_lbl)
                results_layout.addWidget(res_frame)

            results_area.setWidget(results_content)
            layout.addWidget(results_area)
        else:
            layout.addStretch()
            no_results_lbl = QLabel("Brak wyników badań.")
            no_results_lbl.setStyleSheet("color: #444; font-style: italic;")
            layout.addWidget(no_results_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addStretch()

        close_button = QPushButton("Zamknij", self)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #CCC; color: black; border: 1px solid #888; padding: 5px;
            }
            QPushButton:hover { background-color: #BBB; }
        """)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)


class LogoutWindow(QDialog):
    def __init__(self, parent=None, on_logged_out=None):
        super().__init__(parent)
        self.setWindowTitle("Wylogowanie")
        self.resize(400, 200)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Potwierdzenie</h2>", self))
        layout.addWidget(QLabel("Czy na pewno chcesz się wylogować?", self))

        btn_layout = QHBoxLayout()
        cancel_button = QPushButton("Anuluj", self)
        cancel_button.clicked.connect(self.reject)
        logout_button = QPushButton("Wyloguj", self)
        logout_button.clicked.connect(self._logout)

        btn_layout.addWidget(cancel_button)
        btn_layout.addWidget(logout_button)
        layout.addLayout(btn_layout)
        self.on_logged_out = on_logged_out

    def _logout(self):
        self.accept()
        if self.on_logged_out:
            self.on_logged_out()


# --- KLASA BAZOWA ---
class BaseWindow(QWidget):
    def __init__(self, user_id, role_title):
        super().__init__()
        self.user_id = user_id
        self.role_title = role_title

        self.setWindowTitle(f"MedEX-POL - Panel: {self.role_title}")
        self.resize(1200, 800)
        self.set_palette()

        self.current_selected_frame = None
        self.current_selected_data = None
        self.connection = self.connect_to_database()

        self.main_h_layout = QHBoxLayout(self)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)

        self.side_panel = QFrame(self)
        self.side_panel.setFixedWidth(300)
        self.side_panel.setStyleSheet("background-color: rgb(172, 248, 122); border-right: 1px solid #999;")

        self.side_layout = QVBoxLayout(self.side_panel)
        self.side_layout.setSpacing(15)
        self.side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.side_layout.setContentsMargins(20, 50, 20, 20)

        self.main_content_frame = QFrame(self)
        self.main_content_frame.setStyleSheet("background-color: rgb(240, 255, 230);")
        self.main_v_layout = QVBoxLayout(self.main_content_frame)
        self.main_v_layout.setContentsMargins(0, 0, 0, 0)
        self.main_v_layout.setSpacing(0)

        self.lista_wizyt = QListWidget(self.main_content_frame)
        self.lista_wizyt.setFrameShape(QFrame.Shape.NoFrame)
        self.lista_wizyt.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.lista_wizyt.setStyleSheet("QListWidget { background-color: rgb(240, 255, 230); color: black; }")
        self.lista_wizyt.itemClicked.connect(self._handle_item_clicked)

    def init_ui(self):
        self.setup_sidebar_widgets()
        self.side_layout.addSpacing(20)

        zobacz_btn = self.add_button("ZOBACZ SZCZEGÓŁY")
        zobacz_btn.clicked.connect(self._show_visit_details)

        self.setup_extra_buttons()
        self.side_layout.addStretch(1)

        wyloguj_btn = self.add_button("WYLOGUJ")
        wyloguj_btn.setStyleSheet(
            "QPushButton { background-color: #444; color: #FDD; font-size: 14px; border-radius: 8px; padding: 15px; font-weight: bold; } QPushButton:hover { background-color: #622; }")
        wyloguj_btn.clicked.connect(self._show_logout_window)

        third_col = "DOKTOR:" if self.role_title == "Pacjent" else "PACJENT (PESEL):"
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
                cursor.execute(query, (self.user_id,))
                rows = cursor.fetchall()
                self.add_list_items(rows)
        except Exception as e:
            print(f"SQL Error: {e}")

    def add_list_items(self, data_rows):
        styles = ["background-color: #FFFFFF;", "background-color: #E8E8E8;"]

        # Szerokości kolumn (muszą być takie same jak w nagłówku!)
        WIDTH_DATE = 140
        WIDTH_PERSON = 150

        for i, (data, tytul, osoba) in enumerate(data_rows):
            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""
            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, tytul, str(osoba)))

            frame = QFrame()
            frame.setFixedHeight(60)
            frame.setStyleSheet(styles[i % 2] + "border-bottom: 1px solid #AAA; color: black;")

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(10, 0, 10, 0)

            # Kolumna 1: Data
            lbl_date = QLabel(data_str)
            lbl_date.setFixedWidth(WIDTH_DATE)
            lbl_date.setStyleSheet("border: none; color: black; font-size: 13px;")
            hl.addWidget(lbl_date)

            # Kolumna 2: Opis (Stretch)
            lbl_title = QLabel(tytul)
            lbl_title.setStyleSheet("border: none; color: black; font-size: 13px;")
            hl.addWidget(lbl_title, stretch=1)

            # Kolumna 3: Osoba
            lbl_person = QLabel(str(osoba))
            lbl_person.setFixedWidth(WIDTH_PERSON)
            lbl_person.setStyleSheet("border: none; color: black; font-size: 13px;")
            hl.addWidget(lbl_person)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, 60))
            self.lista_wizyt.setItemWidget(list_item, frame)

    def _handle_item_clicked(self, item):
        if self.current_selected_frame:
            try:
                # Przywracanie koloru
                old_index = -1
                for i in range(self.lista_wizyt.count()):
                    it = self.lista_wizyt.item(i)
                    wid = self.lista_wizyt.itemWidget(it)
                    if wid == self.current_selected_frame:
                        old_index = i
                        break

                if old_index != -1:
                    bg_color = "#FFFFFF" if old_index % 2 == 0 else "#E8E8E8"
                    self.current_selected_frame.setStyleSheet(
                        f"background-color: {bg_color}; color: black; border-bottom: 1px solid #AAA;")

            except RuntimeError:
                self.current_selected_frame = None

        selected_frame = self.lista_wizyt.itemWidget(item)
        if selected_frame:
            selected_frame.setStyleSheet("background-color: #BDE4F7; border: 1px solid #2F9ADF; color: black;")
            self.current_selected_frame = selected_frame
            self.current_selected_data = item.data(Qt.ItemDataRole.UserRole)

    def _show_visit_details(self):
        if not self.current_selected_data:
            QMessageBox.warning(self, "Uwaga", "Wybierz wizytę z listy.")
            return

        d, t, o = self.current_selected_data
        VisitDetailsWindow(d, t, o, lab_results=None, parent=self).exec()

    def _show_logout_window(self):
        LogoutWindow(self, self._handle_logged_out).exec()

    def _handle_logged_out(self):
        from LoginWindow import LoginWindow
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def add_button(self, text):
        button = QPushButton(text.upper(), self)
        button.setFixedHeight(60)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet("""
            QPushButton { 
                background-color: #555; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; border: none;
            } 
            QPushButton:hover { background-color: #777; }
        """)
        self.side_layout.addWidget(button)
        return button

    def create_header_bar(self, parent, col3_text):
        f = QFrame(parent)
        f.setFixedHeight(40)
        f.setStyleSheet("background-color: #666; border-bottom: 2px solid #444;")
        hl = QHBoxLayout(f)
        hl.setContentsMargins(10, 0, 10, 0)

        # Szerokości kolumn
        WIDTH_DATE = 140
        WIDTH_PERSON = 150

        # Kolumna 1: DATA
        l1 = QLabel("DATA")
        l1.setFixedWidth(WIDTH_DATE)
        l1.setStyleSheet("color: white; font-weight: bold; font-size: 12px; border: none;")
        hl.addWidget(l1)

        # Kolumna 2: OPIS (Stretch)
        l2 = QLabel("OPIS")
        l2.setStyleSheet("color: white; font-weight: bold; font-size: 12px; border: none;")
        hl.addWidget(l2, stretch=1)

        # Kolumna 3: OSOBA
        l3 = QLabel(col3_text)
        l3.setFixedWidth(WIDTH_PERSON)
        l3.setStyleSheet("color: white; font-weight: bold; font-size: 12px; border: none;")
        hl.addWidget(l3)

        f.setLayout(hl)
        return f

    def set_palette(self):
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(qRgb(172, 248, 122)))
        self.setPalette(palette)

    def connect_to_database(self):
        try:
            return psycopg2.connect(conn_str)
        except Exception as e:
            print(f"DB Error: {e}")
            return None

    def setup_info_widget(self, title, subtitle):
        frame = QFrame(self)
        frame.setFixedHeight(80)
        frame.setStyleSheet("background-color: #4A4A4A; border-radius: 10px;")
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(2)

        l1 = QLabel(title, frame)
        l1.setStyleSheet("color: white; font-size: 16px; font-weight: bold; border: none;")
        l2 = QLabel(subtitle, frame)
        l2.setStyleSheet("color: #CCCCCC; font-size: 11px; border: none;")

        layout.addWidget(l1)
        layout.addWidget(l2)
        self.side_layout.addWidget(frame)