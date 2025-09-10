import praw, json

with open("config.json") as f:
    creds = json.load(f)

reddit = praw.Reddit(
    client_id=creds["client_id"],
    client_secret=creds["client_secret"],
    username=creds["username"],
    password=creds["password"],
    user_agent=creds["user_agent"],
)

try:
    print("Authenticated as:", reddit.user.me())
except Exception as e:
    print("Error:", e)