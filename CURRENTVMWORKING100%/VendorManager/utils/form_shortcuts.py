import tkinter as tk
from tkinter import messagebox
from functools import partial


class FormShortcuts:
	"""
	Enhanced keyboard shortcuts system for forms
	"""

	def __init__(self, form_window, form_type="Generic"):
		self.form_window = form_window
		self.form_type = form_type
		self.shortcuts_enabled = True
		self.field_navigation_order = []
		self.current_field_index = 0
		self.shortcuts_help_window = None

		# Default shortcuts - can be customized per form
		self.shortcuts = {
			# File operations
			'<Control-s>': ('Save', self.save_form),
			'<Control-S>': ('Save', self.save_form),
			'<Control-d>': ('Delete', self.delete_form),
			'<Control-D>': ('Delete', self.delete_form),
			'<Control-p>': ('Print', self.print_form),
			'<Control-P>': ('Print', self.print_form),
			'<Control-n>': ('New', self.new_form),
			'<Control-N>': ('New', self.new_form),

			# Navigation
			'<Tab>': ('Next Field', self.next_field),
			'<Return>': ('Next Field', self.next_field),  # Enter moves to next field
			'<Shift-Tab>': ('Previous Field', self.previous_field),
			'<Shift-Return>': ('Previous Field', self.previous_field),  # Shift+Enter goes back
			'<Control-Tab>': ('Next Section', self.next_section),
			'<Control-Shift-Tab>': ('Previous Section', self.previous_section),

			# Quick actions
			'<F1>': ('Help', self.show_help),
			'<F5>': ('Refresh', self.refresh_form),
			'<F12>': ('Show Shortcuts', self.show_shortcuts),
			'<Escape>': ('Cancel/Close', self.cancel_form),

			# Quick field access (F keys)
			'<F2>': ('Quick Field 1', lambda: self.jump_to_field(0)),
			'<F3>': ('Quick Field 2', lambda: self.jump_to_field(1)),
			'<F4>': ('Quick Field 3', lambda: self.jump_to_field(2)),

			# Text editing shortcuts
			'<Control-a>': ('Select All', self.select_all),
			'<Control-A>': ('Select All', self.select_all),
			'<Control-c>': ('Copy', self.copy_field),
			'<Control-C>': ('Copy', self.copy_field),
			'<Control-v>': ('Paste', self.paste_field),
			'<Control-V>': ('Paste', self.paste_field),
			'<Control-x>': ('Cut', self.cut_field),
			'<Control-X>': ('Cut', self.cut_field),

			# Form specific shortcuts
			'<Control-r>': ('Calculate Total', self.calculate_total),
			'<Control-R>': ('Calculate Total', self.calculate_total),
			'<Control-f>': ('Find/Search', self.focus_search),
			'<Control-F>': ('Find/Search', self.focus_search),
		}

		# Vendor form specific shortcuts
		if form_type == "Vendor":
			self.shortcuts.update({
				'<Control-1>': ('Tables 6ft', self.focus_six_ft),
				'<Control-2>': ('Tables 8ft', self.focus_eight_ft),
				'<Control-3>': ('Location', self.focus_location),
				'<Control-4>': ('Payment', self.focus_payment),
				'<Control-e>': ('Toggle Electricity', self.toggle_electricity),
				'<Control-E>': ('Toggle Electricity', self.toggle_electricity),
				'<Control-t>': ('Toggle TACA', self.toggle_taca),
				'<Control-T>': ('Toggle TACA', self.toggle_taca),
			})

		# Mailout form specific shortcuts
		elif form_type == "Mailout":
			self.shortcuts.update({
				'<Control-l>': ('Print Labels', self.print_labels),
				'<Control-L>': ('Print Labels', self.print_labels),
				'<Control-e>': ('Export List', self.export_mailouts),
				'<Control-E>': ('Export List', self.export_mailouts),
			})

		self.setup_shortcuts()
		self.create_shortcuts_overlay()

	def setup_shortcuts(self):
		"""Bind all keyboard shortcuts to the form window"""
		for key_combo, (description, callback) in self.shortcuts.items():
			try:
				self.form_window.bind(key_combo, lambda event, cb=callback: self.execute_shortcut(cb))
			except Exception as e:
				print(f"[WARNING] Failed to bind shortcut {key_combo}: {e}")

	def execute_shortcut(self, callback):
		"""Execute a shortcut callback with error handling"""
		if not self.shortcuts_enabled:
			return "break"

		try:
			result = callback()
			return "break"  # Prevent default handling
		except Exception as e:
			print(f"[ERROR] Shortcut execution failed: {e}")
			return "break"

	def set_field_navigation_order(self, field_list):
		"""Set the tab order for form fields"""
		self.field_navigation_order = field_list
		self.current_field_index = 0

	def next_field(self):
		"""Navigate to next field in tab order"""
		if not self.field_navigation_order:
			return

		self.current_field_index = (self.current_field_index + 1) % len(self.field_navigation_order)
		self.focus_field(self.current_field_index)

	def previous_field(self):
		"""Navigate to previous field in tab order"""
		if not self.field_navigation_order:
			return

		self.current_field_index = (self.current_field_index - 1) % len(self.field_navigation_order)
		self.focus_field(self.current_field_index)

	def focus_field(self, index):
		"""Focus on a specific field by index"""
		if 0 <= index < len(self.field_navigation_order):
			field = self.field_navigation_order[index]
			if hasattr(field, 'focus'):
				field.focus()
				if hasattr(field, 'select_range'):
					field.select_range(0, tk.END)

	def jump_to_field(self, index):
		"""Jump to a specific field (for F-key shortcuts)"""
		if hasattr(self.form_window, 'entries'):
			entries = list(self.form_window.entries.values())
			if 0 <= index < len(entries):
				entries[index].focus()
				if hasattr(entries[index], 'select_range'):
					entries[index].select_range(0, tk.END)

	def next_section(self):
		"""Jump to next logical section of form"""
		# This would be customized per form type
		if self.form_type == "Vendor":
			self.focus_next_vendor_section()
		elif self.form_type == "Mailout":
			self.focus_next_mailout_section()

	def previous_section(self):
		"""Jump to previous logical section of form"""
		# This would be customized per form type
		if self.form_type == "Vendor":
			self.focus_previous_vendor_section()
		elif self.form_type == "Mailout":
			self.focus_previous_mailout_section()

	# Form action shortcuts
	def save_form(self):
		"""Save the current form"""
		if hasattr(self.form_window, 'save_vendor'):
			self.form_window.save_vendor()
		elif hasattr(self.form_window, 'save_mailout'):
			self.form_window.save_mailout()
		else:
			self.show_temporary_message("Save function not available")

	def delete_form(self):
		"""Delete current form/record"""
		if hasattr(self.form_window, 'delete_vendor'):
			result = messagebox.askyesno("Confirm Delete",
										 "Delete this record? This cannot be undone.")
			if result:
				self.form_window.delete_vendor()
		elif hasattr(self.form_window, 'delete_mailout'):
			result = messagebox.askyesno("Confirm Delete",
										 "Delete this record? This cannot be undone.")
			if result:
				self.form_window.delete_mailout()
		else:
			self.show_temporary_message("Delete function not available")

	def print_form(self):
		"""Print current form"""
		if hasattr(self.form_window, 'print_vendor'):
			self.form_window.print_vendor()
		else:
			self.show_temporary_message("Print function not available")

	def new_form(self):
		"""Create new form instance"""
		self.show_temporary_message("New form: Use Add button in main window")

	def refresh_form(self):
		"""Refresh form data"""
		if hasattr(self.form_window, 'load_vendor_data'):
			self.form_window.load_vendor_data()
			self.show_temporary_message("Form refreshed")
		elif hasattr(self.form_window, 'load_mailout_data'):
			self.form_window.load_mailout_data()
			self.show_temporary_message("Form refreshed")

	def cancel_form(self):
		"""Cancel/close form"""
		if hasattr(self.form_window, 'destroy'):
			result = messagebox.askyesno("Close Form",
										 "Close form? Any unsaved changes will be lost.")
			if result:
				self.form_window.destroy()

	# Text editing shortcuts
	def select_all(self):
		"""Select all text in focused field"""
		focused = self.form_window.focus_get()
		if hasattr(focused, 'select_range'):
			focused.select_range(0, tk.END)
		elif hasattr(focused, 'tag_add'):  # Text widget
			focused.tag_add(tk.SEL, "1.0", tk.END)

	def copy_field(self):
		"""Copy selected text"""
		try:
			self.form_window.clipboard_clear()
			self.form_window.clipboard_append(self.form_window.selection_get())
		except:
			pass  # No selection

	def paste_field(self):
		"""Paste from clipboard"""
		try:
			focused = self.form_window.focus_get()
			if hasattr(focused, 'insert'):
				text = self.form_window.clipboard_get()
				if hasattr(focused, 'selection_present') and focused.selection_present():
					focused.delete(tk.SEL_FIRST, tk.SEL_LAST)
				focused.insert(tk.INSERT, text)
		except:
			pass

	def cut_field(self):
		"""Cut selected text"""
		try:
			focused = self.form_window.focus_get()
			if hasattr(focused, 'selection_present') and focused.selection_present():
				self.copy_field()
				focused.delete(tk.SEL_FIRST, tk.SEL_LAST)
		except:
			pass

	# Vendor-specific shortcuts
	def focus_six_ft(self):
		"""Focus on 6ft tables section"""
		if hasattr(self.form_window, 'entries'):
			six_ft_fields = ['six_ft_gun', 'six_ft_knife', 'six_ft_display', 'six_ft_nonrelated']
			for field in six_ft_fields:
				if field in self.form_window.entries:
					self.form_window.entries[field].focus()
					break

	def focus_eight_ft(self):
		"""Focus on 8ft tables section"""
		if hasattr(self.form_window, 'entries'):
			eight_ft_fields = ['eight_ft_gun', 'eight_ft_knife', 'eight_ft_display', 'eight_ft_nonrelated']
			for field in eight_ft_fields:
				if field in self.form_window.entries:
					self.form_window.entries[field].focus()
					break

	def focus_location(self):
		"""Focus on location fields"""
		if hasattr(self.form_window, 'entries'):
			location_fields = ['island', 'row', 'table_numbers']
			for field in location_fields:
				if field in self.form_window.entries:
					self.form_window.entries[field].focus()
					break

	def focus_payment(self):
		"""Focus on payment fields"""
		if hasattr(self.form_window, 'entries'):
			payment_fields = ['total_due', 'amount_paid', 'receipt_number']
			for field in payment_fields:
				if field in self.form_window.entries:
					self.form_window.entries[field].focus()
					break

	def toggle_electricity(self):
		"""Toggle electricity checkbox"""
		if hasattr(self.form_window, 'checks') and 'electricity' in self.form_window.checks:
			current = self.form_window.checks['electricity'].get()
			self.form_window.checks['electricity'].set(not current)
			if hasattr(self.form_window, 'update_total_due'):
				self.form_window.update_total_due()
			self.show_temporary_message(f"Electricity: {'ON' if not current else 'OFF'}")

	def toggle_taca(self):
		"""Toggle TACA membership checkbox"""
		if hasattr(self.form_window, 'checks') and 'taca_member' in self.form_window.checks:
			current = self.form_window.checks['taca_member'].get()
			self.form_window.checks['taca_member'].set(not current)
			if hasattr(self.form_window, 'toggle_taca_paid'):
				self.form_window.toggle_taca_paid()
			self.show_temporary_message(f"TACA Member: {'YES' if not current else 'NO'}")

	def calculate_total(self):
		"""Recalculate form totals"""
		if hasattr(self.form_window, 'update_total_due'):
			self.form_window.update_total_due()
			self.show_temporary_message("Total recalculated")

	def focus_search(self):
		"""Focus on search field if available"""
		if hasattr(self.form_window, 'search_var'):
			# This would focus on main window search - needs implementation
			self.show_temporary_message("Return to main window to search")

	# Mailout-specific shortcuts
	def print_labels(self):
		"""Print mailing labels"""
		if hasattr(self.form_window, 'print_labels'):
			self.form_window.print_labels()

	def export_mailouts(self):
		"""Export mailout list"""
		if hasattr(self.form_window, 'export_list'):
			self.form_window.export_list()

	# Vendor section navigation
	def focus_next_vendor_section(self):
		"""Navigate to next vendor form section"""
		sections = ['name', 'location', 'tables', 'payment', 'options']
		# Implementation would jump between logical sections
		self.show_temporary_message("Next section")

	def focus_previous_vendor_section(self):
		"""Navigate to previous vendor form section"""
		self.show_temporary_message("Previous section")

	# Mailout section navigation
	def focus_next_mailout_section(self):
		"""Navigate to next mailout form section"""
		sections = ['name', 'address', 'contact']
		self.show_temporary_message("Next section")

	def focus_previous_mailout_section(self):
		"""Navigate to previous mailout form section"""
		self.show_temporary_message("Previous section")

	def show_help(self):
		"""Show form-specific help"""
		help_text = f"""
{self.form_type} Form Help

Navigation:
• Tab/Shift+Tab: Move between fields
• Ctrl+Tab: Jump between sections
• F2-F4: Quick field access
• Esc: Close form

Actions:
• Ctrl+S: Save
• Ctrl+D: Delete  
• Ctrl+P: Print
• Ctrl+R: Recalculate totals
• F5: Refresh form

Edit:
• Ctrl+A: Select all
• Ctrl+C/V/X: Copy/Paste/Cut

Help:
• F1: This help
• F12: Show all shortcuts
        """

		if self.form_type == "Vendor":
			help_text += """
Vendor Specific:
• Ctrl+1: Focus 6ft tables
• Ctrl+2: Focus 8ft tables  
• Ctrl+3: Focus location
• Ctrl+4: Focus payment
• Ctrl+E: Toggle electricity
• Ctrl+T: Toggle TACA
            """
		elif self.form_type == "Mailout":
			help_text += """
Mailout Specific:
• Ctrl+L: Print labels
• Ctrl+E: Export list
            """

		messagebox.showinfo(f"{self.form_type} Help", help_text.strip())

	def show_shortcuts(self):
		"""Show shortcuts overlay window"""
		if self.shortcuts_help_window and self.shortcuts_help_window.winfo_exists():
			self.shortcuts_help_window.lift()
			return

		self.shortcuts_help_window = tk.Toplevel(self.form_window)
		self.shortcuts_help_window.title(f"{self.form_type} Keyboard Shortcuts")
		self.shortcuts_help_window.geometry("500x600")
		self.shortcuts_help_window.configure(bg="#1e1e1e")
		self.shortcuts_help_window.transient(self.form_window)

		# Create scrollable text widget
		text_frame = tk.Frame(self.shortcuts_help_window, bg="#1e1e1e")
		text_frame.pack(fill="both", expand=True, padx=20, pady=20)

		text_widget = tk.Text(text_frame, bg="#2e2e2e", fg="white",
							  font=("Consolas", 10), wrap="word")
		scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
		text_widget.configure(yscrollcommand=scrollbar.set)

		text_widget.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")

		# Add shortcuts content
		shortcuts_text = f"{self.form_type} Form Keyboard Shortcuts\n{'=' * 50}\n\n"

		categories = {
			"File Operations": [],
			"Navigation": [],
			"Quick Actions": [],
			"Text Editing": [],
			f"{self.form_type} Specific": []
		}

		# Categorize shortcuts
		for key, (desc, _) in self.shortcuts.items():
			if key in ['<Control-s>', '<Control-S>', '<Control-d>', '<Control-D>',
					   '<Control-p>', '<Control-P>', '<Control-n>', '<Control-N>']:
				categories["File Operations"].append((key, desc))
			elif key in ['<Tab>', '<Shift-Tab>', '<Control-Tab>', '<Control-Shift-Tab>']:
				categories["Navigation"].append((key, desc))
			elif key in ['<F1>', '<F5>', '<F12>', '<Escape>', '<F2>', '<F3>', '<F4>']:
				categories["Quick Actions"].append((key, desc))
			elif key in ['<Control-a>', '<Control-A>', '<Control-c>', '<Control-C>',
						 '<Control-v>', '<Control-V>', '<Control-x>', '<Control-X>']:
				categories["Text Editing"].append((key, desc))
			else:
				categories[f"{self.form_type} Specific"].append((key, desc))

		# Build text content
		for category, shortcuts in categories.items():
			if shortcuts:
				shortcuts_text += f"{category}:\n{'-' * 20}\n"
				for key, desc in shortcuts:
					# Clean up key display
					key_display = key.replace('<', '').replace('>', '').replace('Control-', 'Ctrl+')
					shortcuts_text += f"{key_display:<20} {desc}\n"
				shortcuts_text += "\n"

		text_widget.insert("1.0", shortcuts_text)
		text_widget.configure(state="disabled")

		# Close button
		tk.Button(self.shortcuts_help_window, text="Close",
				  command=self.shortcuts_help_window.destroy,
				  bg="#ffdf00", fg="black", font=("Segoe UI", 10)).pack(pady=10)

	def create_shortcuts_overlay(self):
		"""Create a temporary shortcuts overlay"""
		self.overlay = None

	def show_temporary_message(self, message, duration=2000):
		"""Show temporary status message"""
		if hasattr(self.form_window, 'master'):
			# Create temporary label
			temp_label = tk.Label(self.form_window, text=message,
								  bg="#ffdf00", fg="black", font=("Segoe UI", 10, "bold"),
								  relief="solid", bd=1, padx=10, pady=5)
			temp_label.place(x=10, y=10)

			# Remove after duration
			self.form_window.after(duration, temp_label.destroy)

	def enable_shortcuts(self):
		"""Enable keyboard shortcuts"""
		self.shortcuts_enabled = True

	def disable_shortcuts(self):
		"""Disable keyboard shortcuts temporarily"""
		self.shortcuts_enabled = False


