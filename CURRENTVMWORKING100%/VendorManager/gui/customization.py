import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
from models import Session
from models.user import User
from utils.theme import apply_user_theme, apply_user_fonts


class CustomizationWindow(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg="#1e1e1e")
        self.user = user

        self.theme_var = tk.StringVar(value=user.theme_mode or "dark")
        self.accent_color = tk.StringVar(value=user.accent_color or "#ffdf00")

        # Font selections
        font_choices = ["Roboto", "Segoe UI", "Arial", "Courier New", "Calibri"]
        self.global_font = tk.StringVar(value=user.font or "Roboto")
        self.global_font_size = tk.IntVar(value=user.font_size or 12)

        self.label_font_var = tk.StringVar(value=user.font_label or "Roboto")
        self.label_font_size = tk.IntVar(value=user.font_label_size or 12)

        self.button_font_var = tk.StringVar(value=user.font_button or "Roboto")
        self.button_font_size = tk.IntVar(value=user.font_button_size or 12)

        self.entry_font_var = tk.StringVar(value=user.font_entry or "Roboto")
        self.entry_font_size = tk.IntVar(value=user.font_entry_size or 12)

        self.tree_font_var = tk.StringVar(value=user.font_treeview or "Roboto")
        self.tree_font_size = tk.IntVar(value=user.font_treeview_size or 12)

        self.build_ui(font_choices)

    def build_ui(self, font_choices):
        row = 0

        # Theme dropdown
        tk.Label(self, text="Theme Mode", bg="#1e1e1e", fg="white").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        ttk.Combobox(self, textvariable=self.theme_var, values=["dark", "light"], width=10).grid(row=row, column=1, padx=5, sticky="w")
        row += 1

        # Accent color entry + picker
        tk.Label(self, text="Accent Color", bg="#1e1e1e", fg="white").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.accent_entry = tk.Entry(self, textvariable=self.accent_color, bg="#2e2e2e", fg="white", width=10)
        self.accent_entry.grid(row=row, column=1, padx=5, sticky="w")
        tk.Button(self, text="Choose", command=self.pick_color, bg="#444", fg="white").grid(row=row, column=2, padx=5)
        row += 1

        # Global font
        tk.Label(self, text="Global Font", bg="#1e1e1e", fg="white").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        ttk.Combobox(self, textvariable=self.global_font, values=font_choices, width=20).grid(row=row, column=1, padx=5, sticky="w")
        tk.Spinbox(self, from_=8, to=48, textvariable=self.global_font_size, width=5).grid(row=row, column=2, padx=5, sticky="w")
        row += 1

        self._add_font_row("Label Font", self.label_font_var, self.label_font_size, row, font_choices); row += 1
        self._add_font_row("Button Font", self.button_font_var, self.button_font_size, row, font_choices); row += 1
        self._add_font_row("Entry Font", self.entry_font_var, self.entry_font_size, row, font_choices); row += 1
        self._add_font_row("Treeview Font", self.tree_font_var, self.tree_font_size, row, font_choices); row += 1

        # Save / Reset buttons
        tk.Button(self, text="Save Preferences", command=self.save_preferences,
                  bg="#2e2e2e", fg="white", font=("Roboto", 12)).grid(row=row, column=0, columnspan=2, pady=15, padx=10, sticky="w")
        tk.Button(self, text="Reset to Defaults", command=self.reset_defaults,
                  bg="#444", fg="white", font=("Roboto", 12)).grid(row=row, column=2, pady=15, padx=10, sticky="e")

    def _add_font_row(self, label_text, font_var, size_var, row, font_choices):
        tk.Label(self, text=label_text, bg="#1e1e1e", fg="#ffdf00").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        ttk.Combobox(self, textvariable=font_var, values=font_choices, width=20).grid(row=row, column=1, padx=5, sticky="w")
        tk.Spinbox(self, from_=8, to=48, textvariable=size_var, width=5).grid(row=row, column=2, padx=5, sticky="w")

    def pick_color(self):
        color_code = colorchooser.askcolor(title="Choose Accent Color")[1]
        if color_code:
            self.accent_color.set(color_code)

    def save_preferences(self):
        session = Session()
        db_user = session.query(User).filter_by(id=self.user.id).first()
        if not db_user:
            session.close()
            return

        db_user.theme_mode = self.theme_var.get()
        db_user.accent_color = self.accent_color.get()

        db_user.font = self.global_font.get()
        db_user.font_size = self.global_font_size.get()

        db_user.font_label = self.label_font_var.get()
        db_user.font_label_size = self.label_font_size.get()

        db_user.font_button = self.button_font_var.get()
        db_user.font_button_size = self.button_font_size.get()

        db_user.font_entry = self.entry_font_var.get()
        db_user.font_entry_size = self.entry_font_size.get()

        db_user.font_treeview = self.tree_font_var.get()
        db_user.font_treeview_size = self.tree_font_size.get()

        session.commit()
        self.user = db_user  # Update self.user reference
        apply_user_theme(self.master.master, self.user)
        apply_user_fonts(self.master.master, self.user)

        session.close()
        messagebox.showinfo("Saved", "Your preferences have been saved and applied.")

    def reset_defaults(self):
        self.theme_var.set("dark")
        self.accent_color.set("#ffdf00")
        self.global_font.set("Roboto")
        self.global_font_size.set(12)
        self.label_font_var.set("Roboto")
        self.label_font_size.set(12)
        self.button_font_var.set("Roboto")
        self.button_font_size.set(12)
        self.entry_font_var.set("Roboto")
        self.entry_font_size.set(12)
        self.tree_font_var.set("Roboto")
        self.tree_font_size.set(12)
