import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None
    connected: bool = False

    async def connect(self):
        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI.split('@')[-1] if '@' in settings.MONGODB_URI else 'localhost'}...")
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=4000
            )
            self.db = self.client[settings.MONGODB_DB_NAME]
            # Quick ping to verify connectivity
            await self.client.admin.command('ping')
            self.connected = True
            logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            self.connected = False
            logger.warning(f"Could not connect to MongoDB: {e}. Using fallback/degraded storage mode.")

    async def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB client disconnected.")

    def get_collection(self, name: str):
        if self.db is not None and self.connected:
            return self.db[name]
        return None


db_manager = MongoDBManager()


def get_db() -> AsyncIOMotorDatabase:
    return db_manager.db
