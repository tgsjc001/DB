import tkinter as tk
from tkinter import ttk, messagebox
from models import Session
from models.audit_log import AuditLog
from models.activity_log import ActivityLog
from models.user import User
from models.session_log import SessionLog
from utils.theme import apply_user_theme
from sqlalchemy.orm import joinedload

class AuditViewerTab(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg="#1e1e1e")
        self.user = user
        apply_user_theme(self, user)
        self.build_ui()

    def build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.audit_tab = tk.Frame(notebook, bg="#1e1e1e")
        self.activity_tab = tk.Frame(notebook, bg="#1e1e1e")
        self.session_tab = tk.Frame(notebook, bg="#1e1e1e")

        notebook.add(self.audit_tab, text="Audit Logs")
        notebook.add(self.activity_tab, text="Activity Logs")
        notebook.add(self.session_tab, text="Session Logs")

        ttk.Button(self, text="Clear Logs", command=self.clear_visible_logs).pack(pady=10)

        self.build_audits(self.audit_tab)
        self.build_activities(self.activity_tab)
        self.build_sessions(self.session_tab)

    def build_audits(self, parent):
        session = Session()
        records = session.query(ActivityLog).options(joinedload(ActivityLog.user)).all()
        session.close()

        self.audit_tree = ttk.Treeview(parent, columns=("ID", "User", "Action", "Description", "Timestamp"), show="headings")
        for col in ("ID", "User", "Action", "Description", "Timestamp"):
            self.audit_tree.heading(col, text=col)
            self.audit_tree.column(col, anchor="center", width=160)
        self.audit_tree.pack(fill="both", expand=True, padx=10, pady=10)

        for log in records:
            self.audit_tree.insert("", "end",
                                   values=(log.id, log.username, log.action, log.description, log.timestamp.strftime("%Y-%m-%d %H:%M:%S")))

        self.audit_tree.bind("<<TreeviewSelect>>", self.show_audit_details)

    def build_activities(self, parent):
        session = Session()
        records = session.query(ActivityLog).options(joinedload(ActivityLog.user)).all()
        session.close()

        self.activity_tree = ttk.Treeview(parent, columns=("ID", "User", "Action", "Timestamp"), show="headings")
        for col in ("ID", "User", "Action", "Timestamp"):
            self.activity_tree.heading(col, text=col)
            self.activity_tree.column(col, anchor="center", width=160)
        self.activity_tree.pack(fill="both", expand=True)

        for log in records:
            self.activity_tree.insert("", "end",
                                      values=(log.id, log.user.username, log.action, log.timestamp.strftime("%Y-%m-%d %H:%M:%S")))

        self.activity_tree.bind("<<TreeviewSelect>>", self.show_activity_details)

    def build_sessions(self, parent):
        session = Session()
        records = session.query(SessionLog).filter_by(visible=True).join(User).all()
        session.close()

        self.session_tree = ttk.Treeview(parent, columns=("ID", "User", "Login Time", "Logout Time"), show="headings")
        for col in ("ID", "User", "Login Time", "Logout Time"):
            self.session_tree.heading(col, text=col)
            self.session_tree.column(col, anchor="center", width=180)
        self.session_tree.pack(fill="both", expand=True)

        for log in records:
            self.session_tree.insert("", "end",
                                     values=(log.id, log.user.username, str(log.login_time), str(log.logout_time or "Active")))

        self.session_tree.bind("<<TreeviewSelect>>", self.show_session_details)

    def show_audit_details(self, event):
        selected = self.audit_tree.selection()
        if not selected:
            return
        item = self.audit_tree.item(selected[0])
        log_id = item["values"][0]
        session = Session()
        log = session.query(AuditLog).filter_by(id=log_id).first()
        session.close()
        if log:
            detail = (
                f"User: {log.username}\n"
                f"Action: {log.action}\n"
                f"Description: {log.description}\n"
                f"Timestamp: {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            messagebox.showinfo("Audit Log Details", detail)

    def show_activity_details(self, event):
        selected = self.activity_tree.selection()
        if not selected:
            return
        item = self.activity_tree.item(selected[0])
        log_id = item["values"][0]
        session = Session()
        log = session.query(ActivityLog).filter_by(id=log_id).first()
        session.close()
        if log:
            detail = (
                f"User: {log.user.username}\n"
                f"Action: {log.action}\n"
                f"Description: {log.description}\n"
                f"Timestamp: {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            messagebox.showinfo("Activity Log Details", detail)

    def show_session_details(self, event):
        selected = self.session_tree.selection()
        if not selected:
            return
        item = self.session_tree.item(selected[0])
        log_id = item["values"][0]
        session = Session()
        log = session.query(SessionLog).filter_by(id=log_id).first()
        session.close()
        if log:
            detail = (
                f"User: {log.user.username}\n"
                f"Login Time: {log.login_time}\n"
                f"Logout Time: {log.logout_time or 'Active'}"
            )
            messagebox.showinfo("Session Log Details", detail)

    def clear_visible_logs(self):
        session = Session()
        session.query(AuditLog).filter_by(visible=True).update({AuditLog.visible: False})
        session.query(ActivityLog).filter_by(visible=True).update({ActivityLog.visible: False})
        session.query(SessionLog).filter_by(visible=True).update({SessionLog.visible: False})
        session.commit()
        session.close()
        messagebox.showinfo("Logs Cleared", "Visible logs have been cleared.")
        self.build_ui()
