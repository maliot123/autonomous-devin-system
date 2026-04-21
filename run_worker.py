"""Entry-point to start the background worker."""

from app.core.logging_setup import setup_logging
from app.workers.worker import run_worker

if __name__ == "__main__":
    setup_logging()
    run_worker()
