import customtkinter as ctk
import os
import json
import requests
import threading
import time
from tkinter import messagebox

from resource import resource_path


def show_new_server_dialog(view):
    colors = view.colors
    servers_base = view.servers_base
    darken = view._darken_color

    dialog = ctk.CTkToplevel(view)
    dialog.title("New Server")
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

    # Server Name
    ctk.CTkLabel(
        dialog, text="Server Name:",
        font=("Segoe UI", 14),
        text_color=colors["text"]
    ).pack(pady=(20, 5), padx=20, anchor="w")

    name_entry = ctk.CTkEntry(
        dialog, width=340,
        fg_color=colors["element"],
        text_color=colors["text"],
        border_color=colors["border"]
    )
    name_entry.pack(padx=20, pady=5)
    name_entry.insert(0, "My Server")

    # Server Type
    ctk.CTkLabel(
        dialog, text="Server Type:",
        font=("Segoe UI", 14),
        text_color=colors["text"]
    ).pack(pady=(10, 5), padx=20, anchor="w")

    type_var = ctk.StringVar(value="Vanilla")
    type_menu = ctk.CTkOptionMenu(
        dialog,
        values=["Vanilla", "Paper"],
        variable=type_var,
        width=340,
        fg_color=colors["element"],
        button_color=colors["border"],
        button_hover_color=darken(colors["border"], 0.75),
        text_color=colors["text"],
        dropdown_fg_color=colors["element"],
        dropdown_text_color=colors["text"],
        dropdown_hover_color=colors["border"]
    )
    type_menu.pack(padx=20, pady=5)

    # Version
    ctk.CTkLabel(
        dialog, text="Version:",
        font=("Segoe UI", 14),
        text_color=colors["text"]
    ).pack(pady=(10, 5), padx=20, anchor="w")

    version_var = ctk.StringVar()
    version_menu = ctk.CTkOptionMenu(
        dialog,
        values=["Loading..."],
        variable=version_var,
        width=340,
        fg_color=colors["element"],
        button_color=colors["border"],
        button_hover_color=darken(colors["border"], 0.75),
        text_color=colors["text"],
        dropdown_fg_color=colors["element"],
        dropdown_text_color=colors["text"],
        dropdown_hover_color=colors["border"]
    )
    version_menu.pack(padx=20, pady=5)

    # RAM Allocation
    ctk.CTkLabel(
        dialog, text="RAM Allocation:",
        font=("Segoe UI", 14),
        text_color=colors["text"]
    ).pack(pady=(10, 5), padx=20, anchor="w")

    ram_var = ctk.StringVar(value="2G")
    ram_menu = ctk.CTkOptionMenu(
        dialog,
        values=["1G", "2G", "4G", "6G", "8G", "12G", "16G"],
        variable=ram_var,
        width=340,
        fg_color=colors["element"],
        button_color=colors["border"],
        button_hover_color=darken(colors["border"], 0.75),
        text_color=colors["text"],
        dropdown_fg_color=colors["element"],
        dropdown_text_color=colors["text"],
        dropdown_hover_color=colors["border"]
    )
    ram_menu.pack(padx=20, pady=5)

    # Max Players
    ctk.CTkLabel(
        dialog, text="Max Players:",
        font=("Segoe UI", 14),
        text_color=colors["text"]
    ).pack(pady=(10, 5), padx=20, anchor="w")

    players_entry = ctk.CTkEntry(
        dialog, width=340,
        fg_color=colors["element"],
        text_color=colors["text"],
        border_color=colors["border"]
    )
    players_entry.pack(padx=20, pady=5)
    players_entry.insert(0, "20")

    # Create button
    create_btn = ctk.CTkButton(
        dialog,
        text="Create Server",
        width=160,
        height=36,
        fg_color=colors["green"],
        text_color="#05261C",
        font=("Segoe UI", 14),
        hover_color=darken(colors["green"], 0.75),
        state="disabled"
    )
    create_btn.pack(pady=(20, 30))

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
        ram = ram_var.get() or "2G"
        try:
            max_players = int(players_entry.get().strip())
            if max_players < 1:
                max_players = 1
        except ValueError:
            max_players = 20

        dialog.destroy()

        progress_win = ctk.CTkToplevel(view)
        progress_win.title("Creating Server")
        progress_win.geometry("400x150")
        progress_win.resizable(False, False)
        progress_win.transient(view)
        progress_win.grab_set()
        progress_win.configure(fg_color=colors["bg"])
        progress_win.iconbitmap(resource_path("images/logo.ico"))

        x2 = (progress_win.winfo_screenwidth() // 2) - 200
        y2 = (progress_win.winfo_screenheight() // 2) - 75
        progress_win.geometry(f"+{x2}+{y2}")

        progress_label = ctk.CTkLabel(
            progress_win,
            text="Initializing...",
            font=("Segoe UI", 14),
            text_color=colors["text"]
        )
        progress_label.pack(pady=(20, 10))

        progress_bar = ctk.CTkProgressBar(
            progress_win,
            width=340,
            height=12,
            fg_color=colors["element"],
            progress_color=colors["green"]
        )
        progress_bar.pack(pady=10)
        progress_bar.set(0)

        def create_thread():
            try:
                success, server_path = _create_server(
                    servers_base, name, server_type, version,
                    ram, max_players,
                    progress_bar, progress_label, progress_win
                )
                if success:
                    progress_win.after(0, progress_win.destroy)
                    view.after(100, view.refresh_servers)
                    messagebox.showinfo("Success", f"Server '{name}' created successfully!")
            except Exception as e:
                progress_win.after(0, progress_win.destroy)
                messagebox.showerror("Error", f"Failed to create server: {e}")

        threading.Thread(target=create_thread, daemon=True).start()

    create_btn.configure(command=create_server)


def _create_server(servers_base, name, server_type, version, ram_allocation, max_players,
                   progress_bar, progress_label, progress_win):
    """Download the server jar and set up the folder. Runs in a background thread."""
    server_folder = os.path.join(servers_base, name)
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

    # server.properties
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

    # eula.txt
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
    time.sleep(0.5)
    return True, server_folder
