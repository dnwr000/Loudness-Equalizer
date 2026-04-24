import tkinter as tk
from tkinter import ttk, messagebox
import winreg
import ctypes
import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()

RENDER_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render"
ENHANCEMENT_FLAG = "{fc52a749-4be9-4510-896e-966ba6525980},3"

def get_audio_devices():
    devices = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, RENDER_KEY) as render:
            i = 0
            while True:
                try:
                    guid = winreg.EnumKey(render, i)
                    dev_path = RENDER_KEY + "\\" + guid
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, dev_path) as dev:
                        try:
                            state, _ = winreg.QueryValueEx(dev, "DeviceState")
                            if state != 1:
                                i += 1
                                continue
                        except:
                            i += 1
                            continue
                    props_path = dev_path + "\\Properties"
                    name = None
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, props_path) as props:
                            j = 0
                            while True:
                                try:
                                    vname, vdata, _ = winreg.EnumValue(props, j)
                                    if isinstance(vdata, str) and len(vdata) > 2 and not vdata.startswith("{"):
                                        name = vdata
                                        break
                                    j += 1
                                except OSError:
                                    break
                    except:
                        pass
                    if name:
                        devices.append((name, guid))
                    i += 1
                except OSError:
                    break
    except:
        pass
    return devices

def get_loudness_state(guid):
    try:
        fx_path = RENDER_KEY + "\\" + guid + "\\FxProperties"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, fx_path) as fx:
            data, _ = winreg.QueryValueEx(fx, ENHANCEMENT_FLAG)
            if isinstance(data, bytes) and len(data) >= 10:
                return data[8] == 255
    except:
        pass
    return False

def toggle_loudness(guid, enable):
    import tempfile, subprocess
    release_time = 4
    release_str = str(release_time).zfill(2)
    fx_path = "HKEY_LOCAL_MACHINE\\" + RENDER_KEY + "\\" + guid + "\\FxProperties"
    ff_val = "ff,ff" if enable else "00,00"
    reg_content = f"""Windows Registry Editor Version 5.00

[{fx_path}]
"{{d04e05a6-594b-4fb6-a80d-01af5eed7d1d}},1"="{{62dc1a93-ae24-464c-a43e-452f824c4250}}"
"{{d04e05a6-594b-4fb6-a80d-01af5eed7d1d}},2"="{{637c490d-eee3-4c0a-973f-371958802da2}}"
"{{d04e05a6-594b-4fb6-a80d-01af5eed7d1d}},3"="{{5860E1C5-F95C-4a7a-8EC8-8AEF24F379A1}}"
"{{d04e05a6-594b-4fb6-a80d-01af5eed7d1d}},5"="{{62dc1a93-ae24-464c-a43e-452f824c4250}}"
"{{d04e05a6-594b-4fb6-a80d-01af5eed7d1d}},6"="{{637c490d-eee3-4c0a-973f-371958802da2}}"
"{{fc52a749-4be9-4510-896e-966ba6525980}},3"=hex:0b,00,00,00,01,00,00,00,{ff_val},00,00
"{{9c00eeed-edce-4cd8-ae08-cb05e8ef57a0}},3"=hex:03,00,00,00,01,00,00,00,{release_str},00,00,00
"""
    tmp = tempfile.mktemp(suffix=".reg")
    with open(tmp, "w", encoding="utf-16") as f:
        f.write(reg_content)
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    subprocess.run(["regedit.exe", "/s", tmp], startupinfo=si)
    subprocess.run(["net", "stop", "audiosrv", "/y"], startupinfo=si, capture_output=True)
    subprocess.run(["net", "start", "audiosrv"], startupinfo=si, capture_output=True)
    os.remove(tmp)

BG        = "#0f0f13"
CARD      = "#18181f"
BORDER    = "#2a2a36"
TEXT_PRI  = "#f0f0f5"
TEXT_SEC  = "#6b6b80"
GREEN     = "#22c55e"
GREEN_GLOW= "#052e16"
RED       = "#ef4444"
RED_GLOW  = "#1f0707"
YELLOW    = "#f59e0b"

