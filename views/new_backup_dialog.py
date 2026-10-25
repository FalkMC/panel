import customtkinter as ctk
import os

from resource import resource_path

def show_new_backup_dialog(view):
    colors = view.colors

    dialog = ctk.CTkToplevel(view)
    dialog.title("Create Backup")
    dialog.geometry("420x520")
    dialog.resizable(False, False)
    dialog.transient(view)
    dialog.grab_set()
    dialog.configure(fg_color=colors["bg"])
    dialog.iconbitmap(resource_path("images/logo.ico"))

    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - 210
    y = (dialog.winfo_screenheight() // 2) - 260
    dialog.geometry(f"+{x}+{y}")

    dialog.grid_columnconfigure(0, weight=1)

    dialog.grid_rowconfigure(0, weight=0)
    dialog.grid_rowconfigure(1, weight=0)
    dialog.grid_rowconfigure(2, weight=0)
    dialog.grid_rowconfigure(3, weight=0)
    dialog.grid_rowconfigure(4, weight=0)
    dialog.grid_rowconfigure(5, weight=0)
    dialog.grid_rowconfigure(6, weight=0)
    dialog.grid_rowconfigure(7, weight=0)
    dialog.grid_rowconfigure(8, weight=0)
    dialog.grid_rowconfigure(9, weight=0)

    # Get all servers
    servers = []
    if os.path.exists(view.servers_base): # Does servers folder exist?
        for item in os.listdir(view.servers_base): # Go through each item
            path = os.path.join(view.servers_base, item) # Build full path
            if os.path.isdir(path) and os.path.exists(os.path.join(path, "server.jar")): # Is it a server?
                servers.append(item) # Add it to list
    if not servers:
        servers = ["No servers found"] # If nothing is found

    # Function for char limit
    def make_character_limiter(string_var, limit):
        def limit_handler(*_):
            if len(string_var.get()) > limit: # Check if too long
                string_var.set(string_var.get()[:limit]) # Cut off extra chars
        return limit_handler # Send back the rule

    # Header txt
    backup_header_txt = ctk.CTkLabel(
        dialog,
        text="Create Backup",
        font=("Segoe UI", 20, "bold"),
        text_color=colors["text"]
    )
    backup_header_txt.grid(row=0, column=0, sticky="nw", padx=20, pady=(10, 2))

    # Subheading txt
    backup_subheading_txt = ctk.CTkLabel(
        dialog,
        text="Save a full copy of one of your servers",
        font=("Segoe UI", 13),
        text_color=colors["text_muted"]
    )
    backup_subheading_txt.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))

    # Server lbl
    server_label = ctk.CTkLabel(
        dialog,
        text="Server *",
        font=("Segoe UI Semibold", 14),
        text_color=colors["text"],
        anchor="w"
    )
    server_label.grid(row=2, column=0, sticky="nw", padx=20, pady=(0, 3))

    # Server menu
    server_selection = ctk.CTkOptionMenu(
        dialog,
        values=servers,
        width=340,
        fg_color=colors["element"],
        button_color=colors["border"],
        text_color=colors["text"],
        dropdown_fg_color=colors["element"],
        dropdown_text_color=colors["text"],
        dropdown_hover_color=colors["border"]
    )
    server_selection.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))

    # Backup name lbl
    backup_label = ctk.CTkLabel(
        dialog,
        text="Backup name *",
        font=("Segoe UI Semibold", 14),
        text_color=colors["text"],
        anchor="w"
    )
    backup_label.grid(row=4, column=0, sticky="nw", padx=20, pady=(0, 3))

    # Text var
    backup_name_var = ctk.StringVar()
    backup_name_var.trace_add("write", make_character_limiter(backup_name_var, 15)) # Trigger when text changes

    # Backup name input
    backup_name_input = ctk.CTkEntry(
        dialog,
        height=29,
        width=340,
        corner_radius=8,
        border_width=1,
        textvariable=backup_name_var,
        fg_color=colors["element"],
        border_color=colors["border"],
        text_color=colors["text"],
        font=("Segoe UI", 13)
    )
    backup_name_input.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 15))

    # Description name lbl
    desc_label = ctk.CTkLabel(
        dialog,
        text="Description (optional)",
        font=("Segoe UI Semibold", 14),
        text_color=colors["text"],
        anchor="w"
    )
    desc_label.grid(row=6, column=0, sticky="nw", padx=20, pady=(0, 3))

    # Description input
    desc_input = ctk.CTkTextbox(
        dialog,
        height=64,
        width=340,
        corner_radius=8,
        border_width=1,
        fg_color=colors["element"],
        border_color=colors["border"],
        text_color=colors["text"],
        font=("Segoe UI", 13)
    )
    desc_input.grid(row=7, column=0, sticky="ew", padx=20, pady=(0, 25))

    # Info frame
    info_frame = ctk.CTkFrame(
        dialog,
        height=85,
        corner_radius=8,
        fg_color=colors["element"],
        border_color=colors["border"],
        border_width=1
    )
    info_frame.grid(row=8, column=0, padx=20, pady=(0, 30), sticky="nsew")
    info_frame.grid_propagate(False)
    
    # INFO FRAME CONTENT STUFF
    info_frame.grid_columnconfigure(1, weight=1)
    
    # Icon on the left
    info_icon = ctk.CTkLabel(
        info_frame,
        text="ⓘ",
        font=("Segoe UI Semibold", 20),
        text_color=colors["green"]
    )
    info_icon.grid(row=0, column=0, padx=(15, 10), pady=10, sticky="nw")
    
    # Text container on the right
    info_text_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
    info_text_frame.grid(row=0, column=1, sticky="nw", padx=(0, 15), pady=10)
    
    info_title = ctk.CTkLabel(
        info_text_frame,
        text="Full server backup",
        font=("Segoe UI Semibold", 13),
        text_color=colors["text"],
        anchor="w"
    )
    info_title.pack(anchor="w")
    
    info_desc = ctk.CTkLabel(
        info_text_frame,
        text="Includes all Survival worlds, plugins, and configuration files. This may take a few minutes.",
        font=("Segoe UI", 12),
        text_color=colors["text_muted"],
        anchor="w",
        justify="left",
        wraplength=300  # Ensures the text wraps nicely inside the frame
    )
    info_desc.pack(anchor="w", pady=(2, 0))

    # Create backup btn
    btn_create = ctk.CTkButton(
        dialog,
        text="+ Create backup",
        font=("Segoe UI", 12, "bold"),
        fg_color=colors["green"],
        text_color="#05261C",
        hover_color=view._darken_color(colors["green"], 0.75),
        width=120,
        height=32
    )
    btn_create.grid(row=9, column=0, padx=20, pady=(0, 15), sticky="se")
