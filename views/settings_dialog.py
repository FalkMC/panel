import customtkinter as ctk
import os
import json
from tkinter import messagebox

from resource import resource_path


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
        self.iconbitmap(resource_path("images/logo.ico"))
        self.configure(fg_color=self.colors["bg"])

        # Load current settings
        self.props = self.load_properties()
        self.falkmc = self.load_falkmc()

        self.build_ui()
        self.fill_fields()

    # Auto colour darken
    def _darken_color(self, hex_color, factor=0.75):
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

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

    def _make_entry(self, parent, width=180):
        return ctk.CTkEntry(
            parent,
            width=width,
            fg_color=self.colors["element"],
            text_color=self.colors["text"],
            border_color=self.colors["border"]
        )

    def _make_optionmenu(self, parent, values, width=180):
        return ctk.CTkOptionMenu(
            parent,
            values=values,
            width=width,
            fg_color=self.colors["element"],
            button_color=self.colors["border"],
            button_hover_color=self._darken_color(self.colors["border"], 0.75),
            text_color=self.colors["text"],
            dropdown_fg_color=self.colors["element"],
            dropdown_text_color=self.colors["text"],
            dropdown_hover_color=self.colors["border"]
        )

    def _make_checkbox(self, parent, width=20):
        return ctk.CTkCheckBox(
            parent,
            text="",
            width=width,
            fg_color=self.colors["green"],
            hover_color=self._darken_color(self.colors["green"], 0.75),
            border_color=self.colors["border"],
            checkmark_color="#05261C"
        )

    def _make_label(self, parent, text, bold=False):
        return ctk.CTkLabel(
            parent,
            text=text,
            font=("Segoe UI", 13, "bold" if bold else "normal"),
            text_color=self.colors["text"]
        )

    def _make_section_label(self, parent, text):
        return ctk.CTkLabel(
            parent,
            text=text,
            font=("Segoe UI", 16, "bold"),
            text_color=self.colors["text"]
        )

    def build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Server Properties Section
        self._make_section_label(scroll, "Server Properties").pack(anchor="w", pady=(0, 10))

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", pady=5)
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        row = 0

        def add_prop(label, key):
            nonlocal row
            self._make_label(grid, label).grid(row=row, column=0, sticky="w", pady=4)
            entry = self._make_entry(grid)
            entry.grid(row=row, column=1, sticky="w", pady=4, padx=(0, 10))
            setattr(self, f"entry_{key.replace('-', '_')}", entry)
            row += 1

        add_prop("Server Port", "server-port")
        add_prop("MOTD", "motd")
        add_prop("Max Players", "max-players")
        add_prop("Level Name", "level-name")

        self._make_label(grid, "Gamemode").grid(row=row, column=0, sticky="w", pady=4)
        self.gamemode_menu = self._make_optionmenu(
            grid, ["survival", "creative", "adventure", "spectator"]
        )
        self.gamemode_menu.grid(row=row, column=1, sticky="w", pady=4, padx=(0, 10))
        row += 1

        self._make_label(grid, "Difficulty").grid(row=row, column=0, sticky="w", pady=4)
        self.difficulty_menu = self._make_optionmenu(
            grid, ["peaceful", "easy", "normal", "hard"]
        )
        self.difficulty_menu.grid(row=row, column=1, sticky="w", pady=4, padx=(0, 10))
        row += 1

        self._make_label(grid, "Online Mode").grid(row=row, column=0, sticky="w", pady=4)
        self.online_mode_check = self._make_checkbox(grid)
        self.online_mode_check.grid(row=row, column=1, sticky="w", pady=4, padx=(0, 10))
        row += 1

        self._make_label(grid, "White-List").grid(row=row, column=0, sticky="w", pady=4)
        self.white_list_check = self._make_checkbox(grid)
        self.white_list_check.grid(row=row, column=1, sticky="w", pady=4, padx=(0, 10))
        row += 1

        # FalkMC Settings Section
        self._make_section_label(scroll, "FalkMC Settings").pack(anchor="w", pady=(20, 10))

        falk_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        falk_grid.pack(fill="x", pady=5)
        falk_grid.grid_columnconfigure(0, weight=1)
        falk_grid.grid_columnconfigure(1, weight=1)

        row2 = 0

        self._make_label(falk_grid, "Display Name").grid(row=row2, column=0, sticky="w", pady=4)
        self.display_name_entry = self._make_entry(falk_grid)
        self.display_name_entry.grid(row=row2, column=1, sticky="w", pady=4, padx=(0, 10))
        row2 += 1

        self._make_label(falk_grid, "RAM Allocation (e.g. 2G, 4G)").grid(row=row2, column=0, sticky="w", pady=4)
        self.ram_entry = self._make_entry(falk_grid)
        self.ram_entry.grid(row=row2, column=1, sticky="w", pady=4, padx=(0, 10))
        row2 += 1

        self._make_label(falk_grid, "Java Path (optional)").grid(row=row2, column=0, sticky="w", pady=4)
        self.java_path_entry = self._make_entry(falk_grid)
        self.java_path_entry.grid(row=row2, column=1, sticky="w", pady=4, padx=(0, 10))
        row2 += 1

        self._make_label(falk_grid, "Icon Path (optional)").grid(row=row2, column=0, sticky="w", pady=4)
        self.icon_path_entry = self._make_entry(falk_grid)
        self.icon_path_entry.grid(row=row2, column=1, sticky="w", pady=4, padx=(0, 10))
        row2 += 1

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=15)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save",
            width=100,
            height=32,
            fg_color=self.colors["green"],
            text_color="#05261C",
            hover_color=self._darken_color(self.colors["green"], 0.75),
            command=self.save_settings
        )
        save_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            height=32,
            fg_color=self.colors["border"],
            text_color=self.colors["text"],
            hover_color=self._darken_color(self.colors["border"], 0.75),
            command=self.destroy
        )
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
