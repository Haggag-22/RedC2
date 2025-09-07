from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Agent(db.Model):
    __tablename__ = "Agents"
    agent_id = db.Column(db.String, primary_key=True)
    hostname = db.Column(db.String)
    last_seen = db.Column(db.DateTime)
    status = db.Column(db.String)

class Command(db.Model):
    __tablename__ = "Commands"
    id = db.Column(db.Integer, primary_key=True)  # unique command ID
    agent_id = db.Column(db.String, db.ForeignKey("Agents.agent_id"))
    command = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default="Queued")  # Queued / Completed
    result = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    
class ProcessedPost(db.Model):
    __tablename__ = "Processed Posts"
    post_id = db.Column(db.String, primary_key=True)   # Reddit post ID
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)


