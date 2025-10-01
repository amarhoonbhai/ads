import re

def parse_interval_to_seconds(s: str) -> int | None:
    s = s.strip().lower()
    m = re.fullmatch(r"(\d+)\s*(s|sec|secs|second|seconds|m|min|mins|minute|minutes|h|hr|hrs|hour|hours)?", s)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2) or "s"
    if unit.startswith("s"): return n
    if unit.startswith("m"): return n * 60
    if unit.startswith("h"): return n * 3600
    return None
  
