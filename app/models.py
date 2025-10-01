USERS = """
CREATE TABLE IF NOT EXISTS users(
  user_id INTEGER PRIMARY KEY,
  session_name TEXT,
  is_logged_in INTEGER DEFAULT 0
);
"""

ADS = """
CREATE TABLE IF NOT EXISTS ads(
  user_id INTEGER PRIMARY KEY,
  message TEXT DEFAULT '',
  interval_sec INTEGER DEFAULT 1800,
  enabled INTEGER DEFAULT 0
);
"""

GROUPS = """
CREATE TABLE IF NOT EXISTS groups(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  chat_id INTEGER,
  title TEXT,
  username TEXT
);
"""

PROFILES = """
CREATE TABLE IF NOT EXISTS profiles(
  user_id INTEGER PRIMARY KEY,
  orig_first TEXT,
  orig_last TEXT,
  orig_bio TEXT,
  branded INTEGER DEFAULT 0
);
"""

