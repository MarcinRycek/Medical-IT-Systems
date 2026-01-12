import random
from datetime import datetime, timedelta
from PySide6.QtWidgets import QLabel, QFrame, QPushButton, QVBoxLayout, QMessageBox
from PySide6.QtCore import Qt
from BaseWindow import BaseWindow


class PatientWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Pacjent")
        self.code_label = None
        self.init_ui()  # Budujemy UI z klasy bazowej

    def setup_sidebar_widgets(self):
        # Specjalny Widget Pacjenta (Kod)
        code = self.fetch_code()
        code_text = str(code) if code else "------"

        frame = QFrame(self)
        frame.setFixedSize(250, 120)
        frame.setStyleSheet("background-color: white; border-radius: 15px; border: 2px solid #CCCCCC;")

        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)

        layout.addWidget(QLabel("KOD PACJENTA", styleSheet="color: #666; font-size: 12px; border: none;"))

        self.code_label = QLabel(code_text,
                                 styleSheet="font-size: 28px; font-weight: bold; letter-spacing: 4px; color: #000; border: none;")
        layout.addWidget(self.code_label)

        btn = QPushButton("Generuj nowy kod")
        btn.setStyleSheet(
            "QPushButton { background-color: #2F9ADF; color: white; border-radius: 5px; padding: 4px; } QPushButton:hover { background-color: #1F8ACF; }")
        btn.clicked.connect(self.generate_code)
        layout.addWidget(btn)

        self.side_layout.addWidget(frame, alignment=Qt.AlignmentFlag.AlignCenter)

    def get_sql_query(self):
        return "SELECT visit_date, title, coalesce(doctor_id, laborant_id) FROM visits WHERE pesel = %s"

    def fetch_code(self):
        if not self.connection: return None
        try:
            with self.connection.cursor() as cur:
                cur.execute("SELECT code FROM patient_codes WHERE pesel = %s", (self.user_id,))
                res = cur.fetchone()
                return res[0] if res else None
        except:
            return None

    def generate_code(self):
        if not self.connection: return
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