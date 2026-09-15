import os
import sys
import psutil

import customtkinter as ctk
from PIL import Image

# Modules
from settings import load_settings, save_settings
from theme import THEME_COLORS
from resource import resource_path

# Import views
from views.home import HomeView
from views.servers import ServersView

# Folder in docs dir
DOCUMENTS_DIR = os.path.join(os.path.expanduser("~"), "Documents")
FALKMC_DIR = os.path.join(DOCUMENTS_DIR, "FalkMC")
os.makedirs(FALKMC_DIR, exist_ok=True)

# Get logo path
if getattr(sys, 'frozen', False):
    icon_path = os.path.join(sys._MEIPASS, "images", "logo.ico")
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "images", "logo.ico")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Load settings and apply them
        self.settings = load_settings()
        theme_name = self.settings.get("theme", "dark")
        self.iconbitmap(icon_path)
        self.colors = THEME_COLORS[theme_name]

        # Servers folder lives inside Documents\FalkMC\servers
        self.servers_base = os.path.join(FALKMC_DIR, "servers")

        ctk.set_appearance_mode(theme_name)
        ctk.set_default_color_theme("green")

        self.configure(fg_color=self.colors["bg"])
        self.geometry(f"{self.settings['window_width']}x{self.settings['window_height']}")
        self.title("FalkMC")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Grid layout
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.current_view_name = "home"

        self.create_header()
        self.create_navbar()
        self.create_content_area()

        # Load def view (Home)
        self.show_view(self.current_view_name)

    def create_header(self):
        # Logo pill
        name_pill = ctk.CTkFrame(
            self,
            height=50,
            width=190,
            corner_radius=10,
            fg_color=self.colors["element"],
            border_color=self.colors["border"],
            border_width=1
        )
        name_pill.grid(column=0, row=0, padx=(20, 0), pady=(20, 0), sticky="nw")
        name_pill.pack_propagate(False)

        # Logo image
        logo_path = resource_path("images/FalkMC_Logo_DarkMode.png")
        falkmc_img = ctk.CTkImage(
            light_image=Image.open(logo_path),
            dark_image=Image.open(logo_path),
            size=(40, 40)
        )

        logo_label = ctk.CTkLabel(name_pill, image=falkmc_img, text="")
        logo_label.pack(side="left", padx=(5, 0), pady=10)

        text_label = ctk.CTkLabel(
            name_pill,
            text="FalkMC",
            font=("Segoe UI", 21, "bold"),
            text_color=self.colors["text"]
        )
        text_label.pack(side="left", padx=(0, 5), pady=10)

        beta_label = ctk.CTkLabel(
            name_pill,
            text="BETA",
            font=("Segoe UI Black", 14),
            text_color=self.colors["element"],
            fg_color=self.colors["green"],
            corner_radius=7
        )
        beta_label.pack(side="right", padx=(5, 10), pady=10)

        # Header label
        self.header_label = ctk.CTkLabel(
            self,
            text="Home",
            font=("Segoe UI", 21),
            text_color=self.colors["text_muted"]
        )
        self.header_label.grid(column=1, row=0, padx=0, pady=0, sticky="ns")

        # Theme toggle btn
        self.theme_btn = ctk.CTkButton(
            self,
            height=50,
            width=50,
            fg_color=self.colors["element"],
            hover_color=self.colors["border"],
            text="◐",
            font=("Segoe UI", 24),
            corner_radius=12,
            border_color=self.colors["border"],
            border_width=1,
            command=lambda: None        # REMEMBER: Add functionallity later!! :DD
        )
        self.theme_btn.grid(column=2, row=0, padx=(0, 20), pady=(20, 0), sticky="e")

    def create_navbar(self):
        nav_frame = ctk.CTkFrame(
            self,
            width=190,
            fg_color="transparent"
        )
        nav_frame.grid(column=0, row=1, padx=(20, 0), pady=10, sticky="new")
        nav_frame.grid_propagate(False)

        nav_items = ["Home", "Servers", "Console", "Backups", "Settings"]
        self.nav_buttons = []

        for i, text in enumerate(nav_items):
            is_active = (i == 0)

            item_frame = ctk.CTkFrame(
                nav_frame,
                fg_color=self.colors["element"] if is_active else "transparent",
                corner_radius=8
            )
            item_frame.pack(side="top", fill="x", padx=5, pady=8)

            item_frame.grid_columnconfigure(0, weight=0, minsize=25)
            item_frame.grid_columnconfigure(1, weight=1)

            symbol = ctk.CTkLabel(
                item_frame,
                text="■",
                font=("Segoe UI", 10, "bold"),
                text_color=self.colors["green"] if is_active else self.colors["text_muted"],
                anchor="center"
            )
            symbol.grid(column=0, row=0, padx=(5, 0), pady=5, sticky="e")

            label = ctk.CTkLabel(
                item_frame,
                text=text,
                font=("Segoe UI", 18, "bold" if is_active else "normal"),
                text_color=self.colors["text"] if is_active else self.colors["text_muted"],
                anchor="w"
            )
            label.grid(column=1, row=0, padx=(5, 0), pady=5, sticky="w")

            self.nav_buttons.append((item_frame, symbol, label))

            item_frame.bind("<Button-1>", lambda e, idx=i: self.nav_click(idx))
            symbol.bind("<Button-1>", lambda e, idx=i: self.nav_click(idx))
            label.bind("<Button-1>", lambda e, idx=i: self.nav_click(idx))

        self.current_nav = 0

    def nav_click(self, index):
        if index == self.current_nav:
            return

        self.current_nav = index

        for i, (frame, symbol, label) in enumerate(self.nav_buttons):
            is_active = (i == index)
            frame.configure(fg_color=self.colors["element"] if is_active else "transparent")
            symbol.configure(text_color=self.colors["green"] if is_active else self.colors["text_muted"])
            label.configure(
                font=("Segoe UI", 18, "bold" if is_active else "normal"),
                text_color=self.colors["text"] if is_active else self.colors["text_muted"]
            )

        # Switch the view based on the selected nav item
        view_map = ["home", "servers", "console", "backups", "settings"]
        view_name = view_map[index]
        self.current_view_name = view_name
        self.update_header(view_name)
        self.show_view(view_name)

    def update_header(self, view_name):
        display_name = view_name.capitalize()
        self.header_label.configure(text=display_name)

    def create_content_area(self):
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.content_frame.grid(column=1, row=1, columnspan=2, padx=15, pady=15, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

    # Destroy current view + schedule new one
    def show_view(self, view_name):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.after(10, lambda: self._build_view(view_name))

    def _build_view(self, view_name):
        if view_name == "home":
            view = HomeView(self.content_frame, self.colors, self.servers_base)
        elif view_name == "servers":
            view = ServersView(self.content_frame, self.colors, self.servers_base)
        else:
            view = ctk.CTkLabel(
                self.content_frame,
                text=f"{view_name.capitalize()} page - coming soon",
                font=("Segoe UI", 24),
                text_color=self.colors["text_muted"]
            )
        view.grid(row=0, column=0, sticky="nsew")

    def on_closing(self):
        # Kill any Minecraft servers started by FalkMC
        servers_base = self.servers_base
        for proc in psutil.process_iter(['pid', 'cmdline', 'cwd']):
            try:
                cmdline = proc.info.get('cmdline')
                cwd = proc.info.get('cwd')
                if not cmdline or not cwd:
                    continue
                if "java" in cmdline[0].lower() and "server.jar" in " ".join(cmdline):
                    # Only kill servers that live inside our servers_base folder
                    if cwd.startswith(servers_base):
                        try:
                            proc.terminate()
                            proc.wait(timeout=5)
                        except (psutil.TimeoutExpired, psutil.NoSuchProcess):
                            try:
                                proc.kill()
                            except:
                                pass
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Save window size and settings
        self.settings["window_width"] = self.winfo_width()
        self.settings["window_height"] = self.winfo_height()
        save_settings(self.settings)
        self.destroy()


# Splash screen logic
def run():
    # Create the main app window (hidden)
    app = App()
    app.withdraw()

    # Create splash screen
    splash = ctk.CTkToplevel(app)
    splash.overrideredirect(True)
    splash.configure(fg_color="#000000")

    splash_width = 600
    splash_height = 315
    progress_bar_height = 4
    progress_bar_y = splash_height - progress_bar_height - 8

    # Use dark theme colors (splash is always dark)
    dark_colors = THEME_COLORS["dark"]

    cover_path = resource_path("images/FalkMC_Cover.png")
    try:
        cover_img = ctk.CTkImage(light_image=Image.open(cover_path),
                                 dark_image=Image.open(cover_path),
                                 size=(splash_width, splash_height))
        image_label = ctk.CTkLabel(splash, image=cover_img, text="")
        image_label.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception:
        fallback = ctk.CTkLabel(splash, text="FalkMC\nLoading...",
                                font=("Segoe UI", 30, "bold"),
                                text_color="white")
        fallback.pack(expand=True)

    # Progress bar – using existing theme color list
    progress = ctk.CTkProgressBar(
        splash,
        width=splash_width,
        height=progress_bar_height,
        corner_radius=2,
        progress_color=dark_colors["green"],
        fg_color=dark_colors["element"]
    )
    progress.place(x=0, y=progress_bar_y)
    progress.set(0)

    x = (splash.winfo_screenwidth() // 2) - (splash_width // 2)
    y = (splash.winfo_screenheight() // 2) - (splash_height // 2)
    splash.geometry(f"{splash_width}x{splash_height}+{x}+{y}")

    splash.transient(app)
    splash.grab_set()

    steps = 30
    current_step = 0

    def update_progress():
        nonlocal current_step
        current_step += 1
        progress.set(current_step / steps)
        if current_step < steps:
            app.after(100, update_progress)
        else:
            splash.destroy()
            app.deiconify()

    app.after(200, update_progress)
    app.mainloop()


if __name__ == "__main__":
    run()
