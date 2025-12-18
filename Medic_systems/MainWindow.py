import psycopg2
from PySide6.QtWidgets import QWidget, QMessageBox, QListWidgetItem, QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QSize

from MainWindowUI import MainWindowUI, VisitDetailsWindow, AddVisitWindow, LogoutWindow


class MainWindow(QWidget):
    def __init__(self, logged_in_user_id, role):
        super().__init__()
        self.setWindowTitle("MedEX-POL")
        self.setGeometry(100, 100, 1200, 700)

        self.current_selected_frame = None
        self.current_selected_data = None

        self.logged_in_user_id = logged_in_user_id
        self.role = role

        self.connection = self.connect_to_database()

        self.ui = MainWindowUI(self)
        self.ui.set_palette()
        built = self.ui.build()

        self.lista_wizyt = built["lista_wizyt"]

        self.add_list_items()

    def fetch_patient_code(self):
        if not self.connection:
            return None

        query = """
        SELECT code
        FROM patient_codes
        WHERE pesel = %s
        LIMIT 1
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (self.logged_in_user_id,))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Error fetching patient code: {e}")
            return None

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
        add_visit_window = AddVisitWindow(self)
        add_visit_window.exec()

    def _show_logout_window(self):
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

        details_window = VisitDetailsWindow(
            data_wizyty=data,
            tytul_wizyty=tytul,
            lekarz=lekarz,
            parent=self
        )
        details_window.exec()

    def connect_to_database(self):
        conn_str = "postgresql://neondb_owner:npg_yKUJZNj2ShD0@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech/logowanie_db?sslmode=require&channel_binding=require"

        try:
            connection = psycopg2.connect(conn_str)
            print("Successfully connected to the database!")
            return connection
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            return None

    def fetch_visits_from_database(self):
        if not self.connection:
            return []

        query = """
        SELECT visit_date, title, coalesce(doctor_id, laborant_id)
        FROM visits
        WHERE pesel = %s
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (self.logged_in_user_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []

    def add_list_items(self):
        styles = ["background-color: #D3D3D3;", "background-color: #C4C4C4;"]

        all_visits_data = self.fetch_visits_from_database()

        for i, (data, tytul, lekarz) in enumerate(all_visits_data):
            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""

            list_item = QListWidgetItem()
            list_item.setData(
                Qt.ItemDataRole.UserRole,
                (data_str, tytul, lekarz)
            )

            frame = QFrame()
            frame.setFixedHeight(70)
            frame.setStyleSheet(styles[i % 2])

            h_layout = QHBoxLayout(frame)
            h_layout.setContentsMargins(10, 0, 10, 0)

            labels_data = [data_str, tytul, lekarz]
            for j, text in enumerate(labels_data):
                label = QLabel(str(text))  # ← ZERO upper()
                label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                label.setStyleSheet(
                    "background-color: transparent; color: #444444; "
                    "font-size: 14px; font-weight: bold;"
                )
                h_layout.addWidget(label, stretch=1 if j == 1 else 0)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, frame.height()))
            self.lista_wizyt.setItemWidget(list_item, frame)
