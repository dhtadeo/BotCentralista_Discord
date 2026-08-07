import os
import json
import sqlite3

class LogWriter:
    def __init__(self):
        self.logs_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.logs_dir, "bc_logs.db")
        self.root_dir = os.path.dirname(self.logs_dir)
        self.config_path = os.path.join(self.root_dir, "config.json")
        self.ignored_texts = self._load_ignored_texts()
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS servers (
                    server_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    icon TEXT,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS channels (
                    channel_id INTEGER PRIMARY KEY,
                    server_id INTEGER,
                    name TEXT NOT NULL,
                    type TEXT,
                    created_at TEXT,
                    FOREIGN KEY (server_id) REFERENCES servers(server_id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    icon TEXT,
                    is_bot INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY,
                    content TEXT,
                    attachments TEXT,
                    user_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    server_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (channel_id) REFERENCES channels(channel_id) ON DELETE CASCADE,
                    FOREIGN KEY (server_id) REFERENCES servers(server_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
                CREATE INDEX IF NOT EXISTS idx_messages_channel_id ON messages(channel_id);
                CREATE INDEX IF NOT EXISTS idx_messages_server_id ON messages(server_id);
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[LogWriter] ⚠️ Error setting up database SQLite: {e}")

    def _load_ignored_texts(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("ignored_texts", [])
        except Exception as e:
            return []

    def _should_ignore(self, content):
        if not content: return False
        return any(ignored.lower() in content.lower() for ignored in self.ignored_texts)

    def write_log(self, message):
        content = ' '.join(message.content.split()) if message.content else ""
        has_attachments = bool(message.attachments)

        if not content and not has_attachments: return
        if content and self._should_ignore(content): return

        server_id = message.guild.id if message.guild else 0
        global_name = getattr(message.author, 'global_name', None) or message.author.name
        global_avatar = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
        created_at_user = message.author.created_at.strftime('%Y-%m-%d %H:%M:%S')
        attachments_json = json.dumps([a.url for a in message.attachments] if has_attachments else [], ensure_ascii=False)
        created_at_msg = message.created_at.strftime('%Y-%m-%d %H:%M:%S')

        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            # 1. Update servers
            if message.guild:
                cursor.execute("""
                    INSERT INTO servers (server_id, name, icon, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(server_id) DO UPDATE SET
                        name = excluded.name,
                        icon = excluded.icon;
                """, (
                    message.guild.id, 
                    message.guild.name, 
                    message.guild.icon.url if message.guild.icon else None, 
                    message.guild.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ))
            else:
                cursor.execute("""
                    INSERT OR IGNORE INTO servers (server_id, name, icon, created_at)
                    VALUES (0, 'Mensajes Directos', NULL, ?)
                """, (created_at_msg,))

            # 2. Update channels
            cursor.execute("""
                INSERT INTO channels (channel_id, server_id, name, type, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET
                    name = excluded.name,
                    type = excluded.type;
            """, (
                message.channel.id,
                server_id,
                getattr(message.channel, 'name', "Mensaje Directo"),
                str(message.channel.type),
                message.channel.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ))

            # 3. Update users
            cursor.execute("""
                INSERT INTO users (user_id, name, username, icon, is_bot, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    name = excluded.name,
                    username = excluded.username,
                    icon = excluded.icon;
            """, (
                message.author.id,
                global_name,
                message.author.name,
                global_avatar,
                1 if message.author.bot else 0,
                created_at_user
            ))

            # 4. Update messages
            cursor.execute("""
                INSERT INTO messages (message_id, content, attachments, user_id, channel_id, server_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(message_id) DO UPDATE SET
                    content = excluded.content,
                    attachments = excluded.attachments;
            """, (
                message.id,
                content,
                attachments_json,
                message.author.id,
                message.channel.id,
                server_id,
                created_at_msg
            ))

            conn.commit()
            
        except Exception as e:
            print(f"[LogWriter] ❌ Error writing to SQLite database: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
