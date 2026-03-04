import os
import shutil
import re
import time
import requests
import winreg
import sys
import ctypes
import zipfile
import psutil
from datetime import datetime
from dotenv import load_dotenv

# ==========================================
# 🛠️ PyInstaller Resource Path Helper
# ==========================================
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ==========================================
# 🛡️ 1. Security & Environment Setup (.env Load)
# ==========================================
# [Update] Load .env from the bundled resource path
env_path = resource_path(".env")
load_dotenv(env_path)

# 🌐 Server URL (Change to your actual domain or Ngrok URL!)
SERVER_URL = os.getenv("SERVER_URL", "https://kyleigh-metaphorical-noblemanly.ngrok-free.dev")

# 🔑 [Task 1] Secret Access Key (Retrieved from environment variables)
ACCESS_SECRET_KEY = os.getenv("No_Eat_KEY")

# 🛡️ Local Vault Path (AppData/Roaming/TFSpray_Vault)
VAULT_DIR = os.path.join(os.getenv('APPDATA'), 'TFSpray_Vault')

# 🔑 Pre-defined Authentication Headers for the server
CUSTOM_HEADERS = {
    'No-Eat-Secret': ACCESS_SECRET_KEY,
    'ngrok-skip-browser-warning': 'true'
}

# ==========================================
# 🔍 2. System Detection Logic (TF2 Path & Process)
# ==========================================

def find_tf2_temp_path():
    """Automatically detects TF2 installation path by tracking the Windows Registry."""
    try:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
        except FileNotFoundError:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
            
        steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
        winreg.CloseKey(key)
        
        library_paths = [steam_path]
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        
        if os.path.exists(vdf_path):
            with open(vdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
                paths = re.findall(r'"path"\s+"([^"]+)"', content)
                library_paths.extend([p.replace('\\\\', '\\') for p in paths])

        for lib_path in library_paths:
            tf_dir = os.path.join(lib_path, "steamapps", "common", "Team Fortress 2", "tf")
            if os.path.exists(tf_dir):
                tf2_temp = os.path.join(tf_dir, "materials", "temp")
                if not os.path.exists(tf2_temp):
                    os.makedirs(tf2_temp)
                return tf2_temp
    except Exception as e:
        print(f"❌ Path detection failed: {e}") 
    return None

def is_tf2_running():
    """Checks if 64-bit or 32-bit Team Fortress 2 is currently running."""
    target_procs = ['tf_win64.exe', 'hl2.exe']
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'].lower() in target_procs:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

# ==========================================
# ⚙️ 3. Startup Program Registration
# ==========================================

def check_and_add_startup():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, "TFSpraySync")
        winreg.CloseKey(key)
        return
    except FileNotFoundError: pass

    print("\n" + "-" * 50)
    print("⚠️ [Startup Registration]")
    print("Would you like to run the spray sync automatically when Windows starts?")
    choice = input("Do you agree? (Y / N) : ").strip().lower()
    
    if choice == 'y':
        exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, "TFSpraySync", 0, winreg.REG_SZ, f'"{exe_path}"')
            winreg.CloseKey(key)
            print("✅ Registration complete!")
        except Exception as e:
            print(f"❌ Registration failed: {e}")

# ==========================================
# 🔄 4. Core Sync Logic
# ==========================================

def sync_with_server(tf2_temp_dir, do_full_download=False):
    if not os.path.exists(VAULT_DIR): os.makedirs(VAULT_DIR)
    
    vault_files = set(os.listdir(VAULT_DIR))
    temp_files = set(os.listdir(tf2_temp_dir))

    for filename in vault_files - temp_files:
        if filename.endswith('.vtf'):
            shutil.copy2(os.path.join(VAULT_DIR, filename), os.path.join(tf2_temp_dir, filename))

    lock_file = os.path.join(VAULT_DIR, "init_lock.txt")
    if os.path.exists(lock_file):
        to_upload = [f for f in temp_files - vault_files 
                     if re.match(r'^[0-9a-f]{8}\.vtf$', f) and 
                     os.path.getsize(os.path.join(tf2_temp_dir, f)) <= 512 * 1024]

        if to_upload:
            if len(to_upload) >= 10:
                temp_zip = os.path.join(VAULT_DIR, "upload_bundle.zip")
                with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for f in to_upload:
                        src = os.path.join(tf2_temp_dir, f)
                        zf.write(src, f)
                        shutil.copy2(src, os.path.join(VAULT_DIR, f))
                try:
                    with open(temp_zip, 'rb') as f_obj:
                        requests.post(f"{SERVER_URL}/upload_zip", files={"file": f_obj}, headers=CUSTOM_HEADERS)
                    os.remove(temp_zip)
                except: pass
            else:
                for f in to_upload:
                    path = os.path.join(tf2_temp_dir, f)
                    shutil.copy2(path, os.path.join(VAULT_DIR, f))
                    try:
                        with open(path, 'rb') as f_obj:
                            requests.post(f"{SERVER_URL}/upload", files={"file": f_obj}, headers=CUSTOM_HEADERS)
                    except: pass
    else:
        with open(lock_file, 'w') as f_obj: f_obj.write("Old data upload blocked.")

    if do_full_download:
        try:
            res = requests.get(f"{SERVER_URL}/list", headers=CUSTOM_HEADERS, timeout=10)
            if res.status_code == 200:
                server_files = set(res.json().get("files", []))
                missing = list(server_files - set(os.listdir(VAULT_DIR)))
                if missing:
                    if len(missing) > 10:
                        dl_res = requests.post(f"{SERVER_URL}/download_zip", json={"files": missing}, headers=CUSTOM_HEADERS, stream=True)
                        if dl_res.status_code == 200:
                            zip_p = os.path.join(VAULT_DIR, "temp_download.zip")
                            with open(zip_p, 'wb') as f_obj:
                                for chunk in dl_res.iter_content(8192): f_obj.write(chunk)
                            with zipfile.ZipFile(zip_p, 'r') as zf:
                                zf.extractall(VAULT_DIR)
                                for n in zf.namelist():
                                    shutil.copy2(os.path.join(VAULT_DIR, n), os.path.join(tf2_temp_dir, n))
                            os.remove(zip_p)
                    else:
                        for n in missing:
                            file_res = requests.get(f"{SERVER_URL}/download/{n}", headers=CUSTOM_HEADERS)
                            if file_res.status_code == 200:
                                with open(os.path.join(VAULT_DIR, n), 'wb') as f_obj: f_obj.write(file_res.content)
                                shutil.copy2(os.path.join(VAULT_DIR, n), os.path.join(tf2_temp_dir, n))
        except: pass

# ==========================================
# 🏁 5. Main Execution Loop
# ==========================================

if __name__ == "__main__":
    print("🌍 TF2 Global Spray Sync Client is starting...")
    TF2_TEMP_DIR = find_tf2_temp_path()
    
    if not TF2_TEMP_DIR:
        print("❌ Could not find TF2 path.")
        time.sleep(5)
        sys.exit()

    check_and_add_startup()
    
    # Initial sync
    sync_with_server(TF2_TEMP_DIR, do_full_download=True)
    
    # Hide console window
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    timer = 0 
    while True:
        if is_tf2_running():
            if timer >= 300:
                sync_with_server(TF2_TEMP_DIR, do_full_download=True)
                timer = 0
            else:
                sync_with_server(TF2_TEMP_DIR, do_full_download=False)
            time.sleep(10)
            timer += 10
        else:
            time.sleep(30)
            timer = 0
