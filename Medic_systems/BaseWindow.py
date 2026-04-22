"""
BaseWindow.py
─────────────────────────────────────────────────────────────────────────────
Zmiany strukturalne względem poprzedniej wersji:
  • Globalny słownik APP_SETTINGS + funkcja _apply_app_stylesheet()
    → zastąpione klasą ThemeManager (singleton).
  • Hardkodowane setStyleSheet() na side_panel / main_content_frame
    → usunięte; style zdefiniowane przez motywy z użyciem setObjectName().
  • self.setStyleSheet(DIALOG_STYLE) w BaseWindow.__init__
    → usunięte; okno aplikacyjne nie nadpisuje już theme'a.
  • Dialogi wewnątrz BaseWindow (LogoutWindow, VisitDetailsWindow)
    → nie ustawiają już DIALOG_STYLE – wygląd pochodzi z aktywnego motywu.
─────────────────────────────────────────────────────────────────────────────
"""

import psycopg2
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QListWidget, QListWidgetItem,
    QDialog, QMessageBox, QScrollArea, QTextEdit,
    QComboBox, QCheckBox, QApplication,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

conn_str = (
    "postgresql://neondb_owner:npg_yKUJZNj2ShD0"
    "@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech"
    "/logowanie_db?sslmode=require&channel_binding=require"
)

# ═══════════════════════════════════════════════════════════════════════════
#  KOMPLETNE ARKUSZE QSS – trzy motywy
#
#  Dlaczego to teraz działa globalnie?
#  side_panel i main_content_frame NIE mają już setStyleSheet() – używają
#  wyłącznie setObjectName(). Reguła QFrame#sidePanel w app.setStyleSheet()
#  wygrywa, bo nie istnieje żaden widget-level override.
#  Dialogi w tym pliku (Logout, VisitDetails) też nie mają setStyleSheet() –
#  motyw ogarnia je przez QDialog { ... }.
# ═══════════════════════════════════════════════════════════════════════════

_QSS_LIGHT = """
QFrame#sidePanel   { background-color: #2C3E50; }
QFrame#mainContent { background-color: #ECF0F1; }

QWidget { background-color: #ECF0F1; color: #2C3E50; }
QDialog { background-color: #F8F9FA; }
QFrame  { background-color: transparent; }
QLabel  { color: #2C3E50; }

QLineEdit, QTextEdit, QComboBox {
    background-color: #FFFFFF; color: #2C3E50;
    border: 1px solid #BDC3C7; border-radius: 4px; padding: 6px;
}
QLineEdit:focus, QTextEdit:focus { border: 2px solid #3498DB; }
QComboBox QAbstractItemView {
    background-color: #FFFFFF; color: #2C3E50;
    selection-background-color: #3498DB; selection-color: white;
}

QPushButton {
    background-color: #F0F0F0; color: #2C3E50;
    border: 1px solid #BDC3C7; border-radius: 4px; padding: 5px 10px;
}
QPushButton:hover    { background-color: #D5D8DC; }
QPushButton:disabled { background-color: #ECF0F1; color: #BDC3C7; }

QListWidget { background: transparent; border: none; outline: none; color: #2C3E50; }
QListWidget::item:selected { background-color: #3498DB; color: white; }

QScrollBar:vertical { background: #ECF0F1; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #BDC3C7; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QMessageBox             { background-color: #FFFFFF; }
QMessageBox QLabel      { color: #2C3E50; font-size: 13px; }
QMessageBox QPushButton {
    background-color: #3498DB; color: white; font-weight: bold;
    border: none; border-radius: 4px; padding: 6px 20px; min-width: 60px;
}
QMessageBox QPushButton:hover { background-color: #2980B9; }

QCheckBox { color: #2C3E50; spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #BDC3C7; border-radius: 3px; background: white;
}
QCheckBox::indicator:checked { background-color: #27AE60; border-color: #27AE60; }

QTimeEdit {
    background: white; color: #2C3E50;
    border: 1px solid #BDC3C7; border-radius: 4px; padding: 4px;
}
QCalendarWidget QWidget { background-color: white; color: #2C3E50; }
"""

