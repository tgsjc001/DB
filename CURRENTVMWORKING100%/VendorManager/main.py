import tkinter as tk
import traceback
import tkinter.messagebox as mb
from models import Session  # ⬅ this ensures __init__.py runs and binds all relationships


try:
    from gui.login_window import LoginWindow

    def main():
        root = tk.Tk()
        LoginWindow(root)
        root.mainloop()

    if __name__ == "__main__":
        main()

except Exception as e:
    mb.showerror("Startup Crash", str(e))
    with open("error.log", "w") as f:
        f.write(traceback.format_exc())
    input("Press Enter to close...")
