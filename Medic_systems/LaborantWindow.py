import psycopg2
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFrame, QTextEdit,
                               QListWidgetItem, QHBoxLayout)
from PySide6.QtCore import Qt, QSize
from BaseWindow import BaseWindow, conn_str


# --- OKNO WPISYWANIA WYNIKÓW ---
class FillLabResultWindow(QDialog):
    def __init__(self, test_id, test_title, parent=None):
        super().__init__(parent)
        self.test_id = test_id
        self.setWindowTitle(f"Wynik badania: {test_title}")
        self.resize(500, 400)

        # Stylizacja okna
        self.setStyleSheet("background-color: #F0F2F5;")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel(f"<h2>Uzupełnij wynik</h2>"))

        info_lbl = QLabel(f"<b>Badanie:</b> {test_title}")
        info_lbl.setStyleSheet("font-size: 14px; color: #333;")
        layout.addWidget(info_lbl)

        layout.addWidget(QLabel("Opis wyników / Parametry:"))

        self.result_edit = QTextEdit()
        self.result_edit.setPlaceholderText("Wpisz tutaj szczegółowe wyniki badania...")
        self.result_edit.setStyleSheet("""
            QTextEdit {
                background-color: white; 
                border: 1px solid #CCC; 
                border-radius: 5px; 
                padding: 10px;
                font-size: 13px;
                color: black;
            }
        """)
        layout.addWidget(self.result_edit)

        btn = QPushButton("ZAPISZ WYNIK")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(50)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2F9ADF; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px; 
                font-size: 14px;
            }
            QPushButton:hover { background-color: #1F8ACF; }
        """)
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        description = self.result_edit.toPlainText().strip()

        if not description:
            QMessageBox.warning(self, "Błąd", "Pole wyników nie może być puste.")
            return

        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()

            # Aktualizujemy rekord w tabeli lab_tests
            cursor.execute("UPDATE lab_tests SET description = %s WHERE id = %s",
                           (description, self.test_id))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sukces", "Wynik badania został zapisany.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd Bazy", str(e))


# --- GŁÓWNE OKNO LABORANTA ---
class LaborantWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Laborant")
        self.code_input = None
        # Ta metoda z BaseWindow wywoła setup_sidebar_widgets
        self.init_ui()

    # Ta metoda jest WYMAGANA przez BaseWindow
    def setup_sidebar_widgets(self):
        # Info o laborancie (metoda z BaseWindow)
        # Upewnij się, że masz najnowsze BaseWindow, jeśli tu wystąpi błąd
        try:
            self.setup_info_widget("PANEL LABORANTA", f"ID: {self.user_id}")
        except AttributeError:
            # Fallback jeśli masz starszą wersję BaseWindow
            pass

        # --- SEKCJA WYSZUKIWANIA KODEM ---
        search_frame = QFrame(self)
        search_frame.setFixedHeight(150)
        search_frame.setStyleSheet("""
            QFrame { background-color: white; border-radius: 10px; border: 2px solid #CCC; }
        """)

        layout = QVBoxLayout(search_frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        lbl = QLabel("DOSTĘP DO PACJENTA", search_frame)
        lbl.setStyleSheet("color: #333; font-weight: bold; font-size: 11px; border: none;")

        self.code_input = QLineEdit(search_frame)
        self.code_input.setPlaceholderText("Kod (6 cyfr)")
        self.code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_input.setStyleSheet("border: 1px solid #AAA; border-radius: 5px; padding: 5px; color: black;")

        search_btn = QPushButton("SZUKAJ BADAŃ", search_frame)
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.setStyleSheet("""
            QPushButton { background-color: #2F9ADF; color: white; font-weight: bold; border-radius: 5px; padding: 5px; border: none;}
            QPushButton:hover { background-color: #1F8ACF; }
        """)
        search_btn.clicked.connect(self.load_patient_by_code)

        layout.addWidget(lbl)
        layout.addWidget(self.code_input)
        layout.addWidget(search_btn)

        self.side_layout.addWidget(search_frame)

    # Ta metoda jest WYMAGANA przez BaseWindow
    def setup_extra_buttons(self):
        # Przycisk do wpisywania wyników
        self.add_button("WPISZ WYNIKI").clicked.connect(self.open_fill_result)

    def get_sql_query(self):
        # Domyślnie pusta lista (wymagamy kodu)
        return ""

    def load_patient_by_code(self):
        code = self.code_input.text().strip()
        if len(code) != 6:
            QMessageBox.warning(self, "Błąd", "Kod musi mieć 6 cyfr.")
            return

        if not self.connection: return

        try:
            with self.connection.cursor() as cursor:
                # 1. Weryfikacja kodu i pobranie PESEL
                cursor.execute("SELECT pesel FROM patient_codes WHERE code = %s AND expiration_time > %s",
                               (code, datetime.now()))
                res = cursor.fetchone()
                if not res:
                    QMessageBox.warning(self, "Błąd", "Kod nieprawidłowy lub wygasł.")
                    return

                pesel = res[0]

                # 2. Pobranie BADAŃ (lab_tests) dla tego pacjenta
                # Łączymy lab_tests z visits, aby sprawdzić PESEL
                query = """
                    SELECT t.id, v.visit_date, t.title, v.pesel 
                    FROM lab_tests t
                    JOIN visits v ON t.visit_id = v.id
                    WHERE v.pesel = %s
                    ORDER BY v.visit_date DESC
                """
                cursor.execute(query, (pesel,))
                rows = cursor.fetchall()

                self.lista_wizyt.clear()
                self.add_list_items(rows)

                if not rows:
                    QMessageBox.information(self, "Info", "Ten pacjent nie ma zleconych żadnych badań.")
                else:
                    QMessageBox.information(self, "Sukces", f"Znaleziono {len(rows)} badań dla pacjenta: {pesel}")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def open_fill_result(self):
        if not self.current_selected_frame:
            QMessageBox.warning(self, "Uwaga", "Wybierz badanie z listy, aby wpisać wynik.")
            return

        # Pobieramy ukryte ID badania
        test_id = self.current_selected_frame.property("test_id")
        test_title = self.current_selected_frame.property("test_title")

        if not test_id:
            QMessageBox.critical(self, "Błąd", "Nie można zidentyfikować badania.")
            return

        # Otwieramy okno edycji i po zamknięciu (jeśli sukces) nic nie robimy lub odświeżamy
        if FillLabResultWindow(test_id, test_title, self).exec():
            # Można odświeżyć listę, ale wymagałoby to ponownego wpisania kodu,
            # więc na razie zostawiamy widok jak jest
            pass

    # --- NADPISANIE FUNKCJI LISTY (ABY OBSŁUŻYĆ ID BADANIA) ---
    def add_list_items(self, data_rows):
        styles = ["background-color: #FFFFFF;", "background-color: #F0F0F0;"]

        # data_rows: (test_id, data_wizyty, tytul_badania, pesel)
        for i, (tid, data, tytul, pesel) in enumerate(data_rows):
            data_str = data.strftime("%Y-%m-%d") if data else ""
            pesel_str = str(pesel)

            list_item = QListWidgetItem()
            # Dane dla okna szczegółów (kompatybilność z BaseWindow)
            list_item.setData(Qt.ItemDataRole.UserRole, (data_str, f"BADANIE: {tytul}", pesel_str))

            frame = QFrame()
            frame.setFixedHeight(60)
            # Styl z czarnym tekstem
            frame.setStyleSheet(styles[i % 2] + "border-bottom: 1px solid #DDD; color: black;")

            # --- ZAPAMIĘTUJEMY ID BADANIA ---
            frame.setProperty("test_id", tid)
            frame.setProperty("test_title", tytul)

            hl = QHBoxLayout(frame)
            hl.setContentsMargins(10, 0, 10, 0)

            # Wyświetlamy: Data | Nazwa Badania | PESEL
            labels = [data_str, tytul.upper(), pesel_str]
            for j, txt in enumerate(labels):
                lbl = QLabel(txt)
                lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

                # Stylizacja środkowej kolumny (tytuł badania)
                if j == 1:
                    lbl.setStyleSheet("border: none; color: #2F9ADF; font-weight: bold; font-size: 13px;")
                else:
                    lbl.setStyleSheet("border: none; color: black; font-size: 12px;")

                hl.addWidget(lbl, stretch=1 if j == 1 else 0)
                if j < 2: hl.addSpacing(20)

            self.lista_wizyt.addItem(list_item)
            list_item.setSizeHint(QSize(0, 60))
            self.lista_wizyt.setItemWidget(list_item, frame)