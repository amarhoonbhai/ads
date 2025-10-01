from dataclasses import dataclass
from typing import Optional, Dict
from pyrogram import Client
import asyncio

@dataclass
class AuthState:
    stage: str  # "phone" | "code" | "password"
    phone: Optional[str] = None
    phone_code_hash: Optional[str] = None
    session_name: Optional[str] = None

auth_states: Dict[int, AuthState] = {}
user_clients: Dict[int, Client] = {}
ad_tasks: Dict[int, asyncio.Task] = {}
profile_tasks: Dict[int, asyncio.Task] = {}
