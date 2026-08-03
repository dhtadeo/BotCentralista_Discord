import os
import json

class LogWriter:
    def __init__(self):
        self.logs_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.messages_log = os.path.join(self.logs_dir, "messages.json")
        self.users_log = os.path.join(self.logs_dir, "users.json")
        self.servers_log = os.path.join(self.logs_dir, "servers.json")
        self.channels_log = os.path.join(self.logs_dir, "channels.json")
        
        self.root_dir = os.path.dirname(self.logs_dir)
        self.config_path = os.path.join(self.root_dir, "config.json")
        self.ignored_texts = self._load_ignored_texts()
        
        self._init_files()

    def _init_files(self):
        files_defaults = [
            (self.messages_log, []),
            (self.users_log, {}),
            (self.servers_log, {}),
            (self.channels_log, {})
        ]
        for file_path, default_data in files_defaults:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=4)

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

    def _read_json(self, filepath, is_dict=False):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {} if is_dict else []

    def _write_json(self, filepath, data):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[LogWriter] ❌ Error writing to {filepath}: {e}")

    def write_json_log(self, message):
        content = ' '.join(message.content.split()) if message.content else ""
        has_attachments = bool(message.attachments)

        if not content and not has_attachments:
            return

        if content and self._should_ignore(content):
            return

        server_id = message.guild.id if message.guild else None
        
        new_message_entry = {
            "message_id": message.id,
            "content": content,
            "attachments": [a.url for a in message.attachments] if has_attachments else [],
            "user_id": message.author.id,
            "channel_id": message.channel.id,
            "server_id": server_id,
            "created_at": message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

        messages_data = self._read_json(self.messages_log, is_dict=False)
        messages_data.append(new_message_entry)
        self._write_json(self.messages_log, messages_data)

        users_data = self._read_json(self.users_log, is_dict=True)
        user_id_str = str(message.author.id)
        
        global_name = getattr(message.author, 'global_name', None) or message.author.name
        global_avatar = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url

        users_data[user_id_str] = {
            "user_id": message.author.id,
            "name": global_name,
            "username": message.author.name,
            "icon": global_avatar,
            "is_bot": message.author.bot,
            "created_at": message.author.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        self._write_json(self.users_log, users_data)

        if message.guild:
            servers_data = self._read_json(self.servers_log, is_dict=True)
            server_id_str = str(message.guild.id)
            
            servers_data[server_id_str] = {
                "server_id": message.guild.id,
                "name": message.guild.name,
                "icon": message.guild.icon.url if message.guild.icon else None,
                "created_at": message.guild.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            self._write_json(self.servers_log, servers_data)

        channels_data = self._read_json(self.channels_log, is_dict=True)
        channel_id_str = str(message.channel.id)
        
        channels_data[channel_id_str] = {
            "channel_id": message.channel.id,
            "server_id": server_id,
            "name": getattr(message.channel, 'name', "Mensaje Directo"),
            "type": str(message.channel.type),
            "created_at": message.channel.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        self._write_json(self.channels_log, channels_data)
