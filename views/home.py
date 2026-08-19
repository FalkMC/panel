import customtkinter as ctk
import os
import json
import psutil
import threading
from mcstatus import JavaServer

class HomeView(ctk.CTkFrame):
    def __init__(self, master, colors, servers_base, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors
        self.servers_base = servers_base
        self.selected_server_path = None
        self.poll_after_id = None
        self._destroyed = False
        self.configure(fg_color="transparent")

        self.grid_columnconfigure(0, weight=1, uniform="rows")
        self.grid_columnconfigure(1, weight=1, uniform="rows")
        self.grid_rowconfigure(0, weight=2, uniform="rows")
        self.grid_rowconfigure(1, weight=1, uniform="rows")
        self.grid_rowconfigure(2, weight=1, uniform="rows")

        # --- TOP ROW ---
        welcome_frame = ctk.CTkFrame(
            self,
            height=80,
            corner_radius=15,
            fg_color=self.colors["element"],
            border_color=self.colors["border"],
            border_width=1
        )
        welcome_frame.grid(column=0, row=0, columnspan=2, padx=0, pady=(0, 8), sticky="nsew")
        welcome_frame.grid_propagate(False)

        # --- MIDDLE ROW ---
        ram_frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color=self.colors["element"],
            border_color=self.colors["border"],
            border_width=1
        )
        ram_frame.grid(column=0, row=1, padx=(0, 8), pady=8, sticky="nsew")
        ram_frame.grid_propagate(False)

        tps_frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color=self.colors["element"],
            border_color=self.colors["border"],
            border_width=1
        )
        tps_frame.grid(column=1, row=1, padx=(8, 0), pady=8, sticky="nsew")
        tps_frame.grid_propagate(False)

        # --- BOTTOM ROW ---
        players_frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color=self.colors["element"],
            border_color=self.colors["border"],
            border_width=1
        )
        players_frame.grid(column=0, row=2, padx=(0, 8), pady=(8, 0), sticky="nsew")
        players_frame.grid_propagate(False)

        network_frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color=self.colors["element"],
            border_color=self.colors["border"],
            border_width=1
        )
        network_frame.grid(column=1, row=2, padx=(8, 0), pady=(8, 0), sticky="nsew")
        network_frame.grid_propagate(False)

        # === WELCOME FRAME ===
        welcome_frame.grid_columnconfigure(0, weight=1)
        welcome_frame.grid_rowconfigure(0, weight=0)
        welcome_frame.grid_rowconfigure(1, weight=0)
        welcome_frame.grid_rowconfigure(2, weight=1)

        welcome_txt = ctk.CTkLabel(
            welcome_frame,
            text="Welcome back!",
            font=("Segoe UI", 28, "bold"),
            text_color=self.colors["text"]
        )
        welcome_txt.grid(row=0, column=0, sticky="nw", padx=15, pady=(10, 0))

        self.server_dropdown_var = ctk.StringVar(value="Select a server")
        self.server_dropdown = ctk.CTkOptionMenu(
            welcome_frame,
            values=["Select a server"],
            variable=self.server_dropdown_var,
            command=self.on_server_selected,
            font=("Segoe UI", 15),
            width=200,
            fg_color=self.colors["bg"],
            button_color=self.colors["border"],
            button_hover_color=self.colors["element"]
        )
        self.server_dropdown.grid(row=1, column=0, sticky="nw", padx=15, pady=(0, 40))

        info_container = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        info_container.grid(row=2, column=0, sticky="nsew", padx=15, pady=10)
        info_container.grid_rowconfigure(0, weight=1)
        info_container.grid_rowconfigure(1, weight=1)
        info_container.grid_rowconfigure(2, weight=1)
        info_container.grid_columnconfigure(0, weight=1)

        self.server_status_txt = ctk.CTkLabel(
            info_container,
            text="● Server: Not selected",
            text_color=self.colors["text_muted"],
            font=("Segoe UI Semibold", 13)
        )
        self.server_status_txt.grid(row=0, column=0, sticky="w", pady=2)

        self.backups_txt = ctk.CTkLabel(
            info_container,
            text="● Backups: N/A",
            text_color=self.colors["text_muted"],
            font=("Segoe UI Semibold", 13)
        )
        self.backups_txt.grid(row=1, column=0, sticky="w", pady=2)

        self.update_txt = ctk.CTkLabel(
            info_container,
            text="● Update: N/A",
            text_color=self.colors["text_muted"],
            font=("Segoe UI Semibold", 13)
        )
        self.update_txt.grid(row=2, column=0, sticky="w", pady=2)

        # === RAM FRAME ===
        ram_frame.grid_columnconfigure(0, weight=1)
        ram_frame.grid_rowconfigure(0, weight=1)
        ram_frame.grid_rowconfigure(1, weight=1)
        ram_frame.grid_rowconfigure(2, weight=1)

        self.ram_percent = ctk.CTkLabel(
            ram_frame,
            text="--",
            text_color=self.colors["text"],
            font=("Segoe UI", 28, "bold")
        )
        self.ram_percent.grid(row=0, column=0, sticky="sw", padx=15)

        self.ram_amount = ctk.CTkLabel(
            ram_frame,
            text="RAM - not selected",
            text_color=self.colors["text_muted"],
            font=("Segoe UI Semibold", 12)
        )
        self.ram_amount.grid(row=1, column=0, sticky="nw", padx=15)

        self.ram_progbar = ctk.CTkProgressBar(
            ram_frame,
            orientation="horizontal",
            fg_color=self.colors["bg"],
            progress_color=self.colors["green"],
            height=8
        )
        self.ram_progbar.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))
        self.ram_progbar.set(0)

        # === TPS FRAME ===
        tps_frame.grid_columnconfigure(0, weight=1)
        tps_frame.grid_rowconfigure(0, weight=1)
        tps_frame.grid_rowconfigure(1, weight=1)
        tps_frame.grid_rowconfigure(2, weight=1)

        tps_percent = ctk.CTkLabel(
            tps_frame,
            text="N/A",
            text_color=self.colors["text"],
            font=("Segoe UI", 28, "bold")
        )
        tps_percent.grid(row=0, column=0, sticky="sw", padx=15)

        tps_amount = ctk.CTkLabel(
            tps_frame,
            text="TPS - Not available",
            text_color=self.colors["text_muted"],
            font=("Segoe UI Semibold", 12)
        )
        tps_amount.grid(row=1, column=0, sticky="nw", padx=15)

        tps_progbar = ctk.CTkProgressBar(
            tps_frame,
            orientation="horizontal",
            fg_color=self.colors["bg"],
            progress_color=self.colors["green"],
            height=8
        )
        tps_progbar.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))
        tps_progbar.set(0)

        # === PLAYERS FRAME ===
        players_frame.grid_columnconfigure(0, weight=1)
        players_frame.grid_rowconfigure(0, weight=1)
        players_frame.grid_rowconfigure(1, weight=1)
        players_frame.grid_rowconfigure(2, weight=1)

        self.players_title = ctk.CTkLabel(
            players_frame,
            text="Players",
            text_color=self.colors["text"],
            font=("Segoe UI", 18, "bold")
        )
        self.players_title.grid(row=0, column=0, sticky="sw", padx=15)

        self.player_amount = ctk.CTkLabel(
            players_frame,
            text="-- online",
            text_color=self.colors["text_muted"],
            font=("Segoe UI Semibold", 12)
        )
        self.player_amount.grid(row=1, column=0, sticky="nw", padx=15)

        self.player_detail = ctk.CTkLabel(
            players_frame,
            text="● --/--",
            text_color=self.colors["text_muted"],
            font=("Segoe UI Semibold", 13)
        )
        self.player_detail.grid(row=2, column=0, sticky="nw", padx=15, pady=(0, 10))

        # === NETWORK FRAME ===
        network_frame.grid_columnconfigure(0, weight=1)
        network_frame.grid_rowconfigure(0, weight=1)
        network_frame.grid_rowconfigure(1, weight=1)
        network_frame.grid_rowconfigure(2, weight=1)

        network_txt = ctk.CTkLabel(
            network_frame,
            text="Network",
            text_color=self.colors["text"],
            font=("Segoe UI", 18, "bold")
        )
        network_txt.grid(row=0, column=0, sticky="sw", padx=15)

        upnp_txt = ctk.CTkLabel(
            network_frame,
            text="UPnP not connected",
            text_color=self.colors["text_muted"],
            font=("Segoe UI Semibold", 12)
        )
        upnp_txt.grid(row=1, column=0, sticky="nw", padx=15)

        port_txt = ctk.CTkLabel(
            network_frame,
            text="● Port forwarding needed",
            text_color=self.colors["text_muted"],
            font=("Segoe UI Semibold", 13)
        )
        port_txt.grid(row=2, column=0, sticky="nw", padx=15, pady=(0, 10))

        self.refresh_servers()

    def refresh_servers(self):
        if self._destroyed:
            return
        self.selected_server_path = None
        self.stop_polling()
        self.clear_stats()

        def scan():
            servers = []
            if os.path.exists(self.servers_base):
                for item in os.listdir(self.servers_base):
                    path = os.path.join(self.servers_base, item)
                    if os.path.isdir(path) and os.path.exists(os.path.join(path, "server.jar")):
                        servers.append(item)
            if self.winfo_exists() and not self._destroyed:
                self.after(0, lambda: self._update_dropdown(servers))

        threading.Thread(target=scan, daemon=True).start()

    def _update_dropdown(self, servers):
        if not self.winfo_exists() or self._destroyed:
            return
        if servers:
            self.server_dropdown.configure(values=servers)
            current = self.server_dropdown_var.get()
            if current not in servers:
                self.server_dropdown.set(servers[0])
                self.on_server_selected(servers[0])
            else:
                self.on_server_selected(current)
        else:
            self.server_dropdown.configure(values=["No servers found"])
            self.server_dropdown.set("No servers found")
            self.selected_server_path = None
            self.clear_stats()

    def on_server_selected(self, server_name):
        if not self.winfo_exists() or self._destroyed:
            return
        if server_name in ("Select a server", "No servers found"):
            self.selected_server_path = None
            self.stop_polling()
            self.clear_stats()
            return

        self.selected_server_path = os.path.join(self.servers_base, server_name)
        self._poll_async()

    def clear_stats(self):
        if not self.winfo_exists() or self._destroyed:
            return
        self.server_status_txt.configure(text="● Server: Not selected")
        self.ram_percent.configure(text="--")
        self.ram_amount.configure(text="RAM - not selected")
        self.ram_progbar.set(0)
        self.player_amount.configure(text="-- online")
        self.player_detail.configure(text="● --/--")

    def start_polling(self):
        if self.poll_after_id:
            self.after_cancel(self.poll_after_id)
        if not self._destroyed and self.winfo_exists():
            self.poll_after_id = self.after(5000, self._poll_async)

    def stop_polling(self):
        if self.poll_after_id:
            self.after_cancel(self.poll_after_id)
            self.poll_after_id = None

    def _poll_async(self):
        if not self.selected_server_path or self._destroyed or not self.winfo_exists():
            return
        threading.Thread(target=self._poll_worker, daemon=True).start()
        self.start_polling()

    def _poll_worker(self):
        path = self.selected_server_path
        if not path:
            return

        ram = self.get_ram_for_server(path)
        is_running = self.is_server_running(path)
        port = self.get_port_from_properties(path)

        players = None
        max_players = None
        if is_running:
            try:
                server = JavaServer.lookup(f"localhost:{port}")
                status = server.status(timeout=2)
                players = status.players.online
                max_players = status.players.max
            except Exception:
                pass

        if self.winfo_exists() and not self._destroyed:
            self.after(0, lambda: self._update_ui(ram, is_running, players, max_players))

    def _update_ui(self, ram, is_running, players, max_players):
        if not self.winfo_exists() or self._destroyed:
            return
        self.ram_amount.configure(text=f"RAM - {ram}")

        if is_running:
            self.server_status_txt.configure(text="● Server: Running", text_color=self.colors["green"])
        else:
            self.server_status_txt.configure(text="● Server: Stopped", text_color=self.colors["text_muted"])

        if players is not None and max_players is not None:
            self.player_amount.configure(text=f"{players} online")
            self.player_detail.configure(text=f"● {players}/{max_players}")
        else:
            if is_running:
                self.player_amount.configure(text="-- online")
                self.player_detail.configure(text="● --/--")
            else:
                self.player_amount.configure(text="0 online")
                self.player_detail.configure(text="● 0/--")

        self.ram_percent.configure(text="--")
        self.ram_progbar.set(0)

    # ----- Helpers -----
    def get_ram_for_server(self, server_path):
        ram = "2G"
        falkmc_path = os.path.join(server_path, "falkmc.json")
        if os.path.exists(falkmc_path):
            try:
                with open(falkmc_path, "r") as f:
                    data = json.load(f)
                    ram = data.get("ram_allocation", "2G")
            except:
                pass
        return ram

    def get_port_from_properties(self, server_path):
        port = "25565"
        props_path = os.path.join(server_path, "server.properties")
        if os.path.exists(props_path):
            with open(props_path, "r") as f:
                for line in f:
                    if line.startswith("server-port="):
                        port = line.split("=")[1].strip()
                        break
        return port

    def is_server_running(self, server_path):
        jar_path = os.path.join(server_path, "server.jar")
        for proc in psutil.process_iter(['pid', 'cmdline', 'cwd']):
            try:
                cmdline = proc.info['cmdline']
                if not cmdline:
                    continue
                if "java" in cmdline[0].lower() and proc.is_running():
                    if jar_path in " ".join(cmdline) and proc.info['cwd'] == server_path:
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def destroy(self):
        self._destroyed = True
        self.stop_polling()
        super().destroy()
