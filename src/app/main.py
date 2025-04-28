from fastapi import FastAPI, Depends, HTTPException, status
import logging
from app.config.app_config import (
    DATABASE_URL,
    DATA_DIR,
    BACKUP_ENABLED,
    MONITORING_ENABLED,
)
import os
from app.routes.api import api_router
from app.services.datasource_registry import datasource_registry
from app.monitoring.system_monitor import SystemMonitor
from app.monitoring.lightrag_monitor import get_lightrag_monitor
from app.backup.backup_service import get_backup_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="EmbedIQ Backend API",
    description="LightRAG-powered backend for the EmbedIQ application",
    version="0.1.0",
)

# Include routers
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """Execute tasks on application startup"""
    logger.info("Starting EmbedIQ Backend API")
    logger.info(f"Database URL: {DATABASE_URL.replace('devpassword', '****')}")

    # Use a local data directory for development when not in Docker
    if os.path.exists("/.dockerenv"):
        # In Docker, use the configured DATA_DIR
        data_dir = DATA_DIR
    else:
        # For local development, use a directory in the current working directory
        data_dir = os.path.join(os.getcwd(), "data")

    logger.info(f"Data directory: {data_dir}")

    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)

    # Initialize monitoring
    if MONITORING_ENABLED:
        logger.info("Initializing monitoring services")
        # Initialize system monitor
        system_monitor = SystemMonitor(data_dir=data_dir)
        # Initialize LightRAG monitor
        lightrag_monitor = get_lightrag_monitor()
        logger.info("Monitoring services initialized")

    # Initialize backup service
    if BACKUP_ENABLED:
        logger.info("Initializing backup service")
        backup_service = get_backup_service()
        # Start backup scheduler
        await backup_service.start_backup_scheduler()
        logger.info("Backup service initialized and scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute tasks on application shutdown"""
    logger.info("Shutting down EmbedIQ Backend API")

    # Stop backup scheduler
    if BACKUP_ENABLED:
        logger.info("Stopping backup scheduler")
        backup_service = get_backup_service()
        await backup_service.stop_backup_scheduler()
        logger.info("Backup scheduler stopped")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to EmbedIQ Backend API"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker healthchecks"""
    try:
        # Use system monitor for health check if monitoring is enabled
        if MONITORING_ENABLED:
            system_monitor = SystemMonitor(data_dir=DATA_DIR)
            health_data = system_monitor.get_health_check()

            # Add database connection check
            try:
                # In Docker, verify database connection and extensions
                if os.path.exists("/.dockerenv"):
                    from app.db.connection import verify_extensions

                    extensions_status = verify_extensions()
                    health_data["database"] = {
                        "connected": True,
                        "extensions": extensions_status,
                    }
                else:
                    health_data["database"] = {
                        "connected": False,
                        "message": "Skipped in local dev mode",
                    }
            except Exception as db_error:
                health_data["database"] = {"connected": False, "error": str(db_error)}

            return health_data

        # Fall back to basic health check if monitoring is disabled
        # For local testing, skip the database connection check
        if not os.path.exists("/.dockerenv"):
            return {
                "status": "healthy",
                "database": {
                    "connected": False,
                    "message": "Skipped in local dev mode",
                },
                "data_directory": {
                    "path": os.path.join(os.getcwd(), "data"),
                    "exists": True,
                    "writable": True,
                },
            }

        # In Docker, verify database connection and extensions
        from app.db.connection import verify_extensions

        extensions_status = verify_extensions()

        # Check data directory
        data_dir_exists = os.path.isdir(DATA_DIR)
        data_dir_writable = os.access(DATA_DIR, os.W_OK)

        return {
            "status": "healthy",
            "database": {"connected": True, "extensions": extensions_status},
            "data_directory": {
                "path": DATA_DIR,
                "exists": data_dir_exists,
                "writable": data_dir_writable,
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}
