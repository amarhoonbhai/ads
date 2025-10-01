from contextlib import closing
from ..db import connect

def set_ad(user_id: int, message=None, interval_sec=None, enabled=None):
    with closing(connect()) as conn, conn:
        exists = conn.execute("SELECT 1 FROM ads WHERE user_id=?", (user_id,)).fetchone()
        if not exists:
            conn.execute("INSERT INTO ads(user_id) VALUES(?)", (user_id,))
        if message is not None:
            conn.execute("UPDATE ads SET message=? WHERE user_id=?", (message, user_id))
        if interval_sec is not None:
            conn.execute("UPDATE ads SET interval_sec=? WHERE user_id=?", (interval_sec, user_id))
        if enabled is not None:
            conn.execute("UPDATE ads SET enabled=? WHERE user_id=?", (1 if enabled else 0, user_id))

def get_ad(user_id: int):
    with closing(connect()) as conn:
        row = conn.execute("SELECT message, interval_sec, enabled FROM ads WHERE user_id=?", (user_id,)).fetchone()
        if row:
            return {"message": row[0] or "", "interval_sec": row[1] or 1800, "enabled": bool(row[2])}
        return {"message": "", "interval_sec": 1800, "enabled": False}
      
