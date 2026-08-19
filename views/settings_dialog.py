import customtkinter as ctk
import os
import json
from tkinter import messagebox

class ServerSettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, colors, server_path, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors
        self.server_path = server_path
        self.title(f"Settings – {os.path.basename(server_path)}")
        self.geometry("500x550")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # Load current settings
        self.props = self.load_properties()
        self.falkmc = self.load_falkmc()

        self.build_ui()
        self.fill_fields()

    def load_properties(self):
        props = {}
        props_path = os.path.join(self.server_path, "server.properties")
        if os.path.exists(props_path):
            with open(props_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        props[key] = value
        # Set defaults if missing
        props.setdefault("server-port", "25565")
        props.setdefault("motd", "A Minecraft Server")
        props.setdefault("max-players", "20")
        props.setdefault("gamemode", "survival")
        props.setdefault("difficulty", "normal")
        props.setdefault("level-name", "world")
        props.setdefault("online-mode", "true")
        props.setdefault("white-list", "false")
        return props

    def load_falkmc(self):
        falkmc_path = os.path.join(self.server_path, "falkmc.json")
        if os.path.exists(falkmc_path):
            with open(falkmc_path, "r") as f:
                return json.load(f)
        return {
            "display_name": os.path.basename(self.server_path),
            "ram_allocation": "2G",
            "java_path": "",
            "icon_path": ""
        }

    def build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Server properties section
        ctk.CTkLabel(scroll, text="Server Properties", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 10))

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", pady=5)
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        row = 0

        def add_prop(label, key):
            nonlocal row
            ctk.CTkLabel(grid, text=label, font=("Segoe UI", 13)).grid(row=row, column=0, sticky="w", pady=4)
            entry = ctk.CTkEntry(grid, width=180)
            entry.grid(row=row, column=1, sticky="w", pady=4, padx=(0, 10))
            setattr(self, f"entry_{key.replace('-','_')}", entry)
            row += 1

        add_prop("Server Port", "server-port")
        add_prop("MOTD", "motd")
        add_prop("Max Players", "max-players")
        add_prop("Level Name", "level-name")

        ctk.CTkLabel(grid, text="Gamemode", font=("Segoe UI", 13)).grid(row=row, column=0, sticky="w", pady=4)
        self.gamemode_menu = ctk.CTkOptionMenu(grid, values=["survival", "creative", "adventure", "spectator"], width=180)
        self.gamemode_menu.grid(row=row, column=1, sticky="w", pady=4, padx=(0, 10))
        row += 1

        ctk.CTkLabel(grid, text="Difficulty", font=("Segoe UI", 13)).grid(row=row, column=0, sticky="w", pady=4)
        self.difficulty_menu = ctk.CTkOptionMenu(grid, values=["peaceful", "easy", "normal", "hard"], width=180)
        self.difficulty_menu.grid(row=row, column=1, sticky="w", pady=4, padx=(0, 10))
        row += 1

        ctk.CTkLabel(grid, text="Online Mode", font=("Segoe UI", 13)).grid(row=row, column=0, sticky="w", pady=4)
        self.online_mode_check = ctk.CTkCheckBox(grid, text="", width=20)
        self.online_mode_check.grid(row=row, column=1, sticky="w", pady=4, padx=(0, 10))
        row += 1

        ctk.CTkLabel(grid, text="White-List", font=("Segoe UI", 13)).grid(row=row, column=0, sticky="w", pady=4)
        self.white_list_check = ctk.CTkCheckBox(grid, text="", width=20)
        self.white_list_check.grid(row=row, column=1, sticky="w", pady=4, padx=(0, 10))
        row += 1

        # FalkMC settings section
        ctk.CTkLabel(scroll, text="FalkMC Settings", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(20, 10))

        falk_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        falk_grid.pack(fill="x", pady=5)
        falk_grid.grid_columnconfigure(0, weight=1)
        falk_grid.grid_columnconfigure(1, weight=1)

        row2 = 0

        ctk.CTkLabel(falk_grid, text="Display Name", font=("Segoe UI", 13)).grid(row=row2, column=0, sticky="w", pady=4)
        self.display_name_entry = ctk.CTkEntry(falk_grid, width=180)
        self.display_name_entry.grid(row=row2, column=1, sticky="w", pady=4, padx=(0, 10))
        row2 += 1

        ctk.CTkLabel(falk_grid, text="RAM Allocation (e.g. 2G, 4G)", font=("Segoe UI", 13)).grid(row=row2, column=0, sticky="w", pady=4)
        self.ram_entry = ctk.CTkEntry(falk_grid, width=180)
        self.ram_entry.grid(row=row2, column=1, sticky="w", pady=4, padx=(0, 10))
        row2 += 1

        ctk.CTkLabel(falk_grid, text="Java Path (optional)", font=("Segoe UI", 13)).grid(row=row2, column=0, sticky="w", pady=4)
        self.java_path_entry = ctk.CTkEntry(falk_grid, width=180)
        self.java_path_entry.grid(row=row2, column=1, sticky="w", pady=4, padx=(0, 10))
        row2 += 1

        ctk.CTkLabel(falk_grid, text="Icon Path (optional)", font=("Segoe UI", 13)).grid(row=row2, column=0, sticky="w", pady=4)
        self.icon_path_entry = ctk.CTkEntry(falk_grid, width=180)
        self.icon_path_entry.grid(row=row2, column=1, sticky="w", pady=4, padx=(0, 10))
        row2 += 1

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=15)

        save_btn = ctk.CTkButton(btn_frame, text="Save", width=100, height=32,
                                 fg_color=self.colors["green"], text_color="#05261C",
                                 command=self.save_settings)
        save_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", width=100, height=32,
                                   fg_color="#e74c3c", text_color="white",
                                   command=self.destroy)
        cancel_btn.pack(side="left", padx=10)

    def fill_fields(self):
        # Properties
        self.entry_server_port.insert(0, self.props.get("server-port", "25565"))
        self.entry_motd.insert(0, self.props.get("motd", "A Minecraft Server"))
        self.entry_max_players.insert(0, self.props.get("max-players", "20"))
        self.entry_level_name.insert(0, self.props.get("level-name", "world"))

        self.gamemode_menu.set(self.props.get("gamemode", "survival"))
        self.difficulty_menu.set(self.props.get("difficulty", "normal"))

        self.online_mode_check.select() if self.props.get("online-mode", "true").lower() == "true" else self.online_mode_check.deselect()
        self.white_list_check.select() if self.props.get("white-list", "false").lower() == "true" else self.white_list_check.deselect()

        # FalkMC
        self.display_name_entry.insert(0, self.falkmc.get("display_name", os.path.basename(self.server_path)))
        self.ram_entry.insert(0, self.falkmc.get("ram_allocation", "2G"))
        self.java_path_entry.insert(0, self.falkmc.get("java_path", ""))
        self.icon_path_entry.insert(0, self.falkmc.get("icon_path", ""))

    def save_settings(self):
        # Update properties
        self.props["server-port"] = self.entry_server_port.get().strip()
        self.props["motd"] = self.entry_motd.get().strip()
        self.props["max-players"] = self.entry_max_players.get().strip()
        self.props["level-name"] = self.entry_level_name.get().strip()
        self.props["gamemode"] = self.gamemode_menu.get()
        self.props["difficulty"] = self.difficulty_menu.get()
        self.props["online-mode"] = "true" if self.online_mode_check.get() else "false"
        self.props["white-list"] = "true" if self.white_list_check.get() else "false"

        # Write server.properties
        props_path = os.path.join(self.server_path, "server.properties")
        with open(props_path, "w") as f:
            for key, value in self.props.items():
                f.write(f"{key}={value}\n")

        # Update FalkMC
        self.falkmc["display_name"] = self.display_name_entry.get().strip()
        self.falkmc["ram_allocation"] = self.ram_entry.get().strip()
        self.falkmc["java_path"] = self.java_path_entry.get().strip()
        self.falkmc["icon_path"] = self.icon_path_entry.get().strip()

        # Write falkmc.json
        falkmc_path = os.path.join(self.server_path, "falkmc.json")
        with open(falkmc_path, "w") as f:
            json.dump(self.falkmc, f, indent=2)

        messagebox.showinfo("Success", "Settings saved successfully.")
        self.destroy()
