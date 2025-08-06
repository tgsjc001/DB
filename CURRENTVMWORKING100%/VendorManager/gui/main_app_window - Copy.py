
import tkinter as tk
from tkinter import ttk
from gui.vendor_manager import VendorManagerWindow
from gui.user_management import UserManagementPanel
from gui.audit_viewer import AuditViewerTab
from gui.customization import CustomizationWindow
from gui.export_report import ExportReportWindow
from models import Session
from utils.theme import apply_user_theme
from utils.session_logger import log_session_logout

class MainAppWindow(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.title("Vendor Management System")
        self.geometry("1300x800")
        self.current_user = user
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        apply_user_theme(self, user)

        self.tab_buttons = {}
        self.tab_content = tk.Frame(self, bg="#1e1e1e")
        self.tab_content.pack(side="right", fill="both", expand=True)

        self.build_sidebar()
          # Increase global font size
        self.bind_all("<Control-e>", lambda event: self.open_export_window())

        self.show_tab("vendors")

    def build_sidebar(self):
        sidebar = tk.Frame(self, bg="#2b2b2b", width=200)
        sidebar.pack(side="left", fill="y")

        logo = tk.Label(
            sidebar,
            text="🦁",
            font=("Roboto", 26),
            fg=self.current_user.accent_color,
            bg="#2b2b2b"
        )
        logo.pack(pady=20)

        buttons = [
            ("Vendors", lambda: self.show_tab("vendors")),
            ("Settings", lambda: self.show_tab("customization")),
        ]

        if self.current_user.role == "admin":
            buttons.insert(1, ("User Management", lambda: self.show_tab("users")))

        for label, command in buttons:
            btn = tk.Button(
                sidebar,
                text=label,
                font=("Segoe UI", 12),
                fg="white",
                bg=self.current_user.accent_color,
                relief="flat",
                command=command
            )
            btn.pack(fill="x", pady=6, padx=10)
            self.tab_buttons[label] = btn

        logout_btn = tk.Button(
            sidebar,
            text="Logout",
            font=("Segoe UI", 12),
            fg="white",
            bg="#b00020",
            relief="flat",
            command=self.logout
        )
        logout_btn.pack(side="bottom", fill="x", padx=10, pady=10)

    def show_tab(self, tab_name):
        for widget in self.tab_content.winfo_children():
            widget.destroy()

        if tab_name == "vendors":
            vendor_frame = VendorManagerWindow(self.tab_content, user=self.current_user)
            vendor_frame.pack(fill="both", expand=True)
        elif tab_name == "users":
            UserManagementPanel(self.tab_content, self.current_user).pack(fill="both", expand=True)
        elif tab_name == "customization":
            CustomizationWindow(self.tab_content, self.current_user).pack(fill="both", expand=True)

    def logout(self):
        from gui.login_window import LoginWindow
        log_session_logout(self.current_user.id)
        self.destroy()
        root = tk.Tk()
        LoginWindow(root)
        root.mainloop()

    def on_close(self):
        self.destroy()

    def open_export_window(self):
        ExportReportWindow(self, self.current_user)
