from pyrogram import Client
from ..config import API_ID, API_HASH, BOT_TOKEN, WORKDIR

# Single bot instance imported by handlers
bot = Client("spinify_ads_manager_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workdir=WORKDIR)
