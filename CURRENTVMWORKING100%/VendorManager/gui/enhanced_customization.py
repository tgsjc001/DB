import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
from models import Session
from models.user import User
from utils.theme import apply_user_theme, apply_user_fonts
import json
import os


class EnhancedCustomizationWindow(tk.Frame):
	def __init__(self, parent, user):
		super().__init__(parent, bg="#1e1e1e")
		self.user = user
		self.parent = parent

		# Load current settings
		self.load_current_settings()

		# Create notebook for different customization categories
		self.notebook = ttk.Notebook(self)
		self.notebook.pack(fill="both", expand=True, padx=20, pady=20)

		# Build different customization tabs
		self.build_appearance_tab()
		self.build_fonts_tab()
		self.build_behavior_tab()
		self.build_shortcuts_tab()
		self.build_defaults_tab()

		# Save/Reset buttons
		self.build_action_buttons()

	def load_current_settings(self):
		"""Load current user settings"""
		self.settings = {
			# Theme settings
			'theme_mode': getattr(self.user, 'theme_mode', 'dark'),
			'accent_color': getattr(self.user, 'accent_color', '#ffdf00'),

			# Font settings
			'font': getattr(self.user, 'font', 'Segoe UI'),
			'font_size': getattr(self.user, 'font_size', 12),
			'font_label': getattr(self.user, 'font_label', 'Segoe UI'),
			'font_label_size': getattr(self.user, 'font_label_size', 12),
			'font_button': getattr(self.user, 'font_button', 'Segoe UI'),
			'font_button_size': getattr(self.user, 'font_button_size', 12),
			'font_entry': getattr(self.user, 'font_entry', 'Segoe UI'),
			'font_entry_size': getattr(self.user, 'font_entry_size', 12),
			'font_treeview': getattr(self.user, 'font_treeview', 'Segoe UI'),
			'font_treeview_size': getattr(self.user, 'font_treeview_size', 10),

			# Extended theme colors (new)
			'secondary_color': '#2e2e2e',
			'background_color': '#1e1e1e',
			'text_color': '#ffffff',
			'highlight_color': '#444444',

			# Behavior settings (new)
			'auto_save_enabled': True,
			'auto_save_interval': 5,  # minutes
			'confirm_deletions': True,
			'show_tooltips': True,
			'animation_speed': 'normal',
			'default_window_size': 'normal',

			# Default values (new)
			'default_electricity': False,
			'default_taca_member': False,
			'default_show_date': '04/06/2025',
			'default_export_format': 'PDF',
			'recent_searches_count': 10,

			# Column preferences (new)
			'vendor_columns_visible': ['name', 'location', 'phone', 'date', 'status', 'flags'],
			'vendor_column_widths': {'name': 120, 'location': 120, 'phone': 120, 'date': 120, 'status': 120,
									 'flags': 120},
			'mailout_columns_visible': ['name', 'address', 'city_state_zip', 'phone', 'email', 'date'],
		}

	def build_appearance_tab(self):
		"""Build appearance customization tab"""
		appearance_frame = tk.Frame(self.notebook, bg="#1e1e1e")
		self.notebook.add(appearance_frame, text="Appearance")

		# Scrollable content
		canvas = tk.Canvas(appearance_frame, bg="#1e1e1e", highlightthickness=0)
		scrollbar = ttk.Scrollbar(appearance_frame, orient="vertical", command=canvas.yview)
		scrollable_frame = tk.Frame(canvas, bg="#1e1e1e")

		scrollable_frame.bind(
			"<Configure>",
			lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
		)

		canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
		canvas.configure(yscrollcommand=scrollbar.set)

		# Theme Mode Section
		theme_section = tk.LabelFrame(scrollable_frame, text="Theme Mode",
									  bg="#1e1e1e", fg="#ffdf00", font=("Segoe UI", 12, "bold"))
		theme_section.pack(fill="x", padx=10, pady=10)

		self.theme_var = tk.StringVar(value=self.settings['theme_mode'])

		theme_options = [
			("Dark Theme", "dark", "Modern dark interface"),
			("Light Theme", "light", "Classic light interface"),
			("Auto", "auto", "Follow system settings"),
		]

		for text, value, description in theme_options:
			frame = tk.Frame(theme_section, bg="#1e1e1e")
			frame.pack(fill="x", padx=10, pady=5)

			tk.Radiobutton(frame, text=text, variable=self.theme_var, value=value,
						   bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
						   activebackground="#1e1e1e", font=("Segoe UI", 11)).pack(anchor="w")
			tk.Label(frame, text=description, bg="#1e1e1e", fg="#cccccc",
					 font=("Segoe UI", 9)).pack(anchor="w", padx=20)

		# Color Scheme Section
		colors_section = tk.LabelFrame(scrollable_frame, text="Color Scheme",
									   bg="#1e1e1e", fg="#ffdf00", font=("Segoe UI", 12, "bold"))
		colors_section.pack(fill="x", padx=10, pady=10)

		# Accent Color
		accent_frame = tk.Frame(colors_section, bg="#1e1e1e")
		accent_frame.pack(fill="x", padx=10, pady=5)

		tk.Label(accent_frame, text="Accent Color:", bg="#1e1e1e", fg="white",
				 font=("Segoe UI", 11)).pack(side="left")

		self.accent_color_var = tk.StringVar(value=self.settings['accent_color'])
		self.accent_color_preview = tk.Label(accent_frame, text="  Sample  ",
											 bg=self.settings['accent_color'], fg="black",
											 font=("Segoe UI", 10, "bold"))
		self.accent_color_preview.pack(side="right", padx=5)

		tk.Button(accent_frame, text="Choose Color", command=self.choose_accent_color,
				  bg="#2e2e2e", fg="white", font=("Segoe UI", 10)).pack(side="right", padx=5)

		# Preset Color Schemes
		presets_frame = tk.Frame(colors_section, bg="#1e1e1e")
		presets_frame.pack(fill="x", padx=10, pady=10)

		tk.Label(presets_frame, text="Preset Color Schemes:", bg="#1e1e1e", fg="white",
				 font=("Segoe UI", 11)).pack(anchor="w")

		preset_colors = [
			("Gold (Default)", "#ffdf00"),
			("Blue", "#4a90e2"),
			("Green", "#7ed321"),
			("Purple", "#9013fe"),
			("Orange", "#ff9500"),
			("Red", "#d0021b"),
		]

		preset_buttons_frame = tk.Frame(presets_frame, bg="#1e1e1e")
		preset_buttons_frame.pack(fill="x", pady=5)

		for i, (name, color) in enumerate(preset_colors):
			btn = tk.Button(preset_buttons_frame, text=name, bg=color,
							fg="black" if color in ["#ffdf00", "#7ed321", "#ff9500"] else "white",
							font=("Segoe UI", 9), relief="flat", bd=1,
							command=lambda c=color: self.set_accent_color(c))
			btn.grid(row=i // 3, column=i % 3, padx=2, pady=2, sticky="ew")

		# Configure grid weights
		for i in range(3):
			preset_buttons_frame.columnconfigure(i, weight=1)

		# Window Appearance
		window_section = tk.LabelFrame(scrollable_frame, text="Window Appearance",
									   bg="#1e1e1e", fg="#ffdf00", font=("Segoe UI", 12, "bold"))
		window_section.pack(fill="x", padx=10, pady=10)

		# Animation Speed
		anim_frame = tk.Frame(window_section, bg="#1e1e1e")
		anim_frame.pack(fill="x", padx=10, pady=5)

		tk.Label(anim_frame, text="Animation Speed:", bg="#1e1e1e", fg="white",
				 font=("Segoe UI", 11)).pack(side="left")

		self.animation_var = tk.StringVar(value=self.settings['animation_speed'])
		anim_combo = ttk.Combobox(anim_frame, textvariable=self.animation_var,
								  values=["disabled", "slow", "normal", "fast"], state="readonly")
		anim_combo.pack(side="right", padx=5)

		# Default Window Size
		size_frame = tk.Frame(window_section, bg="#1e1e1e")
		size_frame.pack(fill="x", padx=10, pady=5)

		tk.Label(size_frame, text="Default Window Size:", bg="#1e1e1e", fg="white",
				 font=("Segoe UI", 11)).pack(side="left")

		self.window_size_var = tk.StringVar(value=self.settings['default_window_size'])
		size_combo = ttk.Combobox(size_frame, textvariable=self.window_size_var,
								  values=["small", "normal", "large", "maximized"], state="readonly")
		size_combo.pack(side="right", padx=5)

		canvas.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")

	def build_fonts_tab(self):
		"""Build font customization tab"""
		fonts_frame = tk.Frame(self.notebook, bg="#1e1e1e")
		self.notebook.add(fonts_frame, text="Fonts")

		# Font options
		font_families = ["Segoe UI", "Arial", "Helvetica", "Times New Roman",
						 "Courier New", "Calibri", "Verdana", "Tahoma", "Georgia"]
		font_sizes = list(range(8, 25))

		# Create font setting controls
		font_settings = [
			("Global Font", "font", "font_size"),
			("Labels", "font_label", "font_label_size"),
			("Buttons", "font_button", "font_button_size"),
			("Text Fields", "font_entry", "font_entry_size"),
			("Lists/Tables", "font_treeview", "font_treeview_size"),
		]

		self.font_vars = {}
		self.font_size_vars = {}

		for label, font_key, size_key in font_settings:
			section = tk.LabelFrame(fonts_frame, text=f"{label} Font",
									bg="#1e1e1e", fg="#ffdf00", font=("Segoe UI", 11, "bold"))
			section.pack(fill="x", padx=20, pady=10)

			frame = tk.Frame(section, bg="#1e1e1e")
			frame.pack(fill="x", padx=10, pady=10)

			# Font Family
			tk.Label(frame, text="Family:", bg="#1e1e1e", fg="white",
					 font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=5)

			self.font_vars[font_key] = tk.StringVar(value=self.settings[font_key])
			font_combo = ttk.Combobox(frame, textvariable=self.font_vars[font_key],
									  values=font_families, width=15)
			font_combo.grid(row=0, column=1, padx=5, sticky="w")

			# Font Size
			tk.Label(frame, text="Size:", bg="#1e1e1e", fg="white",
					 font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", padx=(20, 5))

			self.font_size_vars[size_key] = tk.IntVar(value=self.settings[size_key])
			size_spin = tk.Spinbox(frame, textvariable=self.font_size_vars[size_key],
								   from_=8, to=24, width=5)
			size_spin.grid(row=0, column=3, padx=5, sticky="w")

			# Preview
			preview_text = f"Sample {label} Text"
			preview_label = tk.Label(frame, text=preview_text, bg="#2e2e2e", fg="white",
									 font=(self.settings[font_key], self.settings[size_key]))
			preview_label.grid(row=1, column=0, columnspan=4, pady=10, sticky="ew")

			# Update preview on change
			def update_preview(font_var=self.font_vars[font_key],
							   size_var=self.font_size_vars[size_key],
							   preview=preview_label):
				try:
					preview.configure(font=(font_var.get(), size_var.get()))
				except:
					pass

			font_combo.bind("<<ComboboxSelected>>", lambda e, up=update_preview: up())
			size_spin.bind("<KeyRelease>", lambda e, up=update_preview: up())

	def build_behavior_tab(self):
		"""Build behavior customization tab"""
		behavior_frame = tk.Frame(self.notebook, bg="#1e1e1e")
		self.notebook.add(behavior_frame, text="Behavior")

		# Auto-save Section
		autosave_section = tk.LabelFrame(behavior_frame, text="Auto-Save Settings",
										 bg="#1e1e1e", fg="#ffdf00", font=("Segoe UI", 12, "bold"))
		autosave_section.pack(fill="x", padx=20, pady=10)

		autosave_frame = tk.Frame(autosave_section, bg="#1e1e1e")
		autosave_frame.pack(fill="x", padx=10, pady=10)

		self.auto_save_var = tk.BooleanVar(value=self.settings['auto_save_enabled'])
		tk.Checkbutton(autosave_frame, text="Enable auto-save", variable=self.auto_save_var,
					   bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
					   activebackground="#1e1e1e", font=("Segoe UI", 11)).pack(anchor="w")

		interval_frame = tk.Frame(autosave_frame, bg="#1e1e1e")
		interval_frame.pack(fill="x", pady=5)

		tk.Label(interval_frame, text="Auto-save interval:", bg="#1e1e1e", fg="white",
				 font=("Segoe UI", 11)).pack(side="left")

		self.auto_save_interval_var = tk.IntVar(value=self.settings['auto_save_interval'])
		tk.Spinbox(interval_frame, textvariable=self.auto_save_interval_var,
				   from_=1, to=60, width=5).pack(side="left", padx=5)
		tk.Label(interval_frame, text="minutes", bg="#1e1e1e", fg="white",
				 font=("Segoe UI", 11)).pack(side="left")

		# Confirmation Settings
		confirm_section = tk.LabelFrame(behavior_frame, text="Confirmation Settings",
										bg="#1e1e1e", fg="#ffdf00", font=("Segoe UI", 12, "bold"))
		confirm_section.pack(fill="x", padx=20, pady=10)

		confirm_frame = tk.Frame(confirm_section, bg="#1e1e1e")
		confirm_frame.pack(fill="x", padx=10, pady=10)

		self.confirm_deletions_var = tk.BooleanVar(value=self.settings['confirm_deletions'])
		tk.Checkbutton(confirm_frame, text="Confirm before deleting records",
					   variable=self.confirm_deletions_var,
					   bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
					   activebackground="#1e1e1e", font=("Segoe UI", 11)).pack(anchor="w")

		self.show_tooltips_var = tk.BooleanVar(value=self.settings['show_tooltips'])
		tk.Checkbutton(confirm_frame, text="Show helpful tooltips",
					   variable=self.show_tooltips_var,
					   bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
					   activebackground="#1e1e1e", font=("Segoe UI", 11)).pack(anchor="w")

		# Search Settings
		search_section = tk.LabelFrame(behavior_frame, text="Search & History",
									   bg="#1e1e1e", fg="#ffdf00", font=("Segoe UI", 12, "bold"))
		search_section.pack(fill="x", padx=20, pady=10)

		search_frame = tk.Frame(search_section, bg="#1e1e1e")
		search_frame.pack(fill="x", padx=10, pady=10)

		tk.Label(search_frame, text="Remember recent searches:", bg="#1e1e1e", fg="white",
				 font=("Segoe UI", 11)).pack(side="left")

		self.recent_searches_var = tk.IntVar(value=self.settings['recent_searches_count'])
		tk.Spinbox(search_frame, textvariable=self.recent_searches_var,
				   from_=0, to=50, width=5).pack(side="right", padx=5)

	def build_shortcuts_tab(self):
		"""Build keyboard shortcuts customization tab"""
		shortcuts_frame = tk.Frame(self.notebook, bg="#1e1e1e")
		self.notebook.add(shortcuts_frame, text="Keyboard Shortcuts")

		# Info section
		info_section = tk.Frame(shortcuts_frame, bg="#1e1e1e")
		info_section.pack(fill="x", padx=20, pady=10)

		tk.Label(info_section, text="Keyboard Shortcuts", bg="#1e1e1e", fg="#ffdf00",
				 font=("Segoe UI", 16, "bold")).pack(anchor="w")
		tk.Label(info_section, text="Customize keyboard shortcuts for faster workflow",
				 bg="#1e1e1e", fg="white", font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 10))

		# Current shortcuts display
		shortcuts_text = tk.Text(shortcuts_frame, bg="#2e2e2e", fg="white",
								 font=("Consolas", 10), height=20, wrap="word")
		shortcuts_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

		shortcuts_content = """
CURRENT KEYBOARD SHORTCUTS
==========================

Form Operations:
Ctrl+S          Save current form
Ctrl+D          Delete current record
Ctrl+P          Print current form
Ctrl+N          New record (return to main window)
Escape          Cancel/close form

Navigation:
Tab             Next field
Shift+Tab       Previous field
Ctrl+Tab        Next section
F2-F4           Quick field access

Vendor Forms:
Ctrl+1          Focus 6ft tables
Ctrl+2          Focus 8ft tables  
Ctrl+3          Focus location fields
Ctrl+4          Focus payment fields
Ctrl+E          Toggle electricity
Ctrl+T          Toggle TACA membership
Ctrl+R          Recalculate totals

Text Editing:
Ctrl+A          Select all
Ctrl+C          Copy
Ctrl+V          Paste
Ctrl+X          Cut

System:
F1              Show help
F5              Refresh current view
F12             Show all shortcuts
Ctrl+F          Focus search
        """

		shortcuts_text.insert("1.0", shortcuts_content.strip())
		shortcuts_text.configure(state="disabled")

		# Future: Add customizable shortcut editing interface
		tk.Label(shortcuts_frame, text="Note: Shortcut customization coming in future update",
				 bg="#1e1e1e", fg="#cccccc", font=("Segoe UI", 10, "italic")).pack(pady=10)

	def build_defaults_tab(self):
		"""Build default values customization tab"""
		defaults_frame = tk.Frame(self.notebook, bg="#1e1e1e")
		self.notebook.add(defaults_frame, text="Defaults")

		# Vendor Defaults
		vendor_section = tk.LabelFrame(defaults_frame, text="New Vendor Defaults",
									   bg="#1e1e1e", fg="#ffdf00", font=("Segoe UI", 12, "bold"))
		vendor_section.pack(fill="x", padx=20, pady=10)

		vendor_frame = tk.Frame(vendor_section, bg="#1e1e1e")
		vendor_frame.pack(fill="x", padx=10, pady=10)

		# Show date default
		show_date_frame = tk.Frame(vendor_frame, bg="#1e1e1e")
		show_date_frame.pack(fill="x", pady=5)

		tk.Label(show_date_frame, text="Default Show Date:", bg="#1e1e1e", fg="white",
				 font=("Segoe UI", 11)).pack(side="left")

		self.show_date_var = tk.StringVar(value=self.settings['default_show_date'])
		tk.Entry(show_date_frame, textvariable=self.show_date_var, width=12,
				 bg="#2e2e2e", fg="white").pack(side="right", padx=5)

		# Default checkboxes
		self.default_electricity_var = tk.BooleanVar(value=self.settings['default_electricity'])
		tk.Checkbutton(vendor_frame, text="Electricity enabled by default",
					   variable=self.default_electricity_var,
					   bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
					   activebackground="#1e1e1e", font=("Segoe UI", 11)).pack(anchor="w", pady=2)

		self.default_taca_var = tk.BooleanVar(value=self.settings['default_taca_member'])
		tk.Checkbutton(vendor_frame, text="TACA member enabled by default",
					   variable=self.default_taca_var,
					   bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
					   activebackground="#1e1e1e", font=("Segoe UI", 11)).pack(anchor="w", pady=2)

		# Export Defaults
		export_section = tk.LabelFrame(defaults_frame, text="Export Defaults",
									   bg="#1e1e1e", fg="#ffdf00", font=("Segoe UI", 12, "bold"))
		export_section.pack(fill="x", padx=20, pady=10)

		export_frame = tk.Frame(export_section, bg="#1e1e1e")
		export_frame.pack(fill="x", padx=10, pady=10)

		tk.Label(export_frame, text="Default Export Format:", bg="#1e1e1e", fg="white",
				 font=("Segoe UI", 11)).pack(side="left")

		self.export_format_var = tk.StringVar(value=self.settings['default_export_format'])
		export_combo = ttk.Combobox(export_frame, textvariable=self.export_format_var,
									values=["PDF", "TXT", "CSV", "Excel"], state="readonly")
		export_combo.pack(side="right", padx=5)

		# Column Defaults
		columns_section = tk.LabelFrame(defaults_frame, text="Column Display",
										bg="#1e1e1e", fg="#ffdf00", font=("Segoe UI", 12, "bold"))
		columns_section.pack(fill="x", padx=20, pady=10)

		columns_frame = tk.Frame(columns_section, bg="#1e1e1e")
		columns_frame.pack(fill="x", padx=10, pady=10)

		tk.Label(columns_frame, text="Vendor List Columns:", bg="#1e1e1e", fg="white",
				 font=("Segoe UI", 11)).pack(anchor="w")

		# Checkboxes for vendor columns
		vendor_columns = ["name", "location", "phone", "date", "status", "flags"]
		self.column_vars = {}

		col_checkboxes = tk.Frame(columns_frame, bg="#1e1e1e")
		col_checkboxes.pack(fill="x", pady=5)

		for i, col in enumerate(vendor_columns):
			var = tk.BooleanVar(value=col in self.settings['vendor_columns_visible'])
			self.column_vars[col] = var

			tk.Checkbutton(col_checkboxes, text=col.title(), variable=var,
						   bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
						   activebackground="#1e1e1e", font=("Segoe UI", 10)).grid(
				row=i // 3, column=i % 3, sticky="w", padx=5, pady=2)

	def build_action_buttons(self):
		"""Build save/reset action buttons"""
		action_frame = tk.Frame(self, bg="#1e1e1e")
		action_frame.pack(fill="x", padx=20, pady=20)

		# Save button
		tk.Button(action_frame, text="Save All Settings", command=self.save_all_settings,
				  bg="#ffdf00", fg="black", font=("Segoe UI", 12, "bold"),
				  padx=20, pady=8).pack(side="left", padx=5)

		# Apply button (save + apply immediately)
		tk.Button(action_frame, text="Apply Changes", command=self.apply_settings,
				  bg="#2e2e2e", fg="white", font=("Segoe UI", 12),
				  padx=20, pady=8).pack(side="left", padx=5)

		# Reset to defaults
		tk.Button(action_frame, text="Reset to Defaults", command=self.reset_to_defaults,
				  bg="#444444", fg="white", font=("Segoe UI", 12),
				  padx=20, pady=8).pack(side="left", padx=5)

		# Import/Export settings
		tk.Button(action_frame, text="Export Settings", command=self.export_settings,
				  bg="#2e2e2e", fg="white", font=("Segoe UI", 10),
				  padx=15, pady=8).pack(side="right", padx=5)

		tk.Button(action_frame, text="Import Settings", command=self.import_settings,
				  bg="#2e2e2e", fg="white", font=("Segoe UI", 10),
				  padx=15, pady=8).pack(side="right", padx=5)

	def choose_accent_color(self):
		"""Open color chooser for accent color"""
		color = colorchooser.askcolor(title="Choose Accent Color",
									  color=self.accent_color_var.get())[1]
		if color:
			self.set_accent_color(color)

	def set_accent_color(self, color):
		"""Set the accent color and update preview"""
		self.accent_color_var.set(color)
		self.accent_color_preview.configure(bg=color)
		# Update preview text color based on brightness
		text_color = "black" if self.is_light_color(color) else "white"
		self.accent_color_preview.configure(fg=text_color)

	def is_light_color(self, color):
		"""Determine if a color is light (for text color selection)"""
		try:
			# Remove # if present
			color = color.lstrip('#')
			# Convert to RGB
			r, g, b = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
			# Calculate brightness
			brightness = (r * 299 + g * 587 + b * 114) / 1000
			return brightness > 128
		except:
			return False

	def save_all_settings(self):
		"""Save all settings to database"""
		try:
			# Collect all settings
			updated_settings = {
				'theme_mode': self.theme_var.get(),
				'accent_color': self.accent_color_var.get(),
				'animation_speed': self.animation_var.get(),
				'default_window_size': self.window_size_var.get(),
				'auto_save_enabled': self.auto_save_var.get(),
				'auto_save_interval': self.auto_save_interval_var.get(),
				'confirm_deletions': self.confirm_deletions_var.get(),
				'show_tooltips': self.show_tooltips_var.get(),
				'recent_searches_count': self.recent_searches_var.get(),
				'default_show_date': self.show_date_var.get(),
				'default_electricity': self.default_electricity_var.get(),
				'default_taca_member': self.default_taca_var.get(),
				'default_export_format': self.export_format_var.get(),
				'vendor_columns_visible': [col for col, var in self.column_vars.items() if var.get()]
			}

			# Add font settings
			for font_key, var in self.font_vars.items():
				updated_settings[font_key] = var.get()

			for size_key, var in self.font_size_vars.items():
				updated_settings[size_key] = var.get()

			# Update database
			session = Session()
			db_user = session.query(User).filter_by(id=self.user.id).first()
			if not db_user:
				session.close()
				return

			# Update user object with new settings
			for key, value in updated_settings.items():
				if hasattr(db_user, key):
					setattr(db_user, key, value)

			session.commit()

			# Update current user reference
			self.user = db_user

			session.close()

			messagebox.showinfo("Settings Saved",
								"Your settings have been saved successfully.\n"
								"Some changes may require restarting the application.")

		except Exception as e:
			messagebox.showerror("Save Error", f"Failed to save settings: {e}")

	def apply_settings(self):
		"""Save and immediately apply settings"""
		self.save_all_settings()

		# Apply theme changes immediately
		try:
			apply_user_theme(self.parent, self.user)
			apply_user_fonts(self.parent, self.user)
		except Exception as e:
			print(f"[ERROR] Applying theme: {e}")

	def reset_to_defaults(self):
		"""Reset all settings to defaults"""
		if not messagebox.askyesno("Reset Settings",
								   "Reset all settings to defaults? This cannot be undone."):
			return

		# Reset all variables to defaults
		self.theme_var.set("dark")
		self.set_accent_color("#ffdf00")
		self.animation_var.set("normal")
		self.window_size_var.set("normal")
		self.auto_save_var.set(True)
		self.auto_save_interval_var.set(5)
		self.confirm_deletions_var.set(True)
		self.show_tooltips_var.set(True)
		self.recent_searches_var.set(10)
		self.show_date_var.set("04/06/2025")
		self.default_electricity_var.set(False)
		self.default_taca_var.set(False)
		self.export_format_var.set("PDF")

		# Reset fonts
		for var in self.font_vars.values():
			var.set("Segoe UI")
		for var in self.font_size_vars.values():
			var.set(12)

		# Reset columns
		for col, var in self.column_vars.items():
			var.set(True)  # All columns visible by default

		messagebox.showinfo("Settings Reset", "All settings have been reset to defaults.")

	def export_settings(self):
		"""Export current settings to file"""
		try:
			filename = filedialog.asksaveasfilename(
				title="Export Settings",
				defaultextension=".json",
				filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
			)

			if not filename:
				return

			# Collect current settings
			settings_export = {}
			settings_export['theme_mode'] = self.theme_var.get()
			settings_export['accent_color'] = self.accent_color_var.get()

			# Add all other settings...
			for key, var in self.font_vars.items():
				settings_export[key] = var.get()
			for key, var in self.font_size_vars.items():
				settings_export[key] = var.get()

			settings_export['export_timestamp'] = datetime.now().isoformat()
			settings_export['exported_by'] = self.user.username

			with open(filename, 'w') as f:
				json.dump(settings_export, f, indent=2)

			messagebox.showinfo("Export Complete", f"Settings exported to: {filename}")

		except Exception as e:
			messagebox.showerror("Export Error", f"Failed to export settings: {e}")

	def import_settings(self):
		"""Import settings from file"""
		try:
			filename = filedialog.askopenfilename(
				title="Import Settings",
				filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
			)

			if not filename:
				return

			with open(filename, 'r') as f:
				imported_settings = json.load(f)

			# Apply imported settings
			if 'theme_mode' in imported_settings:
				self.theme_var.set(imported_settings['theme_mode'])
			if 'accent_color' in imported_settings:
				self.set_accent_color(imported_settings['accent_color'])

			# Apply font settings
			for key, var in self.font_vars.items():
				if key in imported_settings:
					var.set(imported_settings[key])

			for key, var in self.font_size_vars.items():
				if key in imported_settings:
					var.set(imported_settings[key])

			messagebox.showinfo("Import Complete",
								"Settings imported successfully.\n"
								"Click 'Apply Changes' to use the new settings.")

		except Exception as e:
			messagebox.showerror("Import Error", f"Failed to import settings: {e}")