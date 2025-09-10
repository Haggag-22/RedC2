import requests
import sys


SERVER_URL = "http://192.168.1.76:5555"
GREEN = "\033[92m"
RED   = "\033[91m"
BLUE  = "\033[94m"
YELLOW= "\033[93m"
RESET = "\033[0m"

def list_agents():
    response = requests.get(f"{SERVER_URL}/agents")
    data = response.json()
    
    print(RED+"----Agents-----")
    for count, a in enumerate(data, start=1):  
        print(f"{count}: {a['agent_id']}")
    


def show_agent():
    pass

def send_command():
    pass

def list_tasks(status):
    pass


def main():
    while True:
        print(GREEN+"\n--- C2 Operator Menu ---"+RESET)
        print(BLUE+"1. List agents")
        print("2. Show agent details with commands and results")
        print("3. Send command to agent")
        print("4. List queued tasks")
        print("5. List completed tasks")
        print("6. Exit"+RESET)

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