import json
from datetime import datetime

MEMORY_FILE = "logs/user_habits.json"

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"habits": [], "schedule": []}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def remember_habit(message: str):
    memory = load_memory()
    memory["habits"].append({"text": message, "time": datetime.now().isoformat()})
    save_memory(memory)

def add_schedule(plan: str, time: str):
    memory = load_memory()
    memory["schedule"].append({"plan": plan, "time": time})
    save_memory(memory)