class VendorFormShortcuts(FormShortcuts):
	"""Specialized shortcuts for vendor forms"""

	def __init__(self, form_window):
		super().__init__(form_window, "Vendor")

		# Set vendor-specific field navigation order
		vendor_fields = [
			'first_name', 'last_name', 'business_name',
			'phone', 'email', 'address', 'city', 'state', 'zip_code',
			'island', 'row', 'table_numbers',
			'six_ft_gun', 'six_ft_knife', 'six_ft_display', 'six_ft_nonrelated',
			'eight_ft_gun', 'eight_ft_knife', 'eight_ft_display', 'eight_ft_nonrelated',
			'total_due', 'amount_paid', 'receipt_number'
		]

		# Get actual field references if they exist
		if hasattr(form_window, 'entries'):
			field_refs = []
			for field_name in vendor_fields:
				if field_name in form_window.entries:
					field_refs.append(form_window.entries[field_name])
			self.set_field_navigation_order(field_refs)

	def focus_next_vendor_section(self):
		"""Navigate to next vendor form section"""
		# Define vendor form sections
		sections = {
			0: ['first_name', 'last_name', 'business_name'],  # Personal Info
			1: ['phone', 'email', 'address', 'city', 'state', 'zip_code'],  # Contact
			2: ['island', 'row', 'table_numbers'],  # Location
			3: ['six_ft_gun', 'six_ft_knife', 'six_ft_display', 'six_ft_nonrelated'],  # 6ft Tables
			4: ['eight_ft_gun', 'eight_ft_knife', 'eight_ft_display', 'eight_ft_nonrelated'],  # 8ft Tables
			5: ['total_due', 'amount_paid', 'receipt_number']  # Payment
		}

		# Find current section and jump to next
		current_section = getattr(self, '_current_section', 0)
		next_section = (current_section + 1) % len(sections)

		if hasattr(self.form_window, 'entries'):
			for field_name in sections[next_section]:
				if field_name in self.form_window.entries:
					self.form_window.entries[field_name].focus()
					self._current_section = next_section
					self.show_temporary_message(f"Section: {self._get_section_name(next_section)}")
					break

	def focus_previous_vendor_section(self):
		"""Navigate to previous vendor form section"""
		current_section = getattr(self, '_current_section', 0)
		prev_section = (current_section - 1) % 6
		self._current_section = prev_section
		self.focus_next_vendor_section()  # Reuse logic

	def _get_section_name(self, section_num):
		"""Get human-readable section name"""
		names = {
			0: "Personal Info",
			1: "Contact Info",
			2: "Location",
			3: "6ft Tables",
			4: "8ft Tables",
			5: "Payment"
		}
		return names.get(section_num, "Unknown")


