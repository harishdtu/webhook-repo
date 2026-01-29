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

# ---------------- WEBHOOK ENDPOINT ----------------
@webhook_bp.route("/webhook", methods=["POST"])
def github_webhook():
    event_type = request.headers.get("X-GitHub-Event")
    payload = request.get_json(silent=True)

    print("✅ WEBHOOK HIT")
    print("EVENT TYPE:", event_type)

    # Ignore ping or invalid payload
    if event_type in ["ping", None] or not payload:
        return jsonify({"status": "ignored"})

    # ---------------- PUSH EVENT ----------------
    if event_type == "push":
        data = {
            "event_type": "push",
            "author": payload["pusher"]["name"],
            "to_branch": payload["ref"].split("/")[-1],
            "timestamp": payload["head_commit"]["timestamp"]
        }
        collection.insert_one(data)
        print("📌 PUSH SAVED")

    # ---------------- PULL REQUEST EVENT ----------------
    elif event_type == "pull_request":
        pr = payload.get("pull_request", {})
        action = payload.get("action")

        # Always store pull request event
        pr_data = {
            "event_type": "pull_request",
            "action": action,
            "author": pr.get("user", {}).get("login"),
            "from_branch": pr.get("head", {}).get("ref"),
            "to_branch": pr.get("base", {}).get("ref"),
            "merged": pr.get("merged", False),
            "timestamp": pr.get("updated_at") or pr.get("created_at")
        }
        collection.insert_one(pr_data)
        print("📌 PULL REQUEST SAVED")

        # Store merge event separately (brownie points)
        if action == "closed" and pr.get("merged"):
            merge_data = {
                "event_type": "merge",
                "author": pr["merged_by"]["login"],
                "from_branch": pr["head"]["ref"],
                "to_branch": pr["base"]["ref"],
                "timestamp": pr["merged_at"]
            }
            collection.insert_one(merge_data)
            print("🏆 MERGE SAVED")

    return jsonify({"status": "event received"})


# ---------------- EVENTS API (UI POLLING) ----------------
@webhook_bp.route("/events", methods=["GET"])
def get_events():
    events = list(collection.find().sort("timestamp", -1).limit(10))

    response = []

    for e in reversed(events):
        if e["event_type"] == "push":
            msg = f'{e["author"]} pushed to {e["to_branch"]} on {e["timestamp"]}'

        elif e["event_type"] == "pull_request":
            msg = (
                f'{e["author"]} submitted a pull request '
                f'from {e["from_branch"]} to {e["to_branch"]} on {e["timestamp"]}'
            )

        elif e["event_type"] == "merge":
            msg = (
                f'{e["author"]} merged branch '
                f'{e["from_branch"]} to {e["to_branch"]} on {e["timestamp"]}'
            )
        else:
            continue

        response.append({
            "message": msg,
            "timestamp": e["timestamp"]
        })

    return jsonify(response)
