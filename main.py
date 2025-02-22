import random
import time
import requests
import sqlite3
import threading
from libp2p.peerstore import Peerstore

# Mastodon API Configuration
MASTODON_ACCESS_TOKEN = "your_mastodon_access_token"
MASTODON_API_BASE = "https://mastodon.example/api/v1/statuses"
MASTODON_TIMELINE_API = "https://mastodon.example/api/v1/timelines/public"

# Local SQLite storage for decentralized tasks
db = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS tasks (task_id INTEGER PRIMARY KEY, a INTEGER, b INTEGER, solved INTEGER)""")
db.commit()

# P2P Network Configuration
peerstore = Peerstore()

def fetch_tasks_from_mastodon():
    """Fetch mathematical tasks from Mastodon public timeline periodically."""
    while True:
        headers = {"Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}"}
        response = requests.get(MASTODON_TIMELINE_API, headers=headers)
        
        if response.status_code == 200:
            statuses = response.json()
            for status in statuses:
                content = status["content"]
                if "solve" in content and "+" in content:
                    parts = content.split()
                    try:
                        a = int(parts[1])
                        b = int(parts[3])
                        cursor.execute("INSERT INTO tasks (a, b, solved) VALUES (?, ?, 0)", (a, b))
                        db.commit()
                    except ValueError:
                        continue
        time.sleep(30)  # Fetch tasks every 30 seconds

def process_tasks():
    """Process tasks from the database and post results to Mastodon."""
    while True:
        cursor.execute("SELECT * FROM tasks WHERE solved=0 LIMIT 1")
        task = cursor.fetchone()
        if task:
            task_id, a, b, _ = task
            result = a + b
            cursor.execute("UPDATE tasks SET solved=1 WHERE task_id=?", (task_id,))
            db.commit()
            post_to_mastodon(f"Task {task_id} completed! {a} + {b} = {result}")
        time.sleep(10)  # Process tasks every 10 seconds

def post_to_mastodon(message):
    """Post a message to a Mastodon instance."""
    headers = {"Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}"}
    data = {"status": message}
    requests.post(MASTODON_API_BASE, headers=headers, data=data)

# Start background threads for fetching and processing tasks
threading.Thread(target=fetch_tasks_from_mastodon, daemon=True).start()
threading.Thread(target=process_tasks, daemon=True).start()

if __name__ == "__main__":
    while True:
        time.sleep(1)  # Keep the script running
