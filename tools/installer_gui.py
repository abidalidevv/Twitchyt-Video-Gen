"""
StreamMix Studio - Native Windows Setup Wizard & Installer
Extracts the application package to %LocalAppData%\\Programs\\StreamMix Studio,
creates Desktop & Start Menu shortcuts, and launches the native workstation.
"""

import os
import sys
import time
import zipfile
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_NAME = "StreamMix Studio"
DEFAULT_INSTALL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Programs", "StreamMix Studio")

def get_bundle_dir():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return str(Path(__file__).resolve().parent)

def create_windows_shortcut(target_exe: str, shortcut_path: str, icon_path: str = None, work_dir: str = None):
    """Creates a Windows .lnk shortcut using WScript.Shell via PowerShell."""
    work_dir = work_dir or str(Path(target_exe).parent)
    icon_line = f"$s.IconLocation = '{icon_path}';" if icon_path and os.path.exists(icon_path) else ""
    ps_cmd = (
        f"$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{shortcut_path}'); "
        f"$s.TargetPath = '{target_exe}'; "
        f"$s.WorkingDirectory = '{work_dir}'; "
        f"{icon_line} "
        f"$s.Save()"
    )
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} — Setup Wizard")
        self.root.geometry("560x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f172a")

        # Center on screen
        self.root.eval('tk::PlaceWindow . center')

        self.install_path_var = tk.StringVar(value=DEFAULT_INSTALL_DIR)
        self.desktop_icon_var = tk.BooleanVar(value=True)
        self.start_menu_var = tk.BooleanVar(value=True)
        self.launch_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        # Header Frame
        header = tk.Frame(self.root, bg="#1e293b", padx=20, pady=16)
        header.pack(fill="x")

        title_lbl = tk.Label(
            header,
            text=f"⚡ {APP_NAME} Setup",
            font=("Segoe UI", 16, "bold"),
            fg="#00f2fe",
            bg="#1e293b"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            header,
            text="Native 1080p 60fps Single-Pass Desktop Workstation (Hardware GPU Accelerated)",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#1e293b"
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        # Main Body
        body = tk.Frame(self.root, bg="#0f172a", padx=24, pady=16)
        body.pack(fill="both", expand=True)

        # Path Selection
        path_lbl = tk.Label(body, text="Installation Folder:", font=("Segoe UI", 9, "bold"), fg="#e2e8f0", bg="#0f172a")
        path_lbl.pack(anchor="w")

        path_row = tk.Frame(body, bg="#0f172a")
        path_row.pack(fill="x", pady=(4, 14))

        self.path_entry = tk.Entry(
            path_row,
            textvariable=self.install_path_var,
            font=("Consolas", 9),
            bg="#1e293b",
            fg="#ffffff",
            insertbackground="#00f2fe",
            relief="flat",
            bd=6
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = tk.Button(
            path_row,
            text="Browse...",
            font=("Segoe UI", 9),
            bg="#334155",
            fg="#ffffff",
            activebackground="#475569",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=4,
            command=self._browse_dir
        )
        browse_btn.pack(side="right")

        # Checkboxes
        opts_frame = tk.Frame(body, bg="#0f172a")
        opts_frame.pack(fill="x", pady=(0, 14))

        cb1 = tk.Checkbutton(
            opts_frame,
            text="Create Desktop Shortcut (Recommended)",
            variable=self.desktop_icon_var,
            font=("Segoe UI", 9),
            fg="#cbd5e1",
            bg="#0f172a",
            selectcolor="#1e293b",
            activebackground="#0f172a",
            activeforeground="#ffffff"
        )
        cb1.pack(anchor="w", pady=2)

        cb2 = tk.Checkbutton(
            opts_frame,
            text="Add to Windows Start Menu Programs",
            variable=self.start_menu_var,
            font=("Segoe UI", 9),
            fg="#cbd5e1",
            bg="#0f172a",
            selectcolor="#1e293b",
            activebackground="#0f172a",
            activeforeground="#ffffff"
        )
        cb2.pack(anchor="w", pady=2)

        cb3 = tk.Checkbutton(
            opts_frame,
            text="Launch StreamMix Studio immediately after install",
            variable=self.launch_var,
            font=("Segoe UI", 9),
            fg="#38bdf8",
            bg="#0f172a",
            selectcolor="#1e293b",
            activebackground="#0f172a",
            activeforeground="#38bdf8"
        )
        cb3.pack(anchor="w", pady=2)

        # Progress Section
        self.status_lbl = tk.Label(
            body,
            text="Ready to install. Click Install Now to begin.",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#0f172a"
        )
        self.status_lbl.pack(anchor="w", pady=(8, 4))

        # Progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Cyan.Horizontal.TProgressbar",
            troughcolor="#1e293b",
            background="#00f2fe",
            lightcolor="#00f2fe",
            darkcolor="#00c8d7",
            bordercolor="#0f172a",
            thickness=10
        )
        self.prog = ttk.Progressbar(body, style="Cyan.Horizontal.TProgressbar", orient="horizontal", mode="determinate")
        self.prog.pack(fill="x", pady=(0, 16))

        # Footer Actions
        footer = tk.Frame(self.root, bg="#1e293b", padx=20, pady=12)
        footer.pack(fill="x", side="bottom")

        self.btn_cancel = tk.Button(
            footer,
            text="Cancel",
            font=("Segoe UI", 9),
            bg="#334155",
            fg="#e2e8f0",
            relief="flat",
            padx=14,
            pady=6,
            command=self.root.destroy
        )
        self.btn_cancel.pack(side="right", padx=(8, 0))

        self.btn_install = tk.Button(
            footer,
            text="🚀 Install Now",
            font=("Segoe UI", 10, "bold"),
            bg="#9146ff",
            fg="#ffffff",
            activebackground="#772ce8",
            activeforeground="#ffffff",
            relief="flat",
            padx=20,
            pady=6,
            cursor="hand2",
            command=self._start_install
        )
        self.btn_install.pack(side="right")

    def _browse_dir(self):
        d = filedialog.askdirectory(initialdir=self.install_path_var.get(), title="Select Install Folder")
        if d:
            self.install_path_var.set(os.path.join(d, "StreamMix Studio"))

    def _start_install(self):
        target_dir = self.install_path_var.get().strip()
        if not target_dir:
            messagebox.showerror("Error", "Please specify a valid installation directory.")
            return

        self.btn_install.config(state="disabled")
        self.btn_cancel.config(state="disabled")
        self.path_entry.config(state="disabled")

        threading.Thread(target=self._run_install_worker, daemon=True).start()

    def _run_install_worker(self):
        target_dir = self.install_path_var.get().strip()
        os.makedirs(target_dir, exist_ok=True)

        bundle_dir = get_bundle_dir()
        payload_zip = os.path.join(bundle_dir, "payload.zip")

        if not os.path.exists(payload_zip):
            # Check relative directory for development
            cand = os.path.join(str(Path(__file__).resolve().parent.parent), "dist", "payload.zip")
            if os.path.exists(cand):
                payload_zip = cand

        if not os.path.exists(payload_zip):
            self._update_status("Error: Embedded package payload.zip missing!", 0)
            messagebox.showerror("Setup Error", "The setup package is corrupted or missing payload.zip.")
            self.btn_cancel.config(state="normal")
            return

        try:
            self._update_status("Extracting StreamMix Studio files...", 10)
            with zipfile.ZipFile(payload_zip, "r") as zf:
                members = zf.infolist()
                total = len(members)
                for idx, m in enumerate(members):
                    zf.extract(m, target_dir)
                    if idx % 10 == 0 or idx == total - 1:
                        pct = 10 + int((idx / max(1, total)) * 75)
                        self._update_status(f"Extracting: {m.filename[:45]}...", pct)

            self._update_status("Configuring shortcuts and application paths...", 90)

            # Ensure data directories exist
            for sub in ["outputs", "downloads", "temp", "avatars", "bgm", "logs"]:
                os.makedirs(os.path.join(target_dir, "data", sub), exist_ok=True)

            exe_path = os.path.join(target_dir, "StreamMixStudio.exe")

            # Create Desktop Shortcut
            if self.desktop_icon_var.get():
                desktop = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Desktop")
                shortcut = os.path.join(desktop, f"{APP_NAME}.lnk")
                create_windows_shortcut(exe_path, shortcut, exe_path, target_dir)

            # Create Start Menu Shortcut
            if self.start_menu_var.get():
                start_menu = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", APP_NAME)
                os.makedirs(start_menu, exist_ok=True)
                shortcut = os.path.join(start_menu, f"{APP_NAME}.lnk")
                create_windows_shortcut(exe_path, shortcut, exe_path, target_dir)

            # Create Uninstaller Script
            uninstaller_path = os.path.join(target_dir, "Uninstall.bat")
            with open(uninstaller_path, "w", encoding="utf-8") as uf:
                uf.write("@echo off\n")
                uf.write(f"echo Uninstalling {APP_NAME}...\n")
                uf.write(f'del /f /q "%USERPROFILE%\\Desktop\\{APP_NAME}.lnk" 2>nul\n')
                uf.write(f'rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{APP_NAME}" 2>nul\n')
                uf.write('echo Removing files...\n')
                uf.write(f'cd /d "%LOCALAPPDATA%"\n')
                uf.write(f'rmdir /s /q "{target_dir}" 2>nul\n')
                uf.write(f"echo {APP_NAME} has been uninstalled.\n")
                uf.write("pause\n")

            self._update_status("✓ Installation Successful!", 100)
            time.sleep(0.6)

            if self.launch_var.get() and os.path.exists(exe_path):
                subprocess.Popen([exe_path], cwd=target_dir)

            self.root.after(800, self.root.destroy)

        except Exception as e:
            self._update_status(f"Installation failed: {e}", 0)
            messagebox.showerror("Installation Error", str(e))
            self.btn_cancel.config(state="normal")

    def _update_status(self, text, pct):
        def _cb():
            self.status_lbl.config(text=text)
            self.prog["value"] = pct
        self.root.after(0, _cb)

def main():
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
