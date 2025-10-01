import os, asyncio
from pyrogram import filters, types
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid
from ..runtime import bot
from ...state import auth_states, AuthState
from ...repositories.users_repo import get_or_create_user, update_login_status
from ...services.user_session import ensure_client_connected
from ...services.branding import brand_profile, revert_to_original
from ...services.profile_guard import start_profile_guard, stop_profile_guard

# ---- Helpers: version-safe sign_in + tolerant code parsing ----
async def sign_in_compat(c, phone: str, code: str, phone_code_hash: str):
    """
    Works across Pyrogram versions:
      - v2: keyword args
      - v1: positional order (phone, phone_code_hash, code)
    """
    try:
        return await c.sign_in(phone_number=phone, code=code, phone_code_hash=phone_code_hash)
    except TypeError as e:
        if "multiple values for argument 'phone_code_hash'" in str(e) or "positional" in str(e):
            return await c.sign_in(phone, phone_code_hash, code)
        raise

def normalize_code(text: str) -> str:
    """Accept formats like '1 2 2 3 3', '1-2-2-3-3', 'Code: 1 2 2 3 3'."""
    import re
    digits = re.findall(r"\d", text)
    return "".join(digits)[:10]  # cap just in case

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
        try:
            await c.disconnect()
        except Exception:
            pass

    # delete session file
    sess_file = f"{get_or_create_user(uid)}.session"
    try:
        if os.path.exists(sess_file):
            os.remove(sess_file)
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
    if not st:
        return

    from pyrogram import Client
    from ...config import WORKDIR, API_ID, API_HASH

    # ── Stage: phone ──
    if st.stage == "phone":
        phone = m.text.strip()
        st.phone = phone
        c = Client(st.session_name, api_id=API_ID, api_hash=API_HASH, workdir=WORKDIR, in_memory=False)
        await c.connect()
        try:
            sent = await c.send_code(phone)
            st.phone_code_hash = sent.phone_code_hash
            st.stage = "code"
            await m.reply("🔐 Enter the code you received (you can send it spaced like `1 2 2 3 3`).")
        except PhoneNumberInvalid:
            await m.reply("❌ Invalid phone number. Try /login again.")
            auth_states.pop(uid, None)
        except Exception as e:
            await m.reply(f"❌ Could not send code: {e}")
            auth_states.pop(uid, None)
        finally:
            try:
                await c.disconnect()
            except Exception:
                pass
        return

    # ── Stage: code (OTP) ──
    if st.stage == "code":
        code = normalize_code(m.text)
        c = Client(st.session_name, api_id=API_ID, api_hash=API_HASH, workdir=WORKDIR, in_memory=False)
        await c.connect()
        try:
            if not (5 <= len(code) <= 7):  # typical 5–6 digits
                await m.reply("🔐 Please send only the code digits (e.g., `1 2 2 3 3` → `12233`).")
                await c.disconnect()
                return

            await sign_in_compat(c, st.phone, code, st.phone_code_hash)
            update_login_status(uid, True)
            auth_states.pop(uid, None)

            # brand + guard
            await brand_profile(c, uid)
            start_profile_guard(uid)

            await m.reply("✅ Logged in! Profile branded. You can now /addgroup and /startads.")
            # keep connection open; other services can reuse the session file
            return

        except SessionPasswordNeeded:
            st.stage = "password"
            await m.reply("🔑 Two-step verification is enabled. Send your **password**.")
            await c.disconnect()
            return
        except PhoneCodeInvalid:
            await m.reply("❌ Incorrect code. Send the correct code.")
            await c.disconnect()
            return
        except Exception as e:
            await m.reply(f"❌ Login failed: {e}")
            await c.disconnect()
            auth_states.pop(uid, None)
            return

    # ── Stage: password (2FA) ──
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
            await c.disconnect()
            auth_states.pop(uid, None)
            
