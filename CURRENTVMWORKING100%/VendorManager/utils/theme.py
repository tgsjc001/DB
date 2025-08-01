import tkinter as tk
from tkinter import font as tkfont

def apply_user_theme(widget, user):
    settings = None
    if hasattr(user, 'settings') and isinstance(user.settings, list):
        settings = user.settings[0] if user.settings else None
    elif hasattr(user, 'settings'):
        settings = user.settings

    # Safe fallbacks
    theme = 'dark'
    font_name = 'Segoe UI'
    label_size = 12
    entry_size = 12
    tree_size = 10

    if settings:
        theme = getattr(settings, 'theme', theme)
        font_name = getattr(settings, 'font', font_name)

        try:
            label_size = int(getattr(settings, 'font_size_label', label_size))
        except (ValueError, TypeError):
            pass

        try:
            entry_size = int(getattr(settings, 'font_size_entry', entry_size))
        except (ValueError, TypeError):
            pass

        try:
            tree_size = int(getattr(settings, 'font_size_tree', tree_size))
        except (ValueError, TypeError):
            pass

    apply_user_fonts(widget, font_name, label_size, entry_size, tree_size)

    if theme == 'dark':
        apply_dark_style(widget)
    else:
        apply_light_style(widget)


def apply_user_fonts(widget, font_name, label_size, entry_size, tree_size):
    try:
        font_str_label = (font_name, label_size)
        font_str_entry = (font_name, entry_size)
        font_str_tree = (font_name, tree_size)

        widget.option_add("*Font", font_str_label)
        widget.option_add("*Label.Font", font_str_label)
        widget.option_add("*Entry.Font", font_str_entry)
        widget.option_add("*Treeview.Font", font_str_tree)

        tkfont.nametofont("TkDefaultFont").configure(family=font_name, size=label_size)
        tkfont.nametofont("TkTextFont").configure(family=font_name, size=entry_size)
        tkfont.nametofont("TkFixedFont").configure(family=font_name, size=entry_size)
    except Exception as e:
        print(f"Error applying fonts: {e}")



def apply_dark_style(widget):
    try:
        widget.tk_setPalette(background="#1e1e1e", foreground="white")
        widget.option_add("*Background", "#1e1e1e")
        widget.option_add("*Foreground", "white")
        widget.option_add("*Button.Background", "#2e2e2e")
        widget.option_add("*Button.Foreground", "white")
    except Exception as e:
        print(f"Error applying dark style: {e}")


def apply_light_style(widget):
    try:
        widget.tk_setPalette(background="SystemButtonFace", foreground="black")
        widget.option_add("*Background", "SystemButtonFace")
        widget.option_add("*Foreground", "black")
        widget.option_add("*Button.Background", "SystemButtonFace")
        widget.option_add("*Button.Foreground", "black")
    except Exception as e:
        print(f"Error applying light style: {e}")
