from sqlalchemy.orm import joinedload
import tkinter as tk
from tkinter import messagebox, ttk
from models import Session
from models.user import User
from utils.auth import check_password
from utils.session_logger import log_session_login
from gui.main_app_window import MainAppWindow
from utils.theme import apply_dark_style
import json
import os
import time
import threading
from datetime import datetime, timedelta

CONFIG_FILE = "login_config.json"


class AnimatedLabel(tk.Label):
	"""Custom label with fade-in animation"""

	def __init__(self, parent, text="", **kwargs):
		super().__init__(parent, text=text, **kwargs)
		self.original_fg = kwargs.get('fg', 'white')
		self.fade_steps = 20

	def fade_in(self, callback=None):
		"""Animate label fade-in"""

		def animate_step(step=0):
			if step <= self.fade_steps:
				alpha = step / self.fade_steps
				# Simple alpha simulation by adjusting color brightness
				brightness = int(255 * alpha)
				color = f"#{brightness:02x}{brightness:02x}{brightness:02x}"
				self.configure(fg=color)
				if self.winfo_exists():
					self.after(50, lambda: animate_step(step + 1))
			else:
				self.configure(fg=self.original_fg)
				if callback:
					callback()

		animate_step()


class LoginWindow:
	def __init__(self, master):
		self.master = master
		self.master.title("Wanenmacher's Management System - Login")
		self.master.geometry("900x700")
		self.master.resizable(False, False)

		# Center the window
		self.center_window()

		apply_dark_style(self.master)

		# Login attempt tracking
		self.failed_attempts = 0
		self.last_attempt_time = None
		self.lockout_duration = 300  # 5 minutes

		# Form variables
		self.username_var = tk.StringVar()
		self.password_var = tk.StringVar()
		self.remember_var = tk.BooleanVar()
		self.show_password_var = tk.BooleanVar()

		# Animation states
		self.login_in_progress = False
		self.logo_animation_complete = False

		self.load_saved_credentials()
		self.build_ui()
		self.start_logo_animation()

		# Bind Enter key for login
		self.master.bind("<Return>", lambda e: self.login())
		self.master.bind("<Escape>", lambda e: self.master.quit())

		# Focus on appropriate field
		if self.username_var.get():
			self.password_entry.focus()
		else:
			self.username_entry.focus()

	def center_window(self):
		"""Center the window on screen"""
		self.master.update_idletasks()
		x = (self.master.winfo_screenwidth() // 2) - (900 // 2)
		y = (self.master.winfo_screenheight() // 2) - (700 // 2)
		self.master.geometry(f"900x700+{x}+{y}")

	def build_ui(self):
		"""Build the modern login interface"""
		# Main background frame
		main_frame = tk.Frame(self.master, bg="#1a1a1a")
		main_frame.pack(fill="both", expand=True)

		# Left panel - Branding/Info
		left_panel = tk.Frame(main_frame, bg="#2a2a2a", width=400)
		left_panel.pack(side="left", fill="y")
		left_panel.pack_propagate(False)

		self.build_left_panel(left_panel)

		# Right panel - Login form
		right_panel = tk.Frame(main_frame, bg="#1a1a1a", width=500)
		right_panel.pack(side="right", fill="both", expand=True)
		right_panel.pack_propagate(False)

		self.build_right_panel(right_panel)

	def build_left_panel(self, parent):
		"""Build the left branding panel"""
		content = tk.Frame(parent, bg="#2a2a2a")
		content.pack(expand=True, fill="both", padx=40, pady=60)

		# Animated logo
		self.logo_label = tk.Label(content, text="🦁", font=("Arial", 80),
								   bg="#2a2a2a", fg="#ffdf00")
		self.logo_label.pack(pady=(0, 20))

		# Main title with animation
		self.title_label = AnimatedLabel(content, text="Wanenmacher's",
										 font=("Segoe UI", 32, "bold"),
										 bg="#2a2a2a", fg="#ffffff")
		self.title_label.pack(pady=(0, 10))

		self.subtitle_label = AnimatedLabel(content, text="Management System",
											font=("Segoe UI", 18),
											bg="#2a2a2a", fg="#cccccc")
		self.subtitle_label.pack(pady=(0, 30))

		# Features list
		features_frame = tk.Frame(content, bg="#2a2a2a")
		features_frame.pack(pady=(20, 0))

		features = [
			"🎯 Vendor Management",
			"📊 Real-time Analytics",
			"🗺️ Interactive Maps",
			"📧 Mailout System",
			"🖨️ Print & Export Tools",
			"📝 Comprehensive Logging"
		]

		self.feature_labels = []
		for i, feature in enumerate(features):
			label = AnimatedLabel(features_frame, text=feature,
								  font=("Segoe UI", 12),
								  bg="#2a2a2a", fg="#999999")
			label.pack(anchor="w", pady=3)
			self.feature_labels.append(label)

		# Version and copyright
		footer_frame = tk.Frame(content, bg="#2a2a2a")
		footer_frame.pack(side="bottom", fill="x")

		tk.Label(footer_frame, text="Version 2.0", font=("Segoe UI", 10),
				 bg="#2a2a2a", fg="#666666").pack(anchor="w")
		tk.Label(footer_frame, text=f"© {datetime.now().year} Wanenmacher's",
				 font=("Segoe UI", 10), bg="#2a2a2a", fg="#666666").pack(anchor="w")

	def build_right_panel(self, parent):
		"""Build the login form panel"""
		# Login form container
		form_container = tk.Frame(parent, bg="#1a1a1a")
		form_container.pack(expand=True, fill="both", padx=60, pady=80)

		# Welcome section
		welcome_frame = tk.Frame(form_container, bg="#1a1a1a")
		welcome_frame.pack(fill="x", pady=(0, 40))

		tk.Label(welcome_frame, text="Welcome Back", font=("Segoe UI", 28, "bold"),
				 bg="#1a1a1a", fg="#ffffff").pack(anchor="w")

		tk.Label(welcome_frame, text="Please sign in to your account",
				 font=("Segoe UI", 14), bg="#1a1a1a", fg="#cccccc").pack(anchor="w", pady=(5, 0))

		# Current time display
		self.time_label = tk.Label(welcome_frame, font=("Segoe UI", 12),
								   bg="#1a1a1a", fg="#ffdf00")
		self.time_label.pack(anchor="w", pady=(10, 0))
		self.update_time()

		# Username field
		self.build_form_field(form_container, "Username", self.username_var, False)

		# Password field
		self.build_form_field(form_container, "Password", self.password_var, True)

		# Options row
		options_frame = tk.Frame(form_container, bg="#1a1a1a")
		options_frame.pack(fill="x", pady=(15, 25))

		# Remember me checkbox
		remember_frame = tk.Frame(options_frame, bg="#1a1a1a")
		remember_frame.pack(side="left")

		tk.Checkbutton(remember_frame, text="Remember me", variable=self.remember_var,
					   bg="#1a1a1a", fg="#cccccc", selectcolor="#1a1a1a",
					   activebackground="#1a1a1a", activeforeground="#ffdf00",
					   font=("Segoe UI", 11)).pack(side="left")

		# Show password checkbox
		show_pass_frame = tk.Frame(options_frame, bg="#1a1a1a")
		show_pass_frame.pack(side="right")

		tk.Checkbutton(show_pass_frame, text="Show password",
					   variable=self.show_password_var,
					   command=self.toggle_password_visibility,
					   bg="#1a1a1a", fg="#cccccc", selectcolor="#1a1a1a",
					   activebackground="#1a1a1a", activeforeground="#ffdf00",
					   font=("Segoe UI", 11)).pack(side="right")

		# Login button
		self.login_button = tk.Button(form_container, text="Sign In",
									  command=self.login,
									  bg="#ffdf00", fg="#000000",
									  font=("Segoe UI", 14, "bold"),
									  relief="flat", bd=0,
									  padx=30, pady=12,
									  cursor="hand2")
		self.login_button.pack(fill="x", pady=(10, 20))

		# Button hover effects
		self.login_button.bind("<Enter>", lambda e: self.login_button.configure(bg="#e6c600"))
		self.login_button.bind("<Leave>", lambda e: self.login_button.configure(bg="#ffdf00"))

		# Status/error message area
		self.status_frame = tk.Frame(form_container, bg="#1a1a1a")
		self.status_frame.pack(fill="x", pady=(0, 20))

		self.status_label = tk.Label(self.status_frame, text="", font=("Segoe UI", 11),
									 bg="#1a1a1a", fg="#ff4444", wraplength=380)
		self.status_label.pack()

		# Loading indicator (hidden initially)
		self.loading_frame = tk.Frame(form_container, bg="#1a1a1a")
		self.loading_label = tk.Label(self.loading_frame, text="🔄 Signing in...",
									  font=("Segoe UI", 12), bg="#1a1a1a", fg="#ffdf00")

		# Footer info
		footer_info = tk.Frame(form_container, bg="#1a1a1a")
		footer_info.pack(side="bottom", fill="x")

		tk.Label(footer_info, text="Need help? Contact system administrator",
				 font=("Segoe UI", 10), bg="#1a1a1a", fg="#666666").pack()

		# Keyboard shortcuts info
		tk.Label(footer_info, text="Press Enter to login • Escape to exit",
				 font=("Segoe UI", 9), bg="#1a1a1a", fg="#555555").pack(pady=(5, 0))

	def build_form_field(self, parent, label_text, text_var, is_password):
		"""Build a styled form field"""
		field_frame = tk.Frame(parent, bg="#1a1a1a")
		field_frame.pack(fill="x", pady=(0, 20))

		# Field label
		tk.Label(field_frame, text=label_text, font=("Segoe UI", 12, "bold"),
				 bg="#1a1a1a", fg="#ffffff").pack(anchor="w", pady=(0, 8))

		# Entry field with custom styling
		entry_frame = tk.Frame(field_frame, bg="#2e2e2e", relief="flat", bd=1)
		entry_frame.pack(fill="x")

		entry = tk.Entry(entry_frame, textvariable=text_var,
						 font=("Segoe UI", 14), bg="#2e2e2e", fg="#ffffff",
						 relief="flat", bd=0, insertbackground="#ffdf00",
						 show="•" if is_password else "")
		entry.pack(fill="x", padx=15, pady=12)

		# Store entry reference
		if label_text == "Username":
			self.username_entry = entry
		else:
			self.password_entry = entry

		# Field focus effects
		def on_focus_in(event):
			entry_frame.configure(bg="#3e3e3e", relief="solid")

		def on_focus_out(event):
			entry_frame.configure(bg="#2e2e2e", relief="flat")

		entry.bind("<FocusIn>", on_focus_in)
		entry.bind("<FocusOut>", on_focus_out)

	def toggle_password_visibility(self):
		"""Toggle password visibility"""
		if self.show_password_var.get():
			self.password_entry.configure(show="")
		else:
			self.password_entry.configure(show="•")

	def start_logo_animation(self):
		"""Start the logo animation sequence"""

		def animate_logo():
			# Logo bounce animation
			for i in range(3):
				self.logo_label.configure(font=("Arial", 85))
				if self.master.winfo_exists():
					self.master.after(100)
				self.master.update()
				time.sleep(0.1)
				self.logo_label.configure(font=("Arial", 80))
				if self.master.winfo_exists():
					self.master.after(100)
				self.master.update()
				time.sleep(0.1)

			self.logo_animation_complete = True

			# Fade in text elements
			self.title_label.fade_in(lambda: self.subtitle_label.fade_in(self.animate_features))

		# Run animation in thread to prevent blocking
		threading.Thread(target=animate_logo, daemon=True).start()

	def animate_features(self):
		"""Animate feature list appearance"""

		def show_feature(index=0):
			if index < len(self.feature_labels):
				self.feature_labels[index].fade_in()
				if self.master.winfo_exists():
					self.master.after(200, lambda: show_feature(index + 1))

		show_feature()

	def update_time(self):
		"""Update the current time display"""
		current_time = datetime.now().strftime("%A, %B %d, %Y • %I:%M %p")
		self.time_label.configure(text=current_time)
		if self.master.winfo_exists():
			self.update_job_id = self.master.after(1000, self.update_time)

	def show_status_message(self, message, is_error=True):
		"""Show status message with appropriate color"""
		color = "#ff4444" if is_error else "#44ff44"
		self.status_label.configure(text=message, fg=color)

		# Clear message after delay
		if self.master.winfo_exists():
			self.master.after(5000, lambda: self.status_label.configure(text=""))

	def show_loading(self, show=True):
		"""Show/hide loading indicator"""
		if show:
			self.loading_frame.pack(fill="x", pady=(0, 20))
			self.loading_label.pack()
			self.login_button.configure(state="disabled", text="Signing in...")
			self.animate_loading()
		else:
			self.loading_frame.pack_forget()
			self.login_button.configure(state="normal", text="Sign In")

	def animate_loading(self):
		"""Animate loading text"""
		if self.login_in_progress:
			current_text = self.loading_label.cget("text")
			dots = current_text.count(".")
			if dots >= 3:
				new_text = "🔄 Signing in"
			else:
				new_text = current_text + "."

			self.loading_label.configure(text=new_text)
			if self.master.winfo_exists():
				self.master.after(500, self.animate_loading)

	def is_locked_out(self):
		"""Check if account is locked out due to failed attempts"""
		if self.failed_attempts >= 3 and self.last_attempt_time:
			time_since_last = datetime.now() - self.last_attempt_time
			if time_since_last.total_seconds() < self.lockout_duration:
				remaining = self.lockout_duration - time_since_last.total_seconds()
				return True, int(remaining)
		return False, 0

	def login(self):
		"""Handle login attempt"""
		if self.login_in_progress:
			return

		# Check for lockout
		locked, remaining_time = self.is_locked_out()
		if locked:
			minutes = remaining_time // 60
			seconds = remaining_time % 60
			self.show_status_message(
				f"Account locked. Try again in {minutes}m {seconds}s", True
			)
			return

		username = self.username_var.get().strip()
		password = self.password_var.get()

		# Validation
		if not username:
			self.show_status_message("Please enter your username", True)
			self.username_entry.focus()
			return

		if not password:
			self.show_status_message("Please enter your password", True)
			self.password_entry.focus()
			return

		# Start login process
		self.login_in_progress = True
		self.show_loading(True)
		self.status_label.configure(text="")

		# Simulate processing delay for better UX
		if self.master.winfo_exists():
			self.master.after(800, lambda: self.perform_login(username, password))

	def perform_login(self, username, password):
		"""Perform the actual login authentication"""
		try:
			session = Session()
			user = (session.query(User).options(joinedload(User.settings)).filter_by(username=username, is_deleted=False).first())

			if user and check_password(password, user.password_hash):#Successful login
				self.failed_attempts = 0
				self.save_credentials()

			# Log the login
			log_session_login(user.id)

			# Show success message briefly
			self.show_status_message("Login successful! Loading application...", False)

			# IMPORTANT: Get the user ID before closing session
			user_id = user.id
			session.close()

			# Create a fresh session and get user object for main app
			fresh_session = Session()
			fresh_user = (fresh_session.query(User).options(joinedload(User.settings)).filter_by(id=user_id).first())
			fresh_session.close()

					# Delay before opening main app for better UX
			if self.master.winfo_exists():
					self.master.after(1000, lambda: self.open_main_app(fresh_user))

			else:
				# Failed login
				session.close()
				self.failed_attempts += 1
				self.last_attempt_time = datetime.now()

				if self.failed_attempts >= 3:
					self.show_status_message(
						"Too many failed attempts. Account locked for 5 minutes.", True
					)
				else:
					remaining_attempts = 3 - self.failed_attempts
					self.show_status_message(
						f"Invalid credentials. {remaining_attempts} attempts remaining.", True
					)

				# Clear password field
				self.password_var.set("")
				self.password_entry.focus()

		except Exception as e:
			self.show_status_message(f"Login error: {str(e)}", True)
			print(f"[ERROR] Login exception: {e}")

		finally:
			self.login_in_progress = False
			self.show_loading(False)

	def open_main_app(self, user):
		"""Open the main application window"""
		try:
			self.master.destroy()
			app = MainAppWindow(user)
			app.mainloop()
		except Exception as e:
			print(f"[ERROR] Failed to open main application: {e}")
			messagebox.showerror("Application Error",
								 f"Failed to load main application: {str(e)}")

	def load_saved_credentials(self):
		"""Load saved login credentials"""
		if os.path.exists(CONFIG_FILE):
			try:
				with open(CONFIG_FILE, "r") as f:
					data = json.load(f)
					self.username_var.set(data.get("username", ""))
					self.remember_var.set(data.get("remember", False))

					# Check if credentials are recent (within 30 days)
					saved_date = data.get("saved_date")
					if saved_date:
						saved_datetime = datetime.fromisoformat(saved_date)
						if datetime.now() - saved_datetime > timedelta(days=30):
							# Credentials too old, clear them
							self.username_var.set("")
							self.remember_var.set(False)

			except Exception as e:
				print(f"[ERROR] Loading saved credentials: {e}")

	def save_credentials(self):
		"""Save login credentials if remember me is checked"""
		try:
			if self.remember_var.get():
				data = {
					"username": self.username_var.get(),
					"remember": True,
					"saved_date": datetime.now().isoformat()
				}
				with open(CONFIG_FILE, "w") as f:
					json.dump(data, f)
			else:
				# Remove saved credentials
				if os.path.exists(CONFIG_FILE):
					os.remove(CONFIG_FILE)
		except Exception as e:
			print(f"[ERROR] Saving credentials: {e}")


# Main application entry point
def main():
	root = tk.Tk()
	app = LoginWindow(root)
	root.mainloop()


if __name__ == "__main__":
	main()
	def on_close(self):
		if hasattr(self, 'update_job_id'):
			try:
				self.master.after_cancel(self.update_job_id)
			except Exception:
				pass
		self.destroy()
