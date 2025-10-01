from datetime import datetime
from pyrogram import filters, types
from ..runtime import bot
from ...config import IST
from ...repositories.ads_repo import get_ad, set_ad
from ...repositories.groups_repo import list_groups
from ...state import ad_tasks, profile_tasks
from ...utils.timewin import in_window
from ...services.ad_sender import start_user_ads, stop_user_ads
from ...services.user_session import get_user_client
from ...services.profile_guard import start_profile_guard

@bot.on_message(filters.command("startads"))
async def startads_cmd(_, m: types.Message):
    uid = m.from_user.id
    ad = get_ad(uid)
    if not ad["message"]:
        await m.reply("✍️ Set your ad first with `/setad ...`"); return
    set_ad(uid, enabled=True)
    start_user_ads(uid)
    start_profile_guard(uid)
    await m.reply("🚀 Ads started. (Posts only between 06:00–12:00 IST)")

@bot.on_message(filters.command("stopads"))
async def stopads_cmd(_, m: types.Message):
    uid = m.from_user.id
    stop_user_ads(uid)
    set_ad(uid, enabled=False)
    await m.reply("⛔ Ads stopped.")

@bot.on_message(filters.command("status"))
async def status_cmd(_, m: types.Message):
    uid = m.from_user.id
    ad = get_ad(uid)
    gcount = len(list_groups(uid))
    running = uid in ad_tasks and not ad_tasks[uid].done()
    pg_running = uid in profile_tasks and not profile_tasks[uid].done()
    now = datetime.now(IST)
    txt = (
        f"**Status**\n"
        f"Logged in: {'✅' if (await get_user_client(uid)) else '❌'}\n"
        f"Ad enabled: {'✅' if ad['enabled'] else '❌'}\n"
        f"Interval: {ad['interval_sec']} sec\n"
        f"Groups: {gcount}\n"
        f"Ad loop: {'✅' if running else '❌'}\n"
        f"Profile guard: {'✅' if pg_running else '❌'}\n"
        f"IST: {now.strftime('%H:%M')} | In window 06–12: {'✅' if in_window(now) else '❌'}\n"
    )
    await m.reply(txt)
  
