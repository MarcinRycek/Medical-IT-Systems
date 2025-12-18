from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QListWidget,QDialog, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette, qRgb


class VisitDetailsWindow(QDialog):
    def __init__(self, data_wizyty, tytul_wizyty, lekarz, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Szczegóły Wizyty: {tytul_wizyty}")
        self.setGeometry(300, 300, 600, 400)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"<h2>Szczegóły Wizyty</h2>", self))
        layout.addWidget(QLabel(f"<b>Data:</b> {data_wizyty}", self))
        layout.addWidget(QLabel(f"<b>Tytuł:</b> {tytul_wizyty}", self))
        layout.addWidget(QLabel(f"<b>Doktor/Laborant:</b> {lekarz}", self))
        close_button = QPushButton("Zamknij", self)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)


class AddVisitWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dodaj Nową Wizytę")
        self.setGeometry(300, 300, 600, 400)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<h2>Dodaj Nową Wizytę</h2>", self))
        layout.addWidget(QLabel(f"<b>Wprowadź dane wizyty:</b>", self))

        self.date_input = QLineEdit(self)
        self.title_input = QLineEdit(self)
        self.doctor_input = QLineEdit(self)

        layout.addWidget(QLabel("Data:", self))
        layout.addWidget(self.date_input)
        layout.addWidget(QLabel("Tytuł:", self))
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("Doktor/Laborant:", self))
        layout.addWidget(self.doctor_input)

        add_button = QPushButton("Dodaj Wizytę", self)
        add_button.clicked.connect(self._add_visit)
        layout.addWidget(add_button, alignment=Qt.AlignmentFlag.AlignRight)

        close_button = QPushButton("Zamknij", self)
        close_button.clicked.connect(self.reject)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

    def _add_visit(self):
        QMessageBox.information(self, "Dodaj Wizytę", "Wizytę została dodana (placeholder).")
        self.accept()


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


class MainWindowUI:
    def __init__(self, main_window: QWidget):
        self.w = main_window  # MainWindow instance

    def set_palette(self):
        palette = self.w.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(qRgb(172, 248, 122)))
        self.w.setPalette(palette)

    def add_button(self, layout, text):
        button = QPushButton(text.upper(), self.w)
        button.setFixedSize(QSize(250, 70))
        button.setStyleSheet("""
            QPushButton {
                background-color: #555555; 
                color: white; 
                font-size: 16px;
                border: none;
                border-radius: 10px; 
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        return button

    def create_header_bar(self, parent):
        header_frame = QFrame(parent)
        header_frame.setFixedHeight(40)
        header_frame.setStyleSheet("background-color: #808080;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 0, 10, 0)

        headers = ["DATA", "OPIS:", "DOKTOR:"]
        for i, text in enumerate(headers):
            label = QLabel(text, header_frame)
            label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet("background-color: #808080;font-weight: bold; color: #FFFFFF; font-size: 14px;")
            header_layout.addWidget(label, stretch=1 if i == 1 else 0)

        header_frame.setLayout(header_layout)
        return header_frame

    def build(self):
        """
        Builds the full UI and returns references needed by MainWindow.
        """
        main_h_layout = QHBoxLayout(self.w)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        side_panel = QFrame(self.w)
        side_panel.setFixedWidth(300)
        side_panel.setStyleSheet("background-color: rgb(172, 248, 122);")
        side_layout = QVBoxLayout(side_panel)
        side_layout.setSpacing(40)
        side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        side_layout.setContentsMargins(20, 150, 20, 20)

        patient_code = self.w.fetch_patient_code()
        code_text = str(patient_code) if patient_code else "------"

        code_frame = QFrame(self.w)
        code_frame.setFixedSize(250, 80)
        code_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 2px solid #CCCCCC;
            }
        """)

        code_layout = QVBoxLayout(code_frame)
        code_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        code_label_title = QLabel("KOD PACJENTA", code_frame)
        code_label_title.setStyleSheet("color: #666666; font-size: 12px;")

        code_label = QLabel(code_text, code_frame)
        code_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            letter-spacing: 4px;
            color: #000000;
        """)

        code_layout.addWidget(code_label_title)
        code_layout.addWidget(code_label)

        side_layout.addWidget(code_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        zobacz_wizyte_btn = self.add_button(side_layout, "zobacz wizytę")
        dodaj_wizyte_btn = self.add_button(side_layout, "dodaj nową wizytę")
        wyloguj_btn = self.add_button(side_layout, "wyloguj")

        side_layout.addStretch(1)

        zobacz_wizyte_btn.clicked.connect(self.w._show_visit_details)
        dodaj_wizyte_btn.clicked.connect(self.w._show_add_visit_window)
        wyloguj_btn.clicked.connect(self.w._show_logout_window)

        main_content_frame = QFrame(self.w)
        main_content_frame.setStyleSheet("background-color: rgb(172, 248, 122);")
        main_v_layout = QVBoxLayout(main_content_frame)
        main_v_layout.setContentsMargins(0, 0, 0, 0)
        main_v_layout.setSpacing(0)

        header_frame = self.create_header_bar(main_content_frame)
        main_v_layout.addWidget(header_frame)

        lista_wizyt = QListWidget(main_content_frame)
        lista_wizyt.setFrameShape(QFrame.Shape.NoFrame)
        lista_wizyt.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        lista_wizyt.setMinimumSize(QSize(100, 100))

        lista_wizyt.itemClicked.connect(self.w._handle_item_clicked)

        main_v_layout.addWidget(lista_wizyt)

        main_h_layout.addWidget(side_panel)
        main_h_layout.addWidget(main_content_frame)

        self.w.setLayout(main_h_layout)

        return {
            "side_panel": side_panel,
            "side_layout": side_layout,
            "main_content_frame": main_content_frame,
            "lista_wizyt": lista_wizyt,
            "buttons": {
                "zobacz_wizyte_btn": zobacz_wizyte_btn,
                "dodaj_wizyte_btn": dodaj_wizyte_btn,
                "wyloguj_btn": wyloguj_btn,
            }
        }
