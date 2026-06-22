import os
import json
from datetime import datetime

class LogWriter:
    def __init__(self):
        self.logs_dir = os.path.dirname(os.path.abspath(__file__))
        self.basic_log = os.path.join(self.logs_dir, "chat_log.txt")
        self.detailed_log = os.path.join(self.logs_dir, "chat_log_prop.txt")
        self.server_logs_dir = os.path.join(self.logs_dir, "server")
        
        self.root_dir = os.path.dirname(self.logs_dir)
        self.config_path = os.path.join(self.root_dir, "config.json")
        
        self.ignored_texts = self._load_ignored_texts()
        
        if not os.path.exists(self.basic_log):
            with open(self.basic_log, 'w', encoding='utf-8') as f:
                f.write(f"=== Log iniciado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        
        if not os.path.exists(self.detailed_log):
            with open(self.detailed_log, 'w', encoding='utf-8') as f:
                f.write(f"=== Log detallado iniciado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

        if not os.path.exists(self.server_logs_dir):
            os.makedirs(self.server_logs_dir)

    def _load_ignored_texts(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("ignored_texts", [])
        except Exception as e:
            print(f"⚠️ Error al cargar 'ignored_texts' desde config.json: {e}")
            return []

    def _should_ignore(self, content):
        if not content:
            return True
        return any(ignored.lower() in content.lower() for ignored in self.ignored_texts)

    def _clean_content(self, content):
        return ' '.join(content.split()) if content else ""

    def _get_attachments(self, message):
        if message.attachments:
            return ' '.join([a.url for a in message.attachments])
        return ""

    def write_basic_log(self, message):
        content = self._clean_content(message.content)

        if self._should_ignore(content):
            return

        attachments = self._get_attachments(message)
        log_entry = f"{content} {attachments}".strip()
        
        with open(self.basic_log, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")

    def write_detailed_log(self, message):
        content = self._clean_content(message.content)

        if self._should_ignore(content):
            return
        
        server = message.guild.name if message.guild else "[DM]"
        channel = message.channel.name if hasattr(message.channel, 'name') else "[Directo]"
        author = str(message.author)
        attachments = self._get_attachments(message)
        
        log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {server} | #{channel} | {author}: {content} {attachments}".strip()
        
        with open(self.detailed_log, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")

    def write_channel_log(self, message):
        content = self._clean_content(message.content)

        if self._should_ignore(content):
            return

        attachments = self._get_attachments(message)
        log_entry = f"{content} {attachments}".strip()
        
        if not log_entry:
            return

        if message.guild:
            server_id = str(message.guild.id)
            channel_id = str(message.channel.id)
            
            server_path = os.path.join(self.server_logs_dir, server_id)
            
            if not os.path.exists(server_path):
                os.makedirs(server_path)
                
            channel_file_path = os.path.join(server_path, f"{channel_id}.txt")
            
            with open(channel_file_path, 'a', encoding='utf-8') as f:
                f.write(f"{log_entry}\n")
        else:
            dm_path = os.path.join(self.server_logs_dir, "DMs")
            if not os.path.exists(dm_path):
                os.makedirs(dm_path)
            
            channel_id = str(message.channel.id)
            channel_file_path = os.path.join(dm_path, f"{channel_id}.txt")
            
            with open(channel_file_path, 'a', encoding='utf-8') as f:
                f.write(f"{log_entry}\n")