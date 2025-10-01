from contextlib import closing
from ..db import connect
from ..config import SESSIONS_DIR

def get_or_create_user(user_id: int) -> str:
    session_name = f"{SESSIONS_DIR}/{user_id}"
    with closing(connect()) as conn, conn:
        row = conn.execute("SELECT session_name FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row is None:
            conn.execute("INSERT INTO users(user_id, session_name, is_logged_in) VALUES(?,?,0)", (user_id, session_name))
        else:
            session_name = row[0]
    return session_name

def update_login_status(user_id: int, is_logged_in: bool):
    with closing(connect()) as conn, conn:
        conn.execute("UPDATE users SET is_logged_in=? WHERE user_id=?", (1 if is_logged_in else 0, user_id))
      
