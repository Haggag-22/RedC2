from flask import Flask, request, jsonify
import time

app = Flask(__name__)
agents = {}   # {agent_id: last_seen_time}

processed_posts = {}


@app.route("/processed", methods=["POST"])
def mark_processed():
    data = request.get_json()
    post_id = data.get("post_id")
    agent_id = data.get("agent_id")
    if post_id and agent_id:
        if post_id not in processed_posts:
            processed_posts[post_id] = []
        if agent_id not in processed_posts[post_id]:
            processed_posts[post_id].append(agent_id)
        return jsonify({"status": "marked", "post_id": post_id, "agent_id": agent_id})
    else:
        return jsonify({"error": "No post ID or agent ID provided"}), 400


@app.route("/processed", methods=["GET"])
def list_processed():
    return jsonify(processed_posts)

@app.route("/register", methods=["POST"])  # Registar First Time
def register():
    data = request.get_json()
    agent_id = data.get("Agent Id")
    if agent_id:
        agents[agent_id] = time.time()
        print(f"[+] Agent registered: {agent_id}")
        return jsonify({"status": "registered", "agent_id": agent_id})
    else:
        return jsonify({"error": "No agent ID provided"}), 400       

@app.route("/beacon", methods=["POST"])
def beacon():
    data = request.get_json()
    agent_id = data.get("Agent Id")
    if agent_id:
        agents[agent_id] = time.time()
        print(f"[*] Heartbeat from: {agent_id}")
        return jsonify({"status": "heartbeat_received"})
    else:
        return jsonify({"error": "No agent ID provided"}), 400

@app.route("/agents", methods=["GET"])  # Separate by Alive and Dead
def list_agents():
    alive_agents = []
    dead_agents = []
    for agent in agents:
        if time.time() - agents[agent] < 120:
            alive_agents.append(agent)
        else:
            dead_agents.append(agent)
    
    output = "C2 Agent Status Dashboard\n"
    output += "=" * 50 + "\n"
    output += f"Total Agents: {len(agents)}\n\n"
    
    output += "ALIVE AGENTS:\n"
    output += "-" * 30 + "\n"
    for agent in alive_agents:
        last_seen = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(agents[agent]))
        output += f"{agent:<30} - Last Seen: {last_seen}\n"
    
    output += "\nDEAD AGENTS:\n"
    output += "-" * 30 + "\n"
    for agent in dead_agents:
        last_seen = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(agents[agent]))
        output += f"{agent:<30} - Last Seen: {last_seen}\n"
    
    return output

if __name__ == "__main__":
    print("[+] Starting C2 Server")
    app.run(host="0.0.0.0", port=5000, debug=True)