import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from models import Session
from models.vendor import Vendor
from utils.theme import apply_user_theme
from datetime import datetime


class ExportReportWindow(tk.Toplevel):
    def __init__(self, parent, user, prefiltered_vendors=None):
        super().__init__(parent)
        self.user = user
        self.prefiltered_vendors = prefiltered_vendors
        self.title("Export Vendor Report")
        self.configure(bg="#1e1e1e")
        apply_user_theme(self, user)

        self.include_paid = tk.BooleanVar(value=True)
        self.include_unpaid = tk.BooleanVar(value=True)
        self.include_noshow = tk.BooleanVar(value=True)
        self.export_format = tk.StringVar(value="line")

        tk.Label(self, text="Filters:", fg="white", bg="#1e1e1e").pack(pady=(10, 5))
        filter_frame = tk.Frame(self, bg="#1e1e1e")
        filter_frame.pack()
        tk.Checkbutton(filter_frame, text="Include Paid", variable=self.include_paid, bg="#1e1e1e", fg="white").pack(side="left", padx=5)
        tk.Checkbutton(filter_frame, text="Include Unpaid", variable=self.include_unpaid, bg="#1e1e1e", fg="white").pack(side="left", padx=5)
        tk.Checkbutton(filter_frame, text="Include No-Shows", variable=self.include_noshow, bg="#1e1e1e", fg="white").pack(side="left", padx=5)

        date_frame = tk.Frame(self, bg="#1e1e1e")
        date_frame.pack(pady=5)
        tk.Label(date_frame, text="From (YYYY-MM-DD):", bg="#1e1e1e", fg="white").pack(side="left")
        self.start_date = tk.Entry(date_frame)
        self.start_date.pack(side="left", padx=5)
        tk.Label(date_frame, text="To:", bg="#1e1e1e", fg="white").pack(side="left")
        self.end_date = tk.Entry(date_frame)
        self.end_date.pack(side="left", padx=5)

        tk.Label(self, text="Export Style:", bg="#1e1e1e", fg="white").pack(pady=(10, 0))
        format_box = ttk.Combobox(self, textvariable=self.export_format, values=["line", "table"], state="readonly")
        format_box.pack(pady=5)

        tk.Label(self, text="Choose export format:", bg="#1e1e1e", fg="white").pack(pady=10)
        btn_frame = tk.Frame(self, bg="#1e1e1e")
        btn_frame.pack()
        tk.Button(btn_frame, text="Export as PDF", command=self.export_pdf, bg=self.user.accent_color).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Export as TXT", command=self.export_txt, bg=self.user.accent_color).pack(side="left", padx=10)

    def filter_vendors(self, vendors):
        try:
            start = datetime.strptime(self.start_date.get(), "%Y-%m-%d") if self.start_date.get() else None
            end = datetime.strptime(self.end_date.get(), "%Y-%m-%d") if self.end_date.get() else None
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter valid dates in YYYY-MM-DD format.")
            return []

        filtered = []
        for v in vendors:
            is_paid = v.amount_paid >= (v.total_due or 0)
            is_noshow = getattr(v, "no_show", False)
            created = getattr(v, "reservation_date", None)

            if (self.include_paid.get() and is_paid) or (self.include_unpaid.get() and not is_paid):
                if self.include_noshow.get() or not is_noshow:
                    if start and created and created < start:
                        continue
                    if end and created and created > end:
                        continue
                    filtered.append(v)
        return filtered

    def export_txt(self):
        export_mode = self.export_format.get()
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return

        vendors = self.prefiltered_vendors
        if not vendors:
            session = Session()
            vendors = self.filter_vendors(session.query(Vendor).all())
            session.close()

        with open(file_path, "w", encoding="utf-8") as f:
            if export_mode == "table":
                f.write("ID\tName\tPhone\tPaid\tDue\t6'\t8'\tTACA\tNotes\n")
                for v in vendors:
                    f.write(f"{v.id}\t{v.first_name} {v.last_name}\t{v.phone}\t${int(v.amount_paid)}\t${v.total_due or 0}\t{v.six_ft_total or 0}\t{v.eight_ft_total or 0}\t{'Yes' if v.taca_member else 'No'}\t{v.notes or ''}\n")
            else:
                for v in vendors:
                    f.write(f"{v.id}: {v.first_name} {v.last_name}, {v.phone}, Paid: ${int(v.amount_paid)} / ${int(v.total_due)}\n")
                    f.write(f"  Tables: 6'={v.six_ft_total}  8'={v.eight_ft_total}  TACA: {'Yes' if v.taca_member else 'No'}  Notes: {v.notes or ''}\n")

        messagebox.showinfo("Success", "Vendor list exported as TXT.")

    def export_pdf(self):
        export_mode = self.export_format.get()
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if not file_path:
            return

        vendors = self.prefiltered_vendors
        if not vendors:
            session = Session()
            vendors = self.filter_vendors(session.query(Vendor).all())
            session.close()

        if export_mode == "table":
            from reportlab.platypus import Table, TableStyle, SimpleDocTemplate
            from reportlab.lib import colors
            data = [["ID", "Name", "Phone", "Paid", "Due", "6'", "8'", "TACA", "Notes"]]
            for v in vendors:
                data.append([
                    v.id,
                    f"{v.first_name} {v.last_name}",
                    v.phone,
                    f"${int(v.amount_paid)}",
                    f"${int(v.total_due or 0)}",
                    v.six_ft_total or 0,
                    v.eight_ft_total or 0,
                    "Yes" if v.taca_member else "No",
                    v.notes or ""
                ])
            pdf = SimpleDocTemplate(file_path, pagesize=LETTER)
            t = Table(data, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.black),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]))
            pdf.build([t])
        else:
            c = canvas.Canvas(file_path, pagesize=LETTER)
            width, height = LETTER
            y = height - 50
            c.setFont("Helvetica", 10)

            c.drawString(50, y, "Vendor List")
            y -= 20
            for v in vendors:
                line1 = f"{v.id}: {v.first_name} {v.last_name}, {v.phone}, Paid: ${int(v.amount_paid)} / ${int(float(v.total_due or 0))}"
                line2 = f"Tables: 6'={v.six_ft_total or 0}  8'={v.eight_ft_total or 0}  TACA: {'Yes' if v.taca_member else 'No'}  Notes: {v.notes or ''}"
                c.drawString(50, y, line1)
                y -= 15
                c.drawString(50, y, line2)
                y -= 20
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = height - 50
            c.save()

        messagebox.showinfo("Success", "Vendor list exported as PDF.")