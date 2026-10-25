import os
import tkinter as tk
import customtkinter as ctk

from views.new_backup_dialog import show_new_backup_dialog


class BackupsView(ctk.CTkFrame):
    def __init__(self, master, colors, servers_base, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors
        self.servers_base = servers_base
        self.configure(fg_color="transparent")

        # Runtime state attributes
        self.current_servers = None
        self.servers_check_job = None

        self.build_ui()
        self.refresh_server_list()
        self._check_servers_changed()

    # ============================================================
    #   UTILITIES
    # ============================================================
    def _darken_color(self, hex_color, factor=0.75):
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    # 1px horizontal dividing line
    def _divider(self, parent):
        return tk.Frame(parent, height=1, bd=0, highlightthickness=0, bg=self.colors["border"])

    # ============================================================
    #   UI CREATION
    # ============================================================
    def build_ui(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        top_frame.pack(fill="x", pady=(0, 10))
        top_frame.pack_propagate(False)

        self.lbl_title = ctk.CTkLabel(
            top_frame, text="Backups", font=("Segoe UI", 20, "bold"),
            text_color=self.colors["text"]
        )
        self.lbl_title.place(relx=0.0, rely=0.5, anchor="w", x=5)

        self.btn_create = ctk.CTkButton(
            top_frame,
            text="+ Create backup",
            font=("Segoe UI", 12, "bold"),
            fg_color=self.colors["green"],
            text_color="#05261C",
            hover_color=self._darken_color(self.colors["green"], 0.75),
            width=120,
            height=32,
            command=self.new_backup_dialog
        )
        self.btn_create.place(relx=1.0, rely=0.5, anchor="e", x=-5)

        # Main display body
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True, padx=5, pady=5)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(1, weight=1)  # only the table expands

        self.create_filter_section(0)
        self.create_backups_table(1)

    def new_backup_dialog(self):
        show_new_backup_dialog(self)

    def create_filter_section(self, row_idx):
        filter_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        filter_frame.grid(row=row_idx, column=0, sticky="w", pady=(0, 15), padx=2)

        self.server_dropdown_var = ctk.StringVar(value="All servers")
        self.server_dropdown = ctk.CTkOptionMenu(
            filter_frame,
            values=["All servers"],
            variable=self.server_dropdown_var,
            command=self.on_server_selected,
            font=("Segoe UI", 13),
            width=220,
            fg_color=self.colors["element"],
            button_color=self.colors["border"],
            button_hover_color=self._darken_color(self.colors["border"], 0.75),
            text_color=self.colors["text"],
            dropdown_fg_color=self.colors["element"],
            dropdown_text_color=self.colors["text"],
            dropdown_hover_color=self.colors["border"]
        )
        self.server_dropdown.pack(side="left")

    def create_backups_table(self, row_idx):
        self.table_panel = ctk.CTkFrame(
            self.content_container, fg_color=self.colors["element"],
            border_color=self.colors["border"], border_width=1, corner_radius=10
        )
        self.table_panel.grid(row=row_idx, column=0, sticky="nsew", pady=(0, 5), padx=2)
        self.table_panel.grid_columnconfigure(0, weight=1)
        self.table_panel.grid_rowconfigure(3, weight=1)

        # Row 0: panel title
        t_header = ctk.CTkFrame(self.table_panel, fg_color="transparent")
        t_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 10))
        ctk.CTkLabel(
            t_header, text="Your backups", font=("Segoe UI", 14, "bold"),
            text_color=self.colors["text"], height=24
        ).pack(side="left")

        self.lbl_backup_count = ctk.CTkLabel(
            t_header, text="0", font=("Segoe UI", 10),
            text_color=self.colors["text_muted"], fg_color=self.colors["border"],
            corner_radius=6, width=22, height=18
        )
        self.lbl_backup_count.pack(side="left", padx=(8, 0))

        # Row 1: darker band behind the column headers
        header_band = ctk.CTkFrame(
            self.table_panel, corner_radius=0,
            fg_color=self._darken_color(self.colors["element"], 0.8)
        )
        header_band.grid(row=1, column=0, sticky="ew", padx=1)

        grid_header = ctk.CTkFrame(header_band, fg_color="transparent")
        grid_header.pack(fill="x", padx=(14, 20), pady=4)

        self.columns = [("Name", 3), ("Created", 2), ("Type", 1), ("Size", 1), ("Status", 2), ("Actions", 1)]
        for idx, (col_name, weight) in enumerate(self.columns):
            grid_header.grid_columnconfigure(idx, weight=weight, uniform="cols")
            ctk.CTkLabel(
                grid_header, text=col_name, font=("Segoe UI", 11), height=16,
                text_color=self.colors["text_muted"], anchor="w"
            ).grid(row=0, column=idx, sticky="ew")

        # Row 2: divider
        self._divider(self.table_panel).grid(row=2, column=0, sticky="ew", padx=1)

        # Row 3: scrollable body
        self.table_grid = ctk.CTkScrollableFrame(self.table_panel, fg_color="transparent", corner_radius=0)
        self.table_grid.grid(row=3, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self.table_grid._scrollbar.configure(width=6)

    # ============================================================
    #   SERVER LIST MONITOR
    # ============================================================
    def refresh_server_list(self):
        servers = ["All servers"]
        if os.path.exists(self.servers_base):
            for item in os.listdir(self.servers_base):
                path = os.path.join(self.servers_base, item)
                if os.path.isdir(path) and os.path.exists(os.path.join(path, "server.jar")):
                    servers.append(item)

        if servers == self.current_servers:
            return

        self.current_servers = servers
        current = self.server_dropdown_var.get()

        self.server_dropdown.configure(values=servers)
        if current not in servers:
            self.server_dropdown.set("All servers")

    def _check_servers_changed(self):
        if not self.winfo_exists():
            return
        try:
            self.refresh_server_list()
        except Exception as e:
            print(f"Error checking servers: {e}")
        self.servers_check_job = self.after(5000, self._check_servers_changed)

    def on_server_selected(self, server_name):
        print(f"Filtering scope: {server_name}")
