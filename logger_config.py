import sys
from loguru import logger
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logger.remove()
logger.add(sys.stdout, format="{time} | {level} | {name}:{line} | {message}", level=LOG_LEVEL)
logger.add("logs/ai_team_{time:YYYY-MM-DD}.log", rotation="1 day", retention="30 days", level="DEBUG")