_QSS_DARK = """
QFrame#sidePanel   { background-color: #0F1923; }
QFrame#mainContent { background-color: #1A252F; }

QWidget { background-color: #1A252F; color: #D5D8DC; }
QDialog { background-color: #1C2833; }
QFrame  { background-color: transparent; }
QLabel  { color: #D5D8DC; }

QLineEdit, QTextEdit, QComboBox {
    background-color: #2E4053; color: #D5D8DC;
    border: 1px solid #5D6D7E; border-radius: 4px; padding: 6px;
}
QLineEdit:focus, QTextEdit:focus { border: 2px solid #5DADE2; }
QComboBox QAbstractItemView {
    background-color: #2E4053; color: #D5D8DC;
    selection-background-color: #3498DB; selection-color: white;
}

QPushButton {
    background-color: #2E4053; color: #D5D8DC;
    border: 1px solid #5D6D7E; border-radius: 4px; padding: 5px 10px;
}
QPushButton:hover    { background-color: #3D5A6C; }
QPushButton:disabled { background-color: #1C2833; color: #5D6D7E; border-color: #2E4053; }

QListWidget { background: transparent; border: none; outline: none; color: #D5D8DC; }
QListWidget::item:selected { background-color: #2980B9; color: white; }

QScrollBar:vertical { background: #1C2833; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #5D6D7E; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QMessageBox             { background-color: #1C2833; }
QMessageBox QLabel      { color: #D5D8DC; font-size: 13px; }
QMessageBox QPushButton {
    background-color: #2980B9; color: white; font-weight: bold;
    border: none; border-radius: 4px; padding: 6px 20px; min-width: 60px;
}
QMessageBox QPushButton:hover { background-color: #3498DB; }

QCheckBox { color: #D5D8DC; spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #5D6D7E; border-radius: 3px; background: #2E4053;
}
QCheckBox::indicator:checked { background-color: #27AE60; border-color: #27AE60; }

QTimeEdit {
    background: #2E4053; color: #D5D8DC;
    border: 1px solid #5D6D7E; border-radius: 4px; padding: 4px;
}
QCalendarWidget QWidget     { background-color: #1C2833; color: #D5D8DC; }
QCalendarWidget QToolButton { color: #D5D8DC; background-color: #2E4053; }
QCalendarWidget QAbstractItemView:enabled {
    background-color: #1C2833; color: #D5D8DC;
    selection-background-color: #2980B9; selection-color: white;
}
"""

