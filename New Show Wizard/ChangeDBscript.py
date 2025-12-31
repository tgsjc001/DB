"""
New Show Wizard - Database Management Tool
Creates new TGS show databases by cloning existing ones.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
from db_utils import (
    get_existing_databases,
    create_database_from_template,
    OperationalError,
    DatabaseError
)


class ToolTip:
    """
    Create a tooltip for a given widget.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", 9, "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class NewShowWizard:
    """
    Main application class for the New Show Database Wizard.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("TGS New Show Database Wizard")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Initialize variables
        self.show_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.source_var = tk.StringVar()
        self.existing_dbs = []
        
        # Build UI
        self.create_widgets()
        
        # Load databases
        self.load_databases()

    def create_widgets(self):
        """Create and layout all UI widgets."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="New Show Database Wizard",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Description
        desc_label = ttk.Label(
            main_frame,
            text="Create a new show database by cloning an existing one.",
            font=("Arial", 9)
        )
        desc_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Show selection
        show_label = ttk.Label(main_frame, text="Show:", font=("Arial", 10, "bold"))
        show_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=8)
        
        shows = ["apr", "nov"]
        self.show_var.set(shows[0])
        show_combo = ttk.Combobox(
            main_frame, 
            textvariable=self.show_var, 
            values=shows,
            state="readonly",
            width=25
        )
        show_combo.grid(row=2, column=1, padx=5, pady=8)
        ToolTip(show_combo, "Select the show type (April or November)")
        
        # Year selection
        year_label = ttk.Label(main_frame, text="Year:", font=("Arial", 10, "bold"))
        year_label.grid(row=3, column=0, sticky=tk.W, padx=5, pady=8)
        
        years = [str(y) for y in range(1980, 2051)]
        self.year_var.set(years[-1])
        year_combo = ttk.Combobox(
            main_frame,
            textvariable=self.year_var,
            values=years,
            state="readonly",
            width=25
        )
        year_combo.grid(row=3, column=1, padx=5, pady=8)
        ToolTip(year_combo, "Select the year for the new show")
        
        # Source database selection
        source_label = ttk.Label(main_frame, text="Clone From:", font=("Arial", 10, "bold"))
        source_label.grid(row=4, column=0, sticky=tk.W, padx=5, pady=8)
        
        self.source_combo = ttk.Combobox(
            main_frame,
            textvariable=self.source_var,
            state="readonly",
            width=25
        )
        self.source_combo.grid(row=4, column=1, padx=5, pady=8)
        ToolTip(self.source_combo, "Select the database to use as a template")
        
        # Preview of target database name
        preview_label = ttk.Label(main_frame, text="New Database:", font=("Arial", 10, "bold"))
        preview_label.grid(row=5, column=0, sticky=tk.W, padx=5, pady=8)
        
        self.preview_var = tk.StringVar()
        self.update_preview()
        preview_value = ttk.Label(
            main_frame,
            textvariable=self.preview_var,
            font=("Arial", 10),
            foreground="blue"
        )
        preview_value.grid(row=5, column=1, sticky=tk.W, padx=5, pady=8)
        
        # Update preview when selections change
        self.show_var.trace('w', lambda *args: self.update_preview())
        self.year_var.trace('w', lambda *args: self.update_preview())
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        # Create button
        create_btn = ttk.Button(
            button_frame,
            text="Create Database",
            command=self.on_create,
            width=20
        )
        create_btn.grid(row=0, column=0, padx=5)
        
        # Refresh button
        refresh_btn = ttk.Button(
            button_frame,
            text="Refresh List",
            command=self.load_databases,
            width=20
        )
        refresh_btn.grid(row=0, column=1, padx=5)

    def update_preview(self):
        """Update the preview of the target database name."""
        target = f"tgsdb_{self.show_var.get()}_{self.year_var.get()}"
        self.preview_var.set(target)

    def load_databases(self):
        """Load existing databases from the server."""
        try:
            self.existing_dbs = get_existing_databases()
            if not self.existing_dbs:
                messagebox.showwarning(
                    "No Databases",
                    "No TGS databases found. Cannot proceed without a template database."
                )
                self.source_combo['values'] = []
                return
            
            self.source_combo['values'] = self.existing_dbs
            self.source_var.set(self.existing_dbs[0])
            
        except OperationalError as e:
            messagebox.showerror(
                "Connection Error",
                f"Failed to connect to database server:\n\n{str(e)}\n\n"
                "Please check your database configuration and ensure the server is running."
            )
            self.root.quit()
        except DatabaseError as e:
            messagebox.showerror(
                "Database Error",
                f"Failed to retrieve database list:\n\n{str(e)}"
            )
            self.root.quit()
        except Exception as e:
            messagebox.showerror(
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{str(e)}"
            )
            self.root.quit()

    def validate_input(self) -> bool:
        """
        Validate user input before creating database.
        
        Returns:
            bool: True if input is valid, False otherwise
        """
        source = self.source_var.get().strip()
        if not source:
            messagebox.showerror(
                "Validation Error",
                "Please select a database to clone from."
            )
            return False
        
        if not self.show_var.get():
            messagebox.showerror(
                "Validation Error",
                "Please select a show type."
            )
            return False
        
        if not self.year_var.get():
            messagebox.showerror(
                "Validation Error",
                "Please select a year."
            )
            return False
        
        return True

    def on_create(self):
        """Handle database creation button click."""
        if not self.validate_input():
            return
        
        source = self.source_var.get().strip()
        target = f"tgsdb_{self.show_var.get()}_{self.year_var.get()}"
        
        # Confirm with user
        response = messagebox.askyesno(
            "Confirm Creation",
            f"Create new database '{target}' from template '{source}'?\n\n"
            "This operation may take a few moments."
        )
        
        if not response:
            return
        
        try:
            # Disable button during creation
            for widget in self.root.winfo_children():
                widget.configure(state='disabled')
            self.root.update()
            
            # Create the database
            create_database_from_template(source, target)
            
            messagebox.showinfo(
                "Success",
                f"Database '{target}' created successfully!"
            )
            
            # Refresh the list
            self.load_databases()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except DatabaseError as e:
            messagebox.showerror(
                "Database Error",
                f"Failed to create database:\n\n{str(e)}"
            )
        except Exception as e:
            messagebox.showerror(
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{str(e)}"
            )
        finally:
            # Re-enable widgets
            for widget in self.root.winfo_children():
                widget.configure(state='normal')


def main():
    """Main entry point for the application."""
    try:
        root = tk.Tk()
        app = NewShowWizard(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        messagebox.showerror(
            "Fatal Error",
            f"Application failed to start:\n\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
