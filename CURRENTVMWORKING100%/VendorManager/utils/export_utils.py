import os
import webbrowser
from fpdf import FPDF
from datetime import datetime, timedelta
from tkinter import messagebox

from pathlib import Path
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent.parent  # One level up from dist\VendorManager
else:
    BASE_DIR = Path(__file__).resolve().parent

EXPORT_DIR = BASE_DIR / "utils" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def format_date(d):
    return d.strftime("%m/%d/%Y") if hasattr(d, 'strftime') else str(d or "")

def export_to_pdf(vendor, show_message=True):
    if not vendor:
        if show_message:
            messagebox.showerror("Error", "No vendor data to export.")
        return

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)

    def add_row(label, value):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(50, 10, f"{label}:", border=0)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, str(value or "-"), border=0)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Vendor Information", ln=True, align="C")
    pdf.ln(5)

    fields = [
        ("First Name", vendor.first_name),
        ("Last Name", vendor.last_name),
        ("Business Name", vendor.business_name),
        ("Phone", vendor.phone),
        ("Email", vendor.email),
        ("Island", vendor.island),
        ("Row", vendor.row),
        ("Table #", vendor.table_numbers),
        ("Reservation Date", format_date(vendor.reservation_date)),
        ("First Show", format_date(vendor.first_show)),
        ("Last Show Attended", format_date(vendor.last_show_attended)),
        ("Amount Paid", vendor.amount_paid),
        ("Total Due", vendor.total_due),
        ("Receipt #", vendor.receipt_number),
        ("Check #", vendor.check_number),
        ("Notes", vendor.notes),
    ]
    for label, val in fields:
        add_row(label, val)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Options:", ln=True)

    options = [
        ("Electricity", vendor.electricity),
        ("FFL", vendor.ffl),
        ("Early In", vendor.early_in),
        ("Release Signed", vendor.release_signed),
        ("TACA Member", vendor.taca_member),
        ("TACA Paid", vendor.taca_paid),
        ("Saturday Setup", vendor.saturday_setup),
        ("Rollover April", vendor.rta),
        ("Rollover November", vendor.rtn),
        ("No Show", vendor.no_show),
        ("Cash", vendor.cash),
        ("Credit Card", vendor.credit),
        ("Check", vendor.check),
    ]
    for label, value in options:
        pdf.set_font("Arial", "", 12)
        pdf.cell(60, 10, f"{label}: {'Yes' if value else 'No'}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Table Counts:", ln=True)

    table_counts = [
        ("6' Gun", vendor.six_ft_gun),
        ("6' Knife", vendor.six_ft_knife),
        ("6' Display", vendor.six_ft_display),
        ("6' Non-related", vendor.six_ft_nonrelated),
        ("8' Gun", vendor.eight_ft_gun),
        ("8' Knife", vendor.eight_ft_knife),
        ("8' Display", vendor.eight_ft_display),
        ("8' Non-related", vendor.eight_ft_nonrelated),
    ]
    for label, value in table_counts:
        pdf.set_font("Arial", "", 12)
        pdf.cell(60, 10, f"{label}: {value or 0}", ln=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"{vendor.last_name}_{vendor.first_name}_{timestamp}.pdf".replace(" ", "_")
    path = os.path.join(EXPORT_DIR, filename)
    pdf.output(path)

    if show_message:
        messagebox.showinfo("Exported", f"PDF saved to:\n{path}")
        webbrowser.open(path)

def export_to_txt(vendor, show_message=True):
    if not vendor:
        if show_message:
            messagebox.showerror("Error", "No vendor data to export.")
        return

    lines = [
        f"Vendor: {vendor.first_name} {vendor.last_name}",
        f"Business: {vendor.business_name}",
        f"Phone: {vendor.phone} | Email: {vendor.email}",
        f"Location: Island {vendor.island}, Row {vendor.row}, Table(s) {vendor.table_numbers}",
        f"Shows: {format_date(vendor.first_show)} → {format_date(vendor.last_show_attended)}",
        f"Reservation Date: {format_date(vendor.reservation_date)}",
        f"Total Due: ${int(v.total_due)} | Paid: ${int(v.amount_paid)}",
        f"Receipt #: {vendor.receipt_number} | Check #: {vendor.check_number}",
        "Payment Types: " + ", ".join(
            name for name, val in [("Cash", vendor.cash), ("Credit", vendor.credit), ("Check", vendor.check)] if val
        ),
        "Options: " + ", ".join(
            name for name, val in [
                ("Electricity", vendor.electricity),
                ("FFL", vendor.ffl),
                ("Early In", vendor.early_in),
                ("Release Signed", vendor.release_signed),
                ("TACA Member", vendor.taca_member),
                ("TACA Paid", vendor.taca_paid),
                ("Saturday Setup", vendor.saturday_setup),
                ("Rollover to April", vendor.rta),
        ("Rollover to November", vendor.rtn),
                ("No Show", vendor.no_show)
            ] if val
        ),
        "6' Tables: " + ", ".join(f"{name}: {val or 0}" for name, val in [
            ("Gun", vendor.six_ft_gun),
            ("Knife", vendor.six_ft_knife),
            ("Display", vendor.six_ft_display),
            ("Non-related", vendor.six_ft_nonrelated)
        ]),
        "8' Tables: " + ", ".join(f"{name}: {val or 0}" for name, val in [
            ("Gun", vendor.eight_ft_gun),
            ("Knife", vendor.eight_ft_knife),
            ("Display", vendor.eight_ft_display),
            ("Non-related", vendor.eight_ft_nonrelated)
        ]),
        "\nNotes:\n" + (vendor.notes or "None")
    ]

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"{vendor.last_name}_{vendor.first_name}_{timestamp}.txt".replace(" ", "_")
    path = os.path.join(EXPORT_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    if show_message:
        messagebox.showinfo("Exported", f"TXT saved to:\n{path}")
        webbrowser.open(path)

def export_all_vendors_to_single_pdf(vendors):
    if not vendors:
        messagebox.showerror("Error", "No vendor data to export.")
        return

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for v in vendors:
        export_to_pdf(v, show_message=False)
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Vendor: {v.first_name} {v.last_name}", ln=True, align="C")
        pdf.ln(5)

        def row(label, val):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(50, 10, f"{label}:", border=0)
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, str(val or "-"), border=0)

        fields = [
            ("Business Name", v.business_name),
            ("Phone", v.phone),
            ("Email", v.email),
            ("Island", v.island),
            ("Row", v.row),
            ("Table #", v.table_numbers),
            ("Reservation Date", format_date(v.reservation_date)),
            ("First Show", format_date(v.first_show)),
            ("Last Show Attended", format_date(v.last_show_attended)),
            ("Amount Paid", v.amount_paid),
            ("Total Due", v.total_due),
            ("Receipt #", v.receipt_number),
            ("Check #", v.check_number),
            ("Notes", v.notes),
        ]
        for label, val in fields:
            row(label, val)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Options:", ln=True)
        options = [
            ("Electricity", v.electricity),
            ("FFL", v.ffl),
            ("Early In", v.early_in),
            ("Release Signed", v.release_signed),
            ("TACA Member", v.taca_member),
            ("TACA Paid", v.taca_paid),
            ("Saturday Setup", v.saturday_setup),
            ("Rollover to April", v.rta),
        ("Rollover to November", v.rtn),
            ("No Show", v.no_show),
            ("Cash", v.cash),
            ("Credit Card", v.credit),
            ("Check", v.check),
        ]
        for label, value in options:
            pdf.set_font("Arial", "", 12)
            pdf.cell(60, 10, f"{label}: {'Yes' if value else 'No'}", ln=True)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Tables:", ln=True)
        table_counts = [
            ("6' Gun", v.six_ft_gun),
            ("6' Knife", v.six_ft_knife),
            ("6' Display", v.six_ft_display),
            ("6' Non-related", v.six_ft_nonrelated),
            ("6' Rollover", v.six_ft_rollover),
            ("8' Gun", v.eight_ft_gun),
            ("8' Knife", v.eight_ft_knife),
            ("8' Display", v.eight_ft_display),
            ("8' Non-related", v.eight_ft_nonrelated),
            ("8' Rollover", v.eight_ft_rollover),
        ]
        for label, val in table_counts:
            pdf.set_font("Arial", "", 12)
            pdf.cell(60, 10, f"{label}: {val or 0}", ln=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_path = os.path.join(EXPORT_DIR, f"All_Vendors_{timestamp}.pdf")
    pdf.output(output_path)

    messagebox.showinfo("Exported", f"Combined PDF saved to:\n{output_path}")
    webbrowser.open(output_path)

def export_all_vendors_to_single_txt(vendors):
    if not vendors:
        messagebox.showerror("Error", "No vendor data to export.")
        return

    lines = []
    for v in vendors:
        lines.extend([
            f"Vendor: {v.first_name} {v.last_name} | Business: {v.business_name or ''}",
            f"Phone: {v.phone} | Email: {v.email}",
            f"Island: {v.island} | Row: {v.row} | Table #: {v.table_numbers}",
            f"Reservation: {format_date(v.reservation_date)} | First Show: {format_date(v.first_show)} | Last Show: {format_date(v.last_show_attended)}",
            f"Total Due: ${v.total_due} | Paid: ${v.amount_paid} | Receipt: {v.receipt_number or ''} | Check #: {v.check_number or ''}",
            f"Payment: " + ", ".join(name for name, flag in [("Cash", v.cash), ("Credit", v.credit), ("Check", v.check)] if flag),
            f"Options: " + ", ".join(name for name, flag in [
                ("Electricity", v.electricity), ("FFL", v.ffl), ("Early In", v.early_in),
                ("Release Signed", v.release_signed), ("TACA Member", v.taca_member),
                ("TACA Paid", v.taca_paid), ("Saturday Setup", v.saturday_setup),
                ("Rollover to April", v.rta),
        ("Rollover to November", v.rtn), ("No Show", v.no_show)
            ] if flag),
            f"Tables (6'): G={v.six_ft_gun or 0}, K={v.six_ft_knife or 0}, D={v.six_ft_display or 0}, NR={v.six_ft_nonrelated or 0}",
            f"Tables (8'): G={v.eight_ft_gun or 0}, K={v.eight_ft_knife or 0}, D={v.eight_ft_display or 0}, NR={v.eight_ft_nonrelated or 0}",
            f"Notes: {v.notes or 'None'}",
            "-" * 80
        ])

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_path = os.path.join(EXPORT_DIR, f"All_Vendors_{timestamp}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    messagebox.showinfo("Exported", f"Combined TXT saved to:\n{output_path}")
    webbrowser.open(output_path)


def build_tax_sticker_content(vendor):
	if vendor.business_name and vendor.business_name.strip():
		name = vendor.business_name.strip().upper()
	else:
		name = f"{vendor.first_name.strip()} {vendor.last_name.strip()}".upper()

	tax_id = vendor.tax_id if vendor.tax_id else "N/A"

	# Convert show_date (expected format: MM/DD/YYYY)
	try:
		show_date = datetime.strptime(vendor.show_date, "%m/%d/%Y")
		month_name = show_date.strftime("%B").upper()
		day1 = show_date.day
		day2 = (show_date + timedelta(days=1)).day
		year = show_date.year
		date_line = f"{month_name} {day1} & {day2}, {year}"
	except Exception:
		date_line = "SHOW DATE MISSING"

	return (
		f"$\t\t\t\tSALES TAX ENCLOSED\n"
		f"{name}\t\tEnvelope # {tax_id}\n"
		f"WANENMACHER'S\t\tTULSA ARMS SHOW\n"
		f"{date_line}"
	)