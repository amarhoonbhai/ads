import os, asyncio, base64, io
from pyrogram import filters, types, raw
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid
from ..runtime import bot
from ...state import auth_states, AuthState
from ...repositories.users_repo import get_or_create_user, update_login_status
from ...services.user_session import ensure_client_connected
from ...services.branding import brand_profile, revert_to_original
from ...services.profile_guard import start_profile_guard, stop_profile_guard

# NOTE: QR login requires extra deps:
#   pip install qrcode Pillow
import qrcode

# ---- Helpers: version-safe sign_in + tolerant code parsing ----
async def sign_in_compat(c, phone: str, code: str, phone_code_hash: str):
    """
    Works across Pyrogram versions:
      - Newer (v2): sign_in(phone_number=..., code=..., phone_code_hash=...)
      - Older (v1): sign_in(phone, phone_code_hash, code)  [positional only]
    """
    try:
        return await c.sign_in(phone_number=phone, code=code, phone_code_hash=phone_code_hash)
    except TypeError as e:
        msg = str(e).lower()
        if ("multiple values for argument" in msg
            or "unexpected keyword argument" in msg
            or "positional" in msg
            or "takes" in msg):
            return await c.sign_in(phone, phone_code_hash, code)
        raise

def normalize_code(text: str) -> str:
    """Accept formats like '1 2 2 3 3', '1-2-2-3-3', 'Code: 1 2 2 3 3'."""
    import re
    digits = re.findall(r"\d", text)
    return "".join(digits)[:10]  # cap just in case

# ─────────────────────────────────────────────────────────────
# /login  (SMS/Telegram code flow)
# ─────────────────────────────────────────────────────────────
@bot.on_message(filters.command("login"))
async def login_cmd(_, m: types.Message):
    uid = m.from_user.id
    session_name = get_or_create_user(uid)
    auth_states[uid] = AuthState(stage="phone", session_name=session_name)
    await m.reply("📱 Send your phone number in international format (e.g. +9198xxxxxx).")

# ─────────────────────────────────────────────────────────────
# /loginqr  (QR scan flow via ExportLoginToken / AcceptLoginToken)
# ─────────────────────────────────────────────────────────────
@bot.on_message(filters.command("loginqr"))
async def login_qr_cmd(_, m: types.Message):
    """
    Login by scanning a Telegram QR code with the official app:
    Telegram → Settings → Devices → Link Desktop Device → scan QR shown here.
    """
    uid = m.from_user.id
    session_name = get_or_create_user(uid)

    from ...config import WORKDIR, API_ID, API_HASH
    from pyrogram import Client

    async def b64url(b: bytes) -> str:
        # Base64 URL without padding, as expected by tg://login?token=
        return base64.urlsafe_b64encode(b).decode().rstrip("=")

    async def export_token(c: Client):
        # Request a login token (handle possible DC migration)
        res = await c.invoke(raw.functions.auth.ExportLoginToken(
            api_id=int(API_ID), api_hash=str(API_HASH), except_ids=[]
        ))
        if isinstance(res, raw.types.auth.LoginToken):
            return res.token
        if isinstance(res, raw.types.auth.LoginTokenMigrateTo):
            res2 = await c.invoke(raw.functions.auth.ImportLoginToken(token=res.token))
            if isinstance(res2, raw.types.auth.LoginToken):
                return res2.token
            if isinstance(res2, raw.types.auth.LoginTokenSuccess):
                return None  # done
        if isinstance(res, raw.types.auth.LoginTokenSuccess):
            return None
        return None

    c = Client(session_name, api_id=API_ID, api_hash=API_HASH, workdir=WORKDIR, in_memory=False)
    await c.connect()
    try:
        token = await export_token(c)
        if token is None:
            update_login_status(uid, True)
            await brand_profile(c, uid)
            start_profile_guard(uid)
            await m.reply("✅ Logged in via QR!")
            return

        # Render QR with tg://login link
        link = f"tg://login?token={await b64url(token)}"
        img = qrcode.make(link)
        bio = io.BytesIO()
        img.save(bio, format="PNG"); bio.seek(0)
        await bot.send_photo(
            m.chat.id, bio,
            caption="📲 *Scan with Telegram* → *Settings → Devices → Link Desktop Device*.\nThis QR expires in ~1 minute.",
        )

        # Poll for acceptance up to ~70s
        for _ in range(35):
            await asyncio.sleep(2)
            try:
                auth = await c.invoke(raw.functions.auth.AcceptLoginToken(token=token))
                # If password_pending is True, switch to your existing 2FA stage
                if isinstance(auth, raw.types.auth.Authorization):
                    if getattr(auth, "password_pending", False):
                        s = auth_states.get(uid) or AuthState(stage="password", session_name=session_name)
                        auth_states[uid] = s
                        await m.reply("🔑 2FA is enabled. Send your *password* to finish login.")
                    else:
                        update_login_status(uid, True)
                        await brand_profile(c, uid)
                        start_profile_guard(uid)
                        await m.reply("✅ Logged in via QR! You can now /addgroup and /startads.")
                        auth_states.pop(uid, None)
                    return
            except Exception:
                # keep polling
                continue

        await m.reply("⌛ QR expired. Send /loginqr again.")
    finally:
        try:
            await c.disconnect()
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────
# /logout
# ─────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────
# OTP text flow (phone → code → password)
# ─────────────────────────────────────────────────────────────
@bot.on_message(filters.text & ~filters.command([
    "login","loginqr","logout","setad","setinterval","addgroup","delgroup","listgroups",
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
    
