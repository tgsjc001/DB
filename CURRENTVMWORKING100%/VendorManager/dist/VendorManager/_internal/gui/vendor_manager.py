import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from models import Session
from models.vendor import Vendor
from gui.vendor_form import VendorForm
from utils.theme import apply_user_theme
from tkinter import scrolledtext
from utils.pricing import calculate_total_due
from utils.color_rules import (
	get_vendor_status, get_vendor_tags, get_vendor_flag_labels,
	get_vendor_priority_tag, get_highlight_tag
)
from utils.export_utils import export_all_vendors_to_single_pdf, export_all_vendors_to_single_txt, EXPORT_DIR


class VendorManagerWindow(tk.Frame):
	def __init__(self, master, user):
		super().__init__(master, bg="#1e1e1e")
		self.master = master
		self.user = user
		self.current_user = user
		self.selected_vendor = None
		self.search_var = tk.StringVar()
		self.filters = {}
		apply_user_theme(self, user)
		print("[DEBUG] VendorManagerWindow __init__ starting")

		# Build the vendor list interface directly (no tabs)
		self.build_vendor_list_ui()

		try:
			self.load_vendors()
		except Exception as e:
			print(f"[ERROR] load_vendors() failed: {e}")
		print("[DEBUG] VendorManagerWindow __init__ complete")

	def build_vendor_list_ui(self):
		print("[DEBUG] build_layout starting")

		control_frame = tk.Frame(self, bg="#1e1e1e")
		control_frame.pack(fill="x", padx=10, pady=10)

		tk.Label(control_frame, text="Search:", fg="#ffdf00", bg="#1e1e1e").pack(side="left")
		search_entry = tk.Entry(control_frame, bg="#2e2e2e", fg="white", textvariable=self.search_var)
		search_entry.pack(side="left", padx=5, fill="x", expand=True)
		search_entry.bind("<Return>", lambda event: self.load_vendors())

		tk.Button(control_frame, text="Search", command=self.load_vendors, bg="#2e2e2e", fg="white").pack(side="left",
																										  padx=5)
		tk.Button(control_frame, text="Advanced Filters", command=self.open_filter_popup, bg="#2e2e2e",
				  fg="white").pack(side="left", padx=5)

		btn_frame = tk.Frame(control_frame, bg="#1e1e1e")
		btn_frame.pack(side="right")
		tk.Button(btn_frame, text="Add Vendor", command=self.add_vendor, bg="#2e2e2e", fg="white").pack(side="left",
																										padx=(0, 10))
		tk.Button(btn_frame, text="Delete Vendor", command=self.delete_selected_vendor, bg="#2e2e2e", fg="white").pack(
			side="left", padx=(10, 0))

		export_frame = tk.Frame(self, bg="#1e1e1e")
		export_frame.pack(fill="x", padx=10, pady=(0, 10))
		tk.Button(export_frame, text="Export All (PDF)", command=self.export_all_to_pdf, bg="#2e2e2e", fg="white").pack(
			side="left", padx=5)
		tk.Button(export_frame, text="Export All (TXT)", command=self.export_all_to_txt, bg="#2e2e2e", fg="white").pack(
			side="left", padx=5)
		tk.Button(export_frame, text="🖸 Check Print", command=self.export_all_vendors_to_print, bg="#2e2e2e",
				  fg="white").pack(side="left", padx=5)
		tk.Button(export_frame, text="Tax Sticker (Preview)", command=self.preview_tax_stickers, bg="#2e2e2e",
				  fg="white").pack(side="left", padx=5)
		tk.Button(export_frame, text="Book Export (Preview)", command=self.preview_book_export,
				  bg="#2e2e2e", fg="white").pack(side="left", padx=5)

		self.tree = ttk.Treeview(self,
								 columns=("name", "location", "phone", "date", "status", "flags"),
								 show="headings")
		self.tree.heading("name", text="name".title(), command=lambda c="name": self.sort_by_column(c, False))
		self.tree.heading("location", text="location".title(),
						  command=lambda c="location": self.sort_by_column(c, False))
		self.tree.heading("phone", text="phone".title(), command=lambda c="phone": self.sort_by_column(c, False))
		self.tree.heading("date", text="date".title(), command=lambda c="date": self.sort_by_column(c, False))
		self.tree.heading("status", text="status".title(), command=lambda c="status": self.sort_by_column(c, False))
		self.tree.heading("flags", text="flags".title(), command=lambda c="flags": self.sort_by_column(c, False))

		style = ttk.Style()
		style.theme_use("default")
		style.configure("Treeview",
						background="#1e1e1e",
						foreground="white",
						rowheight=25,
						fieldbackground="#1e1e1e")
		style.configure("Treeview.Heading",
						background="#2e2e2e",
						foreground="white")
		style.map("Treeview", background=[("selected", "#444444")])

		for col in ("name", "location", "phone", "date", "status", "flags"):
			self.tree.column(col, anchor="center", width=120, stretch=True)

		self.tree.pack(fill="both", expand=True, padx=10, pady=10)
		self.tree.bind("<Double-1>", self.view_vendor)

		# Tag-based row coloring for status highlights
		tag_colors = {
			'light_yellow': ('#ffffcc', 'black'),
			'dark_yellow': ('#ffd700', 'black'),
			"black": ("#000000", "white"),
			"red": ("#ff0000", "white"),
			"dark_red": ("#8B0000", "white"),
			"yellow": ("#ffff00", "black"),
			"pink": ("#ffc0cb", "black"),
			"purple": ("#800080", "white"),
			"gray": ("#808080", "white")
		}
		for tag, (bg, fg) in tag_colors.items():
			self.tree.tag_configure(tag, background=bg, foreground=fg)

		# ADD LEGEND STATUS BAR
		self.build_legend_status_bar()

		print("[DEBUG] build_layout done")

	def build_legend_status_bar(self):
		"""
		Creates a bottom status bar with color legend and flag explanations that wraps based on window size.
		"""
		legend_frame = tk.Frame(self, bg="#2e2e2e")
		legend_frame.pack(fill="x", side="bottom", padx=5, pady=2)

		# Color legend section
		color_frame = tk.Frame(legend_frame, bg="#2e2e2e")
		color_frame.pack(fill="x", pady=2)

		tk.Label(color_frame, text="Colors:", bg="#2e2e2e", fg="white", font=("Arial", 11, "bold")).pack(side="left",
																										 padx=(5, 8))

		# Color indicators with actual colored squares in the specified order
		color_indicators = [
			("#000000", "white", "DB"),  # Double Booked - Black
			("#8B0000", "white", "UP"),  # Unpaid - Dark Red
			("#ff0000", "white", "OP"),  # Overpaid - Light Red
			("#ffffcc", "black", "RTA"),  # RTA - Light Yellow
			("#ffd700", "black", "RTN"),  # RTN - Dark Yellow
			("#800080", "white", "E"),  # Electricity - Purple
			("#008000", "white", "SS")  # Saturday Setup - Green
		]

		colors_container = tk.Frame(color_frame, bg="#2e2e2e")
		colors_container.pack(side="left", fill="x", expand=True)

		for bg_color, text_color, label in color_indicators:
			color_item_frame = tk.Frame(colors_container, bg="#2e2e2e")
			color_item_frame.pack(side="left", padx=3)

			# Create a small colored square
			color_square = tk.Label(color_item_frame, text="  ", bg=bg_color, width=2, height=1)
			color_square.pack(side="left", padx=(0, 2))

			# Add the label next to the square
			label_widget = tk.Label(color_item_frame, text=label, bg="#2e2e2e", fg="white", font=("Arial", 11, "bold"))
			label_widget.pack(side="left")

		# Separator line
		separator_frame = tk.Frame(legend_frame, bg="#666666", height=1)
		separator_frame.pack(fill="x", pady=2)

		# Flag legend section with wrapping
		flag_frame = tk.Frame(legend_frame, bg="#2e2e2e")
		flag_frame.pack(fill="x", pady=2)

		tk.Label(flag_frame, text="Flags:", bg="#2e2e2e", fg="white", font=("Arial", 12, "bold")).pack(anchor="w",
																									   padx=(5, 0))

		# Flags in the specified order
		flag_explanations = [
			"RTA=Rollover April", "RTN=Rollover November", "On RO=On Rollover", "UP=Unpaid",
			"OP=Overpaid", "NS=No Show", "EI=Early In", "SS=Saturday Setup",
			"G=Gun", "K=Knife", "D=Display", "N=Non-related", "R=Rollover Tables"
		]

		# Create a wrapping container for flags
		flags_container = tk.Frame(flag_frame, bg="#2e2e2e")
		flags_container.pack(fill="x", padx=(20, 5), pady=2)

		current_row_frame = tk.Frame(flags_container, bg="#2e2e2e")
		current_row_frame.pack(fill="x")

		# Track approximate width to determine when to wrap
		current_width = 0
		max_width_per_row = 120  # Approximate characters per row before wrapping

		for i, flag_text in enumerate(flag_explanations):
			# Check if we need to wrap to a new line
			if current_width + len(flag_text) > max_width_per_row and current_width > 0:
				current_row_frame = tk.Frame(flags_container, bg="#2e2e2e")
				current_row_frame.pack(fill="x")
				current_width = 0

			flag_label = tk.Label(current_row_frame, text=flag_text, bg="#2e2e2e", fg="#e0e0e0",
								  font=("Arial", 12, "bold"))
			flag_label.pack(side="left", padx=4)

			# Add separator dot if not the last item in a row
			if i < len(flag_explanations) - 1:
				separator_dot = tk.Label(current_row_frame, text="|", bg="#2e2e2e", fg="#999999",
										 font=("Arial", 12, "bold"))
				separator_dot.pack(side="left", padx=2)
				current_width += len(flag_text) + 3  # Account for separator
			else:
				current_width += len(flag_text)

	def sort_by_column(self, col, reverse):
		try:
			data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
			# Try numeric sort if applicable
			try:
				data.sort(key=lambda t: float(t[0].replace('$', '').replace(',', '')), reverse=reverse)
			except ValueError:
				data.sort(key=lambda t: t[0].lower() if isinstance(t[0], str) else t[0], reverse=reverse)

			for index, (_, child) in enumerate(data):
				self.tree.move(child, '', index)
			self.tree.heading(col, command=lambda: self.sort_by_column(col, not reverse))
		except Exception as e:
			print(f"[ERROR] Sorting failed for column '{col}':", e)

	def open_filter_popup(self):
		popup = tk.Toplevel(self)
		popup.title("Advanced Filters")
		popup.geometry("300x400")
		popup.configure(bg="#1e1e1e")

		filter_options = [
			("No Show", "no_show"),
			("TACA Member", "taca_member"),
			("Early In", "early_in"),
			("Saturday Setup", "saturday_setup"),
			("Unpaid", "unpaid"),
			("Overpaid", "overpaid"),
			("Electricity", "electricity"),
			("Rollover April", "rta"),
			("Rollover November", "rtn"),
			("On Rollover", "on_rollover")
		]

		checkbox_frame = tk.Frame(popup, bg="#1e1e1e")
		checkbox_frame.pack(pady=10, fill="both", expand=True)

		for label, key in filter_options:
			var = self.filters.get(key)
			if not var or not hasattr(var, "get"):
				var = tk.BooleanVar()
				self.filters[key] = var
			cb = tk.Checkbutton(checkbox_frame, text=label, variable=var,
								bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
								activebackground="#1e1e1e")
			cb.pack(anchor="w", pady=2)

		tk.Button(popup, text="Apply Filters", command=lambda: [self.load_vendors(), popup.destroy()], bg="#2e2e2e",
				  fg="white").pack(pady=10)
	def load_vendors(self):
		print("[DEBUG] load_vendors called")
		session = Session()
		query = session.query(Vendor)

		term = self.search_var.get().strip()
		print(f"[DEBUG] Search term: '{term}'")

		vendors = query.all()
		if term:
			vendors = [v for v in vendors if self.matches_search(v, term)]

		vendors = self.get_filtered_vendors(vendors)
		set_double_booked_flags(vendors)

		print(f"[DEBUG] {len(vendors)} vendors to display")

		self.tree.delete(*self.tree.get_children())

		for vendor in vendors:
			try:
				name = vendor.business_name.strip() if vendor.business_name else f"{vendor.first_name or ''} {vendor.last_name or ''}".strip()
				location = f"{(vendor.island or '').strip()} {(vendor.row or '').strip()} {(vendor.table_numbers or '').strip()}"
				phone = vendor.phone or ""
				try:
					date = datetime.strptime(vendor.reservation_date, "%Y-%m-%d").strftime("%m/%d/%Y")
				except Exception:
					date = vendor.reservation_date or ""
				status = get_vendor_status(vendor)
				primary_tag = get_highlight_tag(vendor)
				flag_labels = get_vendor_flag_labels(vendor)

				self.tree.insert(
					"", "end",
					iid=str(vendor.id),
					values=(name, location, phone, date, status, ", ".join(flag_labels)),
					tags=(primary_tag,)
				)
			except Exception as e:
				print(f"[ERROR] Failed to insert vendor ID {getattr(vendor, 'id', '?')}: {e}")

		session.close()

	def get_filtered_vendors(self, vendors):
		def is_checked(val):
			return val.get() if hasattr(val, 'get') else val

		filters = self.filters or {}
		result = []

		for vendor in vendors:
			try:
				total_due = calculate_total_due(vendor)

				if is_checked(filters.get("no_show", False)) and not vendor.no_show:
					continue
				if is_checked(filters.get("taca_member", False)) and not vendor.taca_member:
					continue
				if is_checked(filters.get("early_in", False)) and not vendor.early_in:
					continue
				if is_checked(filters.get("saturday_setup", False)) and not vendor.saturday_setup:
					continue
				if is_checked(filters.get("unpaid", False)) and total_due <= vendor.amount_paid:
					continue
				if is_checked(filters.get("overpaid", False)) and vendor.amount_paid <= total_due:
					continue
				if is_checked(filters.get("electricity", False)) and not vendor.electricity:
					continue
				if is_checked(filters.get("rta", False)) and not vendor.rta:
					continue
				if is_checked(filters.get("rtn", False)) and not vendor.rtn:
					continue

				result.append(vendor)
			except Exception as e:
				print(f"[ERROR] Filtering vendor ID {getattr(vendor, 'id', '?')}: {e}")

		print(f"[DEBUG] {len(result)} vendors passed advanced filters")
		return result

		def is_checked(val):
			return val.get() if hasattr(val, 'get') else val

		filters = self.filters or {}
		result = []

		for vendor in vendors:
			if is_checked(filters.get("no_show", False)) and not vendor.no_show:
				continue
			if is_checked(filters.get("taca_member", False)) and not vendor.taca_member:
				continue
			if is_checked(filters.get("early_in", False)) and not vendor.early_in:
				continue
			if is_checked(filters.get("saturday_setup", False)) and not vendor.saturday_setup:
				continue
			if is_checked(filters.get("unpaid", False)) and vendor.amount_due <= vendor.amount_paid:
				continue
			if is_checked(filters.get("overpaid", False)) and vendor.amount_paid <= vendor.amount_due:
				continue
			if is_checked(filters.get("electricity", False)) and not vendor.electricity:
				continue
			if is_checked(filters.get("rtn", False)) and not vendor.rtn:
				continue
			if is_checked(filters.get("rta", False)) and not vendor.rta:
				continue
			result.append(vendor)

		print(f"[DEBUG] {len(result)} vendors passed advanced filters")
		return result

	def add_vendor(self):
		VendorForm(self, self.user, refresh_callback=self.load_vendors)

	def view_vendor(self, event):
		selected_item = self.tree.selection()
		if selected_item:
			vendor_id = int(selected_item[0])

			# GET VENDOR DATA FOR LOGGING
			session = Session()
			vendor = session.query(Vendor).filter_by(id=vendor_id).first()
			if vendor:
				vendor_data = {
					'business_name': vendor.business_name,
					'first_name': vendor.first_name,
					'last_name': vendor.last_name,
					'island': vendor.island,
					'row': vendor.row,
					'table_numbers': vendor.table_numbers
				}

				# LOG THE DOUBLE-CLICK
				logger = get_enhanced_logger(self.current_user)
				logger.log_double_click("Vendor", vendor_id, vendor_data, "Vendor list double-click")

			session.close()

			# Continue with existing logic
			VendorForm(self, self.user, vendor_id=vendor_id, refresh_callback=self.load_vendors)

	def delete_selected_vendor(self):
		selected = self.tree.selection()
		if not selected:
			messagebox.showinfo("No selection", "Please select a vendor to delete.")
			return

		vendor_id = int(selected[0])
		confirm = messagebox.askyesno("Confirm Delete", f"Delete vendor ID {vendor_id}?")
		if confirm:
			session = Session()
			vendor = session.query(Vendor).filter_by(id=vendor_id).first()
			if vendor:
				session.delete(vendor)
				session.commit()
				self.load_vendors()
				messagebox.showinfo("Deleted", "Vendor deleted successfully.")
			else:
				messagebox.showerror("Error", "Vendor not found.")
			session.close()

	def generate_vendor_export_text(self, vendors):
		"""
		Generate a unified text block for all vendor exports (Print, TXT, PDF).
		"""
		lines = []
		for v in vendors:
			try:
				name = (v.business_name or f"{v.first_name or ''} {v.last_name or ''}").strip()
				location = f"Island: {v.island or ''} | Row: {v.row or ''} | Table #: {v.table_numbers or ''}"

				# Build tags for 6-foot and 8-foot tables
				six_tags = []
				if v.six_ft_gun: six_tags.append("G")
				if v.six_ft_knife: six_tags.append("K")
				if v.six_ft_display: six_tags.append("D")
				if v.six_ft_nonrelated: six_tags.append("N")

				eight_tags = []
				if v.eight_ft_gun: eight_tags.append("G")
				if v.eight_ft_knife: eight_tags.append("K")
				if v.eight_ft_display: eight_tags.append("D")
				if v.eight_ft_nonrelated: eight_tags.append("N")

				# Collect E/RO flags
				ero_flags = []
				if v.electricity:
					ero_flags.append("E")
				if v.rta:
					ero_flags.append("RTA")
				elif v.rtn:
					ero_flags.append("RTN")

				# Build table lines with tags
				table_lines = []
				if six_tags:
					six_line = f"6': {' '.join(six_tags)}"
					if ero_flags and not eight_tags:
						six_line = six_line.ljust(50) + " ".join(ero_flags)
						ero_flags = []
					table_lines.append(six_line)

				if eight_tags:
					eight_line = f"8': {' '.join(eight_tags)}"
					if ero_flags:
						eight_line = eight_line.ljust(50) + " ".join(ero_flags)
						ero_flags = []
					table_lines.append(eight_line)

				if not six_tags and not eight_tags and ero_flags:
					table_lines.append(f"E/RO: {' '.join(ero_flags)}")

				# Monetary values
				total = int(float(v.total_due or 0))
				paid = int(float(v.amount_paid or 0))
				receipt = str(v.receipt_number).zfill(4) if v.receipt_number else "#"

				# Final lines for vendor
				lines.append(f"Name: {name}")
				lines.append(location)
				lines.extend(table_lines)
				lines.append(f"Total Due: ${total} | Paid: ${paid} | Receipt: {receipt}")
				lines.append("-" * 80)
			except Exception as e:
				print(f"[ERROR] Export vendor ID {getattr(v, 'id', '?')}: {e}")
		return "\n".join(lines)

	def export_all_vendors_to_print(self):
		"""
		Print preview and send to printer.
		"""

		def refresh_preview():
			vendors = self.get_filtered_vendors(Session().query(Vendor).all())
			text.config(state="normal")
			text.delete("1.0", "end")
			text.insert("1.0", self.generate_vendor_export_text(vendors))
			text.config(state="disabled")

		def do_print():
			try:
				content = text.get("1.0", "end-1c")
				path = os.path.join(EXPORT_DIR, "all_vendors_print.txt")
				with open(path, "w", encoding="utf-8") as f:
					f.write(content)
				os.startfile(path, "print")
			except Exception as e:
				messagebox.showerror("Error", f"Print failed:\n{e}")

		preview = tk.Toplevel(self)
		preview.title("Print Preview - All Vendors")
		preview.geometry("1000x700")
		preview.configure(bg="#1e1e1e")

		text = tk.Text(preview, wrap="word", bg="#2e2e2e", fg="white", insertbackground="#1e1e1e")
		text.pack(fill="both", expand=True, padx=10, pady=10)

		tk.Button(preview, text="Print", command=do_print, bg="#2e2e2e", fg="white").pack(pady=10)

		refresh_preview()

	def export_all_to_txt(self):
		"""
		Export all vendors to a TXT file.
		"""
		vendors = self.get_filtered_vendors(Session().query(Vendor).all())
		if not vendors:
			messagebox.showinfo("No Vendors", "No vendors matched the current filters.")
			return
		content = self.generate_vendor_export_text(vendors)
		path = os.path.join(EXPORT_DIR, "all_vendors_export.txt")
		with open(path, "w", encoding="utf-8") as f:
			f.write(content)
		messagebox.showinfo("TXT Export", f"TXT file created: {path}")

	def export_all_to_pdf(self):
		"""
		Export all vendors to a PDF file.
		"""
		vendors = self.get_filtered_vendors(Session().query(Vendor).all())
		if not vendors:
			messagebox.showinfo("No Vendors", "No vendors matched the current filters.")
			return
		content = self.generate_vendor_export_text(vendors)
		export_all_vendors_to_single_pdf(content)

	def generate_book_export_text(self, vendors, sort_by="location", page_breaks=True):
		"""
		Generates book-style export text, grouped by Island/Row, Alphabetically by Name, or by Reservation Date.
		sort_by: "location", "name", or "date".
		page_breaks: Insert page breaks between groups if True.
		"""

		def location_sort_key(v):
			row = (v.row or "").upper()
			try:
				island = int(v.island) if v.island and v.island.isdigit() else 999
			except:
				island = 999
			table_start = min(self.parse_table_numbers(v.table_numbers) or [999])
			return (row, island, table_start)

		def name_sort_key(v):
			return (v.business_name or f"{v.first_name or ''} {v.last_name or ''}").lower()

		def date_sort_key(v):
			# Parse reservation_date for sorting
			try:
				if v.reservation_date:
					# Handle different date formats
					if isinstance(v.reservation_date, str):
						# Try common date formats
						for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
							try:
								return datetime.strptime(v.reservation_date, fmt)
							except ValueError:
								continue
					else:
						# Assume it's already a datetime object
						return v.reservation_date
			except:
				pass
			# Return a far future date for vendors without valid dates (sorts them last)
			return datetime(2099, 12, 31)

		# Sort vendors based on the selected method
		if sort_by == "location":
			vendors_sorted = sorted(vendors, key=location_sort_key)
		elif sort_by == "name":
			vendors_sorted = sorted(vendors, key=name_sort_key)
		elif sort_by == "date":
			vendors_sorted = sorted(vendors, key=date_sort_key)
		else:
			vendors_sorted = vendors  # No sorting if unknown option

		lines = []
		current_group = None

		for v in vendors_sorted:
			try:
				if sort_by == "location":
					group_label = (v.row or "").upper()
				elif sort_by == "name":
					name_ref = (v.business_name or f"{v.first_name or ''} {v.last_name or ''}").strip()
					group_label = name_ref[0].upper() if name_ref else "#"
				elif sort_by == "date":
					# Group by month/year of reservation date
					try:
						if v.reservation_date:
							if isinstance(v.reservation_date, str):
								# Try to parse the date string
								for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
									try:
										date_obj = datetime.strptime(v.reservation_date, fmt)
										group_label = date_obj.strftime("%B %Y")  # e.g., "January 2024"
										break
									except ValueError:
										continue
								else:
									group_label = "Unknown Date"
							else:
								# Assume it's already a datetime object
								group_label = v.reservation_date.strftime("%B %Y")
						else:
							group_label = "No Date"
					except:
						group_label = "Unknown Date"
				else:
					group_label = "All Vendors"

				# Add group headers and page breaks
				if group_label != current_group:
					current_group = group_label
					if page_breaks:
						lines.append("\f")  # Page break
					lines.append("=" * 50)
					lines.append(f" {current_group}")
					lines.append("=" * 50)

				# Determine name (Business overrides)
				name = v.business_name.strip() if v.business_name else f"{v.first_name or ''} {v.last_name or ''}".strip()

				# Build G/K/D/N tags
				tags = []
				if v.six_ft_gun or v.eight_ft_gun: tags.append("G")
				if v.six_ft_knife or v.eight_ft_knife: tags.append("K")
				if v.six_ft_display or v.eight_ft_display: tags.append("D")
				if v.six_ft_nonrelated or v.eight_ft_nonrelated: tags.append("N")

				# Electricity & Rollover flags
				ro_flags = "RTA" if v.rta else "RTN" if v.rtn else ""
				if v.electricity:
					tags.append("E")

				table_type = "/".join(tags) if tags else "-"
				location = f"{v.island or ''} {v.row or ''} {v.table_numbers or ''}".strip()

				# Add reservation date to the line when sorting by date
				if sort_by == "date":
					try:
						if v.reservation_date:
							if isinstance(v.reservation_date, str):
								date_str = v.reservation_date
							else:
								date_str = v.reservation_date.strftime("%m/%d/%Y")
						else:
							date_str = "No Date"
					except:
						date_str = "Unknown"

					lines.append(
						f"Name: {name} | Table Type: {table_type} | Location: {location} | Date: {date_str} | {ro_flags}".strip())
				else:
					lines.append(f"Name: {name} | Table Type: {table_type} | Location: {location} | {ro_flags}".strip())
			except Exception as e:
				print(f"[ERROR] Failed to process vendor ID {getattr(v, 'id', '?')}: {e}")

		return "\n".join(lines)

	def export_book_by_location(self):
		"""
		Export book printout sorted by location.
		"""
		vendors = self.get_filtered_vendors(Session().query(Vendor).all())
		if not vendors:
			messagebox.showinfo("No Vendors", "No vendors matched the current filters.")
			return

		content = self.generate_book_export_text(vendors, sort_by="location")
		path = os.path.join(EXPORT_DIR, "book_export_by_location.txt")
		with open(path, "w", encoding="utf-8") as f:
			f.write(content)

		messagebox.showinfo("Book Export", f"Book (Location) TXT created: {path}")

	def export_book_by_name(self):
		"""
		Export book printout sorted by name.
		"""
		vendors = self.get_filtered_vendors(Session().query(Vendor).all())
		if not vendors:
			messagebox.showinfo("No Vendors", "No vendors matched the current filters.")
			return

		content = self.generate_book_export_text(vendors, sort_by="name")
		path = os.path.join(EXPORT_DIR, "book_export_by_name.txt")
		with open(path, "w", encoding="utf-8") as f:
			f.write(content)

		messagebox.showinfo("Book Export", f"Book (Name) TXT created: {path}")

	def preview_book_export(self):
		session = Session()
		vendors = self.get_filtered_vendors(session.query(Vendor).all())
		session.close()

		def refresh_preview():
			content = self.generate_book_export_text(
				vendors,
				sort_by=sort_option.get(),
				page_breaks=page_break_var.get()
			)
			text.config(state="normal")
			text.delete("1.0", "end")
			text.insert("1.0", content)
			text.config(state="disabled")

		def save_txt():
			content = text.get("1.0", "end-1c")
			sort_type = sort_option.get()
			filename = f"book_export_by_{sort_type}.txt"
			path = os.path.join(EXPORT_DIR, filename)
			with open(path, "w", encoding="utf-8") as f:
				f.write(content)
			messagebox.showinfo("Book Export", f"TXT file created: {path}")

		def do_print():
			try:
				content = text.get("1.0", "end-1c")
				temp_path = os.path.join(EXPORT_DIR, "book_export_temp.txt")
				with open(temp_path, "w", encoding="utf-8") as f:
					f.write(content)
				os.startfile(temp_path, "print")
			except Exception as e:
				messagebox.showerror("Error", f"Print failed:\n{e}")

		# Create preview window
		preview = tk.Toplevel(self)
		preview.title("Book Preview")
		preview.geometry("1000x700")
		preview.configure(bg="#1e1e1e")

		text = tk.Text(preview, wrap="word", bg="#2e2e2e", fg="white", insertbackground="white")
		text.pack(fill="both", expand=True, padx=10, pady=10)

		# Options frame
		options_frame = tk.Frame(preview, bg="#1e1e1e")
		options_frame.pack(fill="x", pady=10)

		# Radio buttons for sort mode
		sort_option = tk.StringVar(value="location")
		tk.Label(options_frame, text="Sort by:", bg="#1e1e1e", fg="white").pack(side="left", padx=(5, 10))
		tk.Radiobutton(options_frame, text="Location", variable=sort_option, value="location",
					   command=refresh_preview, bg="#1e1e1e", fg="white", selectcolor="#1e1e1e").pack(side="left",
																									  padx=5)
		tk.Radiobutton(options_frame, text="Name", variable=sort_option, value="name",
					   command=refresh_preview, bg="#1e1e1e", fg="white", selectcolor="#1e1e1e").pack(side="left",
																									  padx=5)
		tk.Radiobutton(options_frame, text="Reservation Date", variable=sort_option, value="date",
					   command=refresh_preview, bg="#1e1e1e", fg="white", selectcolor="#1e1e1e").pack(side="left",
																									  padx=5)

		# Page break checkbox
		page_break_var = tk.BooleanVar(value=True)
		tk.Checkbutton(options_frame, text="Page Breaks per Section", variable=page_break_var,
					   command=refresh_preview, bg="#1e1e1e", fg="white",
					   selectcolor="#1e1e1e", activebackground="#1e1e1e").pack(side="left", padx=10)

		# Action buttons
		tk.Button(options_frame, text="Save TXT", command=save_txt, bg="#2e2e2e", fg="white").pack(side="left", padx=5)
		tk.Button(options_frame, text="Print", command=do_print, bg="#2e2e2e", fg="white").pack(side="left", padx=5)

		refresh_preview()

	def preview_tax_stickers(self):
		window = tk.Toplevel(self)
		window.title("Tax Sticker Preview")
		window.configure(bg="#1e1e1e")

		text_box = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=100, height=40, bg="#1e1e1e", fg="white")
		text_box.pack(padx=10, pady=10)

		from utils.export_utils import build_tax_sticker_content

		vendors = Session().query(Vendor).all()
		vendors.sort(key=lambda v: (v.business_name or f"{v.first_name or ''} {v.last_name or ''}").lower())

		content = '\n\n'.join([build_tax_sticker_content(v) for v in vendors])
		text_box.insert(tk.END, content)

		def save_txt():
			path = os.path.join(EXPORT_DIR, "tax_stickers.txt")
			with open(path, "w", encoding="utf-8") as f:
				f.write(content)
			messagebox.showinfo("Saved", f"Tax stickers saved to {path}")

		def do_print():
			try:
				path = os.path.join(EXPORT_DIR, "tax_stickers_preview.txt")
				with open(path, "w", encoding="utf-8") as f:
					f.write(content)
				os.startfile(path, "print")
			except Exception as e:
				messagebox.showerror("Error", f"Print failed:\n{e}")

		button_frame = tk.Frame(window, bg="#1e1e1e")
		button_frame.pack(pady=10)
		tk.Button(button_frame, text="Save TXT", command=save_txt, bg="#333", fg="white").pack(side="left", padx=5)
		tk.Button(button_frame, text="Print", command=do_print, bg="#333", fg="white").pack(side="left", padx=5)

	def matches_search(self, vendor, term):
		term = term.lower()
		return (
				term in (vendor.first_name or '').lower()
				or term in (vendor.last_name or '').lower()
				or term in (vendor.business_name or '').lower()
				or term in (vendor.row or '').lower()
				or term in (vendor.island or '').lower()
				or term in (vendor.table_numbers or '').lower()
				or term in (vendor.receipt_number or '').lower()
		)

	def parse_table_numbers(self, raw):
		numbers = set()
		if not raw:
			return numbers

		parts = raw.split(',')
		for part in parts:
			if '-' in part:
				try:
					start, end = map(int, part.split('-'))
					numbers.update(range(start, end + 1))
				except ValueError:
					continue
			else:
				try:
					numbers.add(int(part.strip()))
				except ValueError:
					continue
		return numbers


def parse_table_numbers(raw):
	numbers = set()
	if not raw:
		return numbers
	parts = raw.split(',')
	for part in parts:
		if '-' in part:
			try:
				start, end = map(int, part.split('-'))
				numbers.update(range(start, end + 1))
			except ValueError:
				continue
		else:
			try:
				numbers.add(int(part.strip()))
			except ValueError:
				continue
	return numbers


def set_double_booked_flags(vendors):
	seen = {}
	for vendor in vendors:
		vendor.double_booked = False

	for vendor in vendors:
		island = (vendor.island or "").strip().lower()
		row = (vendor.row or "").strip().lower()
		show_date = (vendor.show_date or vendor.reservation_date or "").strip()
		tables = parse_table_numbers(vendor.table_numbers)

		for table in tables:
			key = (island, row, str(table), show_date)
			if key in seen:
				vendor.double_booked = True
				seen[key].double_booked = True
			else:
				seen[key] = vendor

