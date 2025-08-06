import tkinter as tk
from tkinter import ttk
from gui.vendor_manager import VendorManagerWindow
from gui.user_management import UserManagementPanel
from gui.audit_viewer import AuditViewerTab
from gui.customization import CustomizationWindow
from gui.export_report import ExportReportWindow
from gui.mailout_manager import MailoutManagerWindow
from gui.MapManagerWindow import MapManagerWindow
from models.audit_log import AuditLog
from models.activity_log import ActivityLog
from models.session_log import SessionLog
from models import Session
from models.vendor import Vendor
from models.mailout import Mailout
from models.user import User
from utils.theme import apply_user_theme
from utils.session_logger import log_session_logout
from datetime import datetime
import os


class DashboardTile(tk.Frame):
	"""Custom dashboard tile with hover effects and stats"""

	def __init__(self, parent, title, icon, command, bg_color="#2e2e2e", hover_color="#3e3e3e",
				 stats_text="", accent_color="#ffdf00"):
		super().__init__(parent, bg=bg_color, relief="raised", bd=2)
		self.bg_color = bg_color
		self.hover_color = hover_color
		self.command = command
		self.accent_color = accent_color

		# Configure tile size and padding
		self.configure(width=200, height=150)
		self.pack_propagate(False)

		# Create main content frame
		content_frame = tk.Frame(self, bg=bg_color)
		content_frame.pack(expand=True, fill="both", padx=15, pady=15)

		# Icon/emoji at top
		icon_label = tk.Label(content_frame, text=icon, font=("Arial", 32),
							  bg=bg_color, fg=accent_color)
		icon_label.pack(pady=(5, 10))

		# Title
		title_label = tk.Label(content_frame, text=title, font=("Segoe UI", 14, "bold"),
							   bg=bg_color, fg="white", wraplength=180)
		title_label.pack(pady=(0, 5))

		# Stats text
		if stats_text:
			stats_label = tk.Label(content_frame, text=stats_text, font=("Segoe UI", 10),
								   bg=bg_color, fg="#cccccc", wraplength=180)
			stats_label.pack(pady=(0, 5))

		# Status indicator (small colored dot)
		status_frame = tk.Frame(content_frame, bg=bg_color, height=10)
		status_frame.pack(fill="x", pady=(5, 0))
		self.status_dot = tk.Label(status_frame, text="●", font=("Arial", 12),
								   bg=bg_color, fg="#00ff00")  # Green = active
		self.status_dot.pack()

		# Bind hover events to all child widgets
		self.bind_hover_events(self)
		self.bind_hover_events(content_frame)
		self.bind_hover_events(icon_label)
		self.bind_hover_events(title_label)
		if stats_text:
			self.bind_hover_events(stats_label)
		self.bind_hover_events(status_frame)
		self.bind_hover_events(self.status_dot)

		# Bind click events
		self.bind("<Button-1>", lambda e: self.command())
		for widget in [content_frame, icon_label, title_label, status_frame, self.status_dot]:
			widget.bind("<Button-1>", lambda e: self.command())
		if stats_text:
			stats_label.bind("<Button-1>", lambda e: self.command())

	def bind_hover_events(self, widget):
		widget.bind("<Enter>", self.on_hover_enter)
		widget.bind("<Leave>", self.on_hover_leave)

	def on_hover_enter(self, event):
		self.configure(bg=self.hover_color, relief="solid", bd=3)
		self.update_widget_colors(self, self.hover_color)
		self.configure(cursor="hand2")

	def on_hover_leave(self, event):
		self.configure(bg=self.bg_color, relief="raised", bd=2)
		self.update_widget_colors(self, self.bg_color)
		self.configure(cursor="")

	def update_widget_colors(self, widget, color):
		"""Recursively update background colors of child widgets"""
		try:
			if hasattr(widget, 'configure') and 'bg' in widget.configure():
				widget.configure(bg=color)
		except:
			pass

		for child in widget.winfo_children():
			self.update_widget_colors(child, color)

	def update_stats(self, new_stats):
		"""Update the stats text on the tile"""
		for widget in self.winfo_children():
			self.find_and_update_stats(widget, new_stats)

	def find_and_update_stats(self, widget, text):
		if isinstance(widget, tk.Label) and hasattr(widget, 'cget'):
			try:
				font = widget.cget('font')
				if 'Segoe UI' in str(font) and '10' in str(font):
					widget.configure(text=text)
					return
			except:
				pass

		for child in widget.winfo_children():
			self.find_and_update_stats(child, text)


