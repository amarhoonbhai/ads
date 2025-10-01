import asyncio
from pyrogram.errors import FloodWait
from ..config import IST
from ..state import profile_tasks
from ..repositories import profiles_repo
from .user_session import ensure_client_connected
from .branding import compute_targets

async def profile_guard_loop(user_id: int):
    try:
        while True:
            c = await ensure_client_connected(user_id)
            if c is None:
                await asyncio.sleep(10)
                continue

            try:
                row = profiles_repo.get_profile(user_id)
                if not row or row[3] != 1:  # not branded
                    await asyncio.sleep(60); continue

                orig_first, orig_last, _, _ = row
                tgt_first, tgt_last, tgt_bio = compute_targets(orig_first or "", orig_last or "")
                me = await c.get_me()
                chat_me = await c.get_chat("me")
                cur_first = (me.first_name or "").strip()
                cur_last  = (me.last_name or "").strip()
                cur_bio   = (chat_me.bio or "").strip()

                if (cur_first != tgt_first) or (cur_last != tgt_last) or (cur_bio != tgt_bio):
                    await c.update_profile(first_name=tgt_first, last_name=tgt_last, bio=tgt_bio)

            except FloodWait as e:
                await asyncio.sleep(e.value + 2)
            except Exception:
                pass

            await asyncio.sleep(60)
    except asyncio.CancelledError:
        return

def start_profile_guard(user_id: int):
    if user_id in profile_tasks and not profile_tasks[user_id].done():
        return
    profile_tasks[user_id] = asyncio.create_task(profile_guard_loop(user_id))

def stop_profile_guard(user_id: int):
    t = profile_tasks.get(user_id)
    if t and not t.done():
        t.cancel()
      
