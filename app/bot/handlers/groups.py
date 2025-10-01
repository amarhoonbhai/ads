import asyncio
from pyrogram import filters, types
from pyrogram.errors import FloodWait
from ..runtime import bot
from ...repositories.groups_repo import add_group, list_groups, del_group
from ...services.user_session import ensure_client_connected

@bot.on_message(filters.command("addgroup"))
async def addgroup_cmd(_, m: types.Message):
    uid = m.from_user.id
    args = m.text.split(maxsplit=1)
    if len(args) == 1:
        await m.reply("➕ Usage:\n`/addgroup @publicgroup`\n`/addgroup https://t.me/+invite_link`\n`/addgroup -1001234567890`")
        return

    key = args[1].strip()
    c = await ensure_client_connected(uid)
    if not c:
        await m.reply("⚠️ Not logged in. Use /login first."); return

    try:
        if key.startswith("@") or "t.me" in key or "+" in key:
            chat = await c.join_chat(key)
        else:
            try:
                chat = await c.get_chat(int(key))
            except ValueError:
                chat = await c.join_chat(key)
        await asyncio.sleep(0.4)
        chat = await c.get_chat(chat.id)
        add_group(uid, chat.id, chat.title or "", chat.username or "")
        await m.reply(f"✅ Added: **{chat.title or chat.id}**")
    except FloodWait as e:
        await asyncio.sleep(e.value + 2); await m.reply("⏳ Rate limited. Try again.")
    except Exception as e:
        await m.reply(f"❌ Could not add: {e}")

@bot.on_message(filters.command("delgroup"))
async def delgroup_cmd(_, m: types.Message):
    uid = m.from_user.id
    args = m.text.split(maxsplit=1)
    if len(args) == 1:
        await m.reply("🗑️ Usage: `/delgroup @groupusername` or `/delgroup -100...`"); return
    removed = del_group(uid, args[1].strip())
    await m.reply("✅ Removed." if removed else "⚠️ Not found.")

@bot.on_message(filters.command("listgroups"))
async def listgroups_cmd(_, m: types.Message):
    uid = m.from_user.id
    rows = list_groups(uid)
    if not rows:
        await m.reply("📭 No groups yet. Add with `/addgroup ...`"); return
    lines = [f"• {title or chat_id}  `{chat_id}`  {'@'+username if username else ''}" for (chat_id, title, username) in rows]
    await m.reply("**Your Groups:**\n" + "\n".join(lines))
  
