import sqlite3
from contextlib import closing
from .config import DB_PATH
from . import models

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    with closing(connect()) as conn, conn:
        conn.execute(models.USERS)
        conn.execute(models.ADS)
        conn.execute(models.GROUPS)
        conn.execute(models.PROFILES)
      
