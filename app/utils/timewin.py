from datetime import datetime, timedelta
from ..config import IST, WINDOW_START_H, WINDOW_END_H

def in_window(now_ist: datetime) -> bool:
    return WINDOW_START_H <= now_ist.hour < WINDOW_END_H

def next_window_start(now_ist: datetime) -> datetime:
    today_start = now_ist.replace(hour=WINDOW_START_H, minute=0, second=0, microsecond=0)
    if now_ist < today_start:
        return today_start
    tmr = (now_ist + timedelta(days=1)).replace(hour=WINDOW_START_H, minute=0, second=0, microsecond=0)
    return tmr
  
