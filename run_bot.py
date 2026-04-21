"""Entry-point to start the Telegram bot."""

from app.core.logging_setup import setup_logging
from app.database.db import init_db
from app.integrations.telegram_bot import run_bot

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    setup_logging()
    init_db()
    run_bot()
