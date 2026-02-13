"""
Database configuration and connection management for MongoDB
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from pymongo.server_api import ServerApi
import certifi

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "sentinel_ai")

async def init_db():
    """Initialize database connection and Beanie models"""
    client = AsyncIOMotorClient(
        MONGODB_URL,
        tlsCAFile=certifi.where(),
        tls=True,
        server_api=ServerApi('1')
    )
    database = client[DB_NAME]
    
    # Import models here to avoid circular imports
    from models import (
        Employee, 
        BehavioralEvent, 
        BehavioralFingerprint, 
        Anomaly, 
        MitreMapping, 
        MitigationStrategy
    )
    
    await init_beanie(
        database=database,
        document_models=[
            Employee,
            BehavioralEvent,
            BehavioralFingerprint,
            Anomaly,
            MitreMapping,
            MitigationStrategy
        ]
    )
