import sqlite3
import threading
from datetime import datetime, timedelta
import pytz

class Database:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.conn = sqlite3.connect('alya_bot.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.insert_default_settings()
    
    def create_tables(self):
        # Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_admin BOOLEAN DEFAULT 0,
                promoted_by INTEGER,
                promoted_on TIMESTAMP,
                duration TEXT,
                duration_end TIMESTAMP,
                FOREIGN KEY (promoted_by) REFERENCES users(user_id)
            )
        ''')
        
        # Channels table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                channel_id INTEGER PRIMARY KEY,
                channel_name TEXT,
                channel_username TEXT,
                added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                added_by INTEGER,
                invite_link TEXT,
                FOREIGN KEY (added_by) REFERENCES users(user_id)
            )
        ''')
        
        # Posts table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                content_type TEXT,
                content_data TEXT,
                caption TEXT,
                buttons TEXT,
                scheduled_time TIMESTAMP,
                is_posted BOOLEAN DEFAULT 0,
                created_by INTEGER,
                created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES channels(channel_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        ''')
        
        # Settings table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT,
                updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def insert_default_settings(self):
        default_settings = {
            'start_image': 'false',
            'help_image': 'false',
            'settings_image': 'false',
            'alive_image': 'false',
            'start_text': 'ʜᴇʏ {mention}\nɪ ᴀᴍ Alya ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɴɪᴍᴇ ᴛʜᴇᴍᴇ ʙᴏᴛ ᴛʜᴀᴛ ʜᴇʟᴘs ʏᴏᴜ ᴛᴏ ᴩᴏꜱᴛ ʏᴏᴜʀ ᴄᴏɴᴛᴇɴᴛ ɪɴ yᴏᴜʀ ᴄʜᴀɴɴᴇʟ ⚡\n\n────────────────────\n➲ ʜɪᴛ ᴛʜᴇ /help ʙᴜᴛᴛᴏɴ ꜰᴏʀ ᴍᴏʀᴇ ᴅᴇᴛᴀɪʟꜱ.',
            'help_text': '🌸 ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅꜱ:\n\n✦ ᴄʜᴀɴɴᴇʟ ᴄᴏɴᴛʀᴏʟꜱ:\n/addch - ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ\n/delch - ᴅᴇʟᴇᴛᴇ ᴄʜᴀɴɴᴇʟ\n/listch - ᴠɪᴇᴡ ᴄʜᴀɴɴᴇʟꜱ\n\n✦ ᴩᴏꜱᴛɪɴɢ ꜱyꜱᴛᴇᴍ:\n/post - ᴄʀᴇᴀᴛᴇ/ᴇᴅɪᴛ ᴄʜᴀɴɴᴇʟ ᴩᴏꜱᴛꜱ\n\n✦ ᴀᴅᴍɪɴ ᴩᴀɴᴇʟ:\n/settings - ᴍᴀɴᴀɢᴇ ʙᴏᴛ ꜱᴇᴛᴛɪɴɢꜱ\n/promote - ᴩʀᴏᴍᴏᴛᴇ ᴀ ᴜꜱᴇʀ ᴛᴏ ᴀᴅᴍɪɴ\n/demote - ᴅᴇᴍᴏᴛᴇ ᴀᴅᴍɪɴ\n\n✦ ᴍɪꜱᴄ:\n/alive - ᴄʜᴇᴄᴋ ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ\n/ping - ʙᴏᴛ ᴜᴩᴛɪᴍᴇ\n/help - ꜱʜᴏᴡ ᴛʜɪꜱ ʜᴇʟᴩ'
        }
        
        for key, value in default_settings.items():
            self.cursor.execute('''
                INSERT OR IGNORE INTO settings (setting_key, setting_value)
                VALUES (?, ?)
            ''', (key, value))
        self.conn.commit()
    
    # User operations
    def add_user(self, user_id, username, first_name, last_name):
        self.cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        self.conn.commit()
    
    def get_user(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()
    
    def is_admin(self, user_id):
        self.cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else False
    
    def is_owner(self, user_id):
        return user_id == 5373577888
    
    def promote_user(self, user_id, promoted_by, duration=None, duration_end=None):
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
        
        self.cursor.execute('''
            UPDATE users SET 
                is_admin = 1,
                promoted_by = ?,
                promoted_on = ?,
                duration = ?,
                duration_end = ?
            WHERE user_id = ?
        ''', (promoted_by, current_time, duration, duration_end, user_id))
        self.conn.commit()
    
    def demote_user(self, user_id):
        self.cursor.execute('''
            UPDATE users SET 
                is_admin = 0,
                promoted_by = NULL,
                promoted_on = NULL,
                duration = NULL,
                duration_end = NULL
            WHERE user_id = ?
        ''', (user_id,))
        self.conn.commit()
    
    def get_all_admins(self):
        self.cursor.execute('''
            SELECT user_id, username, first_name, last_name, promoted_on, 
                   promoted_by, duration, duration_end 
            FROM users WHERE is_admin = 1
        ''')
        return self.cursor.fetchall()
    
    # Channel operations
    def add_channel(self, channel_id, channel_name, channel_username, added_by, invite_link=None):
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO channels 
            (channel_id, channel_name, channel_username, added_on, added_by, invite_link)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (channel_id, channel_name, channel_username, current_time, added_by, invite_link))
        self.conn.commit()
    
    def remove_channel(self, channel_id):
        self.cursor.execute('DELETE FROM channels WHERE channel_id = ?', (channel_id,))
        self.conn.commit()
    
    def get_channel(self, channel_id):
        self.cursor.execute('SELECT * FROM channels WHERE channel_id = ?', (channel_id,))
        return self.cursor.fetchone()
    
    def get_all_channels(self):
        self.cursor.execute('SELECT * FROM channels ORDER BY added_on DESC')
        return self.cursor.fetchall()
    
    # Settings operations
    def get_setting(self, key):
        self.cursor.execute('SELECT setting_value FROM settings WHERE setting_key = ?', (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def set_setting(self, key, value):
        self.cursor.execute('''
            INSERT OR REPLACE INTO settings (setting_key, setting_value, updated_on)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        self.conn.commit()
    
    # Post operations
    def add_post(self, channel_id, content_type, content_data, caption, buttons, scheduled_time, created_by):
        self.cursor.execute('''
            INSERT INTO posts 
            (channel_id, content_type, content_data, caption, buttons, scheduled_time, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (channel_id, content_type, content_data, caption, buttons, scheduled_time, created_by))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_post(self, post_id):
        self.cursor.execute('SELECT * FROM posts WHERE post_id = ?', (post_id,))
        return self.cursor.fetchone()
    
    def update_post(self, post_id, **kwargs):
        for key, value in kwargs.items():
            self.cursor.execute(f'UPDATE posts SET {key} = ? WHERE post_id = ?', (value, post_id))
        self.conn.commit()
    
    def delete_post(self, post_id):
        self.cursor.execute('DELETE FROM posts WHERE post_id = ?', (post_id,))
        self.conn.commit()
    
    def get_channel_posts(self, channel_id):
        self.cursor.execute('''
            SELECT * FROM posts WHERE channel_id = ? ORDER BY created_on DESC
        ''', (channel_id,))
        return self.cursor.fetchall()
    
    def get_scheduled_posts(self):
        self.cursor.execute('''
            SELECT * FROM posts WHERE is_posted = 0 AND scheduled_time IS NOT NULL
        ''')
        return self.cursor.fetchall()

# Create singleton instance
db = Database()
