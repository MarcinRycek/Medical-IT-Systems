from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QListWidget, QSizePolicy, \
    QListWidgetItem, QDialog, QMessageBox, QLineEdit
from PySide6.QtCore import Qt, QSize, Signal, Slot
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

        # Add your input fields here for a new visit
        # For example:
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
        # Show a message box when the "Dodaj Wizytę" button is clicked
        QMessageBox.information(self, "Dodaj Wizytę", "Wizytę została dodana (placeholder).")

        self.accept()  # Close the window after showing the message box


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

        self.on_logged_out = on_logged_out  # Callback function to handle logout event

    def _logout(self):
        # Show a message box when the "Wyloguj" button is clicked in the confirmation window
        QMessageBox.information(self, "Wylogowanie", "Zostałeś wylogowany.")

        # Close the LogoutWindow and MainWindow after message box is closed
        self.accept()  # Close the LogoutWindow

        # Close the MainWindow (if it exists) and show the LoginWindow
        if self.on_logged_out:
            self.on_logged_out()  # Call the callback to handle the logout in the main window

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MedEX-POL")
        self.setGeometry(100, 100, 1200, 700)
        self.set_palette()

        self.current_selected_frame = None
        self.current_selected_data = None

        main_h_layout = QHBoxLayout(self)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        side_panel = QFrame(self)
        side_panel.setFixedWidth(300)
        side_panel.setStyleSheet("background-color: rgb(172, 248, 122);")
        side_layout = QVBoxLayout(side_panel)
        side_layout.setSpacing(40)
        side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        side_layout.setContentsMargins(20, 150, 20, 20)

        zobacz_wizyte_btn = self.add_button(side_layout, "zobacz wizytę")
        dodaj_wizyte_btn = self.add_button(side_layout, "dodaj nową wizytę")
        wyloguj_btn = self.add_button(side_layout, "wyloguj")

        side_layout.addStretch(1)

        zobacz_wizyte_btn.clicked.connect(self._show_visit_details)
        dodaj_wizyte_btn.clicked.connect(self._show_add_visit_window)
        wyloguj_btn.clicked.connect(self._show_logout_window)

        main_content_frame = QFrame(self)
        main_content_frame.setStyleSheet("background-color: rgb(172, 248, 122);")
        main_v_layout = QVBoxLayout(main_content_frame)
        main_v_layout.setContentsMargins(0, 0, 0, 0)
        main_v_layout.setSpacing(0)

        header_frame = self.create_header_bar(main_content_frame)
        main_v_layout.addWidget(header_frame)

        self.lista_wizyt = QListWidget(main_content_frame)
        self.lista_wizyt.setFrameShape(QFrame.Shape.NoFrame)
        self.lista_wizyt.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.lista_wizyt.setMinimumSize(QSize(100, 100))

        self.lista_wizyt.itemClicked.connect(self._handle_item_clicked)

        self.add_list_items()

        main_v_layout.addWidget(self.lista_wizyt)

        main_h_layout.addWidget(side_panel)
        main_h_layout.addWidget(main_content_frame)
        self.setLayout(main_h_layout)

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

    def _show_add_visit_window(self):
        # Open the "Dodaj Nową Wizytę" window
        add_visit_window = AddVisitWindow(self)
        add_visit_window.exec()

    def _show_logout_window(self):
        # Open the "Wylogowanie" confirmation window
        logout_window = LogoutWindow(self, self._handle_logged_out)
        logout_window.exec()

    def _handle_logged_out(self):
        from LoginWindow import LoginWindow
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def _show_visit_details(self):
        if not self.current_selected_data:
            QMessageBox.warning(self, "Błąd", "Proszę wybrać wizytę z listy.")
            return

        data, tytul, lekarz = self.current_selected_data

        details_window = VisitDetailsWindow(data, tytul, lekarz, self)
        details_window.exec()

    def set_palette(self):
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(qRgb(172, 248, 122)))
        self.setPalette(palette)

    def add_button(self, layout, text):
        button = QPushButton(text.upper(), self)
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

    def add_list_items(self):
        styles = ["background-color: #D3D3D3;", "background-color: #C4C4C4;"]

        all_visits_data = [
            ("2025-11-15", "Kontrolna Morfologia", "Dr. Jan Kowalski"),
            ("2025-11-10", "Badanie EKG", "Laborant Anna Nowak"),
            ("2025-10-28", "Konsultacja kardiologiczna", "Prof. Tomasz Lewicki"),
            ("2025-10-01", "Pobranie Krwi - Lipidogram", "Laborant Ewa Górska"),
            ("2025-09-12", "Wizyta u specjalisty", "Dr. Jan Kowalski"),
        ]

        for i, (data, tytul, lekarz) in enumerate(all_visits_data):
            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, (data, tytul, lekarz))

            frame = QFrame()
            frame.setObjectName(f"visit_frame_{i}")
            frame.setFixedHeight(70)
            frame.setStyleSheet(styles[i % 2])

            h_layout = QHBoxLayout(frame)
            h_layout.setContentsMargins(10, 0, 10, 0)

            labels_data = [data, tytul, lekarz]
            for j, text in enumerate(labels_data):
                label = QLabel(text.upper())
                label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                label.setStyleSheet(f"background-color: transparent; color: #444444; font-size: 14px; font-weight: bold;")

                h_layout.addWidget(label, stretch=1 if j == 1 else 0)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, frame.height()))
            self.lista_wizyt.setItemWidget(list_item, frame)