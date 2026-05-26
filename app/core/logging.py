import logging
import sys
from app.core.config import settings

def setup_logging() -> None:
    """
    Configures standard Python logging to output clean, structured logs.
    Adjusts levels of third-party libraries to reduce noise.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Custom format that includes timestamp, level, logger name, and message
    log_format = (
        "%(asctime)s - %(levelname)s - [%(name)s] - %(message)s"
        if not settings.DEBUG
        else "%(asctime)s - %(levelname)s - %(message)s"
    )

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # Resets existing handlers (e.g. from FastAPI defaults)
    )

    # Reduce noise from verbose libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = logging.getLogger("app")
    logger.info("Logging initialized with level: %s", settings.LOG_LEVEL)
