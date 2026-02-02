import psycopg2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QPushButton,
                               QListWidget, QListWidgetItem, QHBoxLayout,
                               QTimeEdit, QCheckBox, QMessageBox, QScrollArea)
from PySide6.QtCore import Qt, QSize, QTime
from BaseWindow import BaseWindow, conn_str

# Mapowanie dni tygodnia
DAYS_MAP = {
    0: "Poniedziałek",
    1: "Wtorek",
    2: "Środa",
    3: "Czwartek",
    4: "Piątek",
    5: "Sobota",
    6: "Niedziela"
}


class AdminWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Administrator")
        self.selected_doctor_id = None
        self.day_widgets = {}

        self.init_ui()

    def init_ui(self):
        # --- 1. PASEK BOCZNY ---
        self.setup_sidebar()

        # --- 2. GŁÓWNA TREŚĆ ---
        self.header_lbl = QLabel("ZARZĄDZANIE GRAFIKIEM", self.main_content_frame)
        self.header_lbl.setStyleSheet("color: #2C3E50; font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        self.main_v_layout.addWidget(self.header_lbl)

        self.sub_header = QLabel(
            "1. Wybierz lekarza z listy.\n2. Zaznacz dni pracy (checkbox).\n3. Ustaw godziny i kliknij ZAPISZ.",
            self.main_content_frame)
        self.sub_header.setStyleSheet("color: #7F8C8D; font-size: 13px; margin-bottom: 15px;")
        self.main_v_layout.addWidget(self.sub_header)

        # ScrollArea
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")

        self.schedule_container = QWidget()
        self.schedule_layout = QVBoxLayout(self.schedule_container)
        self.schedule_layout.setSpacing(10)
        self.schedule_layout.setContentsMargins(5, 5, 20, 5)

        self.scroll.setWidget(self.schedule_container)
        self.main_v_layout.addWidget(self.scroll)

        # Generujemy wiersze (0-4 dla Pn-Pt)
        self.create_day_rows()

        # Przycisk Zapisz
        self.save_btn = QPushButton("ZAPISZ GRAFIK")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setFixedHeight(50)
        self.save_btn.setStyleSheet("""
            QPushButton { 
                background-color: #27AE60; 
                color: white; 
                font-weight: bold; 
                font-size: 14px; 
                border-radius: 8px; 
                border: none;
            }
            QPushButton:hover { background-color: #2ECC71; }
            QPushButton:disabled { background-color: #BDC3C7; }
        """)
        self.save_btn.clicked.connect(self.save_schedule)
        self.save_btn.setEnabled(False)
        self.main_v_layout.addWidget(self.save_btn)

        self.refresh_doctors_list()

    def setup_sidebar(self):
        self.setup_info_widget("ADMINISTRATOR", f"ID: {self.user_id}")

        self.side_layout.addWidget(QLabel("LEKARZE:",
                                          styleSheet="color: #BDC3C7; font-weight: bold; margin-top: 20px; margin-bottom: 5px; font-size: 12px;"))

        self.doctors_list = QListWidget()
        self.doctors_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.doctors_list.setStyleSheet("""
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item { color: #ECF0F1; padding: 12px; border-bottom: 1px solid #34495E; margin-bottom: 2px; border-radius: 4px; }
            QListWidget::item:selected { background-color: #3498DB; color: white; font-weight: bold; }
            QListWidget::item:hover:!selected { background-color: #34495E; }
        """)
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
        """Generuje wiersze (karty) dla dni tygodnia."""
        for day_idx in range(0, 5):  # 0=Pon, 4=Pt

            card = QFrame()
            card.setFixedHeight(80)
            card.setStyleSheet("""
                QFrame { background-color: white; border: 1px solid #E0E0E0; border-radius: 8px; }
            """)

            layout = QHBoxLayout(card)
            layout.setContentsMargins(20, 10, 20, 10)
            layout.setSpacing(15)

            # Checkbox
            chk = QCheckBox(DAYS_MAP[day_idx])
            chk.setStyleSheet("""
                QCheckBox { font-weight: bold; font-size: 15px; color: #2C3E50; border: none; }
                QCheckBox::indicator { width: 20px; height: 20px; }
            """)

            # Pola czasu
            t_start = QTimeEdit()
            t_start.setDisplayFormat("HH:mm")
            t_start.setTime(QTime(8, 0))
            t_start.setFixedWidth(110)
            t_start.setFixedHeight(35)

            lbl_to = QLabel("—")
            lbl_to.setStyleSheet("border: none; color: #7F8C8D; font-weight: bold;")

            t_end = QTimeEdit()
            t_end.setDisplayFormat("HH:mm")
            t_end.setTime(QTime(16, 0))
            t_end.setFixedWidth(110)
            t_end.setFixedHeight(35)

            # Domyślnie wyłączone
            t_start.setEnabled(False)
            t_end.setEnabled(False)
            self.apply_time_style(t_start, False)
            self.apply_time_style(t_end, False)

            # Połączenie sygnału
            chk.toggled.connect(lambda checked, s=t_start, e=t_end: self.on_day_toggled(checked, s, e))

            layout.addWidget(chk, stretch=1)
            layout.addWidget(t_start)
            layout.addWidget(lbl_to)
            layout.addWidget(t_end)

            self.schedule_layout.addWidget(card)

            self.day_widgets[day_idx] = {
                "check": chk,
                "start": t_start,
                "end": t_end
            }

    def apply_time_style(self, widget, enabled):
        if enabled:
            widget.setStyleSheet("""
                QTimeEdit { 
                    background-color: #FFFFFF; 
                    border: 2px solid #3498DB; 
                    border-radius: 4px; 
                    color: #2C3E50; 
                    font-weight: bold; 
                    padding-left: 10px; 
                }
            """)
        else:
            widget.setStyleSheet("""
                QTimeEdit { 
                    background-color: #F0F0F0; 
                    border: 1px solid #D0D0D0; 
                    border-radius: 4px; 
                    color: #BDC3C7; 
                    padding-left: 10px; 
                }
            """)

    def on_day_toggled(self, checked, t_start, t_end):
        """Obsługa kliknięcia w checkbox."""
        t_start.setEnabled(checked)
        t_end.setEnabled(checked)
        self.apply_time_style(t_start, checked)
        self.apply_time_style(t_end, checked)

    def refresh_doctors_list(self):
        self.doctors_list.clear()
        if not self.connection: return

        try:
            with self.connection.cursor() as cur:
                # Szukamy wszystkich wariacji roli 'lekarz'
                cur.execute("""
                    SELECT id, login 
                    FROM users 
                    WHERE LOWER(role) IN ('doctor', 'lekarz', 'doktor') 
                    ORDER BY login
                """)
                rows = cur.fetchall()
                for uid, login in rows:
                    item = QListWidgetItem(f"Dr {login}")
                    # uid może być teraz PESELem (string), co jest OK
                    item.setData(Qt.ItemDataRole.UserRole, str(uid))
                    self.doctors_list.addItem(item)
        except Exception as e:
            print(e)

    def load_schedule_for_doctor(self, item):
        self.selected_doctor_id = item.data(Qt.ItemDataRole.UserRole)
        doc_name = item.text()

        self.save_btn.setEnabled(True)
        self.save_btn.setText(f"ZAPISZ GRAFIK ({doc_name})")

        # 1. Reset UI
        for widgets in self.day_widgets.values():
            widgets["check"].setChecked(False)  # To wyzwoli on_day_toggled(False)
            widgets["start"].setTime(QTime(8, 0))
            widgets["end"].setTime(QTime(16, 0))

        if not self.connection: return

        # 2. Pobierz z bazy
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    SELECT day_of_week, start_time, end_time 
                    FROM doctor_schedules 
                    WHERE doctor_id = %s
                """, (self.selected_doctor_id,))

                rows = cur.fetchall()
                for day, start, end in rows:
                    if day in self.day_widgets:
                        w = self.day_widgets[day]
                        w["start"].setTime(QTime(start.hour, start.minute))
                        w["end"].setTime(QTime(end.hour, end.minute))
                        w["check"].setChecked(True)  # To włączy style

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def save_schedule(self):
        if not self.selected_doctor_id: return
        if not self.connection: return

        try:
            cur = self.connection.cursor()

            # Usuwamy stary grafik dla tego lekarza
            cur.execute("DELETE FROM doctor_schedules WHERE doctor_id = %s", (self.selected_doctor_id,))

            count = 0
            for day_idx, widgets in self.day_widgets.items():
                if widgets["check"].isChecked():
                    s_time = widgets["start"].time().toString("HH:mm")
                    e_time = widgets["end"].time().toString("HH:mm")

                    cur.execute("""
                        INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time)
                        VALUES (%s, %s, %s, %s)
                    """, (self.selected_doctor_id, day_idx, s_time, e_time))
                    count += 1

            self.connection.commit()
            QMessageBox.information(self, "Sukces", f"Zapisano dni pracy: {count}")

        except Exception as e:
            self.connection.rollback()
            QMessageBox.critical(self, "Błąd", str(e))