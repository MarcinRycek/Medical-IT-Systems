import psycopg2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                               QPushButton, QListWidget, QListWidgetItem,
                               QDialog, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette, qRgb

conn_str = "postgresql://neondb_owner:npg_yKUJZNj2ShD0@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech/logowanie_db?sslmode=require&channel_binding=require"


# --- WSPÓLNE OKNA DIALOGOWE ---
class VisitDetailsWindow(QDialog):
    def __init__(self, data_wizyty, tytul_wizyty, lekarz, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Szczegóły Wizyty")
        self.resize(500, 300)
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
        self.resize(400, 200)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Potwierdzenie</h2>", self))
        layout.addWidget(QLabel("<b>Czy na pewno chcesz się wylogować?</b>", self))

        btn_layout = QHBoxLayout()
        logout_button = QPushButton("Wyloguj", self)
        logout_button.clicked.connect(self._logout)
        cancel_button = QPushButton("Anuluj", self)
        cancel_button.clicked.connect(self.reject)

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
        self.resize(1200, 800)  # Startowy rozmiar okna
        self.set_palette()

        self.current_selected_frame = None
        self.current_selected_data = None
        self.connection = self.connect_to_database()

        # Główny Layout Horyzontalny
        self.main_h_layout = QHBoxLayout(self)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)

        # --- PANEL BOCZNY (Fixed Width) ---
        self.side_panel = QFrame(self)
        self.side_panel.setFixedWidth(300)
        self.side_panel.setStyleSheet("background-color: rgb(172, 248, 122); border-right: 1px solid #999;")

        # Layout Panelu Bocznego
        self.side_layout = QVBoxLayout(self.side_panel)
        self.side_layout.setSpacing(15)  # Zmniejszone odstępy, żeby przyciski nie nachodziły
        self.side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Marginesy: Lewy, Góra, Prawy, Dół. Góra zmniejszona z 150 na 50.
        self.side_layout.setContentsMargins(20, 50, 20, 20)

        # --- GŁÓWNA TREŚĆ (Reszta ekranu) ---
        self.main_content_frame = QFrame(self)
        self.main_content_frame.setStyleSheet("background-color: rgb(240, 255, 230);")
        self.main_v_layout = QVBoxLayout(self.main_content_frame)
        self.main_v_layout.setContentsMargins(0, 0, 0, 0)
        self.main_v_layout.setSpacing(0)

        self.lista_wizyt = QListWidget(self.main_content_frame)
        self.lista_wizyt.setFrameShape(QFrame.Shape.NoFrame)
        self.lista_wizyt.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.lista_wizyt.itemClicked.connect(self._handle_item_clicked)

    def init_ui(self):
        """Buduje interfejs. Wywoływane w __init__ dzieci."""
        # 1. Widgety specyficzne (np. Kod Pacjenta)
        self.setup_sidebar_widgets()

        # 2. Separator/Odstęp
        self.side_layout.addSpacing(20)

        # 3. Przyciski wspólne
        zobacz_btn = self.add_button("ZOBACZ SZCZEGÓŁY")
        zobacz_btn.clicked.connect(self._show_visit_details)

        # 4. Przyciski specyficzne (np. Dodaj wizytę)
        self.setup_extra_buttons()

        # 5. Rozpychacz - przesuwa przycisk wylogowania na sam dół
        self.side_layout.addStretch(1)

        # 6. Przycisk wylogowania (na dole)
        wyloguj_btn = self.add_button("WYLOGUJ")
        wyloguj_btn.setStyleSheet("""
            QPushButton { 
                background-color: #444444; color: #FFDDDD; 
                font-size: 14px; border-radius: 8px; padding: 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #662222; }
        """)
        wyloguj_btn.clicked.connect(self._show_logout_window)

        # Prawa strona (Nagłówek + Lista)
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
        styles = ["background-color: #FFFFFF;", "background-color: #F0F0F0;"]
        for i, (data, tytul, osoba) in enumerate(data_rows):
            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""
            osoba_str = str(osoba)

            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, tytul, osoba_str))

            frame = QFrame()
            frame.setFixedHeight(60)  # Mniejsza wysokość wiersza dla lepszej czytelności
            frame.setStyleSheet(styles[i % 2] + "border-bottom: 1px solid #DDD;")

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(10, 0, 10, 0)

            labels = [data_str, tytul, osoba_str]
            for j, txt in enumerate(labels):
                lbl = QLabel(txt)
                lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                lbl.setStyleSheet("border: none; color: #333; font-size: 13px;")
                hl.addWidget(lbl, stretch=1 if j == 1 else 0)
                if j < 2: hl.addSpacing(20)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, 60))
            self.lista_wizyt.setItemWidget(list_item, frame)

    def _handle_item_clicked(self, item):
        # Reset stylu poprzedniego
        if self.current_selected_frame:
            # Prosty reset stylu nie jest idealny przy naprzemiennych kolorach,
            # ale dla uproszczenia przywracamy biały/szary w nast. odświeżeniu lub ignorujemy
            self.current_selected_frame.setStyleSheet("background-color: #EEE;")

        selected_frame = self.lista_wizyt.itemWidget(item)
        if selected_frame:
            selected_frame.setStyleSheet("background-color: #BDE4F7; border: 1px solid #2F9ADF;")
            self.current_selected_frame = selected_frame
            self.current_selected_data = item.data(Qt.ItemDataRole.UserRole)

    def _show_visit_details(self):
        if not self.current_selected_data:
            QMessageBox.warning(self, "Uwaga", "Wybierz wizytę z listy.")
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
        # ZMIANA: Zamiast FixedSize używamy FixedHeight.
        # Szerokość dostosuje się do panelu (minus marginesy layoutu).
        button.setFixedHeight(60)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet("""
            QPushButton {
                background-color: #555555; 
                color: white; 
                font-size: 14px;
                border: none;
                border-radius: 8px; 
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)
        self.side_layout.addWidget(button)
        return button

    def create_header_bar(self, parent, col3_text):
        f = QFrame(parent)
        f.setFixedHeight(40)
        f.setStyleSheet("background-color: #666; border-bottom: 2px solid #444;")
        hl = QHBoxLayout(f)
        hl.setContentsMargins(10, 0, 10, 0)

        headers = ["DATA", "OPIS", col3_text]
        for i, txt in enumerate(headers):
            l = QLabel(txt)
            l.setStyleSheet("color: white; font-weight: bold; font-size: 12px; border: none;")
            hl.addWidget(l, stretch=1 if i == 1 else 0)
            if i < 2: hl.addSpacing(20)
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
        frame.setFixedHeight(80)  # Stała wysokość
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