import customtkinter as ctk
import os
import subprocess
import psutil
import time
import json
import requests
import threading
import shutil
import glob
import webbrowser
import re
from tkinter import messagebox
from mcstatus import JavaServer

from views.settings_dialog import ServerSettingsDialog

class ServersView(ctk.CTkFrame):
    def __init__(self, master, colors, servers_base, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors
        self.servers_base = servers_base
        self.configure(fg_color="transparent")

        if not os.path.exists(self.servers_base):
            os.makedirs(self.servers_base, exist_ok=True)

        self.server_processes = {}      # subprocess.Popen objects
        self.poll_jobs = {}             # after_id for each server
        self.scan_thread = None
        self.scanning = False
        self._destroyed = False

        self.build_ui()
        self.refresh_servers()

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
            hover_color=self.colors["border"],
            command=self.new_server_dialog
        )
        new_btn.pack(side="right", padx=5)

        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.scrollable_frame._scrollbar.configure(width=6)

    def refresh_servers(self):
        if self._destroyed or not self.winfo_exists():
            return
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        # Cancel all polling jobs
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

        status_color = self.colors["green"] if is_running else self.colors["text_muted"]
        status_label = ctk.CTkLabel(
            card,
            text="●",
            font=("Segoe UI", 18),
            text_color=status_color
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

        controls_frame = ctk.CTkFrame(card, fg_color="transparent")
        controls_frame.grid(row=0, column=2, rowspan=3, padx=10, pady=5, sticky="e")

        start_btn = ctk.CTkButton(
            controls_frame,
            text="Start",
            width=60,
            height=28,
            fg_color=self.colors["green"],
            text_color="#05261C",
            state="normal" if not is_running else "disabled",
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
            state="normal" if is_running else "disabled",
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
            state="normal" if is_running else "disabled",
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
            command=lambda: self.open_settings(server_path)
        )
        settings_btn.pack(side="left", padx=2)

        card.server_path = server_path
        card.port = port
        card.status_label = status_label
        card.info_label = info_label
        card.start_btn = start_btn
        card.stop_btn = stop_btn
        card.restart_btn = restart_btn

        if is_running:
            self._start_player_poll(server_path, card, port)

    # ----- Player count polling (with widget existence check) -----
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

            # Reschedule next poll
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

    # ----- Server running check (fast) -----
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

    # ----- Java detection (unchanged) -----
    def find_java(self):
        candidates = []
        path_java = shutil.which("java")
        if path_java:
            candidates.append(path_java)

        common_patterns = [
            "C:/Program Files/Java/jdk-*/bin/java.exe",
            "C:/Program Files/Java/jre-*/bin/java.exe",
            "C:/Program Files/Java/jdk*/bin/java.exe",
            "C:/Program Files/Java/jre*/bin/java.exe",
            "C:/Program Files (x86)/Java/jdk*/bin/java.exe",
            "C:/Program Files (x86)/Java/jre*/bin/java.exe",
            "C:/Program Files/Eclipse Adoptium/jdk-*/bin/java.exe",
            "C:/Program Files/Temurin/jdk-*/bin/java.exe",
            "C:/Program Files/AdoptOpenJDK/jdk-*/bin/java.exe",
            "C:/Program Files/OpenJDK/openjdk-*/bin/java.exe",
            "C:/Program Files/Amazon Corretto/jdk*/bin/java.exe",
            "C:/Program Files/ojdkbuild/java-*/bin/java.exe",
        ]
        for pattern in common_patterns:
            matches = glob.glob(pattern)
            candidates.extend(matches)

        seen = set()
        unique_candidates = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                unique_candidates.append(c)

        best_version = None
        best_path = None
        for java_path in unique_candidates:
            version = self.get_java_version(java_path)
            if version:
                major = version[0]
                if best_version is None or major > best_version[0]:
                    best_version = version
                    best_path = java_path
                elif major == best_version[0] and (version[1] > best_version[1] or (version[1] == best_version[1] and version[2] > best_version[2])):
                    best_version = version
                    best_path = java_path

        return best_path

    def get_java_version(self, java_path):
        try:
            result = subprocess.run([java_path, "-version"], capture_output=True, text=True)
            output = result.stderr.strip()
            match = re.search(r'version "(\d+)\.(\d+)\.(\d+)"', output)
            if match:
                return tuple(map(int, match.groups()))
            match = re.search(r'version "1\.(\d+)\.(\d+)_(\d+)"', output)
            if match:
                return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            match = re.search(r'(\d+)\.(\d+)\.(\d+)', output)
            if match:
                return tuple(map(int, match.groups()))
            return None
        except Exception:
            return None

    # ----- Server settings helpers -----
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

    # ----- Start / Stop / Restart -----
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

        java_path = self.find_java()
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

        version = self.get_java_version(java_path)
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
        print("Starting:", " ".join(cmd))

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=server_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.server_processes[server_path] = proc
            self.update_card_status(card, running=True)
            print(f"Started server at {server_path} with Java: {java_path}, RAM: {ram}")

            time.sleep(2)
            if proc.poll() is not None:
                error_output = proc.stderr.read() if proc.stderr else ""
                stdout_output = proc.stdout.read() if proc.stdout else ""
                self.update_card_status(card, running=False)
                self.stop_player_poll(server_path)
                if server_path in self.server_processes:
                    del self.server_processes[server_path]
                full_error = f"STDERR:\n{error_output}\n\nSTDOUT:\n{stdout_output}"
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

    def update_card_status(self, card, running):
        if self._destroyed or not self.winfo_exists() or not card.winfo_exists():
            return
        if running:
            card.status_label.configure(text_color=self.colors["green"])
            card.start_btn.configure(state="disabled")
            card.stop_btn.configure(state="normal")
            card.restart_btn.configure(state="normal")
        else:
            card.status_label.configure(text_color=self.colors["text_muted"])
            card.start_btn.configure(state="normal")
            card.stop_btn.configure(state="disabled")
            card.restart_btn.configure(state="disabled")

    def open_settings(self, server_path):
        dialog = ServerSettingsDialog(self, self.colors, server_path)
        dialog.wait_window()
        self.refresh_servers()

    # ----- New Server Dialog (button now visible) -----
    def new_server_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Server")
        dialog.geometry("420x520")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 210
        y = (dialog.winfo_screenheight() // 2) - 260
        dialog.geometry(f"+{x}+{y}")

        # Server Name
        ctk.CTkLabel(dialog, text="Server Name:", font=("Segoe UI", 14)).pack(pady=(20, 5), padx=20, anchor="w")
        name_entry = ctk.CTkEntry(dialog, width=340)
        name_entry.pack(padx=20, pady=5)
        name_entry.insert(0, "My Server")

        # Server Type
        ctk.CTkLabel(dialog, text="Server Type:", font=("Segoe UI", 14)).pack(pady=(10, 5), padx=20, anchor="w")
        type_var = ctk.StringVar(value="Vanilla")
        type_menu = ctk.CTkOptionMenu(dialog, values=["Vanilla", "Paper"], variable=type_var, width=340)
        type_menu.pack(padx=20, pady=5)

        # Version
        ctk.CTkLabel(dialog, text="Version:", font=("Segoe UI", 14)).pack(pady=(10, 5), padx=20, anchor="w")
        version_var = ctk.StringVar()
        version_menu = ctk.CTkOptionMenu(dialog, values=["Loading..."], variable=version_var, width=340)
        version_menu.pack(padx=20, pady=5)

        # RAM Allocation
        ctk.CTkLabel(dialog, text="RAM Allocation:", font=("Segoe UI", 14)).pack(pady=(10, 5), padx=20, anchor="w")
        ram_var = ctk.StringVar(value="2G")
        ram_menu = ctk.CTkOptionMenu(
            dialog,
            values=["1G", "2G", "4G", "6G", "8G", "12G", "16G"],
            variable=ram_var,
            width=340
        )
        ram_menu.pack(padx=20, pady=5)

        # Max Players
        ctk.CTkLabel(dialog, text="Max Players:", font=("Segoe UI", 14)).pack(pady=(10, 5), padx=20, anchor="w")
        players_entry = ctk.CTkEntry(dialog, width=340)
        players_entry.pack(padx=20, pady=5)
        players_entry.insert(0, "20")

        # Create button
        create_btn = ctk.CTkButton(
            dialog,
            text="Create Server",
            width=160,
            height=36,
            fg_color=self.colors["green"],
            text_color="#05261C",
            font=("Segoe UI", 14, "bold"),
            state="disabled"
        )
        create_btn.pack(pady=(20, 30))

        # --- Fetch versions in background ---
        def fetch_versions():
            type_val = type_var.get()
            versions = []
            if type_val == "Vanilla":
                try:
                    resp = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest.json")
                    resp.raise_for_status()
                    data = resp.json()
                    versions = [v["id"] for v in data["versions"] if v["type"] == "release"]
                    versions.sort(key=lambda s: [int(x) for x in s.split('.')], reverse=True)
                except:
                    versions = ["1.21.1", "1.20.4", "1.19.4", "1.18.2"]
            else:
                try:
                    resp = requests.get("https://api.papermc.io/v2/projects/paper")
                    resp.raise_for_status()
                    data = resp.json()
                    versions = data["versions"]
                    versions.sort(key=lambda s: [int(x) for x in s.split('.')], reverse=True)
                except:
                    versions = ["1.21.1", "1.20.4", "1.19.4", "1.18.2"]

            dialog.after(0, lambda: update_version_menu(versions))

        def update_version_menu(versions):
            if versions:
                version_menu.configure(values=versions)
                version_var.set(versions[0])
                create_btn.configure(state="normal")
            else:
                version_menu.configure(values=["No versions found"])
                version_var.set("")
                create_btn.configure(state="disabled")

        threading.Thread(target=fetch_versions, daemon=True).start()

        # --- Create server ---
        def create_server():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a server name.")
                return

            server_type = type_var.get()
            version = version_var.get()
            if not version or version == "No versions found":
                messagebox.showerror("Error", "Please select a valid version.")
                return

            ram = ram_var.get()
            if not ram:
                ram = "2G"

            try:
                max_players = int(players_entry.get().strip())
                if max_players < 1:
                    max_players = 1
            except ValueError:
                max_players = 20

            # Close the dialog
            dialog.destroy()

            # Create a progress window
            progress_win = ctk.CTkToplevel(self)
            progress_win.title("Creating Server")
            progress_win.geometry("400x150")
            progress_win.resizable(False, False)
            progress_win.transient(self)
            progress_win.grab_set()

            x2 = (progress_win.winfo_screenwidth() // 2) - 200
            y2 = (progress_win.winfo_screenheight() // 2) - 75
            progress_win.geometry(f"+{x2}+{y2}")

            progress_label = ctk.CTkLabel(
                progress_win,
                text="Initializing...",
                font=("Segoe UI", 14),
                text_color=self.colors["text"]
            )
            progress_label.pack(pady=(20, 10))

            progress_bar = ctk.CTkProgressBar(progress_win, width=340, height=12)
            progress_bar.pack(pady=10)
            progress_bar.set(0)

            # Run the creation in a thread
            def create_thread():
                try:
                    success, server_path = self._create_server(
                        name, server_type, version,
                        ram, max_players,
                        progress_bar, progress_label, progress_win
                    )
                    if success:
                        # Destroy progress window and refresh list
                        progress_win.after(0, progress_win.destroy)
                        # Schedule refresh after a short delay to let the window close
                        self.after(100, self.refresh_servers)
                        messagebox.showinfo("Success", f"Server '{name}' created successfully!")
                except Exception as e:
                    progress_win.after(0, progress_win.destroy)
                    messagebox.showerror("Error", f"Failed to create server: {e}")

            threading.Thread(target=create_thread, daemon=True).start()

        create_btn.configure(command=create_server)

    def _create_server(self, name, server_type, version, ram_allocation, max_players, progress_bar, progress_label, progress_win):
        server_folder = os.path.join(self.servers_base, name)
        if os.path.exists(server_folder):
            progress_win.after(0, progress_win.destroy)
            messagebox.showerror("Error", f"A server named '{name}' already exists.")
            return False, None

        jar_url = None
        if server_type == "Vanilla":
            progress_label.configure(text="Fetching manifest...")
            progress_bar.set(0.1)
            manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
            resp = requests.get(manifest_url)
            resp.raise_for_status()
            data = resp.json()
            version_info = None
            for v in data["versions"]:
                if v["id"] == version:
                    version_info = v
                    break
            if not version_info:
                progress_win.after(0, progress_win.destroy)
                messagebox.showerror("Error", f"Version {version} not found.")
                return False, None
            progress_label.configure(text="Fetching version details...")
            progress_bar.set(0.2)
            version_detail_url = version_info["url"]
            resp = requests.get(version_detail_url)
            resp.raise_for_status()
            detail = resp.json()
            jar_url = detail["downloads"]["server"]["url"]

        elif server_type == "Paper":
            progress_label.configure(text="Fetching Paper build...")
            progress_bar.set(0.1)
            api_url = f"https://api.papermc.io/v2/projects/paper/versions/{version}/builds/latest"
            resp = requests.get(api_url)
            if resp.status_code != 200:
                progress_win.after(0, progress_win.destroy)
                messagebox.showerror("Error", f"Paper version {version} not found.")
                return False, None
            data = resp.json()
            build = data["build"]
            file_name = data["downloads"]["application"]["name"]
            jar_url = f"https://api.papermc.io/v2/projects/paper/versions/{version}/builds/{build}/downloads/{file_name}"

        if not jar_url:
            progress_win.after(0, progress_win.destroy)
            messagebox.showerror("Error", "Could not determine download URL.")
            return False, None

        os.makedirs(server_folder, exist_ok=True)

        progress_label.configure(text=f"Downloading {server_type} server...")
        progress_bar.set(0.3)
        jar_path = os.path.join(server_folder, "server.jar")
        response = requests.get(jar_url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024
        downloaded = 0
        with open(jar_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        progress_val = 0.3 + 0.6 * (downloaded / total_size)
                        progress_bar.set(progress_val)
                        progress_label.configure(
                            text=f"Downloading... {int(100 * downloaded / total_size)}%"
                        )
        progress_bar.set(0.9)

        # Write server.properties
        props_path = os.path.join(server_folder, "server.properties")
        with open(props_path, "w") as f:
            f.write("server-port=25565\n")
            f.write("motd=A Minecraft Server\n")
            f.write("gamemode=survival\n")
            f.write("difficulty=normal\n")
            f.write(f"max-players={max_players}\n")
            f.write("level-name=world\n")
            f.write("online-mode=true\n")
            f.write("enable-query=true\n")

        # eula.txt – auto-accept
        eula_path = os.path.join(server_folder, "eula.txt")
        with open(eula_path, "w") as f:
            f.write("eula=true\n")

        # falkmc.json
        falkmc_path = os.path.join(server_folder, "falkmc.json")
        with open(falkmc_path, "w") as f:
            json.dump({
                "display_name": name,
                "ram_allocation": ram_allocation,
                "java_path": "",
                "icon_path": ""
            }, f, indent=2)

        progress_label.configure(text="Done!")
        progress_bar.set(1.0)

        # Small delay so the user sees the "Done!" message
        time.sleep(0.5)

        return True, server_folder

    # ----- Cleanup when view is destroyed (only cancels after jobs) -----
    def destroy(self):
        # Cancel all pending polling jobs
        for path, after_id in list(self.poll_jobs.items()):
            if after_id:
                self.after_cancel(after_id)
        self.poll_jobs.clear()
        self._destroyed = True
        super().destroy()
