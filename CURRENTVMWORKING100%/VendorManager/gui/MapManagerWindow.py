import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from models import Session
from models.vendor import Vendor
from utils.theme import apply_user_theme


class MapManagerWindow(tk.Frame):
	def __init__(self, master, user):
		super().__init__(master, bg="#1e1e1e")
		self.master = master
		self.user = user
		self.current_user = user
		self.map_scale = 1.0
		self.current_map_image = None
		self.selected_vendor_id = None

		apply_user_theme(self, user)
		print("[DEBUG] MapManagerWindow __init__ starting")
		self.build_layout()
		self.setup_map_coordinates()
		self.update_map_view()
		print("[DEBUG] MapManagerWindow __init__ complete")

	def build_layout(self):
		"""Build the map manager interface"""
		print("[DEBUG] build_layout starting")

		# Map controls
		control_frame = tk.Frame(self, bg="#1e1e1e")
		control_frame.pack(fill="x", padx=10, pady=10)

		# Level selection
		tk.Label(control_frame, text="Level:", fg="#ffdf00", bg="#1e1e1e", font=("Arial", 12, "bold")).pack(side="left")

		self.map_level_var = tk.StringVar(value="upper")
		level_frame = tk.Frame(control_frame, bg="#1e1e1e")
		level_frame.pack(side="left", padx=10)

		tk.Radiobutton(level_frame, text="Upper Level", variable=self.map_level_var, value="upper",
					   command=self.update_map_view, bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
					   font=("Arial", 10)).pack(side="left", padx=5)
		tk.Radiobutton(level_frame, text="Lower Level", variable=self.map_level_var, value="lower",
					   command=self.update_map_view, bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
					   font=("Arial", 10)).pack(side="left", padx=5)

		# Map controls
		controls_frame = tk.Frame(control_frame, bg="#1e1e1e")
		controls_frame.pack(side="left", padx=20)

		tk.Button(controls_frame, text="Refresh Map", command=self.update_map_view,
				  bg="#2e2e2e", fg="white", font=("Arial", 10)).pack(side="left", padx=5)
		tk.Button(controls_frame, text="Zoom In", command=self.zoom_in,
				  bg="#2e2e2e", fg="white", font=("Arial", 10)).pack(side="left", padx=5)
		tk.Button(controls_frame, text="Zoom Out", command=self.zoom_out,
				  bg="#2e2e2e", fg="white", font=("Arial", 10)).pack(side="left", padx=5)
		tk.Button(controls_frame, text="Reset Zoom", command=self.reset_zoom,
				  bg="#2e2e2e", fg="white", font=("Arial", 10)).pack(side="left", padx=5)

		# Vendor Map Generation
		generation_frame = tk.Frame(control_frame, bg="#1e1e1e")
		generation_frame.pack(side="left", padx=20)

		tk.Button(generation_frame, text="Generate All Vendor Maps", command=self.generate_all_vendor_maps,
				  bg="#4a4a4a", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
		tk.Button(generation_frame, text="Generate Selected Map", command=self.generate_selected_vendor_map,
				  bg="#3a3a3a", fg="white", font=("Arial", 10)).pack(side="left", padx=5)

		# Display options
		options_frame = tk.Frame(control_frame, bg="#1e1e1e")
		options_frame.pack(side="left", padx=20)

		self.show_all_vendors = tk.BooleanVar(value=True)
		tk.Checkbutton(options_frame, text="Show All Vendors", variable=self.show_all_vendors,
					   command=self.update_map_view, bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
					   font=("Arial", 10)).pack(side="left", padx=5)

		self.show_vendor_names = tk.BooleanVar(value=True)
		tk.Checkbutton(options_frame, text="Show Names", variable=self.show_vendor_names,
					   command=self.update_map_view, bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
					   font=("Arial", 10)).pack(side="left", padx=5)

		# Selected vendor info
		info_frame = tk.Frame(control_frame, bg="#1e1e1e")
		info_frame.pack(side="right", padx=10)

		self.selected_vendor_label = tk.Label(info_frame, text="Click a highlighted table to see vendor details",
											  bg="#1e1e1e", fg="#ffdf00", font=("Arial", 10))
		self.selected_vendor_label.pack(side="right")

		tk.Button(info_frame, text="View Vendor", command=self.view_selected_vendor,
				  bg="#2e2e2e", fg="white", font=("Arial", 10)).pack(side="right", padx=(0, 10))

		# Canvas container with scrollbars
		canvas_frame = tk.Frame(self, bg="#1e1e1e")
		canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

		# Create canvas with scrollbars
		self.map_canvas = tk.Canvas(canvas_frame, bg="#2e2e2e", highlightthickness=0)
		v_scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.map_canvas.yview)
		h_scrollbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=self.map_canvas.xview)
		self.map_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

		# Grid layout
		self.map_canvas.grid(row=0, column=0, sticky="nsew")
		v_scrollbar.grid(row=0, column=1, sticky="ns")
		h_scrollbar.grid(row=1, column=0, sticky="ew")

		canvas_frame.grid_rowconfigure(0, weight=1)
		canvas_frame.grid_columnconfigure(0, weight=1)

		# Bind canvas events
		self.map_canvas.bind("<Button-1>", self.on_map_click)
		self.map_canvas.bind("<MouseWheel>", self.on_map_scroll)
		self.map_canvas.bind("<Control-MouseWheel>", self.on_map_zoom)

		# Status bar
		status_frame = tk.Frame(self, bg="#2e2e2e", height=30)
		status_frame.pack(fill="x", side="bottom", padx=5, pady=2)
		status_frame.pack_propagate(False)

		self.status_label = tk.Label(status_frame, text="Map loaded - Click tables to view vendor details",
									 bg="#2e2e2e", fg="white", font=("Arial", 9))
		self.status_label.pack(side="left", padx=10, pady=5)

		zoom_label = tk.Label(status_frame, text="Zoom: Ctrl+Wheel | Pan: Drag",
							  bg="#2e2e2e", fg="#cccccc", font=("Arial", 9))
		zoom_label.pack(side="right", padx=10, pady=5)

		print("[DEBUG] build_layout complete")

	def setup_map_coordinates(self):
		"""Define table coordinates for each layout map"""
		# Upper Level Table Coordinates (based on your upper level image)
		# These coordinates are approximated from your image - adjust as needed for pixel-perfect accuracy
		self.upper_level_coords = {
			# Row A tables (leftmost column)
			"A1": (140, 680, 35, 20), "A2": (140, 655, 35, 20), "A3": (140, 630, 35, 20), "A4": (140, 605, 35, 20),
			"A5": (140, 580, 35, 20), "A6": (140, 555, 35, 20), "A7": (140, 530, 35, 20), "A8": (140, 505, 35, 20),
			"A9": (140, 480, 35, 20), "A10": (140, 455, 35, 20), "A11": (140, 430, 35, 20), "A12": (140, 405, 35, 20),
			"A13": (140, 380, 35, 20), "A14": (140, 355, 35, 20), "A15": (140, 330, 35, 20), "A16": (140, 305, 35, 20),
			"A17": (140, 280, 35, 20), "A18": (140, 255, 35, 20), "A19": (140, 230, 35, 20), "A20": (140, 205, 35, 20),
			"A21": (140, 180, 35, 20), "A22": (140, 155, 35, 20), "A23": (140, 130, 35, 20), "A24": (140, 105, 35, 20),
			"A25": (140, 80, 35, 20), "A26": (140, 55, 35, 20), "A27": (140, 30, 35, 20), "A28": (140, 705, 35, 20),
			"A29": (140, 730, 35, 20), "A30": (140, 755, 35, 20), "A31": (140, 780, 35, 20), "A32": (140, 805, 35, 20),
			"A33": (140, 830, 35, 20), "A34": (140, 855, 35, 20), "A35": (140, 880, 35, 20), "A36": (140, 905, 35, 20),
			"A37": (140, 930, 35, 20),

			# Row B tables
			"B1": (200, 680, 35, 20), "B2": (200, 655, 35, 20), "B3": (200, 630, 35, 20), "B4": (200, 605, 35, 20),
			"B5": (200, 580, 35, 20), "B6": (200, 555, 35, 20), "B7": (200, 530, 35, 20), "B8": (200, 505, 35, 20),
			"B9": (200, 480, 35, 20), "B10": (200, 455, 35, 20), "B11": (200, 430, 35, 20), "B12": (200, 405, 35, 20),
			"B13": (200, 380, 35, 20), "B14": (200, 355, 35, 20), "B15": (200, 330, 35, 20), "B16": (200, 305, 35, 20),
			"B17": (200, 280, 35, 20), "B18": (200, 255, 35, 20), "B19": (200, 230, 35, 20), "B20": (200, 205, 35, 20),
			"B21": (200, 180, 35, 20), "B22": (200, 155, 35, 20), "B23": (200, 130, 35, 20), "B24": (200, 105, 35, 20),
			"B25": (200, 80, 35, 20), "B26": (200, 55, 35, 20), "B27": (200, 30, 35, 20), "B28": (200, 705, 35, 20),
			"B29": (200, 730, 35, 20), "B30": (200, 755, 35, 20), "B31": (200, 780, 35, 20), "B32": (200, 805, 35, 20),
			"B33": (200, 830, 35, 20), "B34": (200, 855, 35, 20), "B35": (200, 880, 35, 20), "B36": (200, 905, 35, 20),
			"B37": (200, 930, 35, 20),

			# Row C tables
			"C1": (260, 680, 35, 20), "C2": (260, 655, 35, 20), "C3": (260, 630, 35, 20), "C4": (260, 605, 35, 20),
			"C5": (260, 580, 35, 20), "C6": (260, 555, 35, 20), "C7": (260, 530, 35, 20), "C8": (260, 505, 35, 20),
			"C9": (260, 480, 35, 20), "C10": (260, 455, 35, 20), "C11": (260, 430, 35, 20), "C12": (260, 405, 35, 20),
			"C13": (260, 380, 35, 20), "C14": (260, 355, 35, 20), "C15": (260, 330, 35, 20), "C16": (260, 305, 35, 20),
			"C17": (260, 280, 35, 20), "C18": (260, 255, 35, 20), "C19": (260, 230, 35, 20), "C20": (260, 205, 35, 20),
			"C21": (260, 180, 35, 20), "C22": (260, 155, 35, 20), "C23": (260, 130, 35, 20), "C24": (260, 105, 35, 20),
			"C25": (260, 80, 35, 20), "C26": (260, 55, 35, 20), "C27": (260, 30, 35, 20), "C28": (260, 705, 35, 20),
			"C29": (260, 730, 35, 20), "C30": (260, 755, 35, 20), "C31": (260, 780, 35, 20), "C32": (260, 805, 35, 20),
			"C33": (260, 830, 35, 20), "C34": (260, 855, 35, 20), "C35": (260, 880, 35, 20), "C36": (260, 905, 35, 20),
			"C37": (260, 930, 35, 20),

			# Row D tables
			"D1": (320, 680, 35, 20), "D2": (320, 655, 35, 20), "D3": (320, 630, 35, 20), "D4": (320, 605, 35, 20),
			"D5": (320, 580, 35, 20), "D6": (320, 555, 35, 20), "D7": (320, 530, 35, 20), "D8": (320, 505, 35, 20),
			"D9": (320, 480, 35, 20), "D10": (320, 455, 35, 20), "D11": (320, 430, 35, 20), "D12": (320, 405, 35, 20),
			"D13": (320, 380, 35, 20), "D14": (320, 355, 35, 20), "D15": (320, 330, 35, 20), "D16": (320, 305, 35, 20),
			"D17": (320, 280, 35, 20), "D18": (320, 255, 35, 20), "D19": (320, 230, 35, 20), "D20": (320, 205, 35, 20),
			"D21": (320, 180, 35, 20), "D22": (320, 155, 35, 20), "D23": (320, 130, 35, 20), "D24": (320, 105, 35, 20),
			"D25": (320, 80, 35, 20), "D26": (320, 55, 35, 20), "D27": (320, 30, 35, 20), "D28": (320, 705, 35, 20),
			"D29": (320, 730, 35, 20), "D30": (320, 755, 35, 20), "D31": (320, 780, 35, 20), "D32": (320, 805, 35, 20),
			"D33": (320, 830, 35, 20), "D34": (320, 855, 35, 20), "D35": (320, 880, 35, 20), "D36": (320, 905, 35, 20),
			"D37": (320, 930, 35, 20),

			# E Row tables (right side) - These are rotated 90 degrees
			"E1": (380, 680, 20, 35), "E2": (380, 655, 20, 35), "E3": (380, 630, 20, 35), "E4": (380, 605, 20, 35),
			"E5": (380, 580, 20, 35), "E6": (380, 555, 20, 35), "E7": (380, 530, 20, 35), "E8": (380, 505, 20, 35),
			"E9": (380, 480, 20, 35), "E10": (380, 455, 20, 35), "E11": (380, 430, 20, 35), "E12": (380, 405, 20, 35),
			"E13": (380, 380, 20, 35), "E14": (380, 355, 20, 35), "E15": (380, 330, 20, 35), "E16": (380, 305, 20, 35),
			"E17": (380, 280, 20, 35), "E18": (380, 255, 20, 35), "E19": (380, 230, 20, 35), "E20": (380, 205, 20, 35),
			"E21": (380, 180, 20, 35), "E22": (380, 155, 20, 35), "E23": (380, 130, 20, 35), "E24": (380, 105, 20, 35),
			"E25": (380, 80, 20, 35), "E26": (380, 55, 20, 35), "E27": (380, 30, 20, 35), "E28": (380, 705, 20, 35),
			"E29": (380, 730, 20, 35), "E30": (380, 755, 20, 35), "E31": (380, 780, 20, 35)
		}

		# Lower level coordinates (based on your lower level images)
		# Format: "RowColumn": (x, y, width, height) - pixel coordinates
		self.lower_level_coords = {
			# Row 1 tables (columns A-D)
			"1A": (140, 680, 35, 20), "1B": (200, 680, 35, 20), "1C": (260, 680, 35, 20), "1D": (320, 680, 35, 20),

			# Row 2 tables
			"2A": (140, 655, 35, 20), "2B": (200, 655, 35, 20), "2C": (260, 655, 35, 20), "2D": (320, 655, 35, 20),

			# Row 3 tables
			"3A": (140, 630, 35, 20), "3B": (200, 630, 35, 20), "3C": (260, 630, 35, 20), "3D": (320, 630, 35, 20),

			# Row 4 tables
			"4A": (140, 605, 35, 20), "4B": (200, 605, 35, 20), "4C": (260, 605, 35, 20), "4D": (320, 605, 35, 20),

			# Row 5 tables
			"5A": (140, 580, 35, 20), "5B": (200, 580, 35, 20), "5C": (260, 580, 35, 20), "5D": (320, 580, 35, 20),

			# Row 6 tables
			"6A": (140, 555, 35, 20), "6B": (200, 555, 35, 20), "6C": (260, 555, 35, 20), "6D": (320, 555, 35, 20),

			# Row 7 tables
			"7A": (140, 530, 35, 20), "7B": (200, 530, 35, 20), "7C": (260, 530, 35, 20), "7D": (320, 530, 35, 20),

			# Row 8 tables
			"8A": (140, 505, 35, 20), "8B": (200, 505, 35, 20), "8C": (260, 505, 35, 20), "8D": (320, 505, 35, 20),

			# Row 9 tables
			"9A": (140, 480, 35, 20), "9B": (200, 480, 35, 20), "9C": (260, 480, 35, 20), "9D": (320, 480, 35, 20),

			# Row 10 tables
			"10A": (140, 455, 35, 20), "10B": (200, 455, 35, 20), "10C": (260, 455, 35, 20), "10D": (320, 455, 35, 20),

			# Row 11 tables
			"11A": (140, 430, 35, 20), "11B": (200, 430, 35, 20), "11C": (260, 430, 35, 20), "11D": (320, 430, 35, 20),

			# Row 12 tables
			"12A": (140, 405, 35, 20), "12B": (200, 405, 35, 20), "12C": (260, 405, 35, 20), "12D": (320, 405, 35, 20),

			# Row 13 tables
			"13A": (140, 380, 35, 20), "13B": (200, 380, 35, 20), "13C": (260, 380, 35, 20), "13D": (320, 380, 35, 20),

			# Row 14 tables
			"14A": (140, 355, 35, 20), "14B": (200, 355, 35, 20), "14C": (260, 355, 35, 20), "14D": (320, 355, 35, 20),

			# Row 15 tables
			"15A": (140, 330, 35, 20), "15B": (200, 330, 35, 20), "15C": (260, 330, 35, 20), "15D": (320, 330, 35, 20),

			# Row 16 tables
			"16A": (140, 305, 35, 20), "16B": (200, 305, 35, 20), "16C": (260, 305, 35, 20), "16D": (320, 305, 35, 20),

			# Row 17 tables
			"17A": (140, 280, 35, 20), "17B": (200, 280, 35, 20), "17C": (260, 280, 35, 20), "17D": (320, 280, 35, 20),

			# Row 18 tables
			"18A": (140, 255, 35, 20), "18B": (200, 255, 35, 20), "18C": (260, 255, 35, 20), "18D": (320, 255, 35, 20),

			# East wall tables (XLN series)
			"1XLN": (380, 680, 20, 35), "2XLN": (380, 655, 20, 35), "3XLN": (380, 630, 20, 35),
			"4XLN": (380, 605, 20, 35), "5XLN": (380, 580, 20, 35), "6XLN": (380, 555, 20, 35),
			"7XLN": (380, 530, 20, 35), "8XLN": (380, 505, 20, 35), "9XLN": (380, 480, 20, 35),
			"10XLN": (380, 455, 20, 35), "11XLN": (380, 430, 20, 35), "12XLN": (380, 405, 20, 35),
			"13XLN": (380, 380, 20, 35), "14XLN": (380, 355, 20, 35), "15XLN": (380, 330, 20, 35),
			"16XLN": (380, 305, 20, 35), "17XLN": (380, 280, 20, 35), "18XLN": (380, 255, 20, 35),
			"19XLN": (380, 230, 20, 35), "20XLN": (380, 205, 20, 35), "21XLN": (380, 180, 20, 35),

			# XLS series (west side)
			"1XLS": (80, 680, 20, 35), "2XLS": (80, 655, 20, 35), "3XLS": (80, 630, 20, 35),
			"4XLS": (80, 605, 20, 35), "5XLS": (80, 580, 20, 35), "6XLS": (80, 555, 20, 35)
		}

	def update_map_view(self):
		"""Update the map view based on current settings"""
		try:
			# Clear canvas
			self.map_canvas.delete("all")

			level = self.map_level_var.get()

			# Try to load background image
			if self.load_background_image(level):
				# Draw vendor highlights on the image
				self.draw_vendor_highlights(level)
			else:
				# Fallback to simple text view
				self.draw_simple_text_view(level)

			# Update status
			vendor_count = self.count_vendors_in_level(level)
			self.status_label.config(text=f"{level.title()} Level - {vendor_count} vendors displayed")

		except Exception as e:
			print(f"[ERROR] Failed to update map view: {e}")
			self.status_label.config(text="Error loading map view")

	def load_background_image(self, level):
		"""Load the background map image"""
		try:
			from PIL import Image, ImageTk

			# Define image paths
			image_paths = {
				"upper": ["maps/upper_level.png", "images/upper_level.png", "upper_level.png"],
				"lower": ["maps/lower_level.png", "images/lower_level.png", "lower_level.png"]
			}

			# Try to find and load the image
			for img_path in image_paths.get(level, []):
				if os.path.exists(img_path):
					image = Image.open(img_path)

					# Scale image if needed
					if self.map_scale != 1.0:
						new_size = (int(image.width * self.map_scale), int(image.height * self.map_scale))
						image = image.resize(new_size, Image.Resampling.LANCZOS)

					self.current_map_image = ImageTk.PhotoImage(image)
					self.map_canvas.create_image(0, 0, anchor="nw", image=self.current_map_image)

					# Set canvas scroll region
					self.map_canvas.configure(scrollregion=self.map_canvas.bbox("all"))

					return True

			return False

		except ImportError:
			print("[WARNING] PIL not installed - install with: pip install Pillow")
			return False
		except Exception as e:
			print(f"[ERROR] Could not load {level} level map image: {e}")
			return False

	def draw_vendor_highlights(self, level):
		"""Draw yellow highlights for vendor table assignments"""
		try:
			session = Session()
			vendors = session.query(Vendor).all() if self.show_all_vendors.get() else []

			coords = self.upper_level_coords if level == "upper" else self.lower_level_coords

			for vendor in vendors:
				if not self.vendor_in_level(vendor, level):
					continue

				# Parse vendor table assignments
				tables = self.parse_vendor_tables(vendor)

				# Draw highlights for each table
				for table in tables:
					if table in coords:
						x, y, w, h = coords[table]

						# Scale coordinates
						x *= self.map_scale
						y *= self.map_scale
						w *= self.map_scale
						h *= self.map_scale

						# Draw yellow highlight rectangle
						highlight = self.map_canvas.create_rectangle(
							x, y, x + w, y + h,
							fill="yellow",
							stipple="gray25",  # Semi-transparent effect
							outline="orange",
							width=2,
							tags=f"vendor_{vendor.id}"
						)

						# Add vendor name text if enabled
						if self.show_vendor_names.get():
							name = vendor.business_name or f"{vendor.first_name or ''} {vendor.last_name or ''}".strip()
							if name:
								text_size = max(6, int(8 * self.map_scale))  # Scale text with zoom
								self.map_canvas.create_text(
									x + w / 2, y + h / 2,
									text=name[:8] + ("..." if len(name) > 8 else ""),
									fill="black",
									font=("Arial", text_size, "bold"),
									tags=f"vendor_{vendor.id}"
								)

			session.close()

		except Exception as e:
			print(f"[ERROR] Failed to draw vendor highlights: {e}")

	def draw_simple_text_view(self, level):
		"""Draw a simple text representation when image isn't available"""
		try:
			# Title
			self.map_canvas.create_text(400, 50, text=f"{level.title()} Level Map",
										fill="white", font=("Arial", 20, "bold"))
			self.map_canvas.create_text(400, 80, text="(Background image not found - showing vendor locations only)",
										fill="#ffdf00", font=("Arial", 12))

			# Draw vendor locations as text
			session = Session()
			vendors = session.query(Vendor).all()
			y_pos = 120

			# Group vendors by row for better organization
			vendor_rows = {}
			for vendor in vendors:
				if self.vendor_in_level(vendor, level):
					row = (vendor.row or "").strip().upper()
					if row not in vendor_rows:
						vendor_rows[row] = []
					vendor_rows[row].append(vendor)

			# Display by rows
			for row in sorted(vendor_rows.keys()):
				# Row header
				self.map_canvas.create_text(50, y_pos, anchor="w", text=f"Row {row}:",
											fill="#ffdf00", font=("Arial", 14, "bold"))
				y_pos += 25

				# Vendors in this row
				for vendor in vendor_rows[row]:
					name = vendor.business_name or f"{vendor.first_name or ''} {vendor.last_name or ''}".strip()
					tables = vendor.table_numbers or ""

					self.map_canvas.create_text(80, y_pos, anchor="w",
												text=f"Tables {tables}: {name}",
												fill="yellow", font=("Arial", 11),
												tags=f"vendor_{vendor.id}")
					y_pos += 20

				y_pos += 10  # Extra space between rows

			session.close()

			# Set scroll region
			self.map_canvas.configure(scrollregion=(0, 0, 800, y_pos + 50))

		except Exception as e:
			print(f"[ERROR] Failed to draw text view: {e}")

	def generate_all_vendor_maps(self):
		"""Generate individual map images for all vendors"""
		try:
			# Get output directory
			output_dir = filedialog.askdirectory(title="Select folder to save vendor maps")
			if not output_dir:
				return

			session = Session()
			vendors = session.query(Vendor).all()

			if not vendors:
				messagebox.showinfo("No Vendors", "No vendors found in database.")
				session.close()
				return

			# Create progress window
			progress_window = tk.Toplevel(self.master)
			progress_window.title("Generating Vendor Maps")
			progress_window.geometry("400x150")
			progress_window.configure(bg="#1e1e1e")

			tk.Label(progress_window, text="Generating individual vendor maps...",
					 bg="#1e1e1e", fg="white", font=("Arial", 12)).pack(pady=10)

			progress_var = tk.StringVar()
			progress_label = tk.Label(progress_window, textvariable=progress_var,
									  bg="#1e1e1e", fg="#ffdf00", font=("Arial", 10))
			progress_label.pack(pady=5)

			progress_bar = ttk.Progressbar(progress_window, length=350, mode='determinate')
			progress_bar.pack(pady=10)
			progress_bar['maximum'] = len(vendors)

			# Generate maps for each vendor
			generated_count = 0
			failed_count = 0

			for i, vendor in enumerate(vendors):
				try:
					# Update progress
					name = vendor.business_name or f"{vendor.first_name or ''} {vendor.last_name or ''}".strip()
					progress_var.set(f"Generating map for: {name}")
					progress_bar['value'] = i + 1
					progress_window.update()

					# Generate the vendor map
					if self.generate_vendor_map_file(vendor, output_dir):
						generated_count += 1
					else:
						failed_count += 1

				except Exception as e:
					print(f"[ERROR] Failed to generate map for vendor {vendor.id}: {e}")
					failed_count += 1

			session.close()
			progress_window.destroy()

			# Show completion message
			messagebox.showinfo("Map Generation Complete",
								f"Generated {generated_count} vendor maps successfully.\n"
								f"{failed_count} maps failed to generate.\n"
								f"Maps saved to: {output_dir}")

		except Exception as e:
			print(f"[ERROR] Failed to generate vendor maps: {e}")
			messagebox.showerror("Error", "Failed to generate vendor maps")

	def generate_selected_vendor_map(self):
		"""Generate map for the currently selected vendor"""
		if not self.selected_vendor_id:
			messagebox.showwarning("No Selection", "Please select a vendor by clicking on their table location first.")
			return

		try:
			# Get output directory
			output_dir = filedialog.askdirectory(title="Select folder to save vendor map")
			if not output_dir:
				return

			session = Session()
			vendor = session.query(Vendor).filter_by(id=self.selected_vendor_id).first()

			if not vendor:
				messagebox.showerror("Error", "Selected vendor not found.")
				session.close()
				return

			# Generate the map
			if self.generate_vendor_map_file(vendor, output_dir):
				name = vendor.business_name or f"{vendor.first_name or ''} {vendor.last_name or ''}".strip()
				messagebox.showinfo("Map Generated", f"Map for {name} saved successfully!")
			else:
				messagebox.showerror("Error", "Failed to generate vendor map.")

			session.close()

		except Exception as e:
			print(f"[ERROR] Failed to generate selected vendor map: {e}")
			messagebox.showerror("Error", "Failed to generate vendor map")

	def generate_vendor_map_file(self, vendor, output_dir):
		"""Generate an individual map file for a specific vendor"""
		try:
			from PIL import Image, ImageDraw, ImageFont

			# Get vendor info
			name = vendor.business_name or f"{vendor.first_name or ''} {vendor.last_name or ''}".strip()
			tables = self.parse_vendor_tables(vendor)

			if not tables:
				print(f"[WARNING] No tables found for vendor {vendor.id}")
				return False

			# Determine which level this vendor is on
			vendor_level = "lower" if self.vendor_in_level(vendor, "lower") else "upper"

			# Load background image
			image_paths = {
				"upper": ["maps/upper_level.png", "images/upper_level.png", "upper_level.png"],
				"lower": ["maps/lower_level.png", "images/lower_level.png", "lower_level.png"]
			}

			background_image = None
			for img_path in image_paths.get(vendor_level, []):
				if os.path.exists(img_path):
					background_image = Image.open(img_path)
					break

			if not background_image:
				print(f"[WARNING] No background image found for {vendor_level} level")
				return False

			# Create a copy to draw on
			map_image = background_image.copy()
			draw = ImageDraw.Draw(map_image)

			# Get coordinates for this level
			coords = self.upper_level_coords if vendor_level == "upper" else self.lower_level_coords

			# Highlight vendor's tables
			for table in tables:
				if table in coords:
					x, y, w, h = coords[table]

					# Draw yellow highlight rectangle
					draw.rectangle([x, y, x + w, y + h], fill="yellow", outline="orange", width=3)

					# Add table number in the center
					try:
						font = ImageFont.truetype("arial.ttf", 12)
					except:
						font = ImageFont.load_default()

					text_bbox = draw.textbbox((0, 0), table, font=font)
					text_w = text_bbox[2] - text_bbox[0]
					text_h = text_bbox[3] - text_bbox[1]
					text_x = x + (w - text_w) // 2
					text_y = y + (h - text_h) // 2
					draw.text((text_x, text_y), table, fill="black", font=font)

			# Add vendor name and info at the top
			try:
				title_font = ImageFont.truetype("arial.ttf", 24)
				info_font = ImageFont.truetype("arial.ttf", 16)
			except:
				title_font = ImageFont.load_default()
				info_font = ImageFont.load_default()

			# Add white background for text
			title_text = f"VENDOR MAP: {name}"
			info_text = f"Tables: {', '.join(tables)} | Level: {vendor_level.title()}"

			title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
			info_bbox = draw.textbbox((0, 0), info_text, font=info_font)

			# Draw background rectangles for text
			draw.rectangle([10, 10, max(title_bbox[2], info_bbox[2]) + 20, 70], fill="white", outline="black")

			# Draw text
			draw.text((15, 15), title_text, fill="black", font=title_font)
			draw.text((15, 45), info_text, fill="black", font=info_font)

			# Generate safe filename
			safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
			if not safe_name:
				safe_name = f"Vendor_{vendor.id}"

			table_list = "-".join(tables[:3])  # First 3 tables to keep filename reasonable
			if len(tables) > 3:
				table_list += f"+{len(tables) - 3}more"

			filename = f"VendorMap_{safe_name}_{table_list}_{vendor_level}.png"
			filepath = os.path.join(output_dir, filename)

			# Save the image
			map_image.save(filepath, "PNG", quality=95)
			print(f"[INFO] Generated vendor map: {filepath}")
			return True

		except ImportError:
			print("[ERROR] PIL (Pillow) is required for map generation. Install with: pip install Pillow")
			return False
		except Exception as e:
			print(f"[ERROR] Failed to generate vendor map file: {e}")
			return False

	def parse_vendor_tables(self, vendor):
		"""Parse vendor table assignments from Island/Row/Table database fields"""
		tables = []
		try:
			# Get the actual database fields
			island = (vendor.island or "").strip()
			row = (vendor.row or "").strip().upper()
			table_numbers = (vendor.table_numbers or "").strip()

			print(
				f"[DEBUG] Parsing vendor {getattr(vendor, 'id', '?')}: Island='{island}', Row='{row}', Tables='{table_numbers}'")

			if not table_numbers:
				return tables

			# Handle special table formats that include letters in table_numbers
			if any(special in table_numbers.upper() for special in
				   ['XLN', 'XLS', 'LN', 'LNW', 'LS', 'LSW', 'LE', 'LW', 'RW']):
				tables = self.parse_special_tables(table_numbers)
			elif row:
				# Standard format: Row + Table Numbers
				# This handles both: Row="A", Tables="1-14" AND Row="", Tables="1A-14A"
				if row.isalpha() or any(char.isalpha() for char in row):
					numbers = self.extract_numbers_from_string(table_numbers)
					for num in numbers:
						tables.append(f"{num}{row}")
				else:
					print(f"[WARNING] Unexpected row format: '{row}' for vendor {getattr(vendor, 'id', '?')}")
			else:
				# No row specified, check if table_numbers contains row info
				tables = self.parse_standalone_tables(table_numbers)

			print(f"[DEBUG] Parsed tables for vendor {getattr(vendor, 'id', '?')}: {tables}")

		except Exception as e:
			print(f"[ERROR] Failed to parse tables for vendor {getattr(vendor, 'id', '?')}: {e}")

		return tables

	def parse_special_tables(self, table_numbers):
		"""Parse special table assignments (XLN, XLS, LN, wall tables, etc.)"""
		tables = []
		try:
			# Split by commas and process each part
			parts = table_numbers.split(',')
			for part in parts:
				part = part.strip().upper()

				# Handle various special table formats
				if any(prefix in part for prefix in
					   ['XLN', 'XLS', 'LN', 'LNW', 'LS', 'LSW', 'LE', 'LW', 'RW', 'SE', 'NE']):
					# Extract the prefix and numbers
					import re

					# Find all letter sequences (prefixes)
					letter_matches = re.findall(r'[A-Z]+', part)
					# Find all number sequences
					number_matches = re.findall(r'\d+', part)

					if letter_matches and number_matches:
						prefix = letter_matches[0]
						# Handle ranges and individual numbers
						for num_part in number_matches:
							if '-' in part and len(number_matches) >= 2:
								# Handle ranges like "1XLN-5XLN" or "LN1-LN5"
								start_num = int(number_matches[0])
								end_num = int(number_matches[-1])
								for num in range(start_num, end_num + 1):
									tables.append(f"{num}{prefix}")
							else:
								# Single number
								tables.append(f"{num_part}{prefix}")
					elif letter_matches:
						# Just the prefix, might be a standalone identifier
						tables.append(letter_matches[0])
				else:
					# Try to parse as regular number
					numbers = self.extract_numbers_from_string(part)
					tables.extend(str(num) for num in numbers)

		except Exception as e:
			print(f"[ERROR] Failed to parse special tables from '{table_numbers}': {e}")

		return tables

	def parse_standalone_tables(self, table_numbers):
		"""Parse table numbers that might contain row information within them"""
		tables = []
		try:
			# Split by commas and process each part
			parts = table_numbers.split(',')
			for part in parts:
				part = part.strip()

				# Check if this looks like a complete table ID (contains letters)
				if any(char.isalpha() for char in part):
					# Handle ranges like "1A-5A" or lists like "1A,2B,3C"
					if '-' in part:
						# Try to parse range
						range_parts = part.split('-')
						if len(range_parts) == 2:
							start_part = range_parts[0].strip()
							end_part = range_parts[1].strip()

							# Extract row letters and numbers
							import re
							start_match = re.match(r'(\d+)([A-Z]+)', start_part)
							end_match = re.match(r'(\d+)([A-Z]+)', end_part)

							if start_match and end_match:
								start_num, row = int(start_match.group(1)), start_match.group(2)
								end_num = int(end_match.group(1))

								# Generate range
								for num in range(start_num, end_num + 1):
									tables.append(f"{num}{row}")
							else:
								# Fallback: treat as individual table
								tables.append(part)
					else:
						# Individual table ID
						tables.append(part.upper())
				else:
					# Pure numbers, can't determine row without more context
					numbers = self.extract_numbers_from_string(part)
					tables.extend(str(num) for num in numbers)

		except Exception as e:
			print(f"[ERROR] Failed to parse standalone tables from '{table_numbers}': {e}")

		return tables
		"""Extract all numbers from a string, handling ranges and lists"""
		numbers = []
		try:
			# Split by commas first
			parts = text.split(',')

			for part in parts:
				part = part.strip()

				if '-' in part:
					# Handle ranges like "1-5" or "10-14"
					range_parts = part.split('-')
					if len(range_parts) == 2:
						try:
							start = int(''.join(filter(str.isdigit, range_parts[0])))
							end = int(''.join(filter(str.isdigit, range_parts[1])))
							numbers.extend(range(start, end + 1))
						except ValueError:
							continue
				else:
					# Extract individual numbers
					import re
					found_numbers = re.findall(r'\d+', part)
					for num_str in found_numbers:
						try:
							numbers.append(int(num_str))
						except ValueError:
							continue

		except Exception as e:
			print(f"[ERROR] Failed to extract numbers from '{text}': {e}")

		return sorted(list(set(numbers)))  # Remove duplicates and sort

	def show_unmapped_tables_warning(self, level):
		"""Show warning for tables that couldn't be mapped to coordinates"""
		try:
			session = Session()
			vendors = session.query(Vendor).all() if self.show_all_vendors.get() else []
			coords = self.upper_level_coords if level == "upper" else self.lower_level_coords

			unmapped_tables = set()

			for vendor in vendors:
				if not self.vendor_in_level(vendor, level):
					continue

				tables = self.parse_vendor_tables(vendor)
				for table in tables:
					if table not in coords:
						unmapped_tables.add(table)

			if unmapped_tables:
				print(f"[WARNING] {len(unmapped_tables)} tables not found in coordinate mapping for {level} level:")
				print(f"[WARNING] Unmapped tables: {sorted(unmapped_tables)}")

				# Show warning on map
				warning_text = f"Warning: {len(unmapped_tables)} tables not mapped"
				self.map_canvas.create_text(
					10, 10, anchor="nw", text=warning_text,
					fill="red", font=("Arial", 12, "bold")
				)

			session.close()

		except Exception as e:
			print(f"[ERROR] Failed to check unmapped tables: {e}")

	def extract_numbers_from_string(self, text):
		"""Extract all numbers from a string, handling ranges and lists"""
		numbers = []
		try:
			# Split by commas first
			parts = text.split(',')

			for part in parts:
				part = part.strip()

				if '-' in part:
					# Handle ranges like "1-5" or "10-14"
					range_parts = part.split('-')
					if len(range_parts) == 2:
						try:
							start = int(''.join(filter(str.isdigit, range_parts[0])))
							end = int(''.join(filter(str.isdigit, range_parts[1])))
							numbers.extend(range(start, end + 1))
						except ValueError:
							continue
				else:
					# Extract individual numbers
					import re
					found_numbers = re.findall(r'\d+', part)
					for num_str in found_numbers:
						try:
							numbers.append(int(num_str))
						except ValueError:
							continue

		except Exception as e:
			print(f"[ERROR] Failed to extract numbers from '{text}': {e}")

		return sorted(list(set(numbers)))  # Remove duplicates and sort

	def vendor_in_level(self, vendor, level):
		"""Check if vendor belongs to the specified level based on row patterns"""
		try:
			row = (vendor.row or "").strip().upper()
			table_numbers = (vendor.table_numbers or "").strip()

			# Level detection based on "L" in row name OR in parsed table IDs
			has_l_in_row = "L" in row

			# Also check if any parsed table IDs contain "L"
			if not has_l_in_row and table_numbers:
				parsed_tables = self.parse_vendor_tables(vendor)
				has_l_in_tables = any("L" in table_id for table_id in parsed_tables)
				has_l_in_row = has_l_in_tables

			if level == "lower":
				return has_l_in_row
			elif level == "upper":
				return not has_l_in_row

		except Exception as e:
			print(f"[ERROR] Failed to check vendor level: {e}")

		return False

	def count_vendors_in_level(self, level):
		"""Count vendors in the specified level"""
		try:
			session = Session()
			vendors = session.query(Vendor).all()
			count = sum(1 for vendor in vendors if self.vendor_in_level(vendor, level))
			session.close()
			return count
		except Exception as e:
			print(f"[ERROR] Failed to count vendors: {e}")
			return 0

	def on_map_click(self, event):
		"""Handle clicks on the map"""
		try:
			x = self.map_canvas.canvasx(event.x)
			y = self.map_canvas.canvasy(event.y)
			clicked_items = self.map_canvas.find_overlapping(x - 2, y - 2, x + 2, y + 2)

			# Find vendor tags
			for item in clicked_items:
				tags = self.map_canvas.gettags(item)
				for tag in tags:
					if tag.startswith("vendor_"):
						vendor_id = int(tag.split("_")[1])
						self.show_vendor_details(vendor_id)
						return

		except Exception as e:
			print(f"[ERROR] Map click handler failed: {e}")

	def show_vendor_details(self, vendor_id):
		"""Show details for clicked vendor"""
		try:
			session = Session()
			vendor = session.query(Vendor).filter_by(id=vendor_id).first()
			if vendor:
				name = vendor.business_name or f"{vendor.first_name or ''} {vendor.last_name or ''}".strip()
				location = f"{vendor.row or ''} {vendor.table_numbers or ''}".strip()
				self.selected_vendor_label.config(text=f"Selected: {name} - Location: {location}")
				self.selected_vendor_id = vendor_id
			session.close()
		except Exception as e:
			print(f"[ERROR] Failed to show vendor details: {e}")

	def view_selected_vendor(self):
		"""Open the selected vendor in vendor form"""
		if self.selected_vendor_id:
			try:
				from gui.vendor_form import VendorForm
				VendorForm(self, self.user, vendor_id=self.selected_vendor_id)
			except Exception as e:
				print(f"[ERROR] Failed to open vendor form: {e}")
				messagebox.showerror("Error", "Could not open vendor form")

	def zoom_in(self):
		"""Zoom in on the map"""
		self.map_scale = min(3.0, self.map_scale * 1.2)
		self.update_map_view()

	def zoom_out(self):
		"""Zoom out on the map"""
		self.map_scale = max(0.3, self.map_scale * 0.8)
		self.update_map_view()

	def reset_zoom(self):
		"""Reset zoom to default"""
		self.map_scale = 1.0
		self.update_map_view()

	def on_map_scroll(self, event):
		"""Handle mouse wheel scrolling on map"""
		try:
			# Regular scrolling
			self.map_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
		except Exception as e:
			print(f"[ERROR] Map scroll handler failed: {e}")

	def on_map_zoom(self, event):
		"""Handle Ctrl+mouse wheel for zooming"""
		try:
			if event.delta > 0:
				self.zoom_in()
			else:
				self.zoom_out()
		except Exception as e:
			print(f"[ERROR] Map zoom handler failed: {e}")