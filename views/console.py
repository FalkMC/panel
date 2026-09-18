import customtkinter as ctk
import os


class ConsoleView(ctk.CTkFrame):
    def __init__(self, master, colors, servers_base, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors
        self.servers_base = servers_base
        self.configure(fg_color="transparent")

        self.selected_server_path = None
        self.auto_scroll = True

        self.build_ui()
        self.refresh_server_list()

    # ============================================================
    #   COLOUR DARKENING THINGG
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

    # ============================================================
    #   UI CREATION
    # ============================================================

    def build_ui(self):
        # Single top bar: server dropdown + auto-scroll + clear
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 10))

        # Server dropdown
        self.server_dropdown_var = ctk.StringVar(value="Select a server")
        self.server_dropdown = ctk.CTkOptionMenu(
            top_frame,
            values=["Select a server"],
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
        self.server_dropdown.pack(side="left", padx=(5, 0))

        # Clear button
        clear_btn = ctk.CTkButton(
            top_frame,
            text="Clear",
            width=80,
            height=32,
            fg_color=self.colors["border"],
            text_color=self.colors["text"],
            hover_color=self._darken_color(self.colors["border"], 0.75),
            command=self.clear_console
        )
        clear_btn.pack(side="right", padx=5)

        # Auto-scroll switch
        self.auto_scroll_switch = ctk.CTkSwitch(
            top_frame,
            text="Auto-scroll",
            font=("Segoe UI", 13),
            text_color=self.colors["text"],
            fg_color=self.colors["border"],
            progress_color=self.colors["green"],
            button_color=self.colors["text"],
            button_hover_color=self.colors["text_muted"],
            command=self._toggle_auto_scroll
        )
        self.auto_scroll_switch.select()
        self.auto_scroll_switch.pack(side="right", padx=15)

        # Console output area
        console_frame = ctk.CTkFrame(
            self,
            fg_color=self.colors["element"],
            border_color=self.colors["border"],
            border_width=1,
            corner_radius=10
        )
        console_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.console_textbox = ctk.CTkTextbox(
            console_frame,
            fg_color=self.colors["element"],
            text_color=self.colors["text"],
            font=("Consolas", 12),
            wrap="word",
            border_width=0,
            corner_radius=10
        )
        self.console_textbox.pack(fill="both", expand=True, padx=8, pady=8)
        self.console_textbox.configure(state="disabled")

        # Command input row
        input_row = ctk.CTkFrame(self, fg_color="transparent")
        input_row.pack(fill="x")

        self.command_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Type a command…",
            font=("Consolas", 13),
            height=36,
            fg_color=self.colors["element"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            placeholder_text_color=self.colors["text_muted"]
        )
        self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.command_entry.bind("<Return>", lambda e: self.send_command())

        send_btn = ctk.CTkButton(
            input_row,
            text="Send",
            width=80,
            height=36,
            fg_color=self.colors["green"],
            text_color="#05261C",
            font=("Segoe UI", 13, "bold"),
            hover_color=self._darken_color(self.colors["green"], 0.75),
            command=self.send_command
        )
        send_btn.pack(side="right")

    # ============================================================
    #   SERVER LIST
    # ============================================================

    # Scan the servers folder and add to the dropdown
    def refresh_server_list(self):
        servers = []
        if os.path.exists(self.servers_base):
            for item in os.listdir(self.servers_base):
                path = os.path.join(self.servers_base, item)
                if os.path.isdir(path) and os.path.exists(os.path.join(path, "server.jar")):
                    servers.append(item)

        if servers:
            self.server_dropdown.configure(values=servers)
            current = self.server_dropdown_var.get()
            if current not in servers:
                self.server_dropdown.set(servers[0])
                self.on_server_selected(servers[0])
        else:
            self.server_dropdown.configure(values=["No servers found"])
            self.server_dropdown.set("No servers found")
            self.selected_server_path = None

    def on_server_selected(self, server_name):
        if server_name in ("Select a server", "No servers found"):
            self.selected_server_path = None
            return

        self.selected_server_path = os.path.join(self.servers_base, server_name)
        # TODO: hook up log streaming here!!!

    # ============================================================
    #   CONSOLE ACTIONS (placeholder!)
    # ============================================================

    def clear_console(self):
        self.console_textbox.configure(state="normal")
        self.console_textbox.delete("1.0", "end")
        self.console_textbox.configure(state="disabled")

    def _toggle_auto_scroll(self):
        self.auto_scroll = bool(self.auto_scroll_switch.get())

    # Send command to the selected server stdin
    def send_command(self):
        command = self.command_entry.get().strip()
        if not command:
            return

        # TODO: actually send command to the running server process
        self.append_to_console(f"> {command}")
        self.command_entry.delete(0, "end")

    # Add line to the output
    def append_to_console(self, text):
        self.console_textbox.configure(state="normal")
        self.console_textbox.insert("end", text + "\n")
        self.console_textbox.configure(state="disabled")
        if self.auto_scroll:
            self.console_textbox.see("end")
