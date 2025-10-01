import os
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

WORKDIR = os.path.abspath(".")
RUNTIME_DIR = os.path.join(WORKDIR, "runtime")
SESSIONS_DIR = os.path.join(RUNTIME_DIR, "sessions")
LOGS_DIR = os.path.join(RUNTIME_DIR, "logs")
DB_PATH = os.path.join(RUNTIME_DIR, "db.sqlite3")

os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Time settings
IST = ZoneInfo("Asia/Kolkata")
WINDOW_START_H = 6     # 06:00 IST
WINDOW_END_H = 12      # 12:00 IST (exclusive)

# Branding
BRAND_SUFFIX = " — Via @SpinifyAdsBot"
BRAND_BIO = "#1 Free Ads Bot — Join @PhiloBots"
