from fastapi import FastAPI, Depends, HTTPException, status
import logging
from app.config import DATABASE_URL, DATA_DIR
import os

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


@app.on_event("startup")
async def startup_event():
    """Execute tasks on application startup"""
    logger.info("Starting EmbedIQ Backend API")
    logger.info(f"Database URL: {DATABASE_URL.replace('devpassword', '****')}")
    logger.info(f"Data directory: {DATA_DIR}")

    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to EmbedIQ Backend API"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker healthchecks"""
    try:
        # Verify database connection and extensions
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
