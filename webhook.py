from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

webhook_bp = Blueprint("webhook", __name__)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)

db = client["github_events"]
collection = db["events"]

# Used to avoid re-sending already displayed events
last_served_timestamp = None


# ---------------- WEBHOOK ENDPOINT ----------------
@webhook_bp.route("/webhook", methods=["POST"])
def github_webhook():
    event_type = request.headers.get("X-GitHub-Event")
    payload = request.json

    if not payload:
        return jsonify({"error": "No payload"}), 400

    # PUSH EVENT
    if event_type == "push":
        data = {
            "event_type": "push",
            "author": payload["pusher"]["name"],
            "to_branch": payload["ref"].split("/")[-1],
            "timestamp": payload["head_commit"]["timestamp"]
        }
        collection.insert_one(data)

    # PULL REQUEST EVENT
    elif event_type == "pull_request":
        pr = payload["pull_request"]
        action = payload["action"]

        # PR opened
        if action == "opened":
            data = {
                "event_type": "pull_request",
                "author": pr["user"]["login"],
                "from_branch": pr["head"]["ref"],
                "to_branch": pr["base"]["ref"],
                "timestamp": pr["created_at"]
            }
            collection.insert_one(data)

        # PR merged (Brownie points)
        elif action == "closed" and pr["merged"]:
            data = {
                "event_type": "merge",
                "author": pr["merged_by"]["login"],
                "from_branch": pr["head"]["ref"],
                "to_branch": pr["base"]["ref"],
                "timestamp": pr["merged_at"]
            }
            collection.insert_one(data)

    return jsonify({"status": "event received"})


# ---------------- EVENTS API (UI POLLING) ----------------
@webhook_bp.route("/events", methods=["GET"])
def get_events():
    global last_served_timestamp

    query = {}
    if last_served_timestamp:
        query = {"timestamp": {"$gt": last_served_timestamp}}

    events = list(collection.find(query).sort("timestamp", 1))

    response = []

    for e in events:
        if e["event_type"] == "push":
            msg = f'{e["author"]} pushed to {e["to_branch"]} on {e["timestamp"]}'
        elif e["event_type"] == "pull_request":
            msg = f'{e["author"]} submitted a pull request from {e["from_branch"]} to {e["to_branch"]} on {e["timestamp"]}'
        elif e["event_type"] == "merge":
            msg = f'{e["author"]} merged branch {e["from_branch"]} to {e["to_branch"]} on {e["timestamp"]}'
        else:
            continue

        response.append({
            "message": msg,
            "timestamp": e["timestamp"]
        })

    if events:
        last_served_timestamp = events[-1]["timestamp"]

    return jsonify(response)
