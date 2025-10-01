import asyncio
from pyrogram.errors import FloodWait
from ..repositories.groups_repo import list_groups
from .user_session import ensure_client_connected

async def broadcast_to_groups(user_id: int, text: str) -> int:
    c = await ensure_client_connected(user_id)
    if not c:
        return 0
    rows = list_groups(user_id)
    sent = 0
    for (chat_id, title, username) in rows:
        try:
            await c.send_message(chat_id, text)
            sent += 1
            await asyncio.sleep(0.2)
        except FloodWait as e:
            await asyncio.sleep(e.value + 2)
        except Exception:
            pass
    return sent
  
