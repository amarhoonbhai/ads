from pyrogram.errors import FloodWait
import asyncio
from ..config import BRAND_SUFFIX, BRAND_BIO
from ..repositories import profiles_repo

def compute_targets(orig_first: str, orig_last: str):
    first = (orig_first or "User").strip() or "User"
    last = ((orig_last or "").strip() + BRAND_SUFFIX).strip()
    if len(last) > 64:
        last = last[:64]
    bio = BRAND_BIO[:70] if len(BRAND_BIO) > 70 else BRAND_BIO
    return first, last, bio

async def brand_profile(c, user_id: int):
    try:
        me = await c.get_me()
        chat_me = await c.get_chat("me")
        orig_first = (me.first_name or "").strip()
        orig_last  = (me.last_name or "").strip()
        orig_bio   = (chat_me.bio or "").strip()

        # save originals
        profiles_repo.save_original_profile(user_id, orig_first, orig_last, orig_bio, branded=0)

        row = profiles_repo.get_profile(user_id)
        branded = row and row[3] == 1
        if branded:
            return

        tgt_first, tgt_last, tgt_bio = compute_targets(orig_first, orig_last)
        await c.update_profile(first_name=tgt_first, last_name=tgt_last, bio=tgt_bio)
        profiles_repo.mark_branded(user_id, True)
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
    except Exception:
        pass

async def revert_to_original(c, user_id: int) -> bool:
    try:
        row = profiles_repo.get_profile(user_id)
        if not row:
            return False
        orig_first, orig_last, orig_bio, _ = row
        await c.update_profile(first_name=(orig_first or "User"), last_name=(orig_last or ""), bio=(orig_bio or ""))
        profiles_repo.mark_branded(user_id, False)
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        return False
    except Exception:
        return False
      