class ToggleSwitch(tk.Canvas):
    W, H, R = 90, 44, 18

    def __init__(self, parent, command=None, **kwargs):
        super().__init__(parent, width=self.W, height=self.H,
                         bg=CARD, highlightthickness=0, cursor="hand2", **kwargs)
        self._on = False
        self._command = command
        self._animating = False
        self._knob_x = self.R + 5
        self._draw()
        self.bind("<Button-1>", self._clicked)

    def _draw(self):
        self.delete("all")
        x = self._knob_x
        cy = self.H // 2
        track_color = GREEN if self._on else "#2a2a36"
        # track rounded rect
        r = self.H // 2 - 3
        x0, y0, x1, y1 = 3, 3, self.W - 3, self.H - 3
        self.create_oval(x0, y0, x0 + (y1-y0), y1, fill=track_color, outline="")
        self.create_oval(x1 - (y1-y0), y0, x1, y1, fill=track_color, outline="")
        self.create_rectangle(x0 + (y1-y0)//2, y0, x1 - (y1-y0)//2, y1, fill=track_color, outline="")
        # knob shadow
        self.create_oval(x - self.R + 1, cy - self.R + 2,
                         x + self.R + 1, cy + self.R + 2,
                         fill="#111111", outline="")
        # knob
        self.create_oval(x - self.R, cy - self.R,
                         x + self.R, cy + self.R,
                         fill=TEXT_PRI, outline="")

    def _animate(self, target_x, step=5):
        if abs(self._knob_x - target_x) <= step:
            self._knob_x = target_x
            self._draw()
            self._animating = False
            if self._command:
                self._command()
        else:
            self._knob_x += step if target_x > self._knob_x else -step
            self._draw()
            self.after(10, lambda: self._animate(target_x, step))

    def _clicked(self, event=None):
        if self._animating:
            return
        self._animating = True
        self._on = not self._on
        target = self.W - self.R - 5 if self._on else self.R + 5
        self._animate(target)

    def set_state(self, on: bool):
        self._on = on
        self._knob_x = self.W - self.R - 5 if on else self.R + 5
        self._draw()

    def get_state(self):
        return self._on


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Loudness Equalizer")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.geometry("420x410")
        self.eval('tk::PlaceWindow . center')
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except:
            pass
        self.devices = get_audio_devices()
        self.is_on = False
        self._build_ui()
        self._load_device()

    def _card(self, parent, pady=(0, 10)):
        outer = tk.Frame(parent, bg=BORDER)
        outer.pack(fill="x", padx=20, pady=pady)
        inner = tk.Frame(outer, bg=CARD)
        inner.pack(fill="x", padx=1, pady=1)
        return inner

    def _build_ui(self):
        # Header
        tk.Label(self, text="Loudness Equalizer",
                 font=("Segoe UI", 18, "bold"), bg=BG, fg=TEXT_PRI
                 ).pack(anchor="w", padx=24, pady=(24, 2))
        tk.Label(self, text="Windows audio enhancement control",
                 font=("Segoe UI", 9), bg=BG, fg=TEXT_SEC
                 ).pack(anchor="w", padx=24, pady=(0, 16))

        # Device card
        dev_card = self._card(self)
        dev_frame = tk.Frame(dev_card, bg=CARD)
        dev_frame.pack(fill="x", padx=16, pady=14)

        tk.Label(dev_frame, text="AUDIO DEVICE", font=("Segoe UI", 7, "bold"),
                 bg=CARD, fg=TEXT_SEC).pack(anchor="w")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("M.TCombobox",
                        fieldbackground="#0f0f13", background="#0f0f13",
                        foreground=TEXT_PRI, selectbackground="#0f0f13",
                        selectforeground=TEXT_PRI, bordercolor=BORDER,
                        arrowcolor=TEXT_SEC, relief="flat")
        style.map("M.TCombobox", fieldbackground=[("readonly", "#0f0f13")])

        self.combo = ttk.Combobox(dev_frame, state="readonly",
                                  font=("Segoe UI", 10), width=34, style="M.TCombobox")
        self.combo.pack(anchor="w", pady=(6, 0))
        if self.devices:
            self.combo["values"] = [d[0] for d in self.devices]
            self.combo.current(0)
        self.combo.bind("<<ComboboxSelected>>", self._on_device_change)

        # Toggle card
        tog_card = self._card(self)
        tog_frame = tk.Frame(tog_card, bg=CARD)
        tog_frame.pack(fill="x", padx=16, pady=16)

        left = tk.Frame(tog_frame, bg=CARD)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text="Loudness Equalization",
                 font=("Segoe UI", 11, "bold"), bg=CARD, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(left, text="Reduces perceived volume differences",
                 font=("Segoe UI", 8), bg=CARD, fg=TEXT_SEC).pack(anchor="w", pady=(3, 0))

        right = tk.Frame(tog_frame, bg=CARD)
        right.pack(side="right", padx=(10, 0))
        self.toggle = ToggleSwitch(right, command=self._on_toggle)
        self.toggle.pack()

        # Status card
        self.st_outer = tk.Frame(self, bg=RED)
        self.st_outer.pack(fill="x", padx=20, pady=(0, 10))
        self.st_inner = tk.Frame(self.st_outer, bg=RED_GLOW)
        self.st_inner.pack(fill="x", padx=1, pady=(0, 1))

        st_row = tk.Frame(self.st_inner, bg=RED_GLOW)
        st_row.pack(fill="x", padx=16, pady=12)

        self.st_dot = tk.Label(st_row, text="●", font=("Segoe UI", 11),
                               bg=RED_GLOW, fg=RED)
        self.st_dot.pack(side="left", padx=(0, 8))

        st_right = tk.Frame(st_row, bg=RED_GLOW)
        st_right.pack(side="left")
        self.st_title = tk.Label(st_right, text="Status: OFF",
                                 font=("Segoe UI", 10, "bold"),
                                 bg=RED_GLOW, fg=RED)
        self.st_title.pack(anchor="w")
        self.st_sub = tk.Label(st_right, text="Loudness equalization is disabled",
                               font=("Segoe UI", 8),
                               bg=RED_GLOW, fg=RED)
        self.st_sub.pack(anchor="w")

        # Bottom
        self.bottom = tk.Label(self, text="", font=("Segoe UI", 8),
                               bg=BG, fg=TEXT_SEC)
        self.bottom.pack(pady=(0, 4))

        def open_github(e):
            import webbrowser
            webbrowser.open("https://github.com/dnwr000")

        github = tk.Label(self, text="github.com/dnwr000",
                          font=("Segoe UI", 8), bg=BG, fg=TEXT_SEC,
                          cursor="hand2")
        github.pack(pady=(0, 10))
        github.bind("<Enter>", lambda e: github.config(fg=TEXT_PRI, font=("Segoe UI", 8, "underline")))
        github.bind("<Leave>", lambda e: github.config(fg=TEXT_SEC, font=("Segoe UI", 8)))
        github.bind("<Button-1>", open_github)

    def _get_selected_guid(self):
        idx = self.combo.current()
        if 0 <= idx < len(self.devices):
            return self.devices[idx][1]
        return None

    def _load_device(self):
        guid = self._get_selected_guid()
        if guid:
            self.is_on = get_loudness_state(guid)
            self.toggle.set_state(self.is_on)
            self._update_status()

    def _on_device_change(self, _=None):
        self._load_device()

    def _on_toggle(self):
        guid = self._get_selected_guid()
        if not guid:
            messagebox.showerror("Error", "No audio device selected.")
            return
        new_state = self.toggle.get_state()
        self.bottom.config(text="Applying... please wait", fg=YELLOW)
        self.update()
        try:
            toggle_loudness(guid, new_state)
            self.is_on = new_state
            self._update_status()
            self.bottom.config(text="Done!  Restart your audio app if needed.", fg=GREEN)
        except Exception as e:
            self.bottom.config(text=f"Error: {e}", fg=RED)

    def _update_status(self):
        if self.is_on:
            c, gc, txt, sub = GREEN, GREEN_GLOW, "Status: ON", "Loudness equalization is enabled"
        else:
            c, gc, txt, sub = RED, RED_GLOW, "Status: OFF", "Loudness equalization is disabled"

        self.st_outer.config(bg=c)
        self.st_inner.config(bg=gc)
        for w in [self.st_inner] + list(self.st_inner.winfo_children()):
            try: w.config(bg=gc)
            except: pass
        for row in self.st_inner.winfo_children():
            for w in row.winfo_children():
                try: w.config(bg=gc)
                except: pass
                for ww in w.winfo_children():
                    try: ww.config(bg=gc, fg=c)
                    except: pass
        self.st_dot.config(fg=c, bg=gc)
        self.st_title.config(text=txt, fg=c, bg=gc)
        self.st_sub.config(text=sub, fg=c, bg=gc)


if __name__ == "__main__":
    if not is_admin():
        run_as_admin()
    else:
        app = App()
        app.mainloop()
