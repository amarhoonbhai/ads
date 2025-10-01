from contextlib import closing
from ..db import connect

def list_groups(user_id: int):
    with closing(connect()) as conn:
        return conn.execute("SELECT chat_id, title, username FROM groups WHERE user_id=?", (user_id,)).fetchall()

def add_group(user_id: int, chat_id: int, title: str, username: str | None):
    with closing(connect()) as conn, conn:
        exists = conn.execute("SELECT 1 FROM groups WHERE user_id=? AND chat_id=?", (user_id, chat_id)).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO groups(user_id, chat_id, title, username) VALUES(?,?,?,?)",
                (user_id, chat_id, title or "", username or "")
            )

def del_group(user_id: int, key: str) -> int:
    with closing(connect()) as conn, conn:
        if key.startswith("@"):
            return conn.execute("DELETE FROM groups WHERE user_id=? AND username=?", (user_id, key[1:])).rowcount
        try:
            cid = int(key)
            return conn.execute("DELETE FROM groups WHERE user_id=? AND chat_id=?", (user_id, cid)).rowcount
        except ValueError:
            return conn.execute("DELETE FROM groups WHERE user_id=? AND username=?", (user_id, key)).rowcount
