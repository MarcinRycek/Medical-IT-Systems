import psycopg2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                               QPushButton, QListWidget, QListWidgetItem,
                               QDialog, QMessageBox, QScrollArea, QTextEdit)
from PySide6.QtCore import Qt, QSize

conn_str = "postgresql://neondb_owner:npg_yKUJZNj2ShD0@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech/logowanie_db?sslmode=require&channel_binding=require"

# --- STYLE ---
DIALOG_STYLE = """
    QDialog { background-color: #F8F9FA; }
    QLabel { color: #2C3E50; font-size: 13px; font-weight: bold; }
    QLineEdit, QTextEdit { 
        background-color: white; color: #2C3E50; 
        border: 1px solid #BDC3C7; border-radius: 4px; padding: 8px; 
    }
    QMessageBox { background-color: white; color: black; }
    QPushButton { background-color: #F0F0F0; color: black; border: 1px solid #888; padding: 5px;}
"""


# --- OKNO SZCZEGÓŁÓW ---
class VisitDetailsWindow(QDialog):
    def __init__(self, d, t, o, res=None, rec=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Karta Wizyty")
        self.resize(500, 600)
        self.setStyleSheet(DIALOG_STYLE)
        l = QVBoxLayout(self)

        l.addWidget(QLabel(f"{t}", styleSheet="font-size: 20px; color: #2C3E50; margin-bottom: 5px;"))
        f = QFrame()
        f.setStyleSheet("background: white; border: 1px solid #ddd; border-radius: 5px;")
        vl = QVBoxLayout(f)
        vl.addWidget(QLabel(f"Data: {d}", styleSheet="color: #555; border:none;"))
        vl.addWidget(QLabel(f"Doktor: {o}", styleSheet="color: #555; border:none;"))
        l.addWidget(f)

        l.addSpacing(10)
        l.addWidget(QLabel("ZALECENIA:", styleSheet="color: #27AE60; font-weight:bold;"))
        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setText(rec if rec else "Brak zaleceń.")
        txt.setFixedHeight(100)
        l.addWidget(txt)

        l.addSpacing(10)
        l.addWidget(QLabel("WYNIKI BADAŃ:", styleSheet="color: #2980B9; font-weight:bold;"))
        if res:
            scroll = QScrollArea()
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            content = QWidget()
            content.setStyleSheet("background: transparent;")
            vbox = QVBoxLayout(content)
            for title, desc in res:
                row = QFrame()
                row.setStyleSheet("background: white; border: 1px solid #eee; border-radius: 4px;")
                rv = QVBoxLayout(row)
                rv.addWidget(QLabel(title.upper(), styleSheet="color: #2980B9; font-weight:bold; border:none;"))
                rv.addWidget(QLabel(desc if desc else "Oczekiwanie...", styleSheet="color:#333; border:none;"))
                vbox.addWidget(row)
            scroll.setWidget(content)
            scroll.setWidgetResizable(True)
            l.addWidget(scroll)
        else:
            l.addWidget(QLabel("Brak zleconych badań.", alignment=Qt.AlignmentFlag.AlignCenter))

        btn = QPushButton("ZAMKNIJ")
        btn.clicked.connect(self.accept)
        l.addWidget(btn)


class LogoutWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wylogowanie")
        self.resize(300, 150)
        self.setStyleSheet(DIALOG_STYLE)
        l = QVBoxLayout(self)
        l.addWidget(QLabel("Czy na pewno chcesz się wylogować?", alignment=Qt.AlignmentFlag.AlignCenter))
        h = QHBoxLayout()
        b1 = QPushButton("ANULUJ");
        b1.clicked.connect(self.reject)
        b2 = QPushButton("WYLOGUJ");
        b2.clicked.connect(self.accept)
        b2.setStyleSheet("background-color: #E74C3C; color: white;")
        h.addWidget(b1);
        h.addWidget(b2)
        l.addLayout(h)


class BaseWindow(QWidget):
    def __init__(self, user_id, role_title):
        super().__init__()
        self.user_id = user_id
        self.role_title = role_title
        self.setWindowTitle(f"MedEX - {role_title}")
        self.resize(1200, 800)
        self.setStyleSheet(DIALOG_STYLE)

        self.connection = self.connect_db()
        self.current_selected_frame = None
        self.current_selected_data = None

        self.main_h_layout = QHBoxLayout(self)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)

        self.side_panel = QFrame()
        self.side_panel.setFixedWidth(280)
        self.side_panel.setStyleSheet("background: #2C3E50; border: none;")
        self.side_layout = QVBoxLayout(self.side_panel)
        self.side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.side_layout.setContentsMargins(20, 40, 20, 20)
        self.main_h_layout.addWidget(self.side_panel)

        self.main_content_frame = QFrame()
        self.main_content_frame.setStyleSheet("background: #ECF0F1;")
        self.main_v_layout = QVBoxLayout(self.main_content_frame)
        self.main_v_layout.setContentsMargins(30, 30, 30, 30)
        self.main_h_layout.addWidget(self.main_content_frame)

    def connect_db(self):
        try:
            conn = psycopg2.connect(conn_str)
            try:
                with conn.cursor() as cur:
                    cur.execute("SET TIME ZONE 'Europe/Warsaw'")
                conn.commit()
            except Exception:
                pass
            return conn
        except:
            return None

    def add_button(self, text):
        btn = QPushButton(text)
        btn.setFixedHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            "background: #34495E; color: white; border-radius: 6px; font-weight: bold; text-align: left; padding-left: 20px;")
        self.side_layout.addWidget(btn)
        return btn

    def setup_info_widget(self, title, subtitle):
        f = QFrame()
        f.setFixedHeight(80)
        f.setStyleSheet("background-color: #243442; border-radius: 8px;")
        l = QVBoxLayout(f)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(QLabel(title, styleSheet="color: #3498DB; font-weight: bold; font-size: 14px; border:none;"))
        l.addWidget(QLabel(subtitle, styleSheet="color: #BDC3C7; font-size: 11px; border:none;"))
        self.side_layout.addWidget(f)

    def create_header_bar(self, col3):
        f = QFrame()
        f.setFixedHeight(40)
        f.setStyleSheet("background: #34495E; border-radius: 5px;")
        hl = QHBoxLayout(f)
        s = "color: white; font-weight: bold; border: none;"
        hl.addWidget(QLabel("DATA", styleSheet=s))
        hl.addWidget(QLabel("TYTUŁ", styleSheet=s), stretch=1)
        hl.addWidget(QLabel(col3, styleSheet=s))
        return f

    def _show_visit_details(self):
        if not self.current_selected_data:
            QMessageBox.warning(self, "Info", "Najpierw wybierz pozycję z listy.")
            return

        d = self.current_selected_data[0]
        t = self.current_selected_data[1]
        o = self.current_selected_data[2]

        vid = None
        recs = None

        if self.current_selected_frame:
            vid = self.current_selected_frame.property("visit_id")

        labs = []
        if vid and self.connection:
            try:
                cur = self.connection.cursor()
                cur.execute("SELECT recommendations FROM visits WHERE id=%s", (vid,))
                x = cur.fetchone()
                if x: recs = x[0]

                cur.execute("SELECT title, description FROM lab_tests WHERE visit_id=%s", (vid,))
                labs = cur.fetchall()
            except:
                pass

        VisitDetailsWindow(str(d), str(t), str(o), labs, recs, self).exec()

    def _show_logout_window(self):
        if LogoutWindow(self).exec():
            self.close()
            try:
                from LoginWindow import LoginWindow
                self.w = LoginWindow()
                self.w.show()
            except:
                pass