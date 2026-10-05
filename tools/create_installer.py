"""
StreamMix Studio - Installer Generator
Generates:
1. dist/StreamMixStudio_Setup.exe (1-Click Standalone Windows Setup Installer)
2. dist/StreamMixStudio_Portable.zip (Standalone Portable ZIP)
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
APP_DIR = DIST_DIR / "StreamMixStudio"
PAYLOAD_ZIP = DIST_DIR / "payload.zip"
PORTABLE_ZIP = DIST_DIR / "StreamMixStudio_Portable.zip"
INSTALLER_ISS = BASE_DIR / "installer.iss"
SETUP_EXE = DIST_DIR / "StreamMixStudio_Setup.exe"

def find_inno_compiler():
    """Checks for ISCC.exe in system PATH or standard Program Files locations."""
    import shutil as sh
    in_path = sh.which("iscc") or sh.which("ISCC")
    if in_path:
        return in_path

    candidates = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
        os.path.expandvars(r"%LocalAppData%\Programs\Inno Setup 6\ISCC.exe")
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None

def build_installer():
    print("=" * 68)
    print("   STREAMMIX STUDIO - WINDOWS SETUP INSTALLER BUILDER")
    print("=" * 68)

    if not APP_DIR.exists() or not (APP_DIR / "StreamMixStudio.exe").exists():
        print("[!] Compiled application directory not found at: dist/StreamMixStudio")
        print("[*] Please run BUILD_EXE.bat first to compile the binary.")
        sys.exit(1)

    # 1. Compress into Portable ZIP and Payload ZIP
    print("\n[1/3] Packing application into distribution archive...")
    if PAYLOAD_ZIP.exists():
        PAYLOAD_ZIP.unlink()

    with zipfile.ZipFile(PAYLOAD_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for file_path in APP_DIR.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(APP_DIR)
                zf.write(file_path, arcname=str(rel_path))

    # Also save as portable zip
    shutil.copyfile(PAYLOAD_ZIP, PORTABLE_ZIP)
    zip_size_mb = round(PORTABLE_ZIP.stat().st_size / (1024 * 1024), 1)
    print(f"    [OK] Portable archive created: dist/StreamMixStudio_Portable.zip ({zip_size_mb} MB)")

    # 2. Check for Inno Setup compiler
    iscc_bin = find_inno_compiler()
    if iscc_bin and INSTALLER_ISS.exists():
        print(f"\n[2/3] Building Inno Setup Windows Installer via {iscc_bin}...")
        cmd = [iscc_bin, str(INSTALLER_ISS)]
        res = subprocess.run(cmd, cwd=str(BASE_DIR))
        if res.returncode == 0 and SETUP_EXE.exists():
            print(f"    [OK] Official Inno Setup installer generated: dist/StreamMixStudio_Setup.exe")
            print_success()
            return
        else:
            print("    [!] Inno Setup failed. Falling back to native Python standalone installer...")

    # 3. Fallback: Build Native Standalone Installer via PyInstaller
    print("\n[2/3] Compiling Native Standalone Setup Executable (Zero-Dependency)...")
    gui_script = BASE_DIR / "tools" / "installer_gui.py"
    build_dir = BASE_DIR / "build" / "installer_build"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "StreamMixStudio_Setup",
        "--distpath", str(DIST_DIR),
        "--workpath", str(build_dir),
        "--specpath", str(build_dir),
        "--add-data", f"{str(PAYLOAD_ZIP)};.",
        str(gui_script)
    ]
    res = subprocess.run(cmd, cwd=str(BASE_DIR))

    if res.returncode == 0 and SETUP_EXE.exists():
        # Clean up temporary payload zip after bundling into the EXE
        if PAYLOAD_ZIP.exists():
            try:
                PAYLOAD_ZIP.unlink()
            except Exception:
                pass
        print(f"    [OK] Standalone Windows Setup Installer generated: dist/StreamMixStudio_Setup.exe")
        print_success()
    else:
        print("\n[ERROR] Failed to compile setup executable.")
        sys.exit(1)

def print_success():
    print("\n" + "=" * 68)
    print("   SUCCESS! INSTALLER & PACKAGES READY TO SHARE")
    print("=" * 68)
    print(f"1. Setup Installer:  {SETUP_EXE}")
    print(f"2. Portable Archive: {PORTABLE_ZIP}")
    print("\nHow your friend uses this:")
    print("  * Send them 'StreamMixStudio_Setup.exe'.")
    print("  * They double-click and click 'Install Now'.")
    print("  * It installs to their PC, creates a Desktop Icon, and launches")
    print("    StreamMix Studio in a Native Hardware-Accelerated Desktop Window!")
    print("    (No Chrome, No 127.0.0.1 localhost URL bar, Low RAM usage!)")
    print("=" * 68 + "\n")

if __name__ == "__main__":
    build_installer()
