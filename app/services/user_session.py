import os
from pyrogram import Client
from ..config import API_ID, API_HASH, WORKDIR
from ..state import user_clients
from ..repositories.users_repo import get_or_create_user

async def get_user_client(user_id: int) -> Client | None:
    if user_id in user_clients:
        return user_clients[user_id]
    session_name = get_or_create_user(user_id)
    c = Client(session_name, api_id=API_ID, api_hash=API_HASH, workdir=WORKDIR, in_memory=False)
    try:
        await c.connect()
        if await c.get_me():
            user_clients[user_id] = c
            return c
    except Exception:
        pass
    await c.disconnect()
    return None

async def ensure_client_connected(user_id: int) -> Client | None:
    c = user_clients.get(user_id)
    if c:
        if c.is_connected:
            return c
        try:
            await c.connect()
            return c
        except Exception:
            return None
    return await get_user_client(user_id)

async def disconnect_and_cleanup(user_id: int):
    c = user_clients.pop(user_id, None)
    if c:
        try:
            await c.disconnect()
        except Exception:
            pass
    # session file path lives in users table; caller removes file if desired
  
