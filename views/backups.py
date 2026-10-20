import os
import tkinter as tk
import customtkinter as ctk

CARD_HEIGHT = 78  # shared height for both stat cards


class BackupsView(ctk.CTkFrame):
    def __init__(self, master, colors, servers_base, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors
        self.servers_base = servers_base
        self.configure(fg_color="transparent")

        # Runtime state attributes
        self.current_servers = None
        self.servers_check_job = None

        # Build UI layout
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

    def _divider(self, parent):
        """1px horizontal dividing line."""
        # Plain tk.Frame: CTkFrame won't reliably draw a 1px-high frame
        return tk.Frame(parent, height=1, bd=0, highlightthickness=0, bg=self.colors["border"])

    # ============================================================
    #   UI CREATION
    # ============================================================
    def build_ui(self):
        # Top bar: fixed height so title and button can be centred on the same axis
        top_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        top_frame.pack(fill="x", pady=(0, 10))
        top_frame.pack_propagate(False)

        self.lbl_title = ctk.CTkLabel(
            top_frame, text="Backups", font=("Segoe UI", 20, "bold"),
            text_color=self.colors["text"]
        )
        # FIX 2: place() with rely=0.5 centres both widgets on the exact same vertical line
        self.lbl_title.place(relx=0.0, rely=0.5, anchor="w", x=5)

        self.btn_create = ctk.CTkButton(
            top_frame,
            text="+ Create backup",
            font=("Segoe UI", 12, "bold"),
            fg_color=self.colors["green"],
            text_color="#05261C",
            hover_color=self._darken_color(self.colors["green"], 0.75),
            width=120,
            height=32
        )
        self.btn_create.place(relx=1.0, rely=0.5, anchor="e", x=-5)

        # Main display body
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True, padx=5, pady=5)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(2, weight=1)

        self.create_filter_section(0)
        self.create_stats_section(1)
        self.create_backups_table(2)

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

    def create_stats_section(self, row_idx):
        stats_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        stats_frame.grid(row=row_idx, column=0, sticky="ew", pady=(0, 15), padx=2)
        stats_frame.grid_columnconfigure((0, 1), weight=1, uniform="stats")

        # ---------- Card 1: last successful backup ----------
        self.card_1 = ctk.CTkFrame(
            stats_frame, fg_color=self.colors["element"],
            border_color=self.colors["border"], border_width=1,
            corner_radius=10, height=CARD_HEIGHT
        )
        self.card_1.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        # FIX 1: children are packed, so pack_propagate (not grid_propagate) locks the height
        self.card_1.pack_propagate(False)

        # FIX 4: bigger emoji font + fixed-width icon cell, so it sits centred
        # between the card edge and the text
        c1_icon = ctk.CTkLabel(
            self.card_1, text="🛡️", font=("Segoe UI Emoji", 26),
            text_color=self.colors["green"]
        )
        # Equal padding on both sides = equal gap to card edge and to the text
        c1_icon.pack(side="left", padx=(20, 20))

        # No fill="y" and no pady -> the text block is vertically centred by pack
        c1_txt_frame = ctk.CTkFrame(self.card_1, fg_color="transparent")
        c1_txt_frame.pack(side="left")
        ctk.CTkLabel(
            c1_txt_frame, text="Last successful backup", font=("Segoe UI", 11),
            text_color=self.colors["text_muted"], anchor="w"
        ).pack(anchor="w")
        self.lbl_last_backup = ctk.CTkLabel(
            c1_txt_frame, text="Today, 03:00", font=("Segoe UI", 12, "bold"),
            text_color=self.colors["text"], anchor="w"
        )
        self.lbl_last_backup.pack(anchor="w")

        # ---------- Card 2: storage use ----------
        self.card_2 = ctk.CTkFrame(
            stats_frame, fg_color=self.colors["element"],
            border_color=self.colors["border"], border_width=1,
            corner_radius=10, height=CARD_HEIGHT
        )
        self.card_2.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        self.card_2.pack_propagate(False)

        # expand=True with no fill="y" vertically centres the content in the card
        storage_inner = ctk.CTkFrame(self.card_2, fg_color="transparent")
        storage_inner.pack(expand=True, fill="x", padx=15)

        # Top row: "Backup storage" on the left, used / total on the right
        storage_top = ctk.CTkFrame(storage_inner, fg_color="transparent")
        storage_top.pack(fill="x")
        ctk.CTkLabel(
            storage_top, text="Backup storage", font=("Segoe UI", 11),
            text_color=self.colors["text_muted"]
        ).pack(side="left")
        self.lbl_storage_amount = ctk.CTkLabel(
            storage_top, text="— / —", font=("Segoe UI", 11, "bold"),
            text_color=self.colors["text"]
        )
        self.lbl_storage_amount.pack(side="right")

        self.storage_progress = ctk.CTkProgressBar(
            storage_inner, progress_color=self.colors["green"],
            fg_color=self.colors["border"], height=6
        )
        self.storage_progress.set(0)
        self.storage_progress.pack(fill="x", pady=(6, 4))

        self.lbl_storage_detail = ctk.CTkLabel(
            storage_inner, text="0% used", font=("Segoe UI", 10),
            text_color=self.colors["text_muted"], anchor="w"
        )
        self.lbl_storage_detail.pack(anchor="w")

    def create_backups_table(self, row_idx):
        self.table_panel = ctk.CTkFrame(
            self.content_container, fg_color=self.colors["element"],
            border_color=self.colors["border"], border_width=1, corner_radius=10
        )
        self.table_panel.grid(row=row_idx, column=0, sticky="nsew", pady=(0, 5), padx=2)
        self.table_panel.grid_columnconfigure(0, weight=1)
        self.table_panel.grid_rowconfigure(3, weight=1)  # scrollable body gets the spare space

        # Row 0: panel title
        t_header = ctk.CTkFrame(self.table_panel, fg_color="transparent")
        t_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 10))
        ctk.CTkLabel(
            t_header, text="Your backups", font=("Segoe UI", 14, "bold"),
            text_color=self.colors["text"], height=24
        ).pack(side="left")

        # Count badge next to the title
        self.lbl_backup_count = ctk.CTkLabel(
            t_header, text="0", font=("Segoe UI", 10),
            text_color=self.colors["text_muted"], fg_color=self.colors["border"],
            corner_radius=6, width=22, height=18
        )
        self.lbl_backup_count.pack(side="left", padx=(8, 0))

        # Row 1: darker band behind the column headers (no divider above it)
        # (padx=1 keeps it inside the panel's rounded border)
        header_band = ctk.CTkFrame(
            self.table_panel, corner_radius=0,
            fg_color=self._darken_color(self.colors["element"], 0.8)
        )
        header_band.grid(row=1, column=0, sticky="ew", padx=1)

        grid_header = ctk.CTkFrame(header_band, fg_color="transparent")
        grid_header.pack(fill="x", padx=(14, 20), pady=4)

        self.columns = [("Name", 3), ("Created", 2), ("Type", 1), ("Size", 1), ("Status", 2), ("Actions", 1)]
        for idx, (col_name, weight) in enumerate(self.columns):
            # uniform= keeps data rows built later perfectly aligned with these headers
            grid_header.grid_columnconfigure(idx, weight=weight, uniform="cols")
            ctk.CTkLabel(
                grid_header, text=col_name, font=("Segoe UI", 11), height=16,
                text_color=self.colors["text_muted"], anchor="w"
            ).grid(row=0, column=idx, sticky="ew")

        # Row 2: divider between column headers and the rows
        self._divider(self.table_panel).grid(row=2, column=0, sticky="ew", padx=1)

        # Row 3: scrollable data area (add backup rows here)
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

    def update_storage(self, used_gb, total_gb):
        """Call this once you have real numbers, e.g. update_storage(8.4, 20)."""
        pct = used_gb / total_gb if total_gb else 0
        self.storage_progress.set(min(pct, 1))
        self.lbl_storage_amount.configure(text=f"{used_gb:g} GB / {total_gb:g} GB")
        self.lbl_storage_detail.configure(
            text=f"{round(pct * 100)}% used · {total_gb - used_gb:g} GB available"
        )