_QSS_CONTRAST = """
QFrame#sidePanel   { background-color: #000000; border-right: 3px solid #FFFF00; }
QFrame#mainContent { background-color: #000000; }

QWidget { background-color: #000000; color: #FFFFFF; }
QDialog { background-color: #000000; }
QFrame  { background-color: transparent; border-color: #FFFFFF; }
QLabel  { color: #FFFFFF; font-weight: bold; }

QLineEdit, QTextEdit, QComboBox {
    background-color: #000000; color: #FFFFFF;
    border: 2px solid #FFFFFF; border-radius: 0px; padding: 6px;
}
QLineEdit:focus, QTextEdit:focus { border: 3px solid #FFFF00; }
QComboBox QAbstractItemView {
    background-color: #000000; color: #FFFFFF;
    selection-background-color: #FFFF00; selection-color: #000000;
}

QPushButton {
    background-color: #000000; color: #FFFF00;
    border: 2px solid #FFFF00; font-weight: bold; padding: 6px 12px;
}
QPushButton:hover    { background-color: #1A1A00; }
QPushButton:disabled { color: #888800; border-color: #888800; }

QListWidget { background: #000000; border: 2px solid #FFFFFF; outline: none; color: #FFFFFF; }
QListWidget::item:selected { background-color: #FFFF00; color: #000000; }

QScrollBar:vertical { background: #000000; width: 14px; border: 1px solid #FFFFFF; }
QScrollBar::handle:vertical { background: #FFFF00; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QMessageBox             { background-color: #000000; }
QMessageBox QLabel      { color: #FFFFFF; font-size: 13px; font-weight: bold; }
QMessageBox QPushButton {
    background-color: #000000; color: #FFFF00;
    border: 2px solid #FFFF00; font-weight: bold; padding: 6px 20px; min-width: 60px;
}
QMessageBox QPushButton:hover { background-color: #1A1A00; }

QCheckBox { color: #FFFFFF; font-weight: bold; spacing: 10px; }
QCheckBox::indicator {
    width: 20px; height: 20px;
    border: 2px solid #FFFFFF; border-radius: 0px; background: #000000;
}
QCheckBox::indicator:checked { background-color: #FFFF00; border-color: #FFFF00; }

QTimeEdit { background: #000000; color: #FFFFFF; border: 2px solid #FFFFFF; padding: 4px; }
QCalendarWidget QWidget     { background-color: #000000; color: #FFFFFF; }
QCalendarWidget QToolButton { color: #FFFF00; background-color: #000000; border: 1px solid #FFFF00; }
QCalendarWidget QAbstractItemView:enabled {
    background-color: #000000; color: #FFFFFF;
    selection-background-color: #FFFF00; selection-color: #000000;
}
"""

_QSS_SPACIOUS = """
QPushButton  { min-height: 48px; padding: 8px 16px; }
QLineEdit, QComboBox { min-height: 42px; padding: 8px; }
QListWidget::item { min-height: 52px; padding: 6px 0px; }
QCheckBox { spacing: 12px; }
QCheckBox::indicator { width: 22px; height: 22px; }
"""

# Zachowany dla zewnętrznych dialogów w DoctorWindow / LaborantWindow
DIALOG_STYLE = """
    QDialog    { background-color: #F8F9FA; }
    QLabel     { color: #2C3E50; font-size: 13px; font-weight: bold; }
    QLineEdit, QTextEdit {
        background-color: white; color: #2C3E50;
        border: 1px solid #BDC3C7; border-radius: 4px; padding: 8px;
    }
    QMessageBox { background-color: white; color: black; }
    QPushButton { background-color: #F0F0F0; color: black; border: 1px solid #888; padding: 5px; }
"""


# ═══════════════════════════════════════════════════════════════════════════
#  THEME MANAGER – singleton
# ═══════════════════════════════════════════════════════════════════════════

