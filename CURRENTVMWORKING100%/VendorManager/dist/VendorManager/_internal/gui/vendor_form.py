import tkinter as tk
from tkinter import messagebox
from models import Session
from models.vendor import Vendor
from utils.pricing import calculate_total_due
from utils.export_utils import export_to_pdf, export_to_txt
import re
import os
import sys
from utils.audit_logger import log_audit
from utils.activity_logger import log_activity
from sqlalchemy.sql import func
from utils.enhanced_logger import get_enhanced_logger, FormSession
from utils.form_shortcuts import VendorFormShortcuts
from datetime import datetime

class CreateToolTip:
	def __init__(self, widget, text):
		self.widget = widget
		self.text = text
		self.tipwindow = None
		widget.bind("<Enter>", self.show)
		widget.bind("<Leave>", self.hide)

	def show(self, _):
		if self.tipwindow:
			return
		x, y, _, _ = self.widget.bbox("insert")
		x += self.widget.winfo_rootx() + 20
		y += self.widget.winfo_rooty() + 20
		self.tipwindow = tw = tk.Toplevel(self.widget)
		tw.wm_overrideredirect(True)
		tw.geometry(f"+{x}+{y}")
		label = tk.Label(tw, font=("Roboto", 14), text=self.text, background="#333", foreground="white", relief="solid",
						 borderwidth=1)
		label.pack(fill='x', expand=True, )

	def hide(self, _):
		if self.tipwindow:
			self.tipwindow.destroy()
			self.tipwindow = None


