from ..db import init_db
from .runtime import bot

# Import handlers to register routes
from .handlers import start, auth, ads, groups, control, broadcast  # noqa: F401

def main():
    init_db()
    print("Starting Spinify Ads UserBot…")
    bot.run()

if __name__ == "__main__":
    main()
  
