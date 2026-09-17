import customtkinter as ctk
import os
import subprocess
import psutil
import time
import json
import requests
import threading
import webbrowser
import re
import socket
from tkinter import messagebox
from mcstatus import JavaServer

from views.settings_dialog import ServerSettingsDialog
from views.java import find_java, get_java_version
from views.new_server_dialog import show_new_server_dialog


class ServersView(ctk.CTkFrame):
    def __init__(self, master, colors, servers_base, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors
        self.servers_base = servers_base
        self.configure(fg_color="transparent")

        if not os.path.exists(self.servers_base):
            os.makedirs(self.servers_base, exist_ok=True)

        self.server_processes = {}
        self.poll_jobs = {}
        self.scan_thread = None
        self.scanning = False
        self._destroyed = False

        # Public IP cache
        self._cached_public_ip = None
        self._public_ip_fetch_time = 0

        self.build_ui()
        self.refresh_servers()

    # ============================================================
    #   UI CONSTRUCTION
    # ============================================================

    def build_ui(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 10))

        title = ctk.CTkLabel(
            top_frame,
            text="Your Servers",
            font=("Segoe UI", 20, "bold"),
            text_color=self.colors["text"]
        )
        title.pack(side="left", padx=5)

        new_btn = ctk.CTkButton(
            top_frame,
            text="+ New Server",
            width=120,
            height=32,
            fg_color=self.colors["green"],
            text_color="#05261C",
            hover_color=self._darken_color(self.colors["green"], 0.75),
            command=self.new_server_dialog
        )
        new_btn.pack(side="right", padx=5)

        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.scrollable_frame._scrollbar.configure(width=6)

    # ============================================================
    #   HELPERS
    # ============================================================

    def _darken_color(self, hex_color, factor=0.75):
        # Return a darker version of a hex color
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_local_ip(self):
        try:
            hostname = socket.gethostname()
            ip_list = socket.gethostbyname_ex(hostname)[2]
            for ip in ip_list:
                if not ip.startswith("127.") and "." in ip:
                    return ip
        except:
            pass
        return "Unknown"

    def _get_public_ip(self):
        now = time.time()
        if self._cached_public_ip and (now - self._public_ip_fetch_time) < 300:
            return self._cached_public_ip
        try:
            response = requests.get("https://api.ipify.org", timeout=3)
            if response.status_code == 200:
                self._cached_public_ip = response.text.strip()
                self._public_ip_fetch_time = now
                return self._cached_public_ip
        except:
            pass
        return self._cached_public_ip or "Unknown"

    def _copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def _toggle_ip_visibility(self, card):
        card.show_ips = not getattr(card, 'show_ips', False)
        local_ip = getattr(card, 'local_ip', '')
        public_ip = getattr(card, 'public_ip', '')
        port = getattr(card, 'port', '')
        show = card.show_ips

        if local_ip:
            if show:
                card.local_label.configure(text=f"Local: {local_ip}:{port}")
            else:
                card.local_label.configure(text="Local: ***.***.***.***")
        if public_ip:
            if show:
                card.public_label.configure(text=f"Public: {public_ip}:{port}")
            else:
                card.public_label.configure(text="Public: ***.***.***.***")

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
                    line = line.strip()
                    if line.startswith("server-port="):
                        port = line.split("=")[1]
                        break
        return port

    # ============================================================
    #   SERVER SCANNING
    # ============================================================

    def refresh_servers(self):
        if self._destroyed or not self.winfo_exists():
            return
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        for path, after_id in list(self.poll_jobs.items()):
            if after_id:
                self.after_cancel(after_id)
        self.poll_jobs.clear()

        loading_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="Locating servers...",
            font=("Segoe UI", 16),
            text_color=self.colors["text_muted"]
        )
        loading_label.pack(pady=50)
        self.update_idletasks()

        if self.scan_thread and self.scan_thread.is_alive():
            pass
        self.scanning = True
        self.scan_thread = threading.Thread(target=self._scan_servers, daemon=True)
        self.scan_thread.start()

    def _scan_servers(self):
        running_paths = set()
        for proc in psutil.process_iter(['pid', 'cmdline', 'cwd']):
            try:
                cmdline = proc.info['cmdline']
                if not cmdline:
                    continue
                if "java" in cmdline[0].lower() and proc.is_running():
                    if "server.jar" in " ".join(cmdline):
                        cwd = proc.info['cwd']
                        if cwd:
                            running_paths.add(cwd)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        servers_data = []
        if os.path.exists(self.servers_base):
            for item in os.listdir(self.servers_base):
                server_path = os.path.join(self.servers_base, item)
                if os.path.isdir(server_path):
                    if os.path.exists(os.path.join(server_path, "server.jar")):
                        port = "25565"
                        motd = "A Minecraft Server"
                        props_path = os.path.join(server_path, "server.properties")
                        if os.path.exists(props_path):
                            with open(props_path, "r") as f:
                                for line in f:
                                    line = line.strip()
                                    if line.startswith("server-port="):
                                        port = line.split("=")[1]
                                    elif line.startswith("motd="):
                                        motd = line.split("=")[1]
                        is_running = server_path in running_paths
                        servers_data.append({
                            "name": item,
                            "path": server_path,
                            "port": port,
                            "motd": motd,
                            "running": is_running
                        })
        if self.winfo_exists() and not self._destroyed:
            self.after(0, lambda: self._update_servers(servers_data))

    def _update_servers(self, servers_data):
        if not self.winfo_exists() or self._destroyed:
            return
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not servers_data:
            placeholder = ctk.CTkLabel(
                self.scrollable_frame,
                text="No servers found.\nClick 'New Server' to create one.",
                font=("Segoe UI", 16),
                text_color=self.colors["text_muted"],
                justify="center"
            )
            placeholder.pack(pady=50)
        else:
            for data in servers_data:
                ram = self.get_ram_for_server(data["path"])
                self.add_server_card(
                    data["name"],
                    data["path"],
                    data["port"],
                    data["motd"],
                    data["running"],
                    ram
                )
        self.scanning = False

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

    # ============================================================
    #   SERVER CARD
    # ============================================================

    def add_server_card(self, server_name, server_path, port, motd, is_running, ram="2G"):
        card = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color=self.colors["element"],
            border_color=self.colors["border"],
            border_width=1,
            corner_radius=10
        )
        card.pack(fill="x", pady=6, padx=2)

        card.grid_columnconfigure(0, weight=0)
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=0)

        status_label = ctk.CTkLabel(
            card,
            text="●",
            font=("Segoe UI", 18),
            text_color=self.colors["green"] if is_running else self.colors["text_muted"]
        )
        status_label.grid(row=0, column=0, padx=(15, 5), pady=10, sticky="w")

        name_label = ctk.CTkLabel(
            card,
            text=server_name,
            font=("Segoe UI", 16, "bold"),
            text_color=self.colors["text"]
        )
        name_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        details_label = ctk.CTkLabel(
            card,
            text=f"Port: {port}  •  {motd}",
            font=("Segoe UI", 12),
            text_color=self.colors["text_muted"]
        )
        details_label.grid(row=1, column=1, padx=5, pady=(0, 5), sticky="w")

        info_label = ctk.CTkLabel(
            card,
            text=f"0/20 players  •  {ram} RAM",
            font=("Segoe UI", 12),
            text_color=self.colors["text_muted"]
        )
        info_label.grid(row=2, column=1, padx=5, pady=(0, 5), sticky="w")

        ip_row = ctk.CTkFrame(card, fg_color="transparent")
        ip_row.grid(row=3, column=1, padx=5, pady=(0, 5), sticky="w")

        local_ip = self._get_local_ip()
        public_ip = self._get_public_ip()

        card.local_ip = local_ip
        card.public_ip = public_ip
        card.port = port
        card.show_ips = False

        local_label = ctk.CTkLabel(
            ip_row,
            text="Local: ***.***.***.***",
            font=("Segoe UI", 10),
            text_color=self.colors["text_muted"]
        )
        local_label.pack(side="left", padx=(0, 5))

        copy_local_btn = ctk.CTkButton(
            ip_row,
            text="Copy",
            width=40,
            height=18,
            fg_color=self.colors["border"],
            text_color=self.colors["text"],
            font=("Segoe UI", 9),
            hover_color=self._darken_color(self.colors["border"], 0.75),
            command=lambda: self._copy_to_clipboard(f"{local_ip}:{port}")
        )
        copy_local_btn.pack(side="left", padx=(0, 15))

        public_label = ctk.CTkLabel(
            ip_row,
            text="Public: ***.***.***.***",
            font=("Segoe UI", 10),
            text_color=self.colors["text_muted"]
        )
        public_label.pack(side="left", padx=(0, 5))

        copy_public_btn = ctk.CTkButton(
            ip_row,
            text="Copy",
            width=40,
            height=18,
            fg_color=self.colors["border"],
            text_color=self.colors["text"],
            font=("Segoe UI", 9),
            hover_color=self._darken_color(self.colors["border"], 0.75),
            command=lambda: self._copy_to_clipboard(f"{public_ip}:{port}")
        )
        copy_public_btn.pack(side="left", padx=(0, 10))

        eye_btn = ctk.CTkButton(
            ip_row,
            text="👁",
            width=30,
            height=20,
            fg_color="transparent",
            text_color=self.colors["text_muted"],
            font=("Segoe UI", 12),
            hover_color=self.colors["border"],
            command=lambda: self._toggle_ip_visibility(card)
        )
        eye_btn.pack(side="left", padx=5)

        card.local_label = local_label
        card.public_label = public_label
        card.eye_btn = eye_btn

        controls_frame = ctk.CTkFrame(card, fg_color="transparent")
        controls_frame.grid(row=0, column=2, rowspan=4, padx=10, pady=5, sticky="e")

        start_btn = ctk.CTkButton(
            controls_frame,
            text="Start",
            width=60,
            height=28,
            fg_color=self.colors["green"],
            text_color="#05261C",
            hover_color=self._darken_color(self.colors["green"], 0.75),
            command=lambda: self.start_server(server_path, card)
        )
        start_btn.pack(side="left", padx=2)

        stop_btn = ctk.CTkButton(
            controls_frame,
            text="Stop",
            width=60,
            height=28,
            fg_color="#e74c3c",
            text_color="white",
            hover_color=self._darken_color("#e74c3c", 0.75),
            command=lambda: self.stop_server(server_path, card)
        )
        stop_btn.pack(side="left", padx=2)

        restart_btn = ctk.CTkButton(
            controls_frame,
            text="Restart",
            width=70,
            height=28,
            fg_color=self.colors["border"],
            text_color=self.colors["text"],
            hover_color=self._darken_color(self.colors["border"], 0.75),
            command=lambda: self.restart_server(server_path, card)
        )
        restart_btn.pack(side="left", padx=2)

        settings_btn = ctk.CTkButton(
            controls_frame,
            text="⚙",
            width=30,
            height=28,
            fg_color=self.colors["border"],
            text_color=self.colors["text"],
            hover_color=self._darken_color(self.colors["border"], 0.75),
            command=lambda: self.open_settings(server_path)
        )
        settings_btn.pack(side="left", padx=2)

        card.server_path = server_path
        card.status_label = status_label
        card.info_label = info_label
        card.start_btn = start_btn
        card.stop_btn = stop_btn
        card.restart_btn = restart_btn
        card.settings_btn = settings_btn

        self.update_card_status(card, is_running)

        if is_running:
            self._start_player_poll(server_path, card, port)

    def update_card_status(self, card, running):
        if self._destroyed or not self.winfo_exists() or not card.winfo_exists():
            return

        disabled_bg = "#555555"
        disabled_text = "#888888"

        if running:
            card.start_btn.configure(
                state="disabled",
                fg_color=disabled_bg,
                text_color=disabled_text
            )
            card.stop_btn.configure(
                state="normal",
                fg_color="#e74c3c",
                text_color="white"
            )
            card.restart_btn.configure(
                state="normal",
                fg_color=self.colors["border"],
                text_color=self.colors["text"]
            )
            card.status_label.configure(text_color=self.colors["green"])
        else:
            card.start_btn.configure(
                state="normal",
                fg_color=self.colors["green"],
                text_color="#05261C"
            )
            card.stop_btn.configure(
                state="disabled",
                fg_color=disabled_bg,
                text_color=disabled_text
            )
            card.restart_btn.configure(
                state="disabled",
                fg_color=disabled_bg,
                text_color=disabled_text
            )
            card.status_label.configure(text_color=self.colors["text_muted"])

    # ============================================================
    #   PLAYER COUNT POLLING
    # ============================================================

    def _start_player_poll(self, server_path, card, port):
        if server_path in self.poll_jobs:
            self.after_cancel(self.poll_jobs[server_path])
            del self.poll_jobs[server_path]

        def poll():
            if self._destroyed or not self.winfo_exists() or not card.winfo_exists():
                if server_path in self.poll_jobs:
                    del self.poll_jobs[server_path]
                return

            proc = self.server_processes.get(server_path)
            if proc is not None and proc.poll() is not None:
                if card.winfo_exists():
                    self.update_card_status(card, running=False)
                if server_path in self.poll_jobs:
                    del self.poll_jobs[server_path]
                return

            if proc is None and not self.is_server_running(server_path):
                if card.winfo_exists():
                    self.update_card_status(card, running=False)
                if server_path in self.poll_jobs:
                    del self.poll_jobs[server_path]
                return

            try:
                server = JavaServer.lookup(f"localhost:{port}")
                status = server.status(timeout=2)
                players = status.players.online
                max_players = status.players.max
                ram = self.get_ram_for_server(server_path)
                if card.winfo_exists():
                    card.info_label.configure(text=f"{players}/{max_players} players  •  {ram} RAM")
            except Exception:
                pass

            if proc is None:
                if self.is_server_running(server_path) and self.winfo_exists() and not self._destroyed:
                    self.poll_jobs[server_path] = self.after(5000, poll)
                else:
                    if server_path in self.poll_jobs:
                        del self.poll_jobs[server_path]
            else:
                if proc.poll() is None and self.winfo_exists() and not self._destroyed:
                    self.poll_jobs[server_path] = self.after(5000, poll)
                else:
                    if server_path in self.poll_jobs:
                        del self.poll_jobs[server_path]

        self.after(1000, poll)

    def stop_player_poll(self, server_path):
        if server_path in self.poll_jobs:
            self.after_cancel(self.poll_jobs[server_path])
            del self.poll_jobs[server_path]

    # ============================================================
    #   SERVER LIFECYCLE
    # ============================================================

    def start_server(self, server_path, card):
        if self.is_server_running(server_path):
            messagebox.showinfo("Server Running", "This server is already running.")
            self.update_card_status(card, running=True)
            port = self.get_port_from_properties(server_path)
            self._start_player_poll(server_path, card, port)
            return

        jar_path = os.path.join(server_path, "server.jar")
        if not os.path.exists(jar_path):
            messagebox.showerror("Error", f"server.jar not found in {server_path}")
            return

        java_path = find_java()
        if not java_path:
            result = messagebox.askyesno(
                "Java Not Found",
                "Java is not installed or not in your system PATH.\n\n"
                "FalkMC Panel requires Java 21 or higher to run servers.\n\n"
                "Would you like to open the Java download page?"
            )
            if result:
                webbrowser.open("https://adoptium.net/temurin/releases/?version=21")
            return

        version = get_java_version(java_path)
        if version and version[0] < 21:
            result = messagebox.askyesno(
                "Java Version Too Old",
                f"Your Java version is {version[0]}.x, but this server requires Java 21 or higher.\n\n"
                f"Found at: {java_path}\n\n"
                "Would you like to open the Java 21 download page?"
            )
            if result:
                webbrowser.open("https://adoptium.net/temurin/releases/?version=21")
            return

        ram = self.get_ram_for_server(server_path)
        cmd = [java_path, f"-Xmx{ram}", f"-Xms{ram}", "-jar", jar_path, "-nogui"]

        log_path = os.path.join(server_path, "falkmc_console.log")
        log_file = open(log_path, "w", encoding="utf-8", errors="replace")

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=server_path,
                stdin=subprocess.PIPE,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.server_processes[server_path] = proc
            self.update_card_status(card, running=True)
            print(f"Started server at {server_path} with Java: {java_path}, RAM: {ram}")

            time.sleep(2)
            if proc.poll() is not None:
                try:
                    log_file.flush()
                except:
                    pass
                try:
                    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                        error_output = f.read()
                except:
                    error_output = ""
                self.update_card_status(card, running=False)
                self.stop_player_poll(server_path)
                if server_path in self.server_processes:
                    del self.server_processes[server_path]
                full_error = f"LOG:\n{error_output}"
                if "UnsupportedClassVersionError" in error_output:
                    match = re.search(r'version (\d+)\.0', error_output)
                    if match:
                        required_version_num = int(match.group(1))
                        java_versions = {65: 21, 66: 22, 67: 23, 68: 24, 69: 25}
                        required_java = java_versions.get(required_version_num, required_version_num - 44)
                        messagebox.showerror(
                            "Java Version Error",
                            f"The server requires Java {required_java} or higher.\n\n"
                            f"Your Java version: {version[0]}.{version[1]}.{version[2]}\n"
                            f"Required class file version: {required_version_num}\n\n"
                            "Install the correct Java version or choose a different server version."
                        )
                    else:
                        messagebox.showerror("Error", f"Server crashed.\n\n{full_error}")
                else:
                    messagebox.showerror("Error", f"Server crashed immediately.\n\n{full_error}")
            else:
                port = self.get_port_from_properties(server_path)
                self._start_player_poll(server_path, card, port)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
            self.update_card_status(card, running=False)
            if server_path in self.server_processes:
                del self.server_processes[server_path]

    def stop_server(self, server_path, card):
        proc = self.server_processes.get(server_path)
        if proc is None:
            if self.is_server_running(server_path):
                for p in psutil.process_iter(['pid', 'cmdline', 'cwd']):
                    try:
                        if "java" in p.info['cmdline'][0].lower() and p.info['cwd'] == server_path:
                            p.terminate()
                            p.wait(timeout=5)
                            break
                    except:
                        pass
            self.update_card_status(card, running=False)
            self.stop_player_poll(server_path)
            if server_path in self.server_processes:
                del self.server_processes[server_path]
            return

        try:
            if proc.poll() is not None:
                if server_path in self.server_processes:
                    del self.server_processes[server_path]
                self.update_card_status(card, running=False)
                self.stop_player_poll(server_path)
                return

            try:
                if proc.stdin and not proc.stdin.closed:
                    proc.stdin.write("stop\n")
                    proc.stdin.flush()
                    time.sleep(2)
            except (BrokenPipeError, OSError, ValueError):
                pass

            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)

        except (subprocess.TimeoutExpired, psutil.NoSuchProcess, psutil.AccessDenied):
            try:
                proc.kill()
            except:
                pass
        except Exception as e:
            print(f"Error stopping server: {e}")
        finally:
            if server_path in self.server_processes:
                del self.server_processes[server_path]
            self.update_card_status(card, running=False)
            self.stop_player_poll(server_path)
            print(f"Stopped server at {server_path}")

    def restart_server(self, server_path, card):
        self.stop_server(server_path, card)
        card.after(1000, lambda: self.start_server(server_path, card))

    # ============================================================
    #   SETTINGS + NEW SERVER
    # ============================================================

    def open_settings(self, server_path):
        dialog = ServerSettingsDialog(self, self.colors, server_path)
        dialog.wait_window()
        self.refresh_servers()

    def new_server_dialog(self):
        show_new_server_dialog(self)

    # ============================================================
    #   CLEANUP
    # ============================================================

    def destroy(self):
        for path, after_id in list(self.poll_jobs.items()):
            if after_id:
                self.after_cancel(after_id)
        self.poll_jobs.clear()
        self._destroyed = True
        super().destroy()