class ThemeManager:
    """
    Singleton – jedyne miejsce zarządzania motywem w całej aplikacji.

    Zamiast globalnego APP_SETTINGS i funkcji _apply_app_stylesheet():
      - jeden obiekt, dostępny z każdego modułu przez ThemeManager.get()
      - metoda apply() przyjmuje tylko te parametry które chcemy zmienić
      - apply_current() reaplikuje obecny stan (wywoływane w BaseWindow.__init__)

    Przykład:
        ThemeManager.get().apply(theme="dark", font_size=13)
        ThemeManager.get().apply(spacious=True)
    """

    _THEMES: dict = {
        "light":    _QSS_LIGHT,
        "dark":     _QSS_DARK,
        "contrast": _QSS_CONTRAST,
    }

    _THEME_LABELS: dict = {
        "light":    "Jasny (Standard)",
        "dark":     "Ciemny (Ochrona oczu)",
        "contrast": "Wysoki kontrast",
    }

    _FONT_SIZES: dict = {
        "Mała (9)":         9,
        "Standardowa (10)": 10,
        "Duża (13)":        13,
        "Bardzo duża (16)": 16,
    }

    _instance = None

    def __init__(self) -> None:
        if ThemeManager._instance is not None:
            raise RuntimeError("Użyj ThemeManager.get() zamiast konstruktora.")
        self.theme:     str  = "light"
        self.font_size: int  = 10
        self.spacious:  bool = False

    @classmethod
    def get(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── publiczne API ─────────────────────────────────────────────────────

    def apply(self, *, theme=None, font_size=None, spacious=None) -> None:
        """Zaktualizuj wybrane parametry i natychmiast zastosuj do QApplication."""
        if theme     is not None: self.theme     = theme
        if font_size is not None: self.font_size = font_size
        if spacious  is not None: self.spacious  = spacious
        self._push()

    def apply_current(self) -> None:
        """Reaplikuje obecny stan – wywołuj po otwarciu nowego okna."""
        self._push()

    def _push(self) -> None:
        app = QApplication.instance()
        if not app:
            return
        qss = self._THEMES.get(self.theme, _QSS_LIGHT)
        if self.spacious:
            qss += _QSS_SPACIOUS
        app.setStyleSheet(qss)
        app.setFont(QFont("Segoe UI", self.font_size))

    # ── helpery dla SettingsDialog ────────────────────────────────────────

    @classmethod
    def theme_labels(cls) -> list:
        return list(cls._THEME_LABELS.values())

    @classmethod
    def key_for_label(cls, label: str) -> str:
        return {v: k for k, v in cls._THEME_LABELS.items()}.get(label, "light")

    @classmethod
    def label_for_key(cls, key: str) -> str:
        return cls._THEME_LABELS.get(key, "Jasny (Standard)")

    @classmethod
    def font_size_labels(cls) -> list:
        return list(cls._FONT_SIZES.keys())

    @classmethod
    def size_for_label(cls, label: str) -> int:
        return cls._FONT_SIZES.get(label, 10)

    @classmethod
    def label_for_size(cls, size: int) -> str:
        for lbl, s in cls._FONT_SIZES.items():
            if s == size:
                return lbl
        return "Standardowa (10)"


# ═══════════════════════════════════════════════════════════════════════════
#  OKNO SZCZEGÓŁÓW WIZYTY
# ═══════════════════════════════════════════════════════════════════════════

class VisitDetailsWindow(QDialog):
    def __init__(self, d, t, o, res=None, rec=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Karta Wizyty")
        self.resize(500, 600)
        # Bez setStyleSheet() – motyw obsługuje wygląd przez app.setStyleSheet()

        l = QVBoxLayout(self)
        l.addWidget(QLabel(f"{t}", styleSheet="font-size: 20px; font-weight: bold; margin-bottom: 5px;"))

        info = QFrame()
        info.setStyleSheet("border: 1px solid #BDC3C7; border-radius: 5px;")
        vl = QVBoxLayout(info)
        vl.addWidget(QLabel(f"Data: {d}",          styleSheet="border:none;"))
        vl.addWidget(QLabel(f"Pacjent/Osoba: {o}", styleSheet="border:none;"))
        l.addWidget(info)

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
            vbox = QVBoxLayout(content)
            for title, desc in res:
                row = QFrame()
                row.setStyleSheet("border: 1px solid #BDC3C7; border-radius: 4px;")
                rv = QVBoxLayout(row)
                rv.addWidget(QLabel(title.upper(), styleSheet="color: #2980B9; font-weight:bold; border:none;"))
                rv.addWidget(QLabel(desc if desc else "Oczekiwanie...", styleSheet="border:none;"))
                vbox.addWidget(row)
            scroll.setWidget(content)
            scroll.setWidgetResizable(True)
            l.addWidget(scroll)
        else:
            l.addWidget(QLabel("Brak zleconych badań.", alignment=Qt.AlignmentFlag.AlignCenter))

        btn = QPushButton("ZAMKNIJ")
        btn.clicked.connect(self.accept)
        l.addWidget(btn)


# ═══════════════════════════════════════════════════════════════════════════
#  OKNO WYLOGOWANIA  (naprawione – usunięty błędny kod przed super().__init__)
# ═══════════════════════════════════════════════════════════════════════════

class LogoutWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wylogowanie")
        self.resize(320, 160)
        # Bez setStyleSheet() – motyw obsługuje wygląd

        l = QVBoxLayout(self)
        l.setSpacing(20)
        l.setContentsMargins(30, 30, 30, 30)

        lbl = QLabel("Czy na pewno chcesz się wylogować?")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(lbl)

        h = QHBoxLayout()
        b1 = QPushButton("ANULUJ")
        b1.setCursor(Qt.CursorShape.PointingHandCursor)
        b1.clicked.connect(self.reject)

        b2 = QPushButton("WYLOGUJ")
        b2.setCursor(Qt.CursorShape.PointingHandCursor)
        b2.clicked.connect(self.accept)
        b2.setStyleSheet("""
            QPushButton       { background-color: #E74C3C; color: white;
                                border: none; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #C0392B; }
        """)

        h.addWidget(b1)
        h.addWidget(b2)
        l.addLayout(h)


# ═══════════════════════════════════════════════════════════════════════════
#  OKNO USTAWIEŃ DOSTĘPNOŚCI
# ═══════════════════════════════════════════════════════════════════════════

class SettingsDialog(QDialog):
    """
    Trzy grupy ustawień obsługiwane przez ThemeManager:
      1. Rozmiar czcionki       – podgląd na żywo
      2. Motyw kolorystyczny    – podgląd na żywo (cała aplikacja zmienia wygląd
                                  od razu, zanim użytkownik zamknie okno)
      3. Tryb przestronny ♿     – większe przyciski i wiersze list

    Anulowanie dialogu (X lub Esc) cofa zmiany do stanu sprzed otwarcia.
    """

    _HINTS: dict = {
        "Jasny (Standard)":      "Domyślny wygląd – zalecany przy dobrym oświetleniu.",
        "Ciemny (Ochrona oczu)": "Ciemne tło redukuje zmęczenie oczu przy dłuższej pracy.",
        "Wysoki kontrast":       "Maksymalny kontrast (czarno-żółty) – dla osób słabowidzących.",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙  Ustawienia dostępności")
        self.setFixedWidth(420)

        tm = ThemeManager.get()
        # Zapamiętaj stan na wypadek anulowania
        self._orig_theme     = tm.theme
        self._orig_font_size = tm.font_size
        self._orig_spacious  = tm.spacious

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(25, 25, 25, 25)

        # nagłówek
        hdr = QLabel("Ustawienia dostępności")
        hdr.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(hdr)
        sub = QLabel("Zmiany widoczne są natychmiast w całej aplikacji.")
        sub.setStyleSheet("font-size: 11px; font-weight: normal;")
        layout.addWidget(sub)

        self._sep(layout)

        # ── 1. Rozmiar czcionki ────────────────────────────────────────────
        layout.addWidget(QLabel("1.  Rozmiar czcionki", styleSheet="color: #3498DB; font-size: 13px;"))
        self.font_combo = QComboBox()
        self.font_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.font_combo.addItems(ThemeManager.font_size_labels())
        self.font_combo.setCurrentText(ThemeManager.label_for_size(tm.font_size))
        self.font_combo.currentIndexChanged.connect(self._on_font_changed)
        layout.addWidget(self.font_combo)

        self._sep(layout)

        # ── 2. Motyw ───────────────────────────────────────────────────────
        layout.addWidget(QLabel("2.  Motyw kolorystyczny", styleSheet="color: #3498DB; font-size: 13px;"))
        self.theme_combo = QComboBox()
        self.theme_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_combo.addItems(ThemeManager.theme_labels())
        self.theme_combo.setCurrentText(ThemeManager.label_for_key(tm.theme))
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        layout.addWidget(self.theme_combo)

        self.hint_lbl = QLabel(self._HINTS.get(self.theme_combo.currentText(), ""))
        self.hint_lbl.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.hint_lbl.setWordWrap(True)
        self.theme_combo.currentTextChanged.connect(
            lambda t: self.hint_lbl.setText(self._HINTS.get(t, ""))
        )
        layout.addWidget(self.hint_lbl)

        self._sep(layout)

        # ── 3. Tryb przestronny ────────────────────────────────────────────
        layout.addWidget(QLabel("3.  Tryb przestronny  ♿", styleSheet="color: #3498DB; font-size: 13px;"))
        self.spacious_chk = QCheckBox("Włącz powiększone przyciski i wiersze list")
        self.spacious_chk.setChecked(tm.spacious)
        self.spacious_chk.toggled.connect(lambda v: ThemeManager.get().apply(spacious=v))
        layout.addWidget(self.spacious_chk)

        hint3 = QLabel(
            "Zwiększa min. wysokość przycisków (≥48 px) i wierszy list (≥52 px).\n"
            "Pomocne przy ekranie dotykowym lub ograniczonej motoryce."
        )
        hint3.setStyleSheet("font-size: 11px; font-weight: normal;")
        hint3.setWordWrap(True)
        layout.addWidget(hint3)

        self._sep(layout)

        # ── przyciski akcji ────────────────────────────────────────────────
        row = QHBoxLayout()
        btn_reset = QPushButton("Przywróć domyślne")
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.clicked.connect(self._reset)

        btn_ok = QPushButton("✔  Zamknij")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setFixedHeight(42)
        btn_ok.setStyleSheet("""
            QPushButton       { background-color: #27AE60; color: white; font-weight: bold;
                                border-radius: 4px; border: none; padding: 8px 20px; }
            QPushButton:hover { background-color: #2ECC71; }
        """)
        btn_ok.clicked.connect(self.accept)

        row.addWidget(btn_reset)
        row.addStretch()
        row.addWidget(btn_ok)
        layout.addLayout(row)

    # ── podgląd na żywo ───────────────────────────────────────────────────

    def _on_font_changed(self) -> None:
        size = ThemeManager.size_for_label(self.font_combo.currentText())
        ThemeManager.get().apply(font_size=size)

    def _on_theme_changed(self) -> None:
        key = ThemeManager.key_for_label(self.theme_combo.currentText())
        ThemeManager.get().apply(theme=key)

    def _reset(self) -> None:
        ThemeManager.get().apply(theme="light", font_size=10, spacious=False)
        self.font_combo.setCurrentText(ThemeManager.label_for_size(10))
        self.theme_combo.setCurrentText(ThemeManager.label_for_key("light"))
        self.spacious_chk.setChecked(False)

    def reject(self) -> None:
        """Zamknięcie przez X lub Esc → cofnij zmiany."""
        ThemeManager.get().apply(
            theme=self._orig_theme,
            font_size=self._orig_font_size,
            spacious=self._orig_spacious,
        )
        super().reject()

    @staticmethod
    def _sep(layout) -> None:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("max-height: 1px; background-color: #BDC3C7;")
        layout.addWidget(line)


# ═══════════════════════════════════════════════════════════════════════════
#  BAZOWE OKNO APLIKACJI
# ═══════════════════════════════════════════════════════════════════════════

class BaseWindow(QWidget):
    def __init__(self, user_id, role_title):
        super().__init__()
        self.user_id    = user_id
        self.role_title = role_title
        self.setWindowTitle(f"MedEX - {role_title}")
        self.resize(1200, 800)
        # Brak setStyleSheet() – motyw zarządza całą aplikacją

        self.connection = self.connect_db()
        self.current_selected_frame = None
        self.current_selected_data  = None

        self.main_h_layout = QHBoxLayout(self)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)

        # ── sidebar ───────────────────────────────────────────────────────
        self.side_panel = QFrame()
        self.side_panel.setObjectName("sidePanel")
        # KLUCZOWE: brak setStyleSheet() → QFrame#sidePanel w motywie działa
        self.side_panel.setFixedWidth(280)
        self.side_layout = QVBoxLayout(self.side_panel)
        self.side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.side_layout.setContentsMargins(20, 40, 20, 20)
        self.main_h_layout.addWidget(self.side_panel)

        # ── treść główna ──────────────────────────────────────────────────
        self.main_content_frame = QFrame()
        self.main_content_frame.setObjectName("mainContent")
        # KLUCZOWE: brak setStyleSheet() → QFrame#mainContent w motywie działa
        self.main_v_layout = QVBoxLayout(self.main_content_frame)
        self.main_v_layout.setContentsMargins(30, 30, 30, 30)
        self.main_h_layout.addWidget(self.main_content_frame)

        # Zastosuj aktywny motyw do nowego okna
        ThemeManager.get().apply_current()

    # ── baza danych ───────────────────────────────────────────────────────

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
        except Exception:
            return None

    # ── sidebar – helpery ─────────────────────────────────────────────────

    def add_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            "background: #34495E; color: white; border-radius: 6px; "
            "font-weight: bold; text-align: left; padding-left: 20px; border: none;"
        )
        self.side_layout.addWidget(btn)
        return btn

    def add_settings_button(self) -> QPushButton:
        """
        Dodaje przycisk ⚙ USTAWIENIA do sidebara.
        Wywołuj w setup_sidebar() każdego okna, bezpośrednio PRZED przyciskiem WYLOGUJ.
        """
        btn = QPushButton("⚙  USTAWIENIA")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton       { background-color: #1A252F; color: #BDC3C7;
                                border-radius: 6px; font-weight: bold; font-size: 12px;
                                text-align: left; padding-left: 20px; border: none; }
            QPushButton:hover { background-color: #273746; color: #ECF0F1; }
        """)
        btn.clicked.connect(self._show_settings_window)
        self.side_layout.addWidget(btn)
        return btn

    def setup_info_widget(self, title: str, subtitle: str) -> None:
        f = QFrame()
        f.setFixedHeight(80)
        f.setStyleSheet("background-color: #243442; border-radius: 8px;")
        l = QVBoxLayout(f)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(QLabel(title,    styleSheet="color: #3498DB; font-weight: bold; font-size: 14px; border:none;"))
        l.addWidget(QLabel(subtitle, styleSheet="color: #BDC3C7; font-size: 11px; border:none;"))
        self.side_layout.addWidget(f)

    def create_header_bar(self, col3: str) -> QFrame:
        f = QFrame()
        f.setFixedHeight(40)
        f.setStyleSheet("background: #34495E; border-radius: 5px;")
        hl = QHBoxLayout(f)
        s = "color: white; font-weight: bold; border: none;"
        hl.addWidget(QLabel("DATA",  styleSheet=s))
        hl.addWidget(QLabel("TYTUŁ", styleSheet=s), stretch=1)
        hl.addWidget(QLabel(col3,    styleSheet=s))
        return f

    # ── akcje wspólne ─────────────────────────────────────────────────────

    def _show_visit_details(self) -> None:
        if not self.current_selected_data:
            QMessageBox.warning(self, "Info", "Najpierw wybierz pozycję z listy.")
            return

        d, t, o = (self.current_selected_data[i] for i in range(3))
        vid  = self.current_selected_frame.property("visit_id") if self.current_selected_frame else None
        recs = None
        labs = []

        if vid and self.connection:
            try:
                cur = self.connection.cursor()
                cur.execute("SELECT recommendations FROM visits WHERE id=%s", (vid,))
                row = cur.fetchone()
                if row:
                    recs = row[0]
                cur.execute("SELECT title, description FROM lab_tests WHERE visit_id=%s", (vid,))
                labs = cur.fetchall()
            except Exception:
                pass

        VisitDetailsWindow(str(d), str(t), str(o), labs, recs, self).exec()

    def _show_settings_window(self) -> None:
        SettingsDialog(self).exec()

    def _show_logout_window(self) -> None:
        if LogoutWindow(self).exec():
            self.close()
            try:
                from LoginWindow import LoginWindow
                self.w = LoginWindow()
                self.w.show()
            except Exception:
                pass