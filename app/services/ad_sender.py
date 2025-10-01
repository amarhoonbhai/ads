import asyncio
from datetime import datetime
from pyrogram.errors import FloodWait, ChatAdminRequired
from ..config import IST, WINDOW_END_H
from ..state import ad_tasks
from ..utils.timewin import in_window, next_window_start
from ..repositories.ads_repo import get_ad
from ..repositories.groups_repo import list_groups
from .user_session import ensure_client_connected

async def ad_sender_loop(user_id: int):
    try:
        while True:
            now = datetime.now(IST)
            if not in_window(now):
                nxt = next_window_start(now)
                await asyncio.sleep(max(5, (nxt - now).total_seconds()))
                continue

            ad = get_ad(user_id)
            if not ad["enabled"] or not ad["message"]:
                await asyncio.sleep(5); continue

            c = await ensure_client_connected(user_id)
            if not c:
                await asyncio.sleep(10); continue

            groups = list_groups(user_id)
            if not groups:
                await asyncio.sleep(10); continue

            for (chat_id, title, username) in groups:
                try:
                    await c.send_message(chat_id, ad["message"])
                except FloodWait as e:
                    await asyncio.sleep(e.value + 2)
                except ChatAdminRequired:
                    continue
                except Exception:
                    continue

            # sleep until next tick or window end
            sleep_sec = max(10, int(ad["interval_sec"]))
            now2 = datetime.now(IST)
            end_today = now2.replace(hour=WINDOW_END_H, minute=0, second=0, microsecond=0)
            remaining = (end_today - now2).total_seconds()
            await asyncio.sleep(min(sleep_sec, max(5, int(remaining))))
    except asyncio.CancelledError:
        return

def start_user_ads(user_id: int):
    if user_id in ad_tasks and not ad_tasks[user_id].done():
        return
    ad_tasks[user_id] = asyncio.create_task(ad_sender_loop(user_id))

def stop_user_ads(user_id: int):
    t = ad_tasks.get(user_id)
    if t and not t.done():
        t.cancel()
      