class VendorForm(tk.Toplevel):
	SHOW_DATE = "04/06/2025"  # Set your specific show date here

	def __init__(self, parent, user, vendor_id=None, refresh_callback=None):
		super().__init__(parent)
		self.user = user
		self.vendor_id = vendor_id
		self.refresh_callback = refresh_callback
		self.vendor = None
		self.entries = {}
		self.checks = {}
		self.icons = {}
		self.on_rollover_var = tk.BooleanVar()

		# ADD THESE NEW LINES:
		# Enhanced logging system
		self.logger = get_enhanced_logger(user)
		self.form_session = None
		self.original_data = {}
		self.start_time = datetime.now()

		# Keyboard shortcuts system
		self.keyboard_shortcuts = None

		# Continue with existing code...
		self.title("Vendor Form")
		self.configure(bg="#1e1e1e")
		self.geometry("1280x720")

		if vendor_id:
			session = Session()
			self.vendor = session.query(Vendor).filter_by(id=vendor_id).first()
			session.close()

			# LOG: Form opened for existing vendor
			if self.vendor:
				vendor_data = {
					'business_name': self.vendor.business_name,
					'first_name': self.vendor.first_name,
					'last_name': self.vendor.last_name,
					'id': self.vendor.id
				}
				self.logger.log_double_click("Vendor", self.vendor.id, vendor_data, "Form opened")

		self.build_form()
		self.build_button_bar()

		# ADD: Setup keyboard shortcuts AFTER UI is built
		self.keyboard_shortcuts = VendorFormShortcuts(self)

		if self.vendor:
			self.load_vendor_data()
			# Store original data for change tracking
			self.store_original_data()
		else:
			self.toggle_check_number()
			self.toggle_taca_paid()
			self.toggle_tables()

			# LOG: New vendor form opened
			self.logger.log_form_interaction("Vendor", "New Form Opened")

	def toggle_tables(self):
		for key in getattr(self, "six_ft_fields", {}):
			state = "normal" if self.checks["table_size_six"].get() else "disabled"
			self.six_ft_fields[key].config(state=state, disabledbackground="#2e2e2e", disabledforeground="white")
		for key in getattr(self, "eight_ft_fields", {}):
			state = "normal" if self.checks["table_size_eight"].get() else "disabled"
			self.eight_ft_fields[key].config(state=state, disabledbackground="#2e2e2e", disabledforeground="white")

	def toggle_check_number(self):
		if self.checks.get('check') and self.checks['check'].get():
			self.check_number_label.grid(row=0, column=6, padx=5, pady=4, sticky='ew')
			self.check_number_entry.grid(row=0, column=7, padx=5, pady=4, sticky='ew')
		else:
			self.check_number_label.grid_remove()
			self.check_number_entry.grid_remove()

	def toggle_taca_paid(self):
		if "taca_member" in self.checks and hasattr(self, "taca_paid_chk") and hasattr(self, "taca_paid_amt"):
			if self.checks["taca_member"].get():
				self.taca_paid_chk.pack(fill='x', expand=True, side="left", padx=2)
				self.taca_paid_amt.pack(fill='x', expand=True, side="left")
			else:
				self.taca_paid_chk.pack_forget()
				self.taca_paid_amt.pack_forget()

	def build_form(self):
		bg = "#1e1e1e"
		fg = "#ffdf00"

		main = tk.Frame(self, bg="#1e1e1e")
		main.pack(fill="both", expand=True, padx=2, pady=2)

		def label_entry(row, label, key, width=18, readonly=False):
			wrapper = tk.Frame(row, bg="#1e1e1e")
			wrapper.pack(fill='x', expand=True, side="left", padx=2)
			tk.Label(wrapper, font=("Roboto", 14), text=label, bg="#1e1e1e", fg="#ffdf00").pack(fill='x', expand=True, )

			var = tk.StringVar()
			entry_config = {
				"font": ("Roboto", 14),
				"width": width,
				"bg": "#2e2e2e",
				"fg": "white" if not readonly else "#999999",
				"insertbackground": "white",
				"justify": "center",
				"disabledbackground": "#2e2e2e",
				"textvariable": var
			}

			if readonly:
				entry_config.update({
					"state": "readonly",
					"readonlybackground": "#2e2e2e"
				})

			entry = tk.Entry(wrapper, **entry_config)

			# Live phone formatting
			if key == "phone" and not readonly:
				def format_phone_live(e):
					raw = re.sub(r"\D", "", entry.get())[:10]
					digits_before_cursor = len(re.sub(r"\D", "", entry.get()[:entry.index(tk.INSERT)]))
					if len(raw) >= 7:
						formatted = f"{raw[:3]}-{raw[3:6]}-{raw[6:]}"
					elif len(raw) >= 4:
						formatted = f"{raw[:3]}-{raw[3:]}"
					else:
						formatted = raw
					entry.delete(0, tk.END)
					entry.insert(0, formatted)

					# Restore cursor
					digit_count = 0
					new_pos = 0
					for c in formatted:
						if c.isdigit():
							digit_count += 1
						new_pos += 1
						if digit_count >= digits_before_cursor:
							break
					entry.icursor(new_pos)

				entry.bind("<KeyRelease>", format_phone_live)

			# Live date formatting
			elif key in ("reservation_date", "first_show", "last_show_attended") and not readonly:
				def format_date(*_):
					raw = re.sub(r"\D", "", var.get())[:8]
					if len(raw) == 6:
						month, day, year = raw[:2], raw[2:4], "20" + raw[4:]
						var.set(f"{month}/{day}/{year}")
					elif len(raw) == 8:
						var.set(f"{raw[:2]}/{raw[2:4]}/{raw[4:]}")

				var.trace_add("write", lambda *_: format_date())

			# Insert value if editing an existing vendor or set default for show_date
			formatted_value = ""
			if key == "show_date":
				formatted_value = self.SHOW_DATE
			elif self.vendor and hasattr(self.vendor, key):
				val = getattr(self.vendor, key)
				if val is None:
					formatted_value = ""
				elif key == "phone":
					formatted_value = re.sub(r"(\d{3})(\d{3})(\d{4})", r"\1-\2-\3", val)
				elif key in ("reservation_date", "first_show", "last_show_attended") and hasattr(val, 'strftime'):
					formatted_value = val.strftime("%m/%d/%Y")
				elif key in ("total_due", "amount_paid", "taca_amount"):
					formatted_value = f"${int(val)}"
				else:
					formatted_value = str(val)

			# Special handling for readonly fields - temporarily enable to insert value
			if readonly:
				entry.config(state="normal")
				entry.insert(0, formatted_value)
				entry.config(state="readonly")
			else:
				entry.insert(0, formatted_value)

			entry.pack(fill='x', expand=True, )
			self.entries[key] = entry

		def checkbox(row, label, key, command=None):
			var = tk.BooleanVar()
			cb = tk.Checkbutton(row, font=("Roboto", 14), text=label, variable=var,
								command=command or self.update_total_due,
								bg="#1e1e1e", fg="#ffdf00", selectcolor="#1e1e1e",
								activebackground="#1e1e1e", activeforeground="#ffdf00")
			cb.pack(fill='x', expand=True, side="left", padx=2)
			self.checks[key] = var
			return cb

		# Row 0: Reservation Date and Show Date
		row0 = tk.Frame(main, bg="#1e1e1e")
		row0.pack(fill='x', expand=True)
		label_entry(row0, "Reservation Date", "reservation_date")
		label_entry(row0, "Show Date", "show_date", readonly=True)

		# Row 1: First Show and Last Show
		row1 = tk.Frame(main, bg="#1e1e1e")
		row1.pack(fill='x', expand=True)
		label_entry(row1, "First Show", "first_show")
		label_entry(row1, "Last Show", "last_show_attended")

		row2 = tk.Frame(main, bg="#1e1e1e");
		row2.pack(fill='x', expand=True, )
		self.checks["table_size_six"] = tk.BooleanVar()
		tk.Checkbutton(row2, font=("Roboto", 14), text="6'", variable=self.checks["table_size_six"],
					   command=self.toggle_tables, bg="#1e1e1e", fg="#ffdf00",
					   selectcolor="#1e1e1e").pack(fill='x', expand=True, side="left", padx=2)
		self.six_ft_fields = {}
		for key in ["six_ft_gun", "six_ft_knife", "six_ft_display", "six_ft_nonrelated", "six_ft_rollover"]:
			lbl = tk.Label(row2, font=("Roboto", 14), text=key.split("_")[-1][0].upper(), bg="#1e1e1e", fg="#ffdf00")
			lbl.pack(fill='x', expand=True, side="left", padx=(2, 2))
			entry = tk.Entry(row2, font=("Roboto", 14), width=3, justify="center", bg="#2e2e2e", fg="white",
							 insertbackground="white", disabledbackground="#2e2e2e")
			entry.pack(fill='x', expand=True, side="left")
			entry.bind("<KeyRelease>", lambda e: self.update_total_due())
			self.entries[key] = entry
			self.six_ft_fields[key] = entry

		row3 = tk.Frame(main, bg="#1e1e1e");
		row3.pack(fill='x', expand=True, )
		self.checks["table_size_eight"] = tk.BooleanVar()
		tk.Checkbutton(row3, font=("Roboto", 14), text="8'", variable=self.checks["table_size_eight"],
					   command=self.toggle_tables, bg="#1e1e1e", fg="#ffdf00",
					   selectcolor="#1e1e1e").pack(fill='x', expand=True, side="left", padx=2)
		self.eight_ft_fields = {}
		for key in ["eight_ft_gun", "eight_ft_knife", "eight_ft_display", "eight_ft_nonrelated", "eight_ft_rollover"]:
			lbl = tk.Label(row3, font=("Roboto", 14), text=key.split("_")[-1][0].upper(), bg="#1e1e1e", fg="#ffdf00")
			lbl.pack(fill='x', expand=True, side="left", padx=(2, 2))
			entry = tk.Entry(row3, font=("Roboto", 14), width=3, justify="center", bg="#2e2e2e", fg="white",
							 insertbackground="white", disabledbackground="#2e2e2e")
			entry.pack(fill='x', expand=True, side="left")
			entry.bind("<KeyRelease>", lambda e: self.update_total_due())
			self.entries[key] = entry
			self.eight_ft_fields[key] = entry

		row4 = tk.Frame(main, bg="#1e1e1e");
		row4.pack(fill='x', expand=True, )
		label_entry(row4, "Island", "island")
		label_entry(row4, "Row", "row")
		label_entry(row4, "Table #", "table_numbers")

		row5 = tk.Frame(main, bg="#1e1e1e");
		row5.pack(fill='x', expand=True, )
		label_entry(row5, "First Name", "first_name")
		label_entry(row5, "Last Name", "last_name")
		label_entry(row5, "Business Name", "business_name")

		row6 = tk.Frame(main, bg="#1e1e1e");
		row6.pack(fill='x', expand=True, )
		label_entry(row6, "Address", "address", width=18)
		label_entry(row6, "City", "city", width=14)
		label_entry(row6, "State", "state", width=2)
		label_entry(row6, "Zip Code", "zip_code", width=5)

		row7 = tk.Frame(main, bg="#1e1e1e");
		row7.pack(fill='x', expand=True, )
		label_entry(row7, "Phone", "phone")
		label_entry(row7, "Email", "email")

		row7 = tk.Frame(main, bg=bg)
		row7.pack(fill=tk.X, pady=2)
		cb = checkbox(row7, "On Rollover", "on_rollover")
		self.checks["on_rollover"] = self.on_rollover_var
		cb.config(variable=self.on_rollover_var)
		checkbox(row7, "Rollover to April", "rta")
		checkbox(row7, "Rollover to November", "rtn")
		checkbox(row7, "Release Signed", "release_signed")
		checkbox(row7, "Saturday Setup", "saturday_setup")
		checkbox(row7, "No Show", "no_show")

		# Row 8: TACA
		row8 = tk.Frame(main, bg="#1e1e1e");
		row8.pack(fill='x', expand=True, )
		checkbox(row8, "Electricity", "electricity")
		checkbox(row8, "FFL", "ffl")
		checkbox(row8, "Early In", "early_in")
		checkbox(row8, "TACA Member", "taca_member", self.toggle_taca_paid)
		self.taca_paid_chk = checkbox(row8, "Paid", "taca_paid")
		self.taca_paid_amt = tk.Entry(row8, font=("Roboto", 14), width=3, justify="center", bg="#2e2e2e", fg="white",
									  insertbackground="white")
		self.entries["taca_amount"] = self.taca_paid_amt
		self.taca_paid_amt.pack(fill='x', expand=True, side="left", padx=2)

		# Row 10: Payment method
		row10 = tk.Frame(main, bg="#1e1e1e");
		row10.pack(fill='x', expand=True, )
		checkbox(row10, "Cash", "cash")
		checkbox(row10, "Credit Card", "credit")
		checkbox(row10, "Check", "check", self.toggle_check_number)

		# Row 11: Total, paid, receipt, check #
		row11 = tk.Frame(main, bg="#1e1e1e");
		# Row 11: Total Due, Amount Paid, Receipt #, Check #, Tax ID (Clean Centered Grid)
		row11.pack(fill="x", expand=True)
		row11.columnconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), weight=1)
		tk.Label(row11, text="Total Due", bg="#1e1e1e", fg="#ffdf00", font=("Roboto", 14)).grid(row=0, column=0, padx=5,
																								pady=4, sticky="ew")
		self.entries["total_due"] = tk.Entry(row11, font=("Roboto", 14), bg="#2e2e2e", fg="white", width=10)
		self.entries["total_due"].grid(row=0, column=1, padx=5, pady=4, sticky="ew")
		tk.Label(row11, text="Amount Paid", bg="#1e1e1e", fg="#ffdf00", font=("Roboto", 14)).grid(row=0, column=2,
																								  padx=5, pady=4,
																								  sticky="ew")
		self.entries["amount_paid"] = tk.Entry(row11, font=("Roboto", 14), bg="#2e2e2e", fg="white", width=10)
		self.entries["amount_paid"].grid(row=0, column=3, padx=5, pady=4, sticky="ew")
		tk.Label(row11, text="Receipt #", bg="#1e1e1e", fg="#ffdf00", font=("Roboto", 14)).grid(row=0, column=4, padx=5,
																								pady=4, sticky="ew")
		self.entries["receipt_number"] = tk.Entry(row11, font=("Roboto", 14), bg="#2e2e2e", fg="white", width=10)
		self.entries["receipt_number"].grid(row=0, column=5, padx=5, pady=4, sticky="ew")
		self.check_number_label = tk.Label(row11, text="Check #", bg="#1e1e1e", fg="#ffdf00", font=("Roboto", 14))
		self.check_number_entry = tk.Entry(row11, font=("Roboto", 14), bg="#2e2e2e", fg="white", width=10)
		self.entries["check_number"] = self.check_number_entry
		tk.Label(row11, text="Tax ID", bg="#1e1e1e", fg="#ffdf00", font=("Roboto", 14)).grid(row=0, column=8, padx=5,
																							 pady=4, sticky="ew")
		self.tax_id_var = tk.StringVar()
		self.tax_id_entry = tk.Entry(row11, textvariable=self.tax_id_var, state="readonly",
									 font=("Roboto", 14), bg="#2e2e2e", fg="white", width=10,
									 insertbackground="white", readonlybackground="#2e2e2e")
		self.tax_id_entry.grid(row=0, column=9, padx=5, pady=4, sticky="ew")
		row12 = tk.Frame(main, bg="#1e1e1e");
		row12.pack(fill='x', expand=True, pady=(2, 2))
		tk.Label(row12, font=("Roboto", 14), text="Notes", bg="#1e1e1e", fg="#ffdf00").pack(fill='x', expand=True, )
		self.entries["notes"] = tk.Text(row12, font=("Roboto", 14), height=5, width=100, bg="#2e2e2e", fg="white",
										insertbackground="white")
		self.entries["notes"].pack(fill='x', expand=True, )

	def build_button_bar(self):
		bar = tk.Frame(self, bg="#1e1e1e")
		bar.pack(fill='x', expand=True, pady=2)

		# Support both PyInstaller and dev mode
		if hasattr(sys, '_MEIPASS'):
			icon_dir = os.path.join(sys._MEIPASS, "converted_icons")
		else:
			icon_dir = os.path.abspath("converted_icons")

		buttons = [
			("save", self.save_vendor),
			("delete", self.delete_vendor),
			("print", self.print_vendor),
			("pdf", lambda: export_to_pdf(self.vendor)),
			("txt", lambda: export_to_txt(self.vendor))
		]

		tooltips = {
			"save": "Save Vendor",
			"delete": "Delete Vendor",
			"print": "Print",
			"pdf": "Export to PDF",
			"txt": "Export to TXT"
		}

		for name, cmd in buttons:
			try:
				icon_path = os.path.join(icon_dir, f"{name}.png")
				img = tk.PhotoImage(file=icon_path)
				self.icons[name] = img
				btn = tk.Button(bar, font=("Roboto", 14), image=img, command=cmd, bg="#1e1e1e", relief="flat")
				btn.pack(fill='x', expand=True, side="left", padx=2)
				CreateToolTip(btn, tooltips[name])
			except Exception as e:
				print(f"[ERROR] Loading icon '{name}':", e)

	def format_currency(self, key):
		widget = self.entries[key]
		try:
			raw = widget.get().replace("$", "").strip()
			widget.delete(0, tk.END)
			widget.insert(0, f"${int(float(raw))}")
		except:
			pass

	def format_phone(self):
		raw = re.sub(r"\D", "", self.entries["phone"].get())
		if len(raw) == 10:
			self.entries["phone"].delete(0, tk.END)
			self.entries["phone"].insert(0, f"{raw[:3]}-{raw[3:6]}-{raw[6:]}")

	def update_total_due(self):
		try:
			temp = Vendor()
			for k, w in self.entries.items():
				if isinstance(w, tk.Text):
					val = w.get("1.0", "end").strip()
				else:
					val = w.get().replace("$", "").strip()

				if k in ("taca_amount", "amount_paid", "total_due",
						 "six_ft_gun", "six_ft_knife", "six_ft_display", "six_ft_nonrelated", "six_ft_rollover",
						 "eight_ft_gun", "eight_ft_knife", "eight_ft_display", "eight_ft_nonrelated",
						 "eight_ft_rollover"):
					try:
						val = int(val)
					except (ValueError, TypeError):
						val = 0

				setattr(temp, k, val)

			for k, v in self.checks.items():
				setattr(temp, k, v.get())

			total = calculate_total_due(temp)
			self.entries["total_due"].delete(0, tk.END)
			self.entries["total_due"].insert(0, f"${int(total)}")
		except Exception as e:
			print("[ERROR] Total Due update:", e)

	def save_vendor(self):
		# Track changes before saving
		field_changes = self.track_field_changes()

		session = Session()
		is_new_vendor = not self.vendor

		if not self.vendor:
			self.vendor = Vendor()

		# Your existing validation and saving code here...
		# (keep all your existing logic)

		for k, w in self.entries.items():
			val = w.get("1.0", "end").strip() if isinstance(w, tk.Text) else w.get().replace("$", "").strip()

			# Normalize date fields
			if k in ("reservation_date", "first_show", "last_show_attended", "show_date"):
				val = None if val in ("", "--/--/--") else val

			# Validate state
			if k == "state":
				if val and not re.fullmatch(r"[A-Z]{2}", val.upper()):
					messagebox.showerror("Validation Error", "State must be 2 uppercase letters.")
					return
				val = val.upper() if val else ""

			# Validate zip code
			if k == "zip_code":
				if val and not re.fullmatch(r"\d{5}", val):
					messagebox.showerror("Validation Error", "Zip Code must be 5 digits.")
					return

			# Handle integers safely
			elif k in ("taca_amount", "amount_paid", "total_due",
					   "six_ft_gun", "six_ft_knife", "six_ft_display", "six_ft_nonrelated", "six_ft_rollover",
					   "eight_ft_gun", "eight_ft_knife", "eight_ft_display", "eight_ft_nonrelated",
					   "eight_ft_rollover"):
				try:
					val = int(val)
				except (ValueError, TypeError):
					val = 0

			setattr(self.vendor, k, val)

		for k, v in self.checks.items():
			setattr(self.vendor, k, v.get())

		self.vendor.total_due = calculate_total_due(self.vendor)
		self.vendor.on_rollover = self.on_rollover_var.get()

		vendor_name = self.vendor.business_name or f"{self.vendor.first_name or ''} {self.vendor.last_name or ''}".strip()

		# ENHANCED LOGGING:
		try:
			# Calculate form duration
			duration = (datetime.now() - self.start_time).total_seconds()

			# Log detailed vendor interaction
			vendor_data = {
				'business_name': self.vendor.business_name,
				'first_name': self.vendor.first_name,
				'last_name': self.vendor.last_name,
				'id': getattr(self.vendor, 'id', None)
			}

			action = "Created" if is_new_vendor else "Updated"
			self.logger.log_vendor_interaction(
				action=action,
				vendor_id=getattr(self.vendor, 'id', None),
				vendor_data=vendor_data,
				changes=field_changes,
				context=f"Form duration: {duration:.1f}s"
			)

			# Log form interaction
			self.logger.log_form_interaction(
				form_type="Vendor",
				action="Saved",
				form_data=vendor_data,
				field_changes=field_changes,
				duration=duration
			)

		except Exception as e:
			print(f"[LOG ERROR] {e}")

		# Your existing save logic continues...
		if not self.vendor.id:
			max_tax_id = session.query(func.max(Vendor.tax_id)).scalar() or 0
			self.vendor.tax_id = max_tax_id + 1
			self.tax_id_var.set(str(self.vendor.tax_id))

		session.merge(self.vendor)
		session.commit()
		session.close()

		if self.refresh_callback:
			self.refresh_callback()
		self.destroy()

	def delete_vendor(self):
		if self.vendor and messagebox.askyesno("Confirm Delete", "Are you sure?"):
			# LOG: Vendor deletion
			vendor_data = {
				'business_name': self.vendor.business_name,
				'first_name': self.vendor.first_name,
				'last_name': self.vendor.last_name,
				'id': self.vendor.id
			}

			self.logger.log_vendor_interaction(
				action="Deleted",
				vendor_id=self.vendor.id,
				vendor_data=vendor_data,
				context="User confirmed deletion"
			)

			session = Session()
			session.delete(self.vendor)
			session.commit()
			session.close()

			if self.refresh_callback:
				self.refresh_callback()
			self.destroy()

	def print_vendor(self):
		print("[PRINT] Not implemented.")

	def load_vendor_data(self):
		for k, w in self.entries.items():
			if hasattr(self.vendor, k):
				val = getattr(self.vendor, k)
				if isinstance(w, tk.Text):
					w.delete("1.0", "end")
					w.insert("1.0", str(val or ""))
				elif isinstance(w, tk.Entry):
					if k == "show_date":
						# Show date should always display the fixed date
						continue  # Skip loading - it's already set to SHOW_DATE
					elif k in ("total_due", "amount_paid", "taca_amount"):
						w.delete(0, tk.END)
						w.insert(0, f"${int(val)}" if val else "")
					elif k == "phone":
						w.delete(0, tk.END)
						w.insert(0, re.sub(r"(\d{3})(\d{3})(\d{4})", r"\1-\2-\3", val or ""))
					elif hasattr(val, 'strftime'):
						w.delete(0, tk.END)
						w.insert(0, val.strftime("%m/%d/%Y"))
					else:
						w.delete(0, tk.END)
						w.insert(0, str(val or ""))
		for k, v in self.checks.items():
			if hasattr(self.vendor, k):
				v.set(bool(getattr(self.vendor, k)))

		self.toggle_check_number()
		self.toggle_taca_paid()
		self.toggle_tables()
		self.tax_id_var.set(str(self.vendor.tax_id) if self.vendor and self.vendor.tax_id else "")
		self.on_rollover_var.set(self.vendor.on_rollover if self.vendor else False)

	def print_vendor(self):
		from fpdf import FPDF
		import tempfile
		import webbrowser

		if not self.vendor:
			messagebox.showerror("Error", "No vendor selected.")
			return

		pdf = FPDF()
		pdf.add_page()
		pdf.set_font("Arial", size=12)

		def format_date(d):
			return d.strftime("%m/%d/%Y") if hasattr(d, 'strftime') else str(d or "")

		def add_row(label, value):
			pdf.set_font("Arial", "B", 12)
			pdf.cell(50, 10, f"{label}:", border=0)
			pdf.set_font("Arial", "", 12)
			pdf.multi_cell(0, 10, str(value or "-"), border=0)

		pdf.set_font("Arial", "B", 16)
		pdf.cell(0, 10, "Vendor Printout", ln=True, align="C")
		pdf.ln(5)

		fields = [
			("First Name", self.vendor.first_name),
			("Last Name", self.vendor.last_name),
			("Business Name", self.vendor.business_name),
			("Phone", self.vendor.phone),
			("Email", self.vendor.email),
			("Island", self.vendor.island),
			("Row", self.vendor.row),
			("Table #", self.vendor.table_numbers),
			("Reservation Date", format_date(self.vendor.reservation_date)),
			("Show Date", self.vendor.show_date),
			("First Show", format_date(self.vendor.first_show)),
			("Last Show Attended", format_date(self.vendor.last_show_attended)),
			("Amount Paid", self.vendor.amount_paid),
			("Total Due", self.vendor.total_due),
			("Receipt #", self.vendor.receipt_number),
			("Check #", self.vendor.check_number),
			("Notes", self.vendor.notes),
		]

		for label, val in fields:
			add_row(label, val)

		pdf.ln(5)
		pdf.set_font("Arial", "B", 14)
		pdf.cell(0, 10, "Options:", ln=True)

		options = [
			("Electricity", self.vendor.electricity),
			("FFL", self.vendor.ffl),
			("Early In", self.vendor.early_in),
			("Release Signed", self.vendor.release_signed),
			("TACA Member", self.vendor.taca_member),
			("TACA Paid", self.vendor.taca_paid),
			("Saturday Setup", self.vendor.saturday_setup),
			("Rollover to April", self.vendor.rta),
			("Rollover to November", self.vendor.rtn),
			("On Rollover", self.vendor.on_rollover),
			("No Show", self.vendor.no_show),
			("Cash", self.vendor.cash),
			("Credit Card", self.vendor.credit),
			("Check", self.vendor.check),
		]

		for label, val in options:
			pdf.set_font("Arial", "", 12)
			pdf.cell(60, 10, f"{label}: {'Yes' if val else 'No'}", ln=True)

		pdf.ln(5)
		pdf.set_font("Arial", "B", 14)
		pdf.cell(0, 10, "Table Counts:", ln=True)

		for label, val in [
			("6' Gun", self.vendor.six_ft_gun),
			("6' Knife", self.vendor.six_ft_knife),
			("6' Display", self.vendor.six_ft_display),
			("6' Non-related", self.vendor.six_ft_nonrelated),
			("6' Rollover", self.vendor.six_ft_rollover),
			("8' Gun", self.vendor.eight_ft_gun),
			("8' Knife", self.vendor.eight_ft_knife),
			("8' Display", self.vendor.eight_ft_display),
			("8' Non-related", self.vendor.eight_ft_nonrelated),
			("8' Rollover", self.vendor.eight_ft_rollover),
		]:
			pdf.set_font("Arial", "", 12)
			pdf.cell(60, 10, f"{label}: {val or 0}", ln=True)

		# Save to temp file and open it
		with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
			pdf.output(tmpfile.name)
			webbrowser.open(tmpfile.name)

	def store_original_data(self):
		"""Store original form data for change tracking"""
		self.original_data = {}

		# Store entry values
		for key, widget in self.entries.items():
			if isinstance(widget, tk.Text):
				self.original_data[key] = widget.get("1.0", "end").strip()
			else:
				self.original_data[key] = widget.get()

		# Store checkbox values
		for key, var in self.checks.items():
			self.original_data[key] = var.get()

	def track_field_changes(self):
		"""Track what fields have changed"""
		changes = {}

		# Check entry changes
		for key, widget in self.entries.items():
			if isinstance(widget, tk.Text):
				current_value = widget.get("1.0", "end").strip()
			else:
				current_value = widget.get()

			original_value = self.original_data.get(key, "")
			if current_value != original_value:
				changes[key] = (original_value, current_value)

		# Check checkbox changes
		for key, var in self.checks.items():
			current_value = var.get()
			original_value = self.original_data.get(key, False)
			if current_value != original_value:
				changes[key] = (original_value, current_value)

		return changes

	def setup_enter_navigation(self):
		"""Setup Enter key to move to next field (like RBase 4.5p)"""
		# Get all entry widgets in logical order
		entry_order = []

		# Define the field order for vendor form
		field_order = [
			'reservation_date', 'first_show', 'last_show_attended',
			'first_name', 'last_name', 'business_name',
			'address', 'city', 'state', 'zip_code',
			'phone', 'email',
			'island', 'row', 'table_numbers',
			'six_ft_gun', 'six_ft_knife', 'six_ft_display', 'six_ft_nonrelated', 'six_ft_rollover',
			'eight_ft_gun', 'eight_ft_knife', 'eight_ft_display', 'eight_ft_nonrelated', 'eight_ft_rollover',
			'total_due', 'amount_paid', 'receipt_number', 'check_number', 'taca_amount'
		]

		# Build entry order list
		for field_name in field_order:
			if field_name in self.entries:
				widget = self.entries[field_name]
				if hasattr(widget, 'focus'):  # Make sure it's a focusable widget
					entry_order.append(widget)

		# Add notes text widget at the end
		if 'notes' in self.entries:
			entry_order.append(self.entries['notes'])

		# Bind Enter key to each entry
		for i, entry in enumerate(entry_order):
			def make_enter_handler(current_index):
				def on_enter(event):
					# Move to next field, or wrap to first if at end
					next_index = (current_index + 1) % len(entry_order)
					next_widget = entry_order[next_index]

					# Focus next widget
					next_widget.focus()

					# Select all text if it's an Entry widget
					if hasattr(next_widget, 'select_range'):
						next_widget.select_range(0, tk.END)
					elif hasattr(next_widget, 'tag_add'):  # Text widget
						next_widget.tag_add(tk.SEL, "1.0", tk.END)

					return "break"  # Prevent default Enter behavior

				return on_enter

			# Bind Enter key
			entry.bind('<Return>', make_enter_handler(i))

			# Also bind Shift+Enter to go to previous field
			def make_shift_enter_handler(current_index):
				def on_shift_enter(event):
					prev_index = (current_index - 1) % len(entry_order)
					prev_widget = entry_order[prev_index]
					prev_widget.focus()
					if hasattr(prev_widget, 'select_range'):
						prev_widget.select_range(0, tk.END)
					return "break"

				return on_shift_enter

			entry.bind('<Shift-Return>', make_shift_enter_handler(i))

		self.setup_enter_navigation()