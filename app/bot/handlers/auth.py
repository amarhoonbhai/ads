import os, re, asyncio
from pyrogram import filters, types
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid
from ..runtime import bot
from ...state import auth_states, AuthState
from ...repositories.users_repo import get_or_create_user, update_login_status
from ...services.user_session import ensure_client_connected
from ...services.branding import brand_profile, revert_to_original
from ...services.profile_guard import start_profile_guard, stop_profile_guard

@bot.on_message(filters.command("login"))
async def login_cmd(_, m: types.Message):
    uid = m.from_user.id
    session_name = get_or_create_user(uid)
    auth_states[uid] = AuthState(stage="phone", session_name=session_name)
    await m.reply("📱 Send your phone number in international format (e.g. +9198xxxxxx).")

@bot.on_message(filters.command("logout"))
async def logout_cmd(_, m: types.Message):
    uid = m.from_user.id
    stop_profile_guard(uid)  # stop guard first
    # revert to original profile if possible
    c = await ensure_client_connected(uid)
    if c:
        await revert_to_original(c, uid)
    # disconnect + delete session file
    try:
        if c:
            await c.disconnect()
    except Exception:
        pass
    sess_file = f"{get_or_create_user(uid)}.session"
    try:
        if os.path.exists(sess_file): os.remove(sess_file)
    except Exception:
        pass
    update_login_status(uid, False)
    await m.reply("✅ Logged out, profile reverted, and session removed.")

@bot.on_message(filters.text & ~filters.command([
    "login","logout","setad","setinterval","addgroup","delgroup","listgroups",
    "startads","stopads","status","broadcastnow","adminbroadcast"
]))
async def otp_flow(_, m: types.Message):
    uid = m.from_user.id
    st = auth_states.get(uid)
    if not st: return

    from pyrogram import Client
    from ...config import WORKDIR, API_ID, API_HASH

    # phone
    if st.stage == "phone":
        phone = m.text.strip()
        st.phone = phone
        c = Client(st.session_name, api_id=API_ID, api_hash=API_HASH, workdir=WORKDIR, in_memory=False)
        await c.connect()
        try:
            sent = await c.send_code(phone)
            st.phone_code_hash = sent.phone_code_hash
            st.stage = "code"
            await m.reply("🔐 Enter the code you received (just the digits).")
        except PhoneNumberInvalid:
            await m.reply("❌ Invalid phone number. Try /login again.")
            await c.disconnect(); auth_states.pop(uid, None)
        except Exception as e:
            await m.reply(f"❌ Could not send code: {e}")
            await c.disconnect(); auth_states.pop(uid, None)
        return

    # code
    if st.stage == "code":
        code = re.sub(r"\D", "", m.text.strip())
        c = Client(st.session_name, api_id=API_ID, api_hash=API_HASH, workdir=WORKDIR, in_memory=False)
        await c.connect()
        try:
            await c.sign_in(st.phone, code, phone_code_hash=st.phone_code_hash)
            update_login_status(uid, True)
            auth_states.pop(uid, None)
            # brand + guard
            await brand_profile(c, uid)
            start_profile_guard(uid)
            await m.reply("✅ Logged in! Profile branded. You can now /addgroup and /startads.")
            return
        except SessionPasswordNeeded:
            st.stage = "password"; await m.reply("🔑 2FA is on. Send your **password**.")
            await c.disconnect(); return
        except PhoneCodeInvalid:
            await m.reply("❌ Incorrect code. Send the correct code."); await c.disconnect(); return
        except Exception as e:
            await m.reply(f"❌ Login failed: {e}")
            await c.disconnect(); auth_states.pop(uid, None)
            return

    # 2FA password
    if st.stage == "password":
        pwd = m.text
        c = Client(st.session_name, api_id=API_ID, api_hash=API_HASH, workdir=WORKDIR, in_memory=False)
        await c.connect()
        try:
            await c.check_password(pwd)
            update_login_status(uid, True)
            auth_states.pop(uid, None)
            await brand_profile(c, uid)
            start_profile_guard(uid)
            await m.reply("✅ Logged in with 2FA! Profile branded. You can now /addgroup and /startads.")
        except Exception as e:
            await m.reply(f"❌ 2FA failed: {e}")
            await c.disconnect(); auth_states.pop(uid, None)
          
