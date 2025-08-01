import tkinter as tk
from tkinter import messagebox
from models import Session
from models.user import User
from utils.auth import check_password
from gui.main_app_window import MainAppWindow
from utils.theme import apply_dark_style
import json
import os

CONFIG_FILE = "login_config.json"

class LoginWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Login")
        self.master.geometry("400x300")
        self.master.resizable(False, False)

        apply_dark_style(self.master)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.remember_var = tk.BooleanVar()
        self.show_password = False

        self.load_saved_username()
        self.build_ui()

    def load_saved_username(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.username_var.set(data.get("remembered_user", ""))
                    self.remember_var.set(True)
            except Exception:
                pass

    def save_username(self):
        if self.remember_var.get():
            with open(CONFIG_FILE, "w") as f:
                json.dump({"remembered_user": self.username_var.get()}, f)
        else:
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)

    def build_ui(self):
        container = tk.Frame(self.master, bg="#1e1e1e")
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(container, text="Username", bg="#1e1e1e", fg="#ffdf00").pack()
        username_entry = tk.Entry(container, textvariable=self.username_var)
        username_entry.pack(pady=5)

        tk.Label(container, text="Password", bg="#1e1e1e", fg="#ffdf00").pack()
        self.password_entry = tk.Entry(container, textvariable=self.password_var, show="*")
        self.password_entry.pack(pady=5)

        tk.Checkbutton(container, text="Show Password", command=self.toggle_password,
                       bg="#1e1e1e", fg="#ffdf00", selectcolor="#1e1e1e").pack()

        tk.Checkbutton(container, text="Remember Me", variable=self.remember_var,
                       bg="#1e1e1e", fg="#ffdf00", selectcolor="#1e1e1e").pack()

        tk.Button(container, text="Login", command=self.login, bg="#ffdf00").pack(pady=10)
        self.master.bind("<Return>", lambda e: self.login())

    def toggle_password(self):
        self.show_password = not self.show_password
        self.password_entry.config(show="" if self.show_password else "*")

    def login(self):
        session = Session()
        user = session.query(User).filter_by(username=self.username_var.get(), is_deleted=False).first()
        if user and check_password(self.password_var.get(), user.password_hash):
            self.save_username()
            self.master.destroy()
            app = MainAppWindow(user)
            app.mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
        session.close()