class MainAppWindow(tk.Tk):
	def periodic_stats_update(self):
		"""Update dashboard stats and refresh logs periodically"""
		try:
			self.update_dashboard_stats()
			self.refresh_all_logs()
			if self.winfo_exists():
				self.stats_update_job = self.after(30000, self.periodic_stats_update)
		except Exception as e:
			print(f"[ERROR] periodic_stats_update failed: {e}")

	def __init__(self, user):
		super().__init__()
		if self.winfo_exists():
			self.stats_update_job = self.after(30000, self.periodic_stats_update)
		self.title("Wanenmacher's Management System")
		self.geometry("1400x900")
		self.current_user = user
		self.protocol("WM_DELETE_WINDOW", self.on_close)

		# Get user accent color safely
		self.user_accent_color = getattr(user, 'accent_color', '#ffdf00')

		apply_user_theme(self, user)

		# Main container
		self.main_container = tk.Frame(self, bg="#1e1e1e")
		self.main_container.pack(fill="both", expand=True)

		# Create dashboard and module frames
		self.dashboard_frame = tk.Frame(self.main_container, bg="#1e1e1e")
		self.module_frame = tk.Frame(self.main_container, bg="#1e1e1e")

		self.tiles = {}  # Store tile references for updates
		self.build_dashboard()
		self.show_dashboard()

		# Keyboard shortcuts
		self.bind_all("<Control-e>", lambda event: self.open_export_window())
		self.bind_all("<Control-d>", lambda event: self.show_dashboard())
		self.bind_all("<F1>", lambda event: self.show_module("vendors"))
		self.bind_all("<F2>", lambda event: self.show_module("mailouts"))
		self.bind_all("<F3>", lambda event: self.show_module("maps"))

		# Update stats every 30 seconds
		self.update_dashboard_stats()
		if self.winfo_exists():
			self.after(30000, self.periodic_stats_update)

	def build_dashboard(self):
		"""Build the main dashboard with tiles"""
		# Clear dashboard
		for widget in self.dashboard_frame.winfo_children():
			widget.destroy()

		# Header section
		header_frame = tk.Frame(self.dashboard_frame, bg="#1e1e1e", height=120)
		header_frame.pack(fill="x", padx=30, pady=(30, 20))
		header_frame.pack_propagate(False)

		# Welcome text
		welcome_frame = tk.Frame(header_frame, bg="#1e1e1e")
		welcome_frame.pack(fill="both", expand=True)

		# Logo and title
		title_frame = tk.Frame(welcome_frame, bg="#1e1e1e")
		title_frame.pack(fill="x")

		logo_label = tk.Label(title_frame, text="🦁", font=("Arial", 48),
							  bg="#1e1e1e", fg=self.user_accent_color)
		logo_label.pack(side="left", padx=(0, 20))

		text_frame = tk.Frame(title_frame, bg="#1e1e1e")
		text_frame.pack(side="left", fill="both", expand=True)

		main_title = tk.Label(text_frame, text="Wanenmacher's Management System",
							  font=("Segoe UI", 28, "bold"), bg="#1e1e1e", fg="white")
		main_title.pack(anchor="w")

		subtitle = tk.Label(text_frame,
							text=f"Welcome back, {self.current_user.username} | {datetime.now().strftime('%A, %B %d, %Y')}",
							font=("Segoe UI", 14), bg="#1e1e1e", fg="#cccccc")
		subtitle.pack(anchor="w", pady=(5, 0))

		# User info on right
		user_frame = tk.Frame(welcome_frame, bg="#1e1e1e")
		user_frame.pack(side="right", padx=(20, 0))

		user_info = tk.Label(user_frame, text=f"Role: {self.current_user.role.title()}",
							 font=("Segoe UI", 12), bg="#1e1e1e", fg="#cccccc")
		user_info.pack(anchor="e")

		time_label = tk.Label(user_frame, text=datetime.now().strftime("%I:%M %p"),
							  font=("Segoe UI", 16, "bold"), bg="#1e1e1e",
							  fg=self.user_accent_color)
		time_label.pack(anchor="e", pady=(5, 0))

		# Tiles container with scrollable frame
		tiles_container = tk.Frame(self.dashboard_frame, bg="#1e1e1e")
		tiles_container.pack(fill="both", expand=True, padx=30, pady=20)

		# Create canvas for scrolling if needed
		canvas = tk.Canvas(tiles_container, bg="#1e1e1e", highlightthickness=0)
		scrollbar = tk.Scrollbar(tiles_container, orient="vertical", command=canvas.yview)
		scrollable_frame = tk.Frame(canvas, bg="#1e1e1e")

		scrollable_frame.bind(
			"<Configure>",
			lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
		)

		canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
		canvas.configure(yscrollcommand=scrollbar.set)

		# Grid for tiles
		tiles_grid = tk.Frame(scrollable_frame, bg="#1e1e1e")
		tiles_grid.pack(fill="both", expand=True, padx=20, pady=20)

		# Configure grid weights for responsive design
		for i in range(4):  # 4 columns
			tiles_grid.columnconfigure(i, weight=1, minsize=220)

		# Get initial stats
		stats = self.get_dashboard_stats()

		# Define tiles with their properties
		tile_configs = [
			{
				"title": "Vendor Manager",
				"icon": "👥",
				"command": lambda: self.show_module("vendors"),
				"stats": f"{stats['total_vendors']} vendors\n{stats['paid_vendors']} paid • {stats['unpaid_vendors']} unpaid",
				"bg_color": "#2d4a2d",
				"hover_color": "#3d5a3d"
			},
			{
				"title": "Map Manager",
				"icon": "🗺️",
				"command": lambda: self.show_module("maps"),
				"stats": f"Upper: {stats['upper_vendors']} vendors\nLower: {stats['lower_vendors']} vendors",
				"bg_color": "#2d3a4a",
				"hover_color": "#3d4a5a"
			},
			{
				"title": "Mailout Manager",
				"icon": "📧",
				"command": lambda: self.show_module("mailouts"),
				"stats": f"{stats['total_mailouts']} contacts\nLast updated today",
				"bg_color": "#4a2d4a",
				"hover_color": "#5a3d5a"
			},
			{
				"title": "Quick Reports",
				"icon": "📊",
				"command": lambda: self.open_export_window(),
				"stats": f"${stats['total_revenue']:,} revenue\n{stats['total_tables']} tables reserved",
				"bg_color": "#4a3d2d",
				"hover_color": "#5a4d3d"
			},
			{
				"title": "Print Center",
				"icon": "🖨️",
				"command": lambda: self.show_module("print"),
				"stats": "Labels • Forms • Reports\nTax Stickers • Receipts",
				"bg_color": "#2d4a4a",
				"hover_color": "#3d5a5a"
			},
			{
				"title": "Activity Logs",
				"icon": "📝",
				"command": lambda: self.show_module("logs"),
				"stats": f"{stats['recent_activities']} recent activities\n{stats['total_sessions']} sessions today",
				"bg_color": "#4a2d3d",
				"hover_color": "#5a3d4d"
			}
		]

		# Add admin-only tiles
		if self.current_user.role == "admin":
			tile_configs.extend([
				{
					"title": "User Management",
					"icon": "👤",
					"command": lambda: self.show_module("users"),
					"stats": f"{stats['total_users']} users\n{stats['active_users']} active",
					"bg_color": "#3d2d4a",
					"hover_color": "#4d3d5a"
				},
				{
					"title": "System Settings",
					"icon": "⚙️",
					"command": lambda: self.show_module("settings"),
					"stats": "Themes • Preferences\nBackup • Maintenance",
					"bg_color": "#4a4a2d",
					"hover_color": "#5a5a3d"
				}
			])
		else:
			# Non-admin settings tile
			tile_configs.append({
				"title": "My Settings",
				"icon": "⚙️",
				"command": lambda: self.show_module("settings"),
				"stats": "Theme • Preferences\nPersonalization",
				"bg_color": "#4a4a2d",
				"hover_color": "#5a5a3d"
			})

		# Create tiles in grid
		row = 0
		col = 0
		for config in tile_configs:
			tile = DashboardTile(
				tiles_grid,
				title=config["title"],
				icon=config["icon"],
				command=config["command"],
				bg_color=config["bg_color"],
				hover_color=config["hover_color"],
				stats_text=config["stats"],
				accent_color=self.current_user.accent_color
			)
			tile.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

			# Store tile reference for updates
			self.tiles[config["title"]] = tile

			col += 1
			if col >= 4:  # 4 columns
				col = 0
				row += 1

		# Pack canvas and scrollbar
		canvas.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")

		# Footer with quick actions
		footer_frame = tk.Frame(self.dashboard_frame, bg="#2e2e2e", height=60)
		footer_frame.pack(fill="x", side="bottom")
		footer_frame.pack_propagate(False)

		footer_content = tk.Frame(footer_frame, bg="#2e2e2e")
		footer_content.pack(expand=True, fill="both", padx=30, pady=15)

		# Quick actions
		tk.Label(footer_content, text="Quick Actions:", font=("Segoe UI", 12, "bold"),
				 bg="#2e2e2e", fg="white").pack(side="left")

		quick_buttons = [
			("Add Vendor", lambda: self.show_module("vendors")),
			("Export Report", lambda: self.open_export_window()),
			("View Logs", lambda: self.show_module("logs")),
			("Logout", self.logout)
		]

		for btn_text, btn_cmd in quick_buttons:
			btn = tk.Button(footer_content, text=btn_text, command=btn_cmd,
							bg="#3e3e3e", fg="white", font=("Segoe UI", 10),
							relief="flat", padx=15, pady=5)
			btn.pack(side="left", padx=10)

			# Hover effects for buttons
			btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.current_user.accent_color, fg="black"))
			btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#3e3e3e", fg="white"))

		# Keyboard shortcuts info
		shortcuts_text = "Shortcuts: Ctrl+D=Dashboard • F1=Vendors • F2=Mailouts • F3=Maps • Ctrl+E=Export"
		tk.Label(footer_content, text=shortcuts_text, font=("Segoe UI", 9),
				 bg="#2e2e2e", fg="#999999").pack(side="right")

	def get_dashboard_stats(self):
		"""Get statistics for dashboard tiles"""
		try:
			session = Session()

			# Vendor stats
			vendors = session.query(Vendor).all()
			total_vendors = len(vendors)
			paid_vendors = sum(1 for v in vendors if (v.amount_paid or 0) >= (v.total_due or 0))
			unpaid_vendors = total_vendors - paid_vendors

			# Revenue and tables
			total_revenue = sum(v.amount_paid or 0 for v in vendors)
			total_tables = sum((v.six_ft_gun or 0) + (v.six_ft_knife or 0) + (v.six_ft_display or 0) +
							   (v.six_ft_nonrelated or 0) + (v.eight_ft_gun or 0) + (v.eight_ft_knife or 0) +
							   (v.eight_ft_display or 0) + (v.eight_ft_nonrelated or 0) for v in vendors)

			# Map stats (simplified level detection)
			upper_vendors = sum(1 for v in vendors if not (v.row and "L" in v.row.upper()))
			lower_vendors = total_vendors - upper_vendors

			# Mailout stats
			try:
				mailouts = session.query(Mailout).all()
				total_mailouts = len(mailouts)
			except:
				total_mailouts = 0

			# User stats - get fresh user data from database
			users = session.query(User).filter_by(is_deleted=False).all()
			total_users = len(users)
			active_users = sum(1 for u in users if getattr(u, 'active', True))

			session.close()

			return {
				'total_vendors': total_vendors,
				'paid_vendors': paid_vendors,
				'unpaid_vendors': unpaid_vendors,
				'total_revenue': int(total_revenue),
				'total_tables': total_tables,
				'upper_vendors': upper_vendors,
				'lower_vendors': lower_vendors,
				'total_mailouts': total_mailouts,
				'total_users': total_users,
				'active_users': active_users,
				'recent_activities': 12,  # Placeholder
				'total_sessions': 5  # Placeholder
			}
		except Exception as e:
			print(f"[ERROR] Getting dashboard stats: {e}")
			return {
				'total_vendors': 0, 'paid_vendors': 0, 'unpaid_vendors': 0,
				'total_revenue': 0, 'total_tables': 0, 'upper_vendors': 0,
				'lower_vendors': 0, 'total_mailouts': 0, 'total_users': 0,
				'active_users': 0, 'recent_activities': 0, 'total_sessions': 0
			}

	def update_dashboard_stats(self):
		"""Update dashboard tile statistics"""
		try:
			stats = self.get_dashboard_stats()

			# Update tile stats
			if "Vendor Manager" in self.tiles:
				self.tiles["Vendor Manager"].update_stats(
					f"{stats['total_vendors']} vendors\n{stats['paid_vendors']} paid • {stats['unpaid_vendors']} unpaid"
				)

			if "Map Manager" in self.tiles:
				self.tiles["Map Manager"].update_stats(
					f"Upper: {stats['upper_vendors']} vendors\nLower: {stats['lower_vendors']} vendors"
				)

			if "Quick Reports" in self.tiles:
				self.tiles["Quick Reports"].update_stats(
					f"${stats['total_revenue']:,} revenue\n{stats['total_tables']} tables reserved"
				)

			if "Mailout Manager" in self.tiles:
				self.tiles["Mailout Manager"].update_stats(
					f"{stats['total_mailouts']} contacts\nLast updated today"
				)

			# Schedule next update
			if self.winfo_exists():
				self.after(30000, self.update_dashboard_stats)

		except Exception as e:
			print(f"[ERROR] Updating dashboard stats: {e}")

	def show_dashboard(self):
		"""Show the dashboard"""
		self.module_frame.pack_forget()
		self.dashboard_frame.pack(fill="both", expand=True)
		self.title("Wanenmacher's Management System - Dashboard")

	def show_module(self, module_name):
		"""Show a specific module"""
		# Clear module frame
		for widget in self.module_frame.winfo_children():
			widget.destroy()

		# Create back button
		back_frame = tk.Frame(self.module_frame, bg="#1e1e1e", height=50)
		back_frame.pack(fill="x", padx=10, pady=10)
		back_frame.pack_propagate(False)

		back_btn = tk.Button(back_frame, text="← Back to Dashboard", command=self.show_dashboard,
							 bg=self.current_user.accent_color, fg="black", font=("Segoe UI", 12, "bold"),
							 relief="flat", padx=20, pady=10)
		back_btn.pack(side="left")

		# Module title
		module_titles = {
			"vendors": "Vendor Management",
			"maps": "Map Manager",
			"mailouts": "Mailout Manager",
			"users": "User Management",
			"settings": "Settings",
			"logs": "Activity Logs",
			"print": "Print Center"
		}

		title_label = tk.Label(back_frame, text=module_titles.get(module_name, "Module"),
							   font=("Segoe UI", 18, "bold"), bg="#1e1e1e", fg="white")
		title_label.pack(side="left", padx=(30, 0))

		# Module content
		content_frame = tk.Frame(self.module_frame, bg="#1e1e1e")
		content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

		# Load appropriate module
		if module_name == "vendors":
			VendorManagerWindow(content_frame, self.current_user).pack(fill="both", expand=True)
		elif module_name == "maps":
			MapManagerWindow(content_frame, self.current_user).pack(fill="both", expand=True)
		elif module_name == "mailouts":
			MailoutManagerWindow(content_frame, self.current_user).pack(fill="both", expand=True)
		elif module_name == "users" and self.current_user.role == "admin":
			UserManagementPanel(content_frame, self.current_user).pack(fill="both", expand=True)
		elif module_name == "settings":
			CustomizationWindow(content_frame, self.current_user).pack(fill="both", expand=True)
		elif module_name == "logs":
			self.build_logs_module(content_frame)
		elif module_name == "print":
			# Create print center interface
			self.build_print_center(content_frame)
		else:
			tk.Label(content_frame, text=f"{module_name.title()} module coming soon...",
					 font=("Segoe UI", 16), bg="#1e1e1e", fg="#cccccc").pack(expand=True)

		# Show module frame
		self.dashboard_frame.pack_forget()
		self.module_frame.pack(fill="both", expand=True)
		self.title(f"Wanenmacher's Management System - {module_titles.get(module_name, 'Module')}")

	def build_logs_module(self, parent):
		"""Build standalone logs module (decoupled from vendor manager)"""
		logs_frame = tk.Frame(parent, bg="#1e1e1e")
		logs_frame.pack(fill="both", expand=True)

		# Create notebook for different log types
		logs_notebook = ttk.Notebook(logs_frame)
		logs_notebook.pack(fill="both", expand=True, padx=10, pady=10)

		# Audit Logs tab
		audit_frame = tk.Frame(logs_notebook, bg="#1e1e1e")
		logs_notebook.add(audit_frame, text="Audit Logs")

		self.audit_tree = ttk.Treeview(audit_frame,
									   columns=("timestamp", "username", "action", "description"),
									   show="headings")

		for col in ("timestamp", "username", "action", "description"):
			self.audit_tree.heading(col, text=col.title())
			self.audit_tree.column(col, width=200, anchor="w")

		# Add scrollbars for audit tree
		audit_scroll_y = ttk.Scrollbar(audit_frame, orient="vertical", command=self.audit_tree.yview)
		audit_scroll_x = ttk.Scrollbar(audit_frame, orient="horizontal", command=self.audit_tree.xview)
		self.audit_tree.configure(yscrollcommand=audit_scroll_y.set, xscrollcommand=audit_scroll_x.set)

		self.audit_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
		audit_scroll_y.grid(row=0, column=1, sticky="ns", pady=10)
		audit_scroll_x.grid(row=1, column=0, sticky="ew", padx=10)

		audit_frame.grid_rowconfigure(0, weight=1)
		audit_frame.grid_columnconfigure(0, weight=1)

		# Activity Logs tab
		activity_frame = tk.Frame(logs_notebook, bg="#1e1e1e")
		logs_notebook.add(activity_frame, text="Activity Logs")

		self.activity_tree = ttk.Treeview(activity_frame,
										  columns=("timestamp", "username", "action", "description"),
										  show="headings")

		for col in ("timestamp", "username", "action", "description"):
			self.activity_tree.heading(col, text=col.title())
			self.activity_tree.column(col, width=200, anchor="w")

		# Add scrollbars for activity tree
		activity_scroll_y = ttk.Scrollbar(activity_frame, orient="vertical", command=self.activity_tree.yview)
		activity_scroll_x = ttk.Scrollbar(activity_frame, orient="horizontal", command=self.activity_tree.xview)
		self.activity_tree.configure(yscrollcommand=activity_scroll_y.set, xscrollcommand=activity_scroll_x.set)

		self.activity_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
		activity_scroll_y.grid(row=0, column=1, sticky="ns", pady=10)
		activity_scroll_x.grid(row=1, column=0, sticky="ew", padx=10)

		activity_frame.grid_rowconfigure(0, weight=1)
		activity_frame.grid_columnconfigure(0, weight=1)

		# Session Logs tab
		session_frame = tk.Frame(logs_notebook, bg="#1e1e1e")
		logs_notebook.add(session_frame, text="Session Logs")

		self.session_tree = ttk.Treeview(session_frame,
										 columns=("login_time", "logout_time", "username", "ip_address"),
										 show="headings")

		for col in ("login_time", "logout_time", "username", "ip_address"):
			self.session_tree.heading(col, text=col.replace("_", " ").title())
			self.session_tree.column(col, width=200, anchor="w")

		# Add scrollbars for session tree
		session_scroll_y = ttk.Scrollbar(session_frame, orient="vertical", command=self.session_tree.yview)
		session_scroll_x = ttk.Scrollbar(session_frame, orient="horizontal", command=self.session_tree.xview)
		self.session_tree.configure(yscrollcommand=session_scroll_y.set, xscrollcommand=session_scroll_x.set)

		self.session_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
		session_scroll_y.grid(row=0, column=1, sticky="ns", pady=10)
		session_scroll_x.grid(row=1, column=0, sticky="ew", padx=10)

		session_frame.grid_rowconfigure(0, weight=1)
		session_frame.grid_columnconfigure(0, weight=1)

		# Control buttons
		button_frame = tk.Frame(logs_frame, bg="#1e1e1e")
		button_frame.pack(fill="x", padx=10, pady=10)

		tk.Button(button_frame, text="Refresh Logs", command=self.refresh_all_logs,
				  bg="#2e2e2e", fg="white", font=("Segoe UI", 10)).pack(side="left", padx=5)

		tk.Button(button_frame, text="Clear Visible Logs", command=self.clear_visible_logs,
				  bg="#2e2e2e", fg="white", font=("Segoe UI", 10)).pack(side="left", padx=5)

		tk.Button(button_frame, text="Export Logs", command=self.export_logs,
				  bg="#2e2e2e", fg="white", font=("Segoe UI", 10)).pack(side="left", padx=5)

		# Load initial data
		self.refresh_all_logs()

		# Bind tab change event to load data when needed
		logs_notebook.bind("<<NotebookTabChanged>>", self.on_logs_tab_change)

	def on_logs_tab_change(self, event):
		"""Handle logs tab change - refresh data for selected tab"""
		try:
			selected_tab = event.widget.select()
			tab_text = event.widget.tab(selected_tab, "text")

			if tab_text == "Audit Logs":
				self.load_audit_logs()
			elif tab_text == "Activity Logs":
				self.load_activity_logs()
			elif tab_text == "Session Logs":
				self.load_session_logs()
		except Exception as e:
			print(f"[ERROR] Logs tab change: {e}")

	def refresh_all_logs(self):
		"""Refresh all log data"""
		self.load_audit_logs()
		self.load_activity_logs()
		self.load_session_logs()

	def load_audit_logs(self):
		"""Load audit logs data"""
		try:
			session = Session()
			self.audit_tree.delete(*self.audit_tree.get_children())

			logs = session.query(AuditLog).filter_by(visible=True).order_by(AuditLog.timestamp.desc()).all()
			for log in logs:
				self.audit_tree.insert("", "end", values=(
					log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
					log.username or "",
					log.action or "",
					log.description or ""
				))
			session.close()
		except Exception as e:
			print(f"[ERROR] Loading audit logs: {e}")

	def load_activity_logs(self):
		"""Load activity logs data"""
		try:
			session = Session()
			self.activity_tree.delete(*self.activity_tree.get_children())

			logs = session.query(ActivityLog).filter_by(visible=True).order_by(ActivityLog.timestamp.desc()).all()
			for log in logs:
				self.activity_tree.insert("", "end", values=(
					log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
					log.username or "",
					log.action or "",
					log.description or ""
				))
			session.close()
		except Exception as e:
			print(f"[ERROR] Loading activity logs: {e}")

	def load_session_logs(self):
		"""Load session logs data"""
		try:
			session = Session()
			self.session_tree.delete(*self.session_tree.get_children())

			logs = session.query(SessionLog).filter_by(visible=True).order_by(SessionLog.login_time.desc()).all()
			for log in logs:
				logout_time = log.logout_time.strftime("%Y-%m-%d %H:%M:%S") if log.logout_time else "Active"
				self.session_tree.insert("", "end", values=(
					log.login_time.strftime("%Y-%m-%d %H:%M:%S") if log.login_time else "",
					logout_time,
					log.user.username if log.user else "",
					log.ip_address or ""
				))
			session.close()
		except Exception as e:
			print(f"[ERROR] Loading session logs: {e}")

	def clear_visible_logs(self):
		"""Clear all visible logs"""
		try:
			from tkinter import messagebox

			result = messagebox.askyesno("Confirm Clear",
										 "Are you sure you want to clear all visible logs?\n"
										 "This action cannot be undone.")
			if not result:
				return

			session = Session()

			# Mark logs as not visible instead of deleting
			session.query(AuditLog).filter_by(visible=True).update({AuditLog.visible: False})
			session.query(ActivityLog).filter_by(visible=True).update({ActivityLog.visible: False})
			session.query(SessionLog).filter_by(visible=True).update({SessionLog.visible: False})

			session.commit()
			session.close()

			# Refresh the display
			self.refresh_all_logs()

			messagebox.showinfo("Logs Cleared", "All visible logs have been cleared from view.")

		except Exception as e:
			print(f"[ERROR] Clearing logs: {e}")
			messagebox.showerror("Error", f"Failed to clear logs: {e}")

	def export_logs(self):
		"""Export logs to file"""
		try:
			from tkinter import filedialog, messagebox
			import csv
			from datetime import datetime

			file_path = filedialog.asksaveasfilename(
				defaultextension=".csv",
				filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
				title="Export Logs"
			)

			if not file_path:
				return

			session = Session()

			with open(file_path, 'w', newline='', encoding='utf-8') as file:
				writer = csv.writer(file)

				# Export Audit Logs
				writer.writerow(["=== AUDIT LOGS ==="])
				writer.writerow(["Timestamp", "Username", "Action", "Description"])

				audit_logs = session.query(AuditLog).filter_by(visible=True).order_by(AuditLog.timestamp.desc()).all()
				for log in audit_logs:
					writer.writerow([
						log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
						log.username or "",
						log.action or "",
						log.description or ""
					])

				writer.writerow([])  # Empty row

				# Export Activity Logs
				writer.writerow(["=== ACTIVITY LOGS ==="])
				writer.writerow(["Timestamp", "Username", "Action", "Description"])

				activity_logs = session.query(ActivityLog).filter_by(visible=True).order_by(
					ActivityLog.timestamp.desc()).all()
				for log in activity_logs:
					writer.writerow([
						log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
						log.username or "",
						log.action or "",
						log.description or ""
					])

				writer.writerow([])  # Empty row

				# Export Session Logs
				writer.writerow(["=== SESSION LOGS ==="])
				writer.writerow(["Login Time", "Logout Time", "Username", "IP Address"])

				session_logs = session.query(SessionLog).filter_by(visible=True).order_by(
					SessionLog.login_time.desc()).all()
				for log in session_logs:
					logout_time = log.logout_time.strftime("%Y-%m-%d %H:%M:%S") if log.logout_time else "Active"
					writer.writerow([
						log.login_time.strftime("%Y-%m-%d %H:%M:%S") if log.login_time else "",
						logout_time,
						log.user.username if log.user else "",
						log.ip_address or ""
					])

			session.close()

			messagebox.showinfo("Export Complete", f"Logs exported successfully to:\n{file_path}")

		except Exception as e:
			print(f"[ERROR] Exporting logs: {e}")
			messagebox.showerror("Export Error", f"Failed to export logs: {e}")
		"""Build the print center interface"""
		print_frame = tk.Frame(parent, bg="#1e1e1e")
		print_frame.pack(fill="both", expand=True, padx=20, pady=20)

		# Print options
		print_options = [
			("Vendor Reports", "Export vendor lists and summaries"),
			("Mailing Labels", "Print addresses for mail campaigns"),
			("Tax Stickers", "Generate tax payment stickers"),
			("Receipts", "Print payment receipts"),
			("Table Maps", "Print venue layout maps"),
			("Activity Reports", "Print system logs and activity")
		]

		for i, (title, desc) in enumerate(print_options):
			option_frame = tk.Frame(print_frame, bg="#2e2e2e", relief="raised", bd=2)
			option_frame.pack(fill="x", pady=10)

			content = tk.Frame(option_frame, bg="#2e2e2e")
			content.pack(fill="both", expand=True, padx=20, pady=15)

			tk.Label(content, text=title, font=("Segoe UI", 14, "bold"),
					 bg="#2e2e2e", fg="white").pack(anchor="w")
			tk.Label(content, text=desc, font=("Segoe UI", 11),
					 bg="#2e2e2e", fg="#cccccc").pack(anchor="w", pady=(5, 10))

			btn = tk.Button(content, text="Print", command=lambda: self.open_export_window(),
							bg=self.current_user.accent_color, fg="black", font=("Segoe UI", 10),
							relief="flat", padx=15, pady=5)
			btn.pack(anchor="w")

	def logout(self):
		"""Logout and return to login screen"""
		from gui.login_window import LoginWindow
		log_session_logout(self.current_user.id)
		self.destroy()
		root = tk.Tk()
		LoginWindow(root)
		root.mainloop()

	def on_close(self):
		"""Handle application close"""
		log_session_logout(self.current_user.id)
		self.destroy()

	def open_export_window(self):
		"""Open export/report window"""
		ExportReportWindow(self, self.current_user)