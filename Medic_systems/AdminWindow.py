import psycopg2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QPushButton,
                               QListWidget, QListWidgetItem, QHBoxLayout,
                               QTimeEdit, QCheckBox, QMessageBox, QScrollArea)
from PySide6.QtCore import Qt, QSize, QTime
from BaseWindow import BaseWindow, conn_str

DAYS_MAP = {0: "Poniedziałek", 1: "Wtorek", 2: "Środa", 3: "Czwartek", 4: "Piątek", 5: "Sobota", 6: "Niedziela"}


class ClickableCard(QFrame):

    def __init__(self, checkbox, parent=None):
        super().__init__(parent)
        self.checkbox = checkbox
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(80)
        self.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 6px;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)



class AdminWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Administrator")
        self.selected_doctor_id = None
        self.day_widgets = {}
        self.init_ui()

    def init_ui(self):
        self.setup_sidebar()

        main_content_layout = QHBoxLayout()

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 10, 0)

        left_layout.addWidget(
            QLabel("ZARZĄDZANIE GRAFIKIEM", styleSheet="color: #2C3E50; font-size: 18px; font-weight: bold;"))
        self.sub_header = QLabel("Wybierz lekarza z paska bocznego.", styleSheet="color: #7F8C8D; margin-bottom: 10px;")
        left_layout.addWidget(self.sub_header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")

        self.schedule_container = QWidget()
        self.schedule_layout = QVBoxLayout(self.schedule_container)
        self.schedule_layout.setSpacing(10)
        self.scroll.setWidget(self.schedule_container)
        left_layout.addWidget(self.scroll)

        self.create_day_rows()

        self.save_btn = QPushButton("ZAPISZ GRAFIK")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setFixedHeight(45)
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #27AE60; color: white; font-weight: bold; border-radius: 5px; border:none; } 
            QPushButton:hover { background-color: #2ECC71; } 
            QPushButton:disabled { background-color: #BDC3C7; }
        """)
        self.save_btn.clicked.connect(self.save_schedule)
        self.save_btn.setEnabled(False)
        left_layout.addWidget(self.save_btn)

        main_content_layout.addWidget(left_container, stretch=3)

        right_container = QFrame()
        right_container.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #BDC3C7;")
        right_layout = QVBoxLayout(right_container)

        right_layout.addWidget(QLabel("OCZEKUJĄCE REJESTRACJE",
                                      styleSheet="color: #E67E22; font-weight: bold; font-size: 14px; border:none;"))

        self.pending_list = QListWidget()
        self.pending_list.setStyleSheet("border: none;")
        right_layout.addWidget(self.pending_list)

        btn_refresh = QPushButton("Odśwież")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh_pending_users)
        btn_refresh.setStyleSheet("""
            QPushButton { background: #ECF0F1; border: none; padding: 5px; color: #555; border-radius: 4px;}
            QPushButton:hover { background: #D0D3D4; }
        """)
        right_layout.addWidget(btn_refresh)

        main_content_layout.addWidget(right_container, stretch=2)

        self.main_v_layout.addLayout(main_content_layout)

        self.refresh_doctors_list()
        self.refresh_pending_users()

    def setup_sidebar(self):
        self.setup_info_widget("ADMIN", f"ID: {self.user_id}")
        self.side_layout.addWidget(QLabel("LEKARZE (DO GRAFIKU):",
                                          styleSheet="color: #BDC3C7; font-weight: bold; margin-top: 20px; font-size: 11px;"))
        self.doctors_list = QListWidget()
        self.doctors_list.setStyleSheet(
            "QListWidget { background: transparent; border: none; outline: none; } QListWidget::item { color: #ECF0F1; padding: 10px; border-bottom: 1px solid #34495E; } QListWidget::item:selected { background-color: #3498DB; }")
        self.doctors_list.itemClicked.connect(self.load_schedule_for_doctor)
        self.side_layout.addWidget(self.doctors_list)
        self.side_layout.addStretch()

        wyloguj = self.add_button("WYLOGUJ")
        wyloguj.setStyleSheet("""
            QPushButton { background-color: #C0392B; color: white; border-radius: 6px; padding: 15px; font-weight: bold; font-size: 13px; text-align: left; padding-left: 20px; border: none;} 
            QPushButton:hover { background-color: #E74C3C; }
        """)
        wyloguj.clicked.connect(self._show_logout_window)

    def create_day_rows(self):
        for day_idx in range(5):
            chk = QCheckBox(DAYS_MAP[day_idx])
            chk.setStyleSheet("font-weight: bold; color: #2C3E50; border: none; background: transparent;")

            card = ClickableCard(chk)

            hl = QHBoxLayout(card)
            hl.setContentsMargins(15, 10, 15, 10)

            t_start = QTimeEdit();
            t_start.setTime(QTime(8, 0));
            t_start.setDisplayFormat("HH:mm")
            t_end = QTimeEdit();
            t_end.setTime(QTime(16, 0));
            t_end.setDisplayFormat("HH:mm")

            t_start.setEnabled(False);
            t_end.setEnabled(False)
            self.apply_time_style(t_start, False);
            self.apply_time_style(t_end, False)

            chk.toggled.connect(lambda c, s=t_start, e=t_end: self.on_day_toggled(c, s, e))

            hl.addWidget(chk, stretch=1)
            hl.addWidget(t_start)
            hl.addWidget(QLabel("-", styleSheet="border:none; background: transparent;"))
            hl.addWidget(t_end)

            self.schedule_layout.addWidget(card)
            self.day_widgets[day_idx] = {"check": chk, "start": t_start, "end": t_end}

    def apply_time_style(self, w, e):
        bg = "#FFFFFF" if e else "#F0F0F0"
        col = "#2C3E50" if e else "#BDC3C7"
        w.setStyleSheet(f"background-color: {bg}; color: {col}; border: 1px solid #BDC3C7; border-radius: 4px;")

    def on_day_toggled(self, c, s, e):
        s.setEnabled(c);
        e.setEnabled(c)
        self.apply_time_style(s, c);
        self.apply_time_style(e, c)

    def refresh_doctors_list(self):
        self.doctors_list.clear()
        if not self.connection: return
        try:
            with self.connection.cursor() as c:
                c.execute("SELECT id, login FROM users WHERE LOWER(role) IN ('doctor','lekarz') ORDER BY login")
                for uid, login in c.fetchall():
                    it = QListWidgetItem(f"Dr {login}")
                    it.setData(Qt.ItemDataRole.UserRole, str(uid))
                    self.doctors_list.addItem(it)
        except:
            pass

    def load_schedule_for_doctor(self, item):
        self.selected_doctor_id = item.data(Qt.ItemDataRole.UserRole)
        self.sub_header.setText(f"Edycja: {item.text()}")
        self.save_btn.setEnabled(True)
        for w in self.day_widgets.values():
            w["check"].setChecked(False)
            w["start"].setTime(QTime(8, 0));
            w["end"].setTime(QTime(16, 0))

        try:
            with self.connection.cursor() as c:
                c.execute("SELECT day_of_week, start_time, end_time FROM doctor_schedules WHERE doctor_id=%s",
                          (self.selected_doctor_id,))
                for d, s, e in c.fetchall():
                    if d in self.day_widgets:
                        self.day_widgets[d]["start"].setTime(QTime(s.hour, s.minute))
                        self.day_widgets[d]["end"].setTime(QTime(e.hour, e.minute))
                        self.day_widgets[d]["check"].setChecked(True)
        except:
            pass

    def save_schedule(self):
        if not self.selected_doctor_id: return
        try:
            with self.connection.cursor() as c:
                c.execute("DELETE FROM doctor_schedules WHERE doctor_id=%s", (self.selected_doctor_id,))
                count = 0
                for d, w in self.day_widgets.items():
                    if w["check"].isChecked():
                        c.execute(
                            "INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES (%s,%s,%s,%s)",
                            (self.selected_doctor_id, d, w["start"].time().toString("HH:mm"),
                             w["end"].time().toString("HH:mm")))
                        count += 1
            self.connection.commit()
            QMessageBox.information(self, "OK", f"Zapisano dni pracy: {count}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def refresh_pending_users(self):
        self.pending_list.clear()
        if not self.connection: return
        try:
            with self.connection.cursor() as c:
                c.execute("SELECT id, login, role FROM users WHERE is_active = FALSE")
                rows = c.fetchall()
                if not rows:
                    self.pending_list.addItem(QListWidgetItem("Brak oczekujących."))
                    return

                for uid, login, role in rows:
                    item = QListWidgetItem()
                    widget = QFrame()
                    hl = QHBoxLayout(widget)
                    hl.setContentsMargins(5, 5, 5, 5)

                    lbl = QLabel(f"{role.upper()}: {login}\nID: {uid}")
                    lbl.setStyleSheet("font-size: 11px; color: #333; border: none;")

                    btn_ok = QPushButton("✔")
                    btn_ok.setFixedSize(30, 30)
                    btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_ok.setStyleSheet("""
                        QPushButton { background: #27AE60; color: white; border: none; border-radius: 4px; }
                        QPushButton:hover { background: #2ECC71; }
                    """)
                    btn_ok.clicked.connect(lambda _, u=uid: self.approve_user(u))

                    btn_no = QPushButton("✖")
                    btn_no.setFixedSize(30, 30)
                    btn_no.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_no.setStyleSheet("""
                        QPushButton { background: #E74C3C; color: white; border: none; border-radius: 4px; }
                        QPushButton:hover { background: #C0392B; }
                    """)
                    btn_no.clicked.connect(lambda _, u=uid: self.reject_user(u))

                    hl.addWidget(lbl, stretch=1)
                    hl.addWidget(btn_ok)
                    hl.addWidget(btn_no)

                    item.setSizeHint(widget.sizeHint())
                    self.pending_list.addItem(item)
                    self.pending_list.setItemWidget(item, widget)
        except Exception as e:
            print(e)

    def approve_user(self, uid):
        try:
            with self.connection.cursor() as c:
                c.execute("UPDATE users SET is_active = TRUE WHERE id = %s", (str(uid),))
            self.connection.commit()
            self.refresh_pending_users()
            self.refresh_doctors_list()
            QMessageBox.information(self, "OK", "Użytkownik zatwierdzony.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def reject_user(self, uid):
        if QMessageBox.question(self, "Potwierdź", "Usunąć to zgłoszenie?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                with self.connection.cursor() as c:
                    c.execute("DELETE FROM users WHERE id = %s", (str(uid),))
                self.connection.commit()
                self.refresh_pending_users()
            except Exception as e:
                QMessageBox.critical(self, "Błąd", str(e))