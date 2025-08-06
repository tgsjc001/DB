# gui/user_management.py

import tkinter as tk
from tkinter import ttk, messagebox
from models import Session
from models.user import User
from utils.theme import apply_user_theme
from sqlalchemy.exc import IntegrityError

class UserManagementPanel(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg="#1e1e1e")
        self.user = user
        apply_user_theme(self, user)
        self.selected_user_id = None

        self.build_ui()
        self.load_users()

    def build_ui(self):
        form_frame = tk.Frame(self, bg="#1e1e1e")
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Username:", bg="#1e1e1e", fg="white").grid(row=0, column=0, sticky="e")
        self.username_entry = tk.Entry(form_frame)
        self.username_entry.grid(row=0, column=1, padx=5)

        tk.Label(form_frame, text="Password:", bg="#1e1e1e", fg="white").grid(row=1, column=0, sticky="e")
        self.password_entry = tk.Entry(form_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5)

        tk.Label(form_frame, text="Role:", bg="#1e1e1e", fg="white").grid(row=2, column=0, sticky="e")
        self.role_combo = ttk.Combobox(form_frame, values=["admin", "user"])
        self.role_combo.grid(row=2, column=1, padx=5)

        button_frame = tk.Frame(self, bg="#1e1e1e")
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Add User", command=self.add_user, bg=self.user.accent_color).pack(side="left", padx=5)
        tk.Button(button_frame, text="Update", command=self.update_user, bg=self.user.accent_color).pack(side="left", padx=5)
        tk.Button(button_frame, text="Delete", command=self.delete_user, bg=self.user.accent_color).pack(side="left", padx=5)

        self.tree = ttk.Treeview(self, columns=("ID", "Username", "Role"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Username", text="Username")
        self.tree.heading("Role", text="Role")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Username", width=150)
        self.tree.column("Role", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def load_users(self):
        self.tree.delete(*self.tree.get_children())
        session = Session()
        users = session.query(User).filter_by(is_deleted=False).all()
        for user in users:
            self.tree.insert("", "end", values=(user.id, user.username, user.role))
        session.close()

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected)["values"]
        self.selected_user_id = values[0]
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, values[1])
        self.role_combo.set(values[2])
        self.password_entry.delete(0, tk.END)

    def add_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_combo.get().strip()

        if not username or not password or not role:
            messagebox.showerror("Error", "All fields are required.")
            return

        log_audit(user.username, "Login", "User logged in successfully.")
        log_activity(user.id, user.username, "Login", "Logged in")

        session = Session()
        user = User(username=username, role=role)
        user.set_password(password)
        session.add(user)

        try:
            session.commit()
            messagebox.showinfo("Success", "User added.")
            self.load_users()
        except IntegrityError:
            session.rollback()
            messagebox.showerror("Error", "Username already exists.")
        finally:
            session.close()

    def update_user(self):
        if not self.selected_user_id:
            messagebox.showwarning("Warning", "No user selected.")
            return

        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_combo.get().strip()

        session = Session()
        user = session.query(User).filter_by(id=self.selected_user_id).first()
        if not user:
            messagebox.showerror("Error", "User not found.")
            session.close()
            return

        user.username = username
        user.role = role
        if password:
            user.set_password(password)

        try:
            session.commit()
            messagebox.showinfo("Success", "User updated.")
            self.load_users()
        except IntegrityError:
            session.rollback()
            messagebox.showerror("Error", "Username already exists.")
        finally:
            session.close()

    def delete_user(self):
        if not self.selected_user_id:
            messagebox.showwarning("Warning", "No user selected.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this user?")
        if not confirm:
            return

        session = Session()
        user = session.query(User).filter_by(id=self.selected_user_id).first()
        if user:
            user.is_deleted = True
            session.commit()
            messagebox.showinfo("Deleted", "User deleted.")
            self.load_users()
        session.close()