class MailoutFormShortcuts(FormShortcuts):
	"""Specialized shortcuts for mailout forms"""

	def __init__(self, form_window):
		super().__init__(form_window, "Mailout")

		# Set mailout-specific field navigation order
		mailout_fields = [
			'name', 'address', 'city', 'state', 'zip_code', 'phone', 'email'
		]

		# Get actual field references if they exist
		if hasattr(form_window, 'entries'):
			field_refs = []
			for field_name in mailout_fields:
				if field_name in form_window.entries:
					field_refs.append(form_window.entries[field_name])
			self.set_field_navigation_order(field_refs)

	def focus_next_mailout_section(self):
		"""Navigate to next mailout form section"""
		sections = {
			0: ['name'],  # Name
			1: ['address', 'city', 'state', 'zip_code'],  # Address
			2: ['phone', 'email']  # Contact
		}

		current_section = getattr(self, '_current_section', 0)
		next_section = (current_section + 1) % len(sections)

		if hasattr(self.form_window, 'entries'):
			for field_name in sections[next_section]:
				if field_name in self.form_window.entries:
					self.form_window.entries[field_name].focus()
					self._current_section = next_section
					section_names = {0: "Name", 1: "Address", 2: "Contact"}
					self.show_temporary_message(f"Section: {section_names[next_section]}")
					break


