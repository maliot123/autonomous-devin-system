"""Entry-point to start the FastAPI server."""

import uvicorn

from app.core.config import get_settings
from app.core.logging_setup import setup_logging

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    setup_logging()
    settings = get_settings()
    uvicorn.run(
        "app.server.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
