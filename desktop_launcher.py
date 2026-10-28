"""
StreamMix Studio - Desktop Application Launcher
Starts the FastAPI server and launches MS Edge / Chrome in native borderless app mode.
"""

import sys
import os
import time
import socket
import subprocess
import threading
import urllib.request
import webbrowser
import multiprocessing

# Suppress benign Windows asyncio ConnectionResetError [WinError 10054]
if sys.platform == "win32":
    import asyncio
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _orig_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

        def _silent_call_connection_lost(self, exc=None):
            try:
                _orig_call_connection_lost(self, exc)
            except (ConnectionResetError, OSError):
                pass

        _ProactorBasePipeTransport._call_connection_lost = _silent_call_connection_lost
    except Exception:
        pass

HOST = "127.0.0.1"
DEFAULT_PORT = 8899

SERVER_CRASHED = threading.Event()
SERVER_ERROR = []


def is_port_in_use(port: int) -> bool:
    """Checks if a TCP port is currently open or listening on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((HOST, port)) == 0


def kill_process_on_port(port: int):
    """Finds and kills zombie processes listening on the target port."""
    if not is_port_in_use(port):
        return
    try:
        cmd = f'netstat -ano | findstr :{port}'
        output = subprocess.check_output(cmd, shell=True, text=True, errors="replace")
        for line in output.strip().splitlines():
            if f':{port}' in line and 'LISTENING' in line:
                pid = line.strip().split()[-1]
                if pid and pid != '0':
                    print(f"Cleaning zombie process on port {port} (PID: {pid})...")
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                    time.sleep(0.8)
    except Exception as e:
        print(f"Port cleanup note: {e}")


def get_available_port(preferred_port: int = DEFAULT_PORT) -> int:
    """
    Ensures an available TCP port.
    First tries to reclaim preferred_port (8899), otherwise scans 8900-8930.
    """
    if is_port_in_use(preferred_port):
        kill_process_on_port(preferred_port)

    if not is_port_in_use(preferred_port):
        return preferred_port

    for candidate in range(8900, 8931):
        if not is_port_in_use(candidate):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((HOST, candidate))
                return candidate
            except OSError:
                continue

    return preferred_port


def run_server(port: int):
    """Executes Uvicorn server with full traceback capture on startup failure."""
    try:
        import uvicorn
        from backend.server import app
        uvicorn.run(app, host=HOST, port=port, log_level="warning")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        SERVER_ERROR.append(tb)
        SERVER_CRASHED.set()

        # Write traceback to persistent crash log
        try:
            from backend.config import LOGS_DIR
            log_path = LOGS_DIR / "startup_crash.log"
        except Exception:
            local_app = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            log_path = os.path.join(local_app, "StreamMixStudio_startup_crash.log")

        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"StreamMix Studio Startup Crash [{time.ctime()}]:\n{tb}\n")
            print(f"[FATAL] Backend server crashed! Logged to: {log_path}", file=sys.stderr)
        except Exception:
            pass


def wait_for_server(base_url: str, timeout: int = 25) -> bool:
    """
    Polls /api/health until server responds HTTP 200 or failure is detected.
    Returns True when healthy, False on failure or timeout.
    """
    start = time.time()
    while time.time() - start < timeout:
        if SERVER_CRASHED.is_set():
            return False
        try:
            with urllib.request.urlopen(f"{base_url}/api/health", timeout=1.5) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def show_error_dialog(title: str, message: str):
    """Displays a native Windows error message dialog box."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # 0x10 = MB_ICONERROR
            return
        except Exception:
            pass
    print(f"[{title}] {message}", file=sys.stderr)


def launch_desktop_window(base_url: str) -> bool:
    """
    Launches a dedicated Native Desktop Application Window.
    Uses Microsoft Edge WebView2 (pywebview) for a 100% native, borderless,
    hardware-accelerated desktop experience without Chrome or localhost address bar.
    """
    # 1. Primary: Native WebView2 Desktop Window
    try:
        import webview
        print("Launching Native Desktop Window (Hardware-Accelerated WebView2)...")
        window = webview.create_window(
            title="StreamMix Studio — Twitch + YouTube 1080p 60fps Remix Engine",
            url=base_url,
            width=1440,
            height=900,
            min_size=(1100, 700),
            background_color="#0b0f19",
            text_select=True
        )
        webview.start(gui="edgechromium", debug=False)
        return True
    except Exception as e:
        print(f"Native WebView2 note: {e}")

    # 2. Fallback: Edge App Mode with isolated profile (never merges into user's browser tabs or shows URL bar)
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    edge_profile = os.path.join(os.path.expanduser("~"), ".streammix", "app_profile")
    try:
        os.makedirs(edge_profile, exist_ok=True)
    except Exception:
        pass

    for path in edge_paths:
        if os.path.exists(path):
            print("Launching Isolated Native App Mode via Edge...")
            proc = subprocess.Popen([
                path,
                f"--app={base_url}",
                f"--user-data-dir={edge_profile}",
                "--no-first-run",
                "--no-default-browser-check",
                "--window-size=1440,900"
            ])
            proc.wait()
            return True

    # 3. Fallback: Chrome App Mode with isolated profile
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe")
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            print("Launching Isolated App Mode via Chrome...")
            proc = subprocess.Popen([
                path,
                f"--app={base_url}",
                f"--user-data-dir={edge_profile}",
                "--no-first-run",
                "--no-default-browser-check",
                "--window-size=1440,900"
            ])
            proc.wait()
            return True

    # 4. Ultimate Fallback to default browser
    print("Opening in default browser...")
    webbrowser.open(base_url)
    return False


def main():
    print("=" * 65)
    print("   STREAMMIX STUDIO - TWITCH + YOUTUBE REMIX ENGINE")
    print("   1080p 60fps Single-Pass Desktop Workstation")
    print("=" * 65)

    active_port = get_available_port(DEFAULT_PORT)
    base_url = f"http://{HOST}:{active_port}"

    # Launch server in background thread
    server_thread = threading.Thread(target=run_server, args=(active_port,), daemon=True)
    server_thread.start()

    print(f"Waiting for backend engine on {base_url}...")
    server_ok = wait_for_server(base_url, timeout=25)

    if not server_ok:
        err_msg = SERVER_ERROR[0] if SERVER_ERROR else "Server startup timed out after 25 seconds."
        try:
            from backend.config import LOGS_DIR
            log_location = str((LOGS_DIR / "startup_crash.log").resolve())
        except Exception:
            log_location = "AppData/Local/StreamMixStudio_startup_crash.log"

        dialog_text = (
            f"StreamMix Studio was unable to connect to the internal engine on port {active_port}.\n\n"
            f"Reason: {err_msg[:200]}...\n\n"
            f"A detailed crash report has been saved to:\n{log_location}\n\n"
            "Please check if your antivirus or local firewall is blocking localhost connections."
        )
        show_error_dialog("StreamMix Studio - Startup Error", dialog_text)
        kill_process_on_port(active_port)
        sys.exit(1)

    print(f"Engine active and ready on {base_url}. Launching native desktop window...")
    is_blocking = launch_desktop_window(base_url)

    if not is_blocking:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    print("\nShutting down StreamMix Studio cleanly...")
    kill_process_on_port(active_port)
    sys.exit(0)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
