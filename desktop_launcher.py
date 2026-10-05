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

PORT = 8899
HOST = "127.0.0.1"
BASE_URL = f"http://{HOST}:{PORT}"

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) == 0

def kill_process_on_port(port: int):
    """Finds and kills zombie processes listening on the target port."""
    if not is_port_in_use(port):
        return
    try:
        cmd = f'netstat -ano | findstr :{port}'
        output = subprocess.check_output(cmd, shell=True, text=True)
        for line in output.strip().splitlines():
            if f':{port}' in line and 'LISTENING' in line:
                pid = line.strip().split()[-1]
                if pid and pid != '0':
                    print(f"Cleaning zombie process on port {port} (PID: {pid})...")
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                    time.sleep(1)
    except Exception as e:
        print(f"Port cleanup note: {e}")

def run_server():
    import uvicorn
    from backend.server import app
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")

def wait_for_server(timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def launch_desktop_window() -> bool:
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
            url=BASE_URL,
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
    os.makedirs(edge_profile, exist_ok=True)

    for path in edge_paths:
        if os.path.exists(path):
            print("Launching Isolated Native App Mode via Edge...")
            proc = subprocess.Popen([
                path,
                f"--app={BASE_URL}",
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
                f"--app={BASE_URL}",
                f"--user-data-dir={edge_profile}",
                "--no-first-run",
                "--no-default-browser-check",
                "--window-size=1440,900"
            ])
            proc.wait()
            return True

    # 4. Ultimate Fallback to default browser
    print("Opening in default browser...")
    webbrowser.open(BASE_URL)
    return False


def main():
    print("=" * 65)
    print("   STREAMMIX STUDIO - TWITCH + YOUTUBE REMIX ENGINE")
    print("   1080p 60fps Single-Pass Desktop Workstation")
    print("=" * 65)

    kill_process_on_port(PORT)

    # Launch server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print(f"Waiting for backend engine on {BASE_URL}...")
    if not wait_for_server():
        print("[ERROR] Server startup timed out. Check firewall or port 8899.")

    print("Engine active and ready. Launching native desktop window...")
    is_blocking = launch_desktop_window()

    if not is_blocking:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    print("\nShutting down StreamMix Studio cleanly...")
    kill_process_on_port(PORT)
    sys.exit(0)


if __name__ == "__main__":
    main()

