# webhook-repo
# webhook-repo

This repository contains the backend and UI implementation for the TechStaX Developer Assessment task.

The application receives GitHub webhook events, processes minimal required data, stores it in MongoDB, and displays the latest events on a UI that refreshes every 15 seconds.

---

## Tech Stack
- Python
- Flask
- GitHub Webhooks
- MongoDB Atlas
- PyMongo
- HTML & Vanilla JavaScript
- ngrok
- python-dotenv

---

## Application Flow

1. GitHub events (Push, Pull Request, Merge) are triggered from the `action-repo`
2. Events are sent to the Flask `/webhook` endpoint via GitHub Webhooks
3. The backend extracts only minimal required data:
   - Author
   - Branch names
   - Timestamp
4. Processed data is stored in MongoDB
5. The UI polls the backend `/events` API every 15 seconds
6. Only new events are returned and rendered (no duplicates)

---

## MongoDB Schema

```json
{
  "event_type": "push | pull_request | merge",
  "author": "string",
  "from_branch": "string (optional)",
  "to_branch": "string",
  "timestamp": "ISO 8601 UTC string"
}
