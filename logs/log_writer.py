import os
import json
from datetime import datetime

class LogWriter:
    def __init__(self):
        self.logs_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_log = os.path.join(self.logs_dir, "chat_log.json")
        
        self.root_dir = os.path.dirname(self.logs_dir)
        self.config_path = os.path.join(self.root_dir, "config.json")
        self.ignored_texts = self._load_ignored_texts()
        
        if not os.path.exists(self.json_log):
            with open(self.json_log, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _load_ignored_texts(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("ignored_texts", [])
        except Exception as e:
            print(f"[LogWriter] ⚠️ Error loading 'ignored_texts': {e}")
            return []

    def _should_ignore(self, content):
        if not content: 
            return False
        return any(ignored.lower() in content.lower() for ignored in self.ignored_texts)

    def write_json_log(self, message):
        content = ' '.join(message.content.split()) if message.content else ""
        has_attachments = bool(message.attachments)

        if not content and not has_attachments:
            return

        if content and self._should_ignore(content):
            return

        data_entry = {
            "server_id": message.guild.id if message.guild else None,
            "channel_id": message.channel.id,
            "user_id": message.author.id,
            "timestamp": message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "content": content,
            "attachments": [a.url for a in message.attachments] if has_attachments else []
        }

        try:
            with open(self.json_log, 'r+', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
                data.append(data_entry)
                
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=4)
                f.truncate()
        except Exception as e:
            print(f"[LogWriter] ❌ Error writing in JSON file: {e}")