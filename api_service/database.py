"""
MongoDB database initialization and session management.
"""
import logging
from typing import Optional
from mongoengine import connect, disconnect
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from shared.config import settings


logger = logging.getLogger(__name__)


class Database:
    """
    MongoDB database connection manager.
    Provides both synchronous (mongoengine) and asynchronous (motor) access.
    """
    
    def __init__(self):
        """Initialize database connection."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """
        Connect to MongoDB.
        Should be called on application startup.
        """
        try:
            # AsyncIO motor client for async operations
            self.client = AsyncIOMotorClient(settings.mongo_uri)
            self.db = self.client[settings.mongo_db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.mongo_db_name}")
            
            # Synchronous mongoengine connection for ODM operations
            connect(
                db=settings.mongo_db_name,
                host=settings.mongo_uri,
            )
            logger.info("MongoEngine connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """
        Disconnect from MongoDB.
        Should be called on application shutdown.
        """
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
        
        try:
            disconnect()
            logger.info("MongoEngine connection closed")
        except Exception as e:
            logger.warning(f"Error closing MongoEngine connection: {e}")
    
    async def health_check(self) -> bool:
        """
        Check if database is responsive.
        
        Returns:
            True if database is healthy, False otherwise
        """
        try:
            if self.client:
                await self.client.admin.command('ping')
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
        
        return False
    
    async def create_indexes(self):
        """
        Create necessary database indexes for performance.
        Should be called once during initialization.
        """
        try:
            # Drivers collection indexes
            await self.db.drivers.create_index("driver_id")
            await self.db.drivers.create_index("email", unique=True)
            
            # Vehicles collection indexes
            await self.db.vehicles.create_index("vehicle_id")
            await self.db.vehicles.create_index("driver_id")
            await self.db.vehicles.create_index("license_plate", unique=True)
            
            # Drowsiness alerts indexes (most queried)
            await self.db.drowsiness_alerts.create_index("vehicle_id")
            await self.db.drowsiness_alerts.create_index("driver_id")
            await self.db.drowsiness_alerts.create_index("timestamp")
            await self.db.drowsiness_alerts.create_index([("vehicle_id", 1), ("timestamp", -1)])
            await self.db.drowsiness_alerts.create_index([("driver_id", 1), ("timestamp", -1)])
            
            # Sessions indexes
            await self.db.sessions.create_index("vehicle_id")
            await self.db.sessions.create_index("driver_id")
            await self.db.sessions.create_index("start_time")
            await self.db.sessions.create_index([("vehicle_id", 1), ("start_time", -1)])
            
            # Predictions indexes
            await self.db.anomaly_predictions.create_index("vehicle_id")
            await self.db.anomaly_predictions.create_index("timestamp")
            
            # Heartbeats indexes
            await self.db.detector_heartbeats.create_index("detector_id")
            await self.db.detector_heartbeats.create_index([("detector_id", 1), ("timestamp", -1)])
            
            logger.info("All database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
            raise


# Global database instance
db = Database()


async def get_db() -> Database:
    """
    Dependency for FastAPI to get database instance.
    Usage: async def my_endpoint(db: Database = Depends(get_db))
    """
    return db