# Factory function to create appropriate shortcuts
def create_form_shortcuts(form_window, form_type):
	"""Create appropriate shortcuts instance for form type"""
	if form_type.lower() == "vendor":
		return VendorFormShortcuts(form_window)
	elif form_type.lower() == "mailout":
		return MailoutFormShortcuts(form_window)
	else:
		return FormShortcuts(form_window, form_type)


# Decorator to add shortcuts to form classes
def add_keyboard_shortcuts(form_type):
	"""Decorator to add keyboard shortcuts to form classes"""

	def decorator(form_class):
		original_init = form_class.__init__

		def new_init(self, *args, **kwargs):
			original_init(self, *args, **kwargs)
			# Add shortcuts after form is initialized
			self.keyboard_shortcuts = create_form_shortcuts(self, form_type)

		form_class.__init__ = new_init
		return form_class

	return decorator


# Context manager for temporarily disabling shortcuts
class ShortcutsDisabled:
	"""Context manager to temporarily disable shortcuts"""

	def __init__(self, shortcuts_instance):
		self.shortcuts = shortcuts_instance
		self.was_enabled = shortcuts_instance.shortcuts_enabled

	def __enter__(self):
		self.shortcuts.disable_shortcuts()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.was_enabled:
			self.shortcuts.enable_shortcuts()


