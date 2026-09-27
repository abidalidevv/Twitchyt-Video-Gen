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

def open_desktop_window():
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]

    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe")
    ]

    # Try Edge App Mode first
    for path in edge_paths:
        if os.path.exists(path):
            print("Launching StreamMix Studio in Native Edge App Mode...")
            subprocess.Popen([path, f"--app={BASE_URL}", "--window-size=1440,900"])
            return

    # Try Chrome App Mode
    for path in chrome_paths:
        if os.path.exists(path):
            print("Launching StreamMix Studio in Native Chrome App Mode...")
            subprocess.Popen([path, f"--app={BASE_URL}", "--window-size=1440,900"])
            return

    # Fallback to default browser
    print("Opening in default browser...")
    webbrowser.open(BASE_URL)

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
    if wait_for_server():
        print("Engine active and ready. Launching studio interface...")
        open_desktop_window()
    else:
        print("Server took longer than expected. Opening browser...")
        open_desktop_window()

    print("\n[INFO] Studio is running. Keep this console window open.")
    print("[INFO] Press Ctrl+C in this console to terminate the studio.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down StreamMix Studio cleanly...")
        sys.exit(0)

if __name__ == "__main__":
    main()
