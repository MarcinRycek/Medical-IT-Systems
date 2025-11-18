import psycopg2
from PySide6.QtWidgets import QApplication
import sys
from LoginWindow import LoginWindow
from MainWindow import MainWindow

conn_str = "postgresql://neondb_owner:npg_yKUJZNj2ShD0@ep-wandering-silence-agr7tkb5-pooler.c-2.eu-central-1.aws.neon.tech/logowanie_db?sslmode=require&channel_binding=require"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    conn = psycopg2.connect(conn_str)
    window = MainWindow(conn)
    window.show()

    app.exec()