# Helper function to show all available shortcuts
def show_all_shortcuts_help(parent_window):
	"""Show comprehensive shortcuts help for all forms"""
	help_window = tk.Toplevel(parent_window)
	help_window.title("All Keyboard Shortcuts")
	help_window.geometry("700x800")
	help_window.configure(bg="#1e1e1e")

	# Create notebook for different sections
	notebook = ttk.Notebook(help_window)
	notebook.pack(fill="both", expand=True, padx=20, pady=20)

	# General shortcuts
	general_frame = tk.Frame(notebook, bg="#1e1e1e")
	notebook.add(general_frame, text="General")

	general_text = tk.Text(general_frame, bg="#2e2e2e", fg="white",
						   font=("Consolas", 10), wrap="word")
	general_text.pack(fill="both", expand=True, padx=10, pady=10)

	general_shortcuts = """
GENERAL SHORTCUTS (All Windows)
===============================

File Operations:
Ctrl+S          Save current form/data
Ctrl+D          Delete current record  
Ctrl+P          Print current view
Ctrl+N          New record (return to main window)

Navigation:
Tab             Next field
Shift+Tab       Previous field
Ctrl+Tab        Next section
Ctrl+Shift+Tab  Previous section
F2-F4           Quick field access

Quick Actions:
F1              Show help
F5              Refresh/reload data
F12             Show keyboard shortcuts
Escape          Cancel/close current window
Ctrl+F          Focus search (main window)

Text Editing:
Ctrl+A          Select all text
Ctrl+C          Copy selected text
Ctrl+V          Paste from clipboard
Ctrl+X          Cut selected text
    """

	general_text.insert("1.0", general_shortcuts.strip())
	general_text.configure(state="disabled")

	# Vendor shortcuts
	vendor_frame = tk.Frame(notebook, bg="#1e1e1e")
	notebook.add(vendor_frame, text="Vendor Forms")

	vendor_text = tk.Text(vendor_frame, bg="#2e2e2e", fg="white",
						  font=("Consolas", 10), wrap="word")
	vendor_text.pack(fill="both", expand=True, padx=10, pady=10)

	vendor_shortcuts = """
VENDOR FORM SHORTCUTS
====================

Quick Navigation:
Ctrl+1          Focus 6ft tables section
Ctrl+2          Focus 8ft tables section
Ctrl+3          Focus location fields
Ctrl+4          Focus payment fields

Quick Toggles:
Ctrl+E          Toggle electricity option
Ctrl+T          Toggle TACA membership

Calculations:
Ctrl+R          Recalculate total due

Section Navigation:
Ctrl+Tab        Next section:
                Personal Info → Contact → Location → 
                6ft Tables → 8ft Tables → Payment

Field Order:
Tab navigates through fields in logical order:
1. First Name → Last Name → Business Name
2. Phone → Email → Address → City → State → ZIP
3. Island → Row → Table Numbers  
4. 6ft tables: Gun → Knife → Display → Non-related
5. 8ft tables: Gun → Knife → Display → Non-related
6. Total Due → Amount Paid → Receipt Number
    """

	vendor_text.insert("1.0", vendor_shortcuts.strip())
	vendor_text.configure(state="disabled")

	# Mailout shortcuts
	mailout_frame = tk.Frame(notebook, bg="#1e1e1e")
	notebook.add(mailout_frame, text="Mailout Forms")

	mailout_text = tk.Text(mailout_frame, bg="#2e2e2e", fg="white",
						   font=("Consolas", 10), wrap="word")
	mailout_text.pack(fill="both", expand=True, padx=10, pady=10)

	mailout_shortcuts = """
MAILOUT FORM SHORTCUTS
=====================

Quick Actions:
Ctrl+L          Print mailing labels
Ctrl+E          Export mailout list

Section Navigation:
Ctrl+Tab        Next section:
                Name → Address → Contact Info

Field Order:
Tab navigates through fields:
1. Name
2. Address → City → State → ZIP Code
3. Phone → Email

Address Validation:
- State field automatically converts to uppercase
- ZIP code validates 5-digit format
- Phone number auto-formats as XXX-XXX-XXXX
    """

	mailout_text.insert("1.0", mailout_shortcuts.strip())
	mailout_text.configure(state="disabled")

	# Close button
	tk.Button(help_window, text="Close", command=help_window.destroy,
			  bg="#ffdf00", fg="black", font=("Segoe UI", 12, "bold")).pack(pady=10)