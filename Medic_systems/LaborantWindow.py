from BaseWindow import BaseWindow

class LaborantWindow(BaseWindow):
    def __init__(self, user_id):
        super().__init__(user_id, "Laborant")
        self.init_ui()

    def setup_sidebar_widgets(self):
        self.setup_info_widget("PANEL LABORANTA", f"ID: {self.user_id}")

    def get_sql_query(self):
        # Laborant widzi wizyty/zlecenia przypisane do niego
        return "SELECT visit_date, title, pesel FROM visits WHERE laborant_id = %s"