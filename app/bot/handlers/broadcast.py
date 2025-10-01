from pyrogram import filters, types
from ..runtime import bot
from ...config import ADMIN_USER_ID
from ...services.broadcaster import broadcast_to_groups
from contextlib import closing
from ...db import connect

@bot.on_message(filters.command("broadcastnow"))
async def broadcastnow_cmd(_, m: types.Message):
    uid = m.from_user.id
    args = m.text.split(maxsplit=1)
    if len(args) == 1 or not args[1].strip():
        await m.reply("📣 Usage: `/broadcastnow Your message to all groups`"); return
    sent = await broadcast_to_groups(uid, args[1].strip())
    await m.reply(f"✅ Broadcast sent to {sent} groups.")

@bot.on_message(filters.command("adminbroadcast"))
async def admin_broadcast_cmd(_, m: types.Message):
    if m.from_user.id != ADMIN_USER_ID: return
    args = m.text.split(maxsplit=1)
    if len(args) == 1: await m.reply("Usage: `/adminbroadcast text`"); return
    text = args[1]
    with closing(connect()) as conn:
        ids = [r[0] for r in conn.execute("SELECT user_id FROM users").fetchall()]
    sent = 0
    for uid in ids:
        try:
            await bot.send_message(uid, text); sent += 1
        except Exception:
            pass
    await m.reply(f"✅ Admin broadcast sent to {sent} users.")
  
