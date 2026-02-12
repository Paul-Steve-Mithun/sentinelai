"""
System Health Monitoring Routes
Exposes server resources, database status, and ML model status
"""
from fastapi import APIRouter, HTTPException
import psutil
import os
import time
from datetime import datetime, timezone
from ml.anomaly_detector import AnomalyDetector
import models

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("/system")
async def get_system_health():
    """
    Get system health metrics including:
    - Server CPU & RAM usage
    - MongoDB connection status
    - ML Model status
    """
    # 1. Server Resources
    cpu_usage = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    
    # 2. Database Status
    try:
        # Simple ping by checking count of employees (fast operation)
        # or accessing the client from a model
        start_time = time.time()
        await models.Employee.find_one()
        db_latency = (time.time() - start_time) * 1000  # ms
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        db_latency = -1

    # 3. ML Model Status
    detector = AnomalyDetector()
    model_info = detector.get_model_info()
    model_status = "active" if model_info['is_trained'] else "not_trained"
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server": {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "memory_total": memory.total,
            "memory_available": memory.available
        },
        "database": {
            "status": db_status,
            "latency_ms": round(db_latency, 2),
            "type": "MongoDB"
        },
        "ml_model": {
            "status": model_status,
            "trained_at": model_info.get('trained_at'),
            "n_samples": model_info.get('n_samples')
        }
    }
