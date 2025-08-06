import tkinter as tk
from tkinter import messagebox
from models import Session
from models.mailout import Mailout
import re
import os
import sys
from utils.enhanced_logger import get_enhanced_logger, FormSession
from utils.form_shortcuts import FormShortcuts
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
		label.pack(fill='x', expand=True)

	def hide(self, _):
		if self.tipwindow:
			self.tipwindow.destroy()
			self.tipwindow = None


class MailoutForm(tk.Toplevel):
	def __init__(self, parent, user, mailout_id=None, refresh_callback=None):
		super().__init__(parent)
		self.user = user
		self.mailout_id = mailout_id
		self.refresh_callback = refresh_callback
		self.mailout = None
		self.entries = {}
		self.icons = {}

		# ADD: Enhanced logging
		self.logger = get_enhanced_logger(user)
		self.start_time = datetime.now()
		self.original_data = {}

		self.title("Mailout Entry Form")
		self.configure(bg="#1e1e1e")
		self.geometry("800x400")

		if mailout_id:
			session = Session()
			self.mailout = session.query(Mailout).filter_by(id=mailout_id).first()
			session.close()

			# LOG: Mailout form opened
			if self.mailout:
				mailout_data = {
					'name': self.mailout.name,
					'city': self.mailout.city,
					'id': self.mailout.id
				}
				self.logger.log_double_click("Mailout", self.mailout.id, mailout_data, "Form opened")

		self.build_form()
		self.build_button_bar()

		# ADD: Keyboard shortcuts for mailout
		self.keyboard_shortcuts = FormShortcuts(self)

		if self.mailout:
			self.load_mailout_data()


	def build_form(self):
		main = tk.Frame(self, bg="#1e1e1e")
		main.pack(fill="both", expand=True, padx=20, pady=20)

		def label_entry(row, label, key, width=25):
			wrapper = tk.Frame(row, bg="#1e1e1e")
			wrapper.pack(fill='x', expand=True, pady=5)

			tk.Label(wrapper, font=("Roboto", 14), text=label, bg="#1e1e1e", fg="#ffdf00", width=15, anchor="w").pack(
				side="left")

			entry = tk.Entry(wrapper, font=("Roboto", 14), width=width, bg="#2e2e2e", fg="white",
							 insertbackground="white", justify="left")

			# Live phone formatting
			if key == "phone":
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

			# Insert existing value if editing
			if self.mailout and hasattr(self.mailout, key):
				val = getattr(self.mailout, key)
				if val:
					if key == "phone":
						# Format phone number for display
						formatted_phone = re.sub(r"(\d{3})(\d{3})(\d{4})", r"\1-\2-\3", val)
						entry.insert(0, formatted_phone)
					else:
						entry.insert(0, str(val))

			entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
			self.entries[key] = entry

		# Form fields in specified order
		label_entry(main, "Name:", "name")
		label_entry(main, "Address:", "address")

		# City, State, ZIP row
		address_row = tk.Frame(main, bg="#1e1e1e")
		address_row.pack(fill='x', expand=True, pady=5)

		tk.Label(address_row, font=("Roboto", 14), text="City:", bg="#1e1e1e", fg="#ffdf00", width=15, anchor="w").pack(
			side="left")
		city_entry = tk.Entry(address_row, font=("Roboto", 14), width=20, bg="#2e2e2e", fg="white",
							  insertbackground="white")
		city_entry.pack(side="left", padx=(10, 5))
		self.entries["city"] = city_entry

		tk.Label(address_row, font=("Roboto", 14), text="State:", bg="#1e1e1e", fg="#ffdf00").pack(side="left",
																								   padx=(10, 5))
		state_entry = tk.Entry(address_row, font=("Roboto", 14), width=3, bg="#2e2e2e", fg="white",
							   insertbackground="white")
		state_entry.pack(side="left", padx=(0, 5))
		self.entries["state"] = state_entry

		tk.Label(address_row, font=("Roboto", 14), text="ZIP:", bg="#1e1e1e", fg="#ffdf00").pack(side="left",
																								 padx=(10, 5))
		zip_entry = tk.Entry(address_row, font=("Roboto", 14), width=10, bg="#2e2e2e", fg="white",
							 insertbackground="white")
		zip_entry.pack(side="left")
		self.entries["zip_code"] = zip_entry

		# Load existing address data if editing
		if self.mailout:
			if self.mailout.city:
				city_entry.insert(0, self.mailout.city)
			if self.mailout.state:
				state_entry.insert(0, self.mailout.state)
			if self.mailout.zip_code:
				zip_entry.insert(0, self.mailout.zip_code)

		label_entry(main, "Phone:", "phone")
		label_entry(main, "Email:", "email")

	def build_button_bar(self):
		bar = tk.Frame(self, bg="#1e1e1e")
		bar.pack(fill='x', expand=True, pady=10)

		# Support both PyInstaller and dev mode for icons
		if hasattr(sys, '_MEIPASS'):
			icon_dir = os.path.join(sys._MEIPASS, "converted_icons")
		else:
			icon_dir = os.path.abspath("converted_icons")

		buttons = [
			("save", self.save_mailout),
			("delete", self.delete_mailout),
		]

		tooltips = {
			"save": "Save Mailout Entry",
			"delete": "Delete Mailout Entry",
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
				# Fallback to text buttons if icons fail
				btn = tk.Button(bar, font=("Roboto", 12), text=tooltips[name], command=cmd, bg="#2e2e2e", fg="white")
				btn.pack(fill='x', expand=True, side="left", padx=2)

	def save_mailout(self):
		# Track changes
		field_changes = {}
		for key, entry in self.entries.items():
			current_val = entry.get().strip()
			original_val = self.original_data.get(key, "")
			if current_val != original_val:
				field_changes[key] = (original_val, current_val)

		session = Session()
		is_new = not self.mailout

		if not self.mailout:
			self.mailout = Mailout()

		# Validate required fields
		if not self.entries["name"].get().strip():
			messagebox.showerror("Validation Error", "Name is required.")
			return

		if not self.entries["address"].get().strip():
			messagebox.showerror("Validation Error", "Address is required.")
			return

		if not self.entries["city"].get().strip():
			messagebox.showerror("Validation Error", "City is required.")
			return

		# Validate state (2 letters)
		state_val = self.entries["state"].get().strip().upper()
		if not state_val or not re.fullmatch(r"[A-Z]{2}", state_val):
			messagebox.showerror("Validation Error", "State must be 2 uppercase letters.")
			return

		# Validate ZIP code (5 digits)
		zip_val = self.entries["zip_code"].get().strip()
		if not zip_val or not re.fullmatch(r"\d{5}", zip_val):
			messagebox.showerror("Validation Error", "ZIP Code must be 5 digits.")
			return

		duration = (datetime.now() - self.start_time).total_seconds()
		mailout_data = {
			'name': self.mailout.name,
			'city': self.mailout.city,
			'id': getattr(self.mailout, 'id', None)
		}

		action = "Created" if is_new else "Updated"
		self.logger.log_form_interaction(
			form_type="Mailout",
			action=action,
			form_data=mailout_data,
			field_changes=field_changes,
			duration=duration
		)

		# Save all fields
		for key, entry in self.entries.items():
			val = entry.get().strip()

			if key == "state":
				val = val.upper()
			elif key == "phone":
				# Remove formatting from phone number for storage
				val = re.sub(r"\D", "", val) if val else ""
			elif key in ("email",) and not val:
				val = None  # Allow empty email

			setattr(self.mailout, key, val)

		try:
			session.merge(self.mailout)
			session.commit()
			session.close()

			if self.refresh_callback:
				self.refresh_callback()
			self.destroy()

			messagebox.showinfo("Success", "Mailout entry saved successfully.")
		except Exception as e:
			session.rollback()
			session.close()
			messagebox.showerror("Database Error", f"Failed to save mailout entry:\n{e}")

	def delete_mailout(self):
		if self.mailout and messagebox.askyesno("Confirm Delete",
												"Are you sure you want to delete this mailout entry?"):
			session = Session()
			try:
				session.delete(self.mailout)
				session.commit()
				session.close()
				if self.refresh_callback:
					self.refresh_callback()
				self.destroy()
				messagebox.showinfo("Deleted", "Mailout entry deleted successfully.")
			except Exception as e:
				session.rollback()
				session.close()
				messagebox.showerror("Database Error", f"Failed to delete mailout entry:\n{e}")

	def load_mailout_data(self):
		"""Load existing mailout data into form fields."""
		if not self.mailout:
			return

		# Name, address, phone, email are handled in label_entry function
		# City, state, zip are handled in build_form function
		pass

	def setup_enter_navigation(self):
		"""Setup Enter key navigation for mailout form"""
		# Mailout field order
		field_order = ['name', 'address', 'city', 'state', 'zip_code', 'phone', 'email']

		entry_order = []
		for field_name in field_order:
			if field_name in self.entries:
				widget = self.entries[field_name]
				if hasattr(widget, 'focus'):
					entry_order.append(widget)

		# Bind Enter navigation
		for i, entry in enumerate(entry_order):
			def make_enter_handler(current_index):
				def on_enter(event):
					next_index = (current_index + 1) % len(entry_order)
					next_widget = entry_order[next_index]
					next_widget.focus()
					if hasattr(next_widget, 'select_range'):
						next_widget.select_range(0, tk.END)
					return "break"

				return on_enter

			entry.bind('<Return>', make_enter_handler(i))

			# Shift+Enter for previous field
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