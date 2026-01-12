import psycopg2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                               QPushButton, QListWidget, QListWidgetItem,
                               QDialog, QMessageBox, QLineEdit)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette, qRgb

conn_str = "postgresql://neondb_owner:npg_yKUJZNj2ShD0@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech/logowanie_db?sslmode=require&channel_binding=require"


# --- WSPÓLNE OKNA DIALOGOWE ---
class VisitDetailsWindow(QDialog):
    def __init__(self, data_wizyty, tytul_wizyty, lekarz, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Szczegóły Wizyty: {tytul_wizyty}")
        self.setGeometry(300, 300, 600, 400)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<h2>Szczegóły Wizyty</h2>", self))
        layout.addWidget(QLabel(f"<b>Data:</b> {data_wizyty}", self))
        layout.addWidget(QLabel(f"<b>Tytuł:</b> {tytul_wizyty}", self))
        layout.addWidget(QLabel(f"<b>Doktor/Laborant/Pacjent:</b> {lekarz}", self))
        close_button = QPushButton("Zamknij", self)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)


class LogoutWindow(QDialog):
    def __init__(self, parent=None, on_logged_out=None):
        super().__init__(parent)
        self.setWindowTitle("Wylogowanie")
        self.setGeometry(300, 300, 600, 400)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Potwierdzenie Wylogowania</h2>", self))
        layout.addWidget(QLabel("<b>Czy na pewno chcesz się wylogować?</b>", self))
        logout_button = QPushButton("Wyloguj", self)
        logout_button.clicked.connect(self._logout)
        layout.addWidget(logout_button, alignment=Qt.AlignmentFlag.AlignRight)
        cancel_button = QPushButton("Anuluj", self)
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.on_logged_out = on_logged_out

    def _logout(self):
        QMessageBox.information(self, "Wylogowanie", "Zostałeś wylogowany.")
        self.accept()
        if self.on_logged_out:
            self.on_logged_out()


# --- KLASA BAZOWA DLA GŁÓWNYCH OKIEN ---
class BaseWindow(QWidget):
    def __init__(self, user_id, role_title):
        super().__init__()
        self.user_id = user_id
        self.role_title = role_title

        self.setWindowTitle(f"MedEX-POL - Panel: {self.role_title}")
        self.setGeometry(100, 100, 1200, 700)
        self.set_palette()

        self.current_selected_frame = None
        self.current_selected_data = None
        self.connection = self.connect_to_database()

        # Layout Główny
        self.main_h_layout = QHBoxLayout(self)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)

        # Panel boczny (Base setup)
        self.side_panel = QFrame(self)
        self.side_panel.setFixedWidth(300)
        self.side_panel.setStyleSheet("background-color: rgb(172, 248, 122);")
        self.side_layout = QVBoxLayout(self.side_panel)
        self.side_layout.setSpacing(40)
        self.side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.side_layout.setContentsMargins(20, 150, 20, 20)

        # Treść główna (Prawa strona)
        self.main_content_frame = QFrame(self)
        self.main_content_frame.setStyleSheet("background-color: rgb(172, 248, 122);")
        self.main_v_layout = QVBoxLayout(self.main_content_frame)
        self.main_v_layout.setContentsMargins(0, 0, 0, 0)
        self.main_v_layout.setSpacing(0)

        # Lista wizyt
        self.lista_wizyt = QListWidget(self.main_content_frame)
        self.lista_wizyt.setFrameShape(QFrame.Shape.NoFrame)
        self.lista_wizyt.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.lista_wizyt.setMinimumSize(QSize(100, 100))
        self.lista_wizyt.itemClicked.connect(self._handle_item_clicked)

    def init_ui(self):
        """Ta metoda musi być wywołana w __init__ klas pochodnych"""
        self.setup_sidebar_widgets()  # Do nadpisania w klasach pochodnych

        # Przyciski wspólne
        zobacz_wizyte_btn = self.add_button("zobacz szczegóły")
        zobacz_wizyte_btn.clicked.connect(self._show_visit_details)

        self.setup_extra_buttons()  # Miejsce na przyciski specyficzne (np. Dodaj Wizytę)

        wyloguj_btn = self.add_button("wyloguj")
        wyloguj_btn.clicked.connect(self._show_logout_window)
        self.side_layout.addStretch(1)

        # Nagłówek i lista
        third_col_name = "DOKTOR:" if self.role_title == "Pacjent" else "PACJENT (PESEL):"
        header_frame = self.create_header_bar(self.main_content_frame, third_col_name)
        self.main_v_layout.addWidget(header_frame)
        self.main_v_layout.addWidget(self.lista_wizyt)

        self.main_h_layout.addWidget(self.side_panel)
        self.main_h_layout.addWidget(self.main_content_frame)
        self.setLayout(self.main_h_layout)
        self.refresh_list()

    def setup_sidebar_widgets(self):
        pass  # Placeholder

    def setup_extra_buttons(self):
        pass  # Placeholder

    def get_sql_query(self):
        return ""  # Placeholder

    def refresh_list(self):
        self.lista_wizyt.clear()
        query = self.get_sql_query()
        if not query or not self.connection: return

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (self.user_id,))
                rows = cursor.fetchall()
                self.add_list_items(rows)
        except Exception as e:
            print(f"Błąd pobierania danych: {e}")

    def add_list_items(self, data_rows):
        styles = ["background-color: #D3D3D3;", "background-color: #C4C4C4;"]
        for i, (data, tytul, osoba) in enumerate(data_rows):
            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""
            osoba_str = str(osoba)

            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, tytul, osoba_str))

            frame = QFrame()
            frame.setFixedHeight(70)
            frame.setStyleSheet(styles[i % 2])
            h_layout = QHBoxLayout(frame)
            h_layout.setContentsMargins(10, 0, 10, 0)

            labels = [data_str, tytul, osoba_str]
            for j, text in enumerate(labels):
                label = QLabel(text)
                label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                label.setStyleSheet(
                    "background-color: transparent; color: #444444; font-size: 14px; font-weight: bold;")
                h_layout.addWidget(label, stretch=1 if j == 1 else 0)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, frame.height()))
            self.lista_wizyt.setItemWidget(list_item, frame)

    def _handle_item_clicked(self, item):
        if self.current_selected_frame:
            idx = self.lista_wizyt.row(self.lista_wizyt.itemAt(self.current_selected_frame.pos()))
            original_style = "background-color: #D3D3D3;" if idx % 2 == 0 else "background-color: #C4C4C4;"
            self.current_selected_frame.setStyleSheet(original_style)

        selected_frame = self.lista_wizyt.itemWidget(item)
        if selected_frame:
            selected_frame.setStyleSheet("background-color: #2F9ADF;")
            self.current_selected_frame = selected_frame
            self.current_selected_data = item.data(Qt.ItemDataRole.UserRole)

    def _show_visit_details(self):
        if not self.current_selected_data:
            QMessageBox.warning(self, "Błąd", "Wybierz wizytę z listy.")
            return
        d, t, o = self.current_selected_data
        VisitDetailsWindow(d, t, o, self).exec()

    def _show_logout_window(self):
        LogoutWindow(self, self._handle_logged_out).exec()

    def _handle_logged_out(self):
        from LoginWindow import LoginWindow
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def add_button(self, text):
        button = QPushButton(text.upper(), self)
        button.setFixedSize(QSize(250, 70))
        button.setStyleSheet("""
            QPushButton { background-color: #555555; color: white; font-size: 16px; border-radius: 10px; border: none; }
            QPushButton:hover { background-color: #666666; }
        """)
        self.side_layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        return button

    def create_header_bar(self, parent, third_col_name):
        f = QFrame(parent)
        f.setFixedHeight(40)
        f.setStyleSheet("background-color: #808080;")
        hl = QHBoxLayout(f)
        hl.setContentsMargins(10, 0, 10, 0)
        for i, txt in enumerate(["DATA", "OPIS", third_col_name]):
            l = QLabel(txt)
            l.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
            hl.addWidget(l, stretch=1 if i == 1 else 0)
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
            print(e)
            return None

    def setup_info_widget(self, title, subtitle):
        frame = QFrame(self)
        frame.setFixedSize(250, 80)
        frame.setStyleSheet("background-color: #555555; border-radius: 15px;")
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        l1 = QLabel(title, frame)
        l1.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        l2 = QLabel(subtitle, frame)
        l2.setStyleSheet("color: #DDDDDD; font-size: 12px;")

        layout.addWidget(l1)
        layout.addWidget(l2)
        self.side_layout.addWidget(frame, alignment=Qt.AlignmentFlag.AlignCenter)