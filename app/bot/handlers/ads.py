from pyrogram import filters, types
from ..runtime import bot
from ...repositories.ads_repo import set_ad
from ...utils.intervals import parse_interval_to_seconds

@bot.on_message(filters.command("setad"))
async def setad_cmd(_, m: types.Message):
    uid = m.from_user.id
    args = m.text.split(maxsplit=1)
    if len(args) == 1:
        await m.reply("✍️ Usage:\n`/setad Your ad text here`"); return
    set_ad(uid, message=args[1].strip())
    await m.reply("✅ Ad message saved.")

@bot.on_message(filters.command("setinterval"))
async def setinterval_cmd(_, m: types.Message):
    uid = m.from_user.id
    args = m.text.split(maxsplit=1)
    if len(args) == 1:
        await m.reply("⏱️ Usage:\n`/setinterval 20m` | `45m` | `1h`"); return
    seconds = parse_interval_to_seconds(args[1])
    if not seconds or seconds < 10:
        await m.reply("❌ Invalid interval. Examples: `20m`, `45m`, `1h`"); return
    set_ad(uid, interval_sec=seconds)
    await m.reply(f"✅ Interval set to {seconds} seconds.")
  
