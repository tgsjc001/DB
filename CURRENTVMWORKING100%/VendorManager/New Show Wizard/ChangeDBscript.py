import psycopg2
import tkinter as tk
from tkinter import ttk, messagebox
import configparser

# Load config
config = configparser.ConfigParser()
config.read('config.ini')
db_config = config['postgres']

def get_existing_databases():
    conn = psycopg2.connect(
        dbname='postgres',
        user=db_config['user'],
        password=db_config['password'],
        host=db_config['host'],
        port=db_config['port']
    )
    cur = conn.cursor()
    cur.execute(r"""
        SELECT datname FROM pg_database
        WHERE datname LIKE 'tgsdb\_%\_%' ESCAPE '\'
        ORDER BY datname DESC;
    """)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in results]

def create_cloned_db(source_db, target_db):
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            port=db_config['port']
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Check if target already exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (target_db,))
        if cur.fetchone():
            messagebox.showerror("Error", f"Database '{target_db}' already exists.")
            return

        # Terminate connections to source (precaution)
        cur.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid();
        """, (source_db,))

        # Clone DB
        cur.execute(f"""
            CREATE DATABASE "{target_db}"
            WITH TEMPLATE "{source_db}"
            OWNER {db_config['user']};
        """)
        messagebox.showinfo("Success", f"Database '{target_db}' created successfully.")

    except Exception as e:
        messagebox.showerror("Error", str(e))

    finally:
        if conn:
            conn.close()

def launch_wizard():
    root = tk.Tk()
    root.title("Database Show Change")

    shows = ["apr", "nov"]
    years = [str(y) for y in range(1980, 2051)]

    existing_dbs = get_existing_databases()

    tk.Label(root, text="Select Show:").grid(row=0, column=0, padx=5, pady=5)
    show_var = tk.StringVar(value=shows[0])
    ttk.Combobox(root, textvariable=show_var, values=shows).grid(row=0, column=1)

    tk.Label(root, text="Select Year:").grid(row=1, column=0, padx=5, pady=5)
    year_var = tk.StringVar(value=years[-1])
    ttk.Combobox(root, textvariable=year_var, values=years).grid(row=1, column=1)

    tk.Label(root, text="Clone From:").grid(row=2, column=0, padx=5, pady=5)
    source_var = tk.StringVar(value=existing_dbs[0] if existing_dbs else "")
    ttk.Combobox(root, textvariable=source_var, values=existing_dbs, width=30).grid(row=2, column=1)

    def on_create():
        source = source_var.get().strip()
        if not source:
            messagebox.showerror("Error", "Please select a database to clone from.")
            return
        target = f"tgsdb_{show_var.get()}_{year_var.get()}"
        create_cloned_db(source, target)

    tk.Button(root, text="Create New Show DB", command=on_create).grid(row=3, columnspan=2, pady=10)
    root.mainloop()

if __name__ == "__main__":
    launch_wizard()
