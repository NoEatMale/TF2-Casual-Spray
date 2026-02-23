import os
import shutil
import re
import time
import requests
import winreg
import sys
import ctypes
import zipfile

# 🌐 Server URL (Change to your actual domain or Ngrok URL!)
SERVER_URL = "https://kyleigh-metaphorical-noblemanly.ngrok-free.dev"
# 🛡️ Bulletproof local Vault (Hidden in AppData)
VAULT_DIR = os.path.join(os.getenv('APPDATA'), 'TFSpray_Vault')

# ==========================================
# 1. 100% Auto-detect TF2 Path (Registry tracking)
# ==========================================
def find_tf2_temp_path():
    print("🔍 Auto-detecting Steam and Team Fortress 2 installation path...")
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
            tf2_temp = os.path.join(lib_path, "steamapps", "common", "Team Fortress 2", "tf", "materials", "temp")
            if os.path.exists(tf2_temp):
                print(f"✅ Found TF2 Temp folder: {tf2_temp}")
                return tf2_temp
    except Exception as e:
        pass
    return None

# ==========================================
# 2. Auto-add to Windows Startup (1-time Y/N consent)
# ==========================================
def check_and_add_startup():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    # [1] Silently check if already registered
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, "TFSpraySync")
        winreg.CloseKey(key)
        return  # Exit function if already registered
    except FileNotFoundError:
        pass  # Proceed to ask user if not registered

    # [2] Ask for user consent (Y/N) if not registered
    print("\n" + "-" * 50)
    print("⚠️ [Startup Execution Setup]")
    print("This program automatically syncs TF2 sprays globally in the background.")
    print("Would you like to register it to run automatically on Windows startup?")
    print("(※ We ask for consent once to prevent false positives from antivirus software.)")
    
    while True:
        choice = input("Do you agree? (Y / N) : ").strip().lower()
        if choice == 'y':
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                exe_path = os.path.abspath(__file__)
            
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
                winreg.SetValueEx(key, "TFSpraySync", 0, winreg.REG_SZ, f'"{exe_path}"')
                winreg.CloseKey(key)
                print("✅ Successfully registered to run on Windows startup!")
            except Exception as e:
                print(f"❌ Failed to register startup item: {e}")
            break
            
        elif choice == 'n':
            print("☑️ Startup execution declined. (You will need to run this program manually when playing TF2.)")
            break
        else:
            print("❗ Please enter Y or N.")

# ==========================================
# 3. Two-Track Server-Client Sync Logic
# ==========================================
def sync_with_server(tf2_temp_dir, do_full_download=False):
    if not os.path.exists(VAULT_DIR):
        os.makedirs(VAULT_DIR)
    if not os.path.exists(tf2_temp_dir):
        os.makedirs(tf2_temp_dir)

    vault_files = set(os.listdir(VAULT_DIR))
    temp_files = set(os.listdir(tf2_temp_dir))

    # [1] ⚡ Fast Local Restore: Vault -> temp
    for filename in vault_files - temp_files:
        shutil.copy2(os.path.join(VAULT_DIR, filename), os.path.join(tf2_temp_dir, filename))

    # [2] ⚡ Instant Upload: temp -> Vault -> Server (Includes DDoS Protection Lock)
    lock_file = os.path.join(VAULT_DIR, "init_lock.txt")
    if not os.path.exists(lock_file):
        # Prevent massive upload of old data on first run
        with open(lock_file, 'w') as f:
            f.write("Old data upload blocked.")
    else:
        for filename in temp_files - vault_files:
            temp_path = os.path.join(tf2_temp_dir, filename)
            # 512KB limit check (512 * 1024)
            if re.match(r'^[0-9a-f]{8}\.vtf$', filename) and os.path.getsize(temp_path) <= 512 * 1024:
                shutil.copy2(temp_path, os.path.join(VAULT_DIR, filename)) # Save to Vault
                try:
                    with open(temp_path, 'rb') as f:
                        requests.post(f"{SERVER_URL}/upload", files={"file": f})
                except:
                    pass # Ignore errors silently if server is down

    # [3] 🐢 Regular Download: Server -> Vault -> temp
    if do_full_download:
        try:
            response = requests.get(f"{SERVER_URL}/list", timeout=10)
            if response.status_code == 200:
                server_files = set(response.json().get("files", []))
                current_vault = set(os.listdir(VAULT_DIR))
                
                missing_files = list(server_files - current_vault)
                
                if len(missing_files) > 0:
                    print(f"📥 Found new sprays to download: {len(missing_files)}")

                    # 🌟 Smart Zip Download for 10+ missing files
                    if len(missing_files) > 10:
                        print("📦 Mass synchronization in progress. Starting zip download...")
                        res = requests.post(f"{SERVER_URL}/download_zip", json={"files": missing_files}, stream=True)
                        if res.status_code == 200:
                            zip_path = os.path.join(VAULT_DIR, "temp_download.zip")
                            with open(zip_path, 'wb') as f:
                                for chunk in res.iter_content(chunk_size=8192):
                                    f.write(chunk)
                                    
                            with zipfile.ZipFile(zip_path, 'r') as zf:
                                zf.extractall(VAULT_DIR)
                                for extracted_file in zf.namelist():
                                    shutil.copy2(os.path.join(VAULT_DIR, extracted_file), os.path.join(tf2_temp_dir, extracted_file))
                                    
                            os.remove(zip_path) 
                            print("✅ Mass zip download and application complete!")
                    
                    # Individual download for 10 or fewer files
                    else:
                        for filename in missing_files:
                            dl_res = requests.get(f"{SERVER_URL}/download/{filename}", timeout=5)
                            if dl_res.status_code == 200:
                                vault_path = os.path.join(VAULT_DIR, filename)
                                with open(vault_path, 'wb') as f:
                                    f.write(dl_res.content)
                                shutil.copy2(vault_path, os.path.join(tf2_temp_dir, filename))
        except Exception as e:
            pass 

# ==========================================
# 4. Main Execution (Optimized for First Run)
# ==========================================
if __name__ == "__main__":
    print("=" * 50)
    print("🌍 TF2 Global Spray Sync Client")
    print("=" * 50)
    
    TF2_TEMP_DIR = find_tf2_temp_path()
    if not TF2_TEMP_DIR:
        print("❌ Could not find Team Fortress 2 installation path.")
        time.sleep(5)
        sys.exit()

    check_and_add_startup()
    
    print("\n📦 Running initial sync with the server...")
    print("This may take some time depending on the number of files. Please wait.")
    
    sync_with_server(TF2_TEMP_DIR, do_full_download=True)
    
    print("✅ Initial sync complete! Switching to background mode.")
    time.sleep(2)
    
    # Hide console window
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    timer = 0 
    while True:
        if timer >= 300: # Full check every 5 mins
            sync_with_server(TF2_TEMP_DIR, do_full_download=True)
            timer = 0
        else: # Local restore & Instant upload every 10 secs
            sync_with_server(TF2_TEMP_DIR, do_full_download=False)
            
        time.sleep(10)
        timer += 10