import random
import psycopg2
from datetime import datetime, timedelta
from PySide6.QtWidgets import QLabel, QFrame, QPushButton, QVBoxLayout, QMessageBox, QListWidgetItem, QHBoxLayout
from PySide6.QtCore import Qt, QSize
from BaseWindow import BaseWindow, VisitDetailsWindow


class PatientWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Pacjent")
        self.code_label = None
        self.init_ui()

    def setup_sidebar_widgets(self):
        code = self.fetch_code()
        code_text = str(code) if code else "------"

        frame = QFrame(self)
        frame.setFixedSize(250, 140)
        frame.setStyleSheet("""
            QFrame {
                background-color: white; 
                border-radius: 15px; 
                border: 2px solid #CCCCCC;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)

        title_lbl = QLabel("KOD DOSTĘPU", frame)
        title_lbl.setStyleSheet("color: #666; font-size: 11px; font-weight: bold; border: none;")
        layout.addWidget(title_lbl)

        self.code_label = QLabel(code_text, frame)
        self.code_label.setStyleSheet(
            "font-size: 32px; font-weight: bold; letter-spacing: 3px; color: #222; border: none;")
        layout.addWidget(self.code_label)

        btn = QPushButton("GENERUJ NOWY KOD")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background-color: #2F9ADF; color: white; border-radius: 5px; padding: 8px; font-weight: bold; border: none; } QPushButton:hover { background-color: #1F8ACF; }")
        btn.clicked.connect(self.generate_code)
        layout.addWidget(btn)

        self.side_layout.addWidget(frame, alignment=Qt.AlignmentFlag.AlignCenter)

    def get_sql_query(self):
        # Pobieramy ID wizyty (v.id) aby móc potem szukać wyników badań
        return """
            SELECT 
                v.id,
                v.visit_date, 
                v.title, 
                u.login 
            FROM visits v
            JOIN users u ON u.id = COALESCE(v.doctor_id, v.laborant_id)
            WHERE v.pesel = %s
            ORDER BY v.visit_date DESC
        """

    # --- NADPISUJEMY ABY ZAPISAĆ ID WIZYTY ---
    def add_list_items(self, data_rows):
        styles = ["background-color: #FFFFFF;", "background-color: #F0F0F0;"]

        # data_rows teraz ma: (id_wizyty, data, tytul, login_lekarza)
        for i, (vid, data, tytul, lekarz) in enumerate(data_rows):
            data_str = data.strftime("%Y-%m-%d %H:%M") if data else ""
            lekarz_str = str(lekarz)

            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, tytul, lekarz_str))

            frame = QFrame()
            frame.setFixedHeight(60)
            frame.setStyleSheet(styles[i % 2] + "border-bottom: 1px solid #DDD;")

            # Zapamiętujemy ID wizyty w ukrytej właściwości
            frame.setProperty("visit_id", vid)

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(10, 0, 10, 0)

            labels = [data_str, tytul, lekarz_str]
            for j, txt in enumerate(labels):
                lbl = QLabel(txt)
                lbl.setStyleSheet("border: none; color: #333;")
                hl.addWidget(lbl, stretch=1 if j == 1 else 0)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, 60))
            self.lista_wizyt.setItemWidget(list_item, frame)

    # --- NADPISUJEMY SZCZEGÓŁY ABY POKAZAĆ WYNIKI ---
    def _show_visit_details(self):
        if not self.current_selected_frame:
            QMessageBox.warning(self, "Uwaga", "Wybierz wizytę z listy.")
            return

        # Pobieramy dane podstawowe z itemu
        d, t, o = self.current_selected_data

        # Pobieramy ID wizyty z widgetu
        visit_id = self.current_selected_frame.property("visit_id")

        lab_results = []
        if self.connection and visit_id:
            try:
                with self.connection.cursor() as cursor:
                    # Pobieramy badania dla tej wizyty
                    cursor.execute("SELECT title, description FROM lab_tests WHERE visit_id = %s", (visit_id,))
                    lab_results = cursor.fetchall()
            except Exception as e:
                print(f"Błąd pobierania badań: {e}")

        # Otwieramy okno z przekazanymi wynikami
        VisitDetailsWindow(d, t, o, lab_results=lab_results, parent=self).exec()

    def fetch_code(self):
        if not self.connection: return None
        try:
            with self.connection.cursor() as cur:
                cur.execute("SELECT code FROM patient_codes WHERE pesel = %s AND expiration_time > %s",
                            (self.user_id, datetime.now()))
                res = cur.fetchone()
                return res[0] if res else None
        except:
            return None

    def generate_code(self):
        if not self.connection:
            QMessageBox.critical(self, "Błąd", "Brak połączenia z bazą.")
            return

        new_code = str(random.randint(100000, 999999))
        exp_time = datetime.now() + timedelta(minutes=15)

        try:
            with self.connection.cursor() as cur:
                cur.execute("SELECT 1 FROM patient_codes WHERE pesel = %s", (self.user_id,))
                if cur.fetchone():
                    cur.execute("UPDATE patient_codes SET code=%s, expiration_time=%s WHERE pesel=%s",
                                (new_code, exp_time, self.user_id))
                else:
                    cur.execute("INSERT INTO patient_codes (pesel, code, expiration_time) VALUES (%s, %s, %s)",
                                (self.user_id, new_code, exp_time))

                self.connection.commit()
                self.code_label.setText(new_code)
                QMessageBox.information(self, "Sukces", "Nowy kod wygenerowany (ważny 15 min)!")
        except Exception as e:
            self.connection.rollback()
            QMessageBox.critical(self, "Błąd", str(e))