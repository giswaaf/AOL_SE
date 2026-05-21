import os
import asyncio
import logging
import certifi
import motor.motor_asyncio
from pymongo.server_api import ServerApi
from app.core.config import settings

logger = logging.getLogger(__name__)

MONGO_URI = settings.MONGO_URI
MONGO_DB = os.getenv("MONGO_DB_NAME", "smart-attendance")

# Retry configuration
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 30  # seconds

client_kwargs = {
    "serverSelectionTimeoutMS": 5000,
    "server_api": ServerApi("1"),
}

if "mongodb+srv" in MONGO_URI or "tls=true" in MONGO_URI:
    client_kwargs["tlsCAFile"] = certifi.where()

client = motor.motor_asyncio.AsyncIOMotorClient(
    MONGO_URI,
    **client_kwargs
)
db = client[MONGO_DB]


async def verify_db_connection():
    """
    Verify MongoDB connection with exponential backoff retry logic.
    This ensures the API doesn't start in a broken state when the database
    is not yet ready (common in Docker Compose scenarios).
    """
    retry_count = 0
    delay = INITIAL_RETRY_DELAY

    while retry_count < MAX_RETRIES:
        try:
            # Attempt to ping the database
            await client.admin.command("ping")
            logger.info("✓ MongoDB connection established successfully")
            return
        except Exception as e:
            retry_count += 1
            if retry_count >= MAX_RETRIES:
                logger.critical(
                    f"✗ Failed to connect to MongoDB after {MAX_RETRIES} attempts. "
                    f"Last error: {str(e)}"
                )
                raise RuntimeError(
                    f"Failed to connect to MongoDB after {MAX_RETRIES} attempts"
                ) from e

            logger.warning(
                f"⚠ MongoDB connection attempt {retry_count}/{MAX_RETRIES} failed. "
                f"Retrying in {delay}s... Error: {str(e)}"
            )
            await asyncio.sleep(delay)
            # Exponential backoff with max cap
            delay = min(delay * 2, MAX_RETRY_DELAY)
