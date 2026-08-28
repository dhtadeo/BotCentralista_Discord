import os
import json

ADMIN_PREFIX = 'bc'

UNAUTHORIZED_MESSAGE = "> ❌ This command can only be used by a small amount of people. You're not allowed to use this command."

def get_authorized_users():
    admin_dir = os.path.dirname(os.path.abspath(__file__))
    cogs_dir = os.path.dirname(admin_dir)
    root_dir = os.path.dirname(cogs_dir)
    config_path = os.path.join(root_dir, "config.json")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("authorized_users", []))
    except (FileNotFoundError, json.JSONDecodeError):
        print("[AdminConfig] ⚠️ Missing config parameters.")
        return set()