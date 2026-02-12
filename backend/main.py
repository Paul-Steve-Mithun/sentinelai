"""
FastAPI main application
Insider Threat Detection System API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="SentinelAI - Insider Threat Detection",
    description="Behavioral-based insider threat detection using ML anomaly detection",
    version="1.0.0",
    redirect_slashes=False  # Prevent 307 redirects that break CORS
)

# Configure CORS
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
if cors_origins_str == "*":
    origins = ["*"]
else:
    origins = cors_origins_str.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False if "*" in origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from routes import employees, events, anomalies, dashboard, ml_ops, agent, init

app.include_router(employees.router, prefix="/api/employees", tags=["employees"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(anomalies.router, prefix="/api/anomalies", tags=["anomalies"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(ml_ops.router, prefix="/api/ml", tags=["ml"])
app.include_router(agent.router)  # Agent routes have their own prefix
app.include_router(init.router)  # Init route for database setup


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SentinelAI - Insider Threat Detection API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
