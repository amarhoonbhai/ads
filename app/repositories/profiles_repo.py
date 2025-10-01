from contextlib import closing
from ..db import connect

def save_original_profile(user_id: int, first: str, last: str, bio: str, branded: int = 0):
    with closing(connect()) as conn, conn:
        conn.execute("""
            INSERT INTO profiles(user_id, orig_first, orig_last, orig_bio, branded)
            VALUES(?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                orig_first=excluded.orig_first,
                orig_last=excluded.orig_last,
                orig_bio=excluded.orig_bio
        """, (user_id, first, last, bio, branded))

def mark_branded(user_id: int, branded: bool):
    with closing(connect()) as conn, conn:
        conn.execute("UPDATE profiles SET branded=? WHERE user_id=?", (1 if branded else 0, user_id))

def get_profile(user_id: int):
    with closing(connect()) as conn:
        return conn.execute(
            "SELECT orig_first, orig_last, orig_bio, branded FROM profiles WHERE user_id=?",
            (user_id,)
        ).fetchone()
      
