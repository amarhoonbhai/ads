from pyrogram import filters, types
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
from ..runtime import bot
from ...config import IST
from datetime import datetime

def menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("/login"), KeyboardButton("/logout")],
            [KeyboardButton("/setad Example offer!"), KeyboardButton("/setinterval 20m")],
            [KeyboardButton("/addgroup @yourgroup"), KeyboardButton("/listgroups")],
            [KeyboardButton("/startads"), KeyboardButton("/stopads")],
            [KeyboardButton("/status"), KeyboardButton("/broadcastnow Send your text...")],
        ],
        resize_keyboard=True
    )

@bot.on_message(filters.command("start"))
async def start_cmd(_, m: types.Message):
    now = datetime.now(IST).strftime("%H:%M")
    text = (
        "✨ **Spinify Ads UserBot**\n"
        "_Run ads from your own Telegram account — safely & on schedule._\n\n"
        "**What you can do**\n"
        "• Login (/login)\n"
        "• Set ad (/setad)\n"
        "• Interval (/setinterval 20m|40m|60m)\n"
        "• Add groups (/addgroup)\n"
        "• Start/Stop (/startads /stopads)\n"
        "• Blast once (/broadcastnow <text>)\n"
        "• Status (/status)\n\n"
        "🕰️ IST now: **" + now + "** | Window: **06:00–12:00 IST**\n"
        "🎛️ Branding enforced automatically.\n"
    )
    await m.reply(text, disable_web_page_preview=True, reply_markup=menu_kb())
  
