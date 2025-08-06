import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from models import Session
from models.mailout import Mailout
from gui.mailout_form import MailoutForm
from utils.theme import apply_user_theme
from utils.export_utils import EXPORT_DIR


class MailoutManagerWindow(tk.Frame):
	def __init__(self, master, user):
		super().__init__(master, bg="#1e1e1e")
		self.master = master
		self.user = user
		self.current_user = user
		self.selected_mailout = None
		self.search_var = tk.StringVar()
		apply_user_theme(self, user)
		print("[DEBUG] MailoutManagerWindow __init__ starting")
		self.build_layout()
		self.load_mailouts()
		print("[DEBUG] MailoutManagerWindow __init__ complete")

	def build_layout(self):
		print("[DEBUG] build_layout starting")

		# Control frame with search and buttons
		control_frame = tk.Frame(self, bg="#1e1e1e")
		control_frame.pack(fill="x", padx=10, pady=10)

		tk.Label(control_frame, text="Search:", fg="#ffdf00", bg="#1e1e1e").pack(side="left")
		search_entry = tk.Entry(control_frame, bg="#2e2e2e", fg="white", textvariable=self.search_var)
		search_entry.pack(side="left", padx=5, fill="x", expand=True)
		search_entry.bind("<Return>", lambda event: self.load_mailouts())

		tk.Button(control_frame, text="Search", command=self.load_mailouts, bg="#2e2e2e", fg="white").pack(side="left",
																										   padx=5)

		# Action buttons
		btn_frame = tk.Frame(control_frame, bg="#1e1e1e")
		btn_frame.pack(side="right")
		tk.Button(btn_frame, text="Add Entry", command=self.add_mailout, bg="#2e2e2e", fg="white").pack(side="left",
																										padx=(0, 10))
		tk.Button(btn_frame, text="Delete Entry", command=self.delete_selected_mailout, bg="#2e2e2e", fg="white").pack(
			side="left", padx=(10, 0))

		# Export frame
		export_frame = tk.Frame(self, bg="#1e1e1e")
		export_frame.pack(fill="x", padx=10, pady=(0, 10))
		tk.Button(export_frame, text="Export All (TXT)", command=self.export_all_to_txt, bg="#2e2e2e", fg="white").pack(
			side="left", padx=5)
		tk.Button(export_frame, text="Print Labels", command=self.print_labels, bg="#2e2e2e", fg="white").pack(
			side="left", padx=5)
		tk.Button(export_frame, text="Label Preview", command=self.preview_labels, bg="#2e2e2e", fg="white").pack(
			side="left", padx=5)

		# Treeview for mailout list
		self.tree = ttk.Treeview(self, columns=("name", "address", "city_state_zip", "phone", "email", "date"),
								 show="headings")
		self.tree.heading("name", text="Name", command=lambda c="name": self.sort_by_column(c, False))
		self.tree.heading("address", text="Address", command=lambda c="address": self.sort_by_column(c, False))
		self.tree.heading("city_state_zip", text="City, State ZIP",
						  command=lambda c="city_state_zip": self.sort_by_column(c, False))
		self.tree.heading("phone", text="Phone", command=lambda c="phone": self.sort_by_column(c, False))
		self.tree.heading("email", text="Email", command=lambda c="email": self.sort_by_column(c, False))
		self.tree.heading("date", text="Added", command=lambda c="date": self.sort_by_column(c, False))

		# Configure treeview style
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

		# Set column widths
		self.tree.column("name", anchor="w", width=150, stretch=True)
		self.tree.column("address", anchor="w", width=200, stretch=True)
		self.tree.column("city_state_zip", anchor="w", width=150, stretch=True)
		self.tree.column("phone", anchor="center", width=120, stretch=True)
		self.tree.column("email", anchor="w", width=180, stretch=True)
		self.tree.column("date", anchor="center", width=100, stretch=True)

		self.tree.pack(fill="both", expand=True, padx=10, pady=10)
		self.tree.bind("<Double-1>", self.view_mailout)

		print("[DEBUG] build_layout done")

	def sort_by_column(self, col, reverse):
		try:
			data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
			data.sort(key=lambda t: t[0].lower() if isinstance(t[0], str) else t[0], reverse=reverse)

			for index, (_, child) in enumerate(data):
				self.tree.move(child, '', index)
			self.tree.heading(col, command=lambda: self.sort_by_column(col, not reverse))
		except Exception as e:
			print(f"[ERROR] Sorting failed for column '{col}':", e)

	def load_mailouts(self):
		print("[DEBUG] load_mailouts called")
		session = Session()
		query = session.query(Mailout)

		term = self.search_var.get().strip()
		print(f"[DEBUG] Search term: '{term}'")

		mailouts = query.all()
		if term:
			mailouts = [m for m in mailouts if self.matches_search(m, term)]

		print(f"[DEBUG] {len(mailouts)} mailouts to display")

		self.tree.delete(*self.tree.get_children())

		for mailout in mailouts:
			try:
				name = mailout.name or ""
				address = mailout.address or ""
				city_state_zip = f"{mailout.city or ''}, {mailout.state or ''} {mailout.zip_code or ''}".strip()
				phone = mailout.phone or ""
				email = mailout.email or ""
				try:
					date = mailout.created_date.strftime("%m/%d/%Y") if mailout.created_date else ""
				except:
					date = ""

				self.tree.insert(
					"", "end",
					iid=str(mailout.id),
					values=(name, address, city_state_zip, phone, email, date)
				)
			except Exception as e:
				print(f"[ERROR] Failed to insert mailout ID {getattr(mailout, 'id', '?')}: {e}")

		session.close()

	def matches_search(self, mailout, term):
		term = term.lower()
		return (
				term in (mailout.name or '').lower()
				or term in (mailout.address or '').lower()
				or term in (mailout.city or '').lower()
				or term in (mailout.state or '').lower()
				or term in (mailout.zip_code or '').lower()
				or term in (mailout.phone or '').lower()
				or term in (mailout.email or '').lower()
		)

	def add_mailout(self):
		MailoutForm(self, self.user, refresh_callback=self.load_mailouts)

	def view_mailout(self, event):
		selected_item = self.tree.selection()
		if selected_item:
			mailout_id = int(selected_item[0])
			MailoutForm(self, self.user, mailout_id=mailout_id, refresh_callback=self.load_mailouts)

	def delete_selected_mailout(self):
		selected = self.tree.selection()
		if not selected:
			messagebox.showinfo("No selection", "Please select a mailout entry to delete.")
			return

		mailout_id = int(selected[0])
		confirm = messagebox.askyesno("Confirm Delete", f"Delete mailout entry ID {mailout_id}?")
		if confirm:
			session = Session()
			mailout = session.query(Mailout).filter_by(id=mailout_id).first()
			if mailout:
				session.delete(mailout)
				session.commit()
				self.load_mailouts()
				messagebox.showinfo("Deleted", "Mailout entry deleted successfully.")
			else:
				messagebox.showerror("Error", "Mailout entry not found.")
			session.close()

	def export_all_to_txt(self):
		"""Export all mailout entries to a TXT file."""
		session = Session()
		mailouts = session.query(Mailout).all()
		session.close()

		if not mailouts:
			messagebox.showinfo("No Entries", "No mailout entries to export.")
			return

		lines = []
		for m in mailouts:
			lines.extend([
				f"Name: {m.name}",
				f"Address: {m.address}",
				f"City: {m.city}, {m.state} {m.zip_code}",
				f"Phone: {m.phone or 'N/A'}",
				f"Email: {m.email or 'N/A'}",
				f"Added: {m.created_date.strftime('%m/%d/%Y') if m.created_date else 'N/A'}",
				"-" * 50
			])

		# Create mailout subdirectory
		mailout_dir = EXPORT_DIR / "mailout"
		mailout_dir.mkdir(exist_ok=True)

		timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
		path = mailout_dir / f"mailout_export_{timestamp}.txt"

		with open(path, "w", encoding="utf-8") as f:
			f.write("\n".join(lines))

		messagebox.showinfo("Export Complete", f"Mailout list exported to:\n{path}")

	def generate_label_content(self, mailouts):
		"""Generate formatted content for mailing labels (name and address only)."""
		lines = []
		for m in mailouts:
			# Format: Name on first line, Address on second line, City State ZIP on third line
			label_text = f"{m.name}\n{m.address}\n{m.city}, {m.state} {m.zip_code}"
			lines.append(label_text)
		return "\n\n".join(lines)  # Double line break between labels

	def print_labels(self):
		"""Print mailing labels."""
		session = Session()
		mailouts = session.query(Mailout).order_by(Mailout.name).all()
		session.close()

		if not mailouts:
			messagebox.showinfo("No Entries", "No mailout entries to print.")
			return

		try:
			content = self.generate_label_content(mailouts)

			# Create mailout subdirectory
			mailout_dir = EXPORT_DIR / "mailout"
			mailout_dir.mkdir(exist_ok=True)

			path = mailout_dir / "mailing_labels.txt"
			with open(path, "w", encoding="utf-8") as f:
				f.write(content)

			os.startfile(str(path), "print")
			messagebox.showinfo("Print Sent", f"Mailing labels sent to printer.\nFile saved: {path}")
		except Exception as e:
			messagebox.showerror("Print Error", f"Failed to print labels:\n{e}")

	def preview_labels(self):
		"""Preview mailing labels before printing."""
		session = Session()
		mailouts = session.query(Mailout).order_by(Mailout.name).all()
		session.close()

		if not mailouts:
			messagebox.showinfo("No Entries", "No mailout entries to preview.")
			return

		def save_labels():
			content = text.get("1.0", "end-1c")

			# Create mailout subdirectory
			mailout_dir = EXPORT_DIR / "mailout"
			mailout_dir.mkdir(exist_ok=True)

			timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
			path = mailout_dir / f"mailing_labels_{timestamp}.txt"

			with open(path, "w", encoding="utf-8") as f:
				f.write(content)
			messagebox.showinfo("Labels Saved", f"Labels saved to:\n{path}")

		def do_print():
			try:
				content = text.get("1.0", "end-1c")

				# Create mailout subdirectory
				mailout_dir = EXPORT_DIR / "mailout"
				mailout_dir.mkdir(exist_ok=True)

				temp_path = mailout_dir / "mailing_labels_temp.txt"
				with open(temp_path, "w", encoding="utf-8") as f:
					f.write(content)
				os.startfile(str(temp_path), "print")
			except Exception as e:
				messagebox.showerror("Error", f"Print failed:\n{e}")

		# Create preview window
		preview = tk.Toplevel(self)
		preview.title("Mailing Labels Preview")
		preview.geometry("600x500")
		preview.configure(bg="#1e1e1e")

		text = tk.Text(preview, wrap="word", bg="#2e2e2e", fg="white", insertbackground="white", font=("Courier", 10))
		text.pack(fill="both", expand=True, padx=10, pady=10)

		# Generate and display content
		content = self.generate_label_content(mailouts)
		text.insert("1.0", content)

		# Button frame
		button_frame = tk.Frame(preview, bg="#1e1e1e")
		button_frame.pack(pady=10)

		tk.Button(button_frame, text="Save Labels", command=save_labels, bg="#2e2e2e", fg="white").pack(side="left",
																										padx=5)
		tk.Button(button_frame, text="Print", command=do_print, bg="#2e2e2e", fg="white").pack(side="left", padx=5)