import psycopg2
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QTextEdit,
    QListWidgetItem, QHBoxLayout, QListWidget
)
from PySide6.QtCore import Qt, QSize

from BaseWindow import BaseWindow, conn_str, DIALOG_STYLE


# --- OKNO ZLECANIA BADANIA ---
class AddLabTestWindow(QDialog):
    def __init__(self, visit_id, parent=None):
        super().__init__(parent)
        self.visit_id = visit_id
        self.setWindowTitle("Zleć Badanie")
        self.resize(400, 280)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        layout.addWidget(QLabel("Nazwa badania:"))
        self.title_in = QLineEdit()
        layout.addWidget(self.title_in)

        layout.addStretch()

        btn = QPushButton("ZLEĆ BADANIE")
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        title = self.title_in.text().strip()
        if not title:
            QMessageBox.warning(self, "Błąd", "Podaj nazwę badania.")
            return

        try:
            conn = psycopg2.connect(conn_str)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO lab_tests (visit_id, title) VALUES (%s, %s)",
                (self.visit_id, title)
            )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "OK", "Badanie zlecone.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))


# --- OKNO ZALECEŃ ---
class AddRecommendationWindow(QDialog):
    def __init__(self, visit_id, current_recs, parent=None):
        super().__init__(parent)
        self.visit_id = visit_id
        self.setWindowTitle("Zalecenia")
        self.resize(500, 450)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Zalecenia:"))

        self.rec_edit = QTextEdit()
        self.rec_edit.setText(current_recs or "")
        layout.addWidget(self.rec_edit)

        btn = QPushButton("ZAPISZ")
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        try:
            conn = psycopg2.connect(conn_str)
            cur = conn.cursor()
            cur.execute(
                "UPDATE visits SET recommendations = %s WHERE id = %s",
                (self.rec_edit.toPlainText(), self.visit_id)
            )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "OK", "Zapisano.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))


# --- OKNO LEKARZA ---
class DoctorWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Lekarz")
        self.code_input = None
        self.setup_doctor_ui()
        self.init_ui()

    # ---------------- UI ----------------
    def setup_doctor_ui(self):
        while self.main_v_layout.count():
            item = self.main_v_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # ===== DZISIAJ =====
        self.main_v_layout.addWidget(self._section_label("WIZYTY DZISIAJ", "#E74C3C"))
        self.main_v_layout.addWidget(self.create_header_bar(self.main_content_frame, "PESEL"))

        self.list_today = QListWidget()
        self.list_today.itemClicked.connect(lambda i: self.handle_list_click(i, "today"))
        self.main_v_layout.addWidget(self.list_today)

        # ===== PRZYSZŁE =====
        self.main_v_layout.addWidget(self._section_label("NADCHODZĄCE WIZYTY", "#3498DB"))
        self.main_v_layout.addWidget(self.create_header_bar(self.main_content_frame, "PESEL"))

        self.list_future = QListWidget()
        self.list_future.itemClicked.connect(lambda i: self.handle_list_click(i, "future"))
        self.main_v_layout.addWidget(self.list_future)

        # ===== HISTORIA PACJENTA =====
        self.main_v_layout.addWidget(self._section_label("HISTORIA PACJENTA", "#27AE60"))
        self.main_v_layout.addWidget(self.create_header_bar(self.main_content_frame, "PESEL"))

        self.list_patient = QListWidget()
        self.list_patient.itemClicked.connect(lambda i: self.handle_list_click(i, "patient"))
        self.main_v_layout.addWidget(self.list_patient)

    def _section_label(self, text, color):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size:18px;font-weight:bold;color:{color};margin-top:15px;")
        return lbl

    # ---------------- LISTY ----------------
    def refresh_list(self):
        self.list_today.clear()
        self.list_future.clear()

        if not self.connection:
            return

        with self.connection.cursor() as cur:
            cur.execute("""
                SELECT id, visit_date, title, pesel, recommendations
                FROM visits
                WHERE doctor_id=%s AND date(visit_date)=CURRENT_DATE
                ORDER BY visit_date
            """, (self.user_id,))
            self.populate_list(self.list_today, cur.fetchall())

            cur.execute("""
                SELECT id, visit_date, title, pesel, recommendations
                FROM visits
                WHERE doctor_id=%s AND date(visit_date)>CURRENT_DATE
                ORDER BY visit_date
            """, (self.user_id,))
            self.populate_list(self.list_future, cur.fetchall())

    def populate_list(self, widget, rows):
        for i, r in enumerate(rows):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, r)

            frame = QFrame()
            frame.setProperty("visit_id", r[0])
            frame.setFixedHeight(60)

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(10, 0, 10, 0)

            hl.addWidget(QLabel(r[1].strftime("%Y-%m-%d %H:%M")))
            hl.addWidget(QLabel(r[2]), 1)
            hl.addWidget(QLabel(str(r[3])))

            widget.addItem(item)
            item.setSizeHint(QSize(0, 60))
            widget.setItemWidget(item, frame)

    # ---------------- KLIK ----------------
    def handle_list_click(self, item, source):
        lists = {
            "today": self.list_today,
            "future": self.list_future,
            "patient": self.list_patient
        }

        active = lists[source]
        others = [l for l in lists.values() if l != active]

        for lst in others:
            lst.clearSelection()

        self.current_selected_frame = active.itemWidget(item)
        self.current_selected_data = item.data(Qt.UserRole)

    # ---------------- KOD PACJENTA ----------------
    def load_patient_by_code(self):
        code = self.code_input.text().strip()
        if len(code) != 6:
            QMessageBox.warning(self, "Błąd", "Kod musi mieć 6 cyfr.")
            return

        with self.connection.cursor() as cur:
            cur.execute("""
                SELECT pesel FROM patient_codes
                WHERE code=%s AND expiration_time > %s
            """, (code, datetime.now()))
            res = cur.fetchone()

            if not res:
                QMessageBox.warning(self, "Błąd", "Kod nieprawidłowy.")
                return

            self.list_patient.clear()

            cur.execute("""
                SELECT id, visit_date, title, pesel, recommendations
                FROM visits
                WHERE pesel=%s
                ORDER BY visit_date DESC
            """, (res[0],))
            self.populate_list(self.list_patient, cur.fetchall())

            QMessageBox.information(self, "OK", "Załadowano historię pacjenta.")
