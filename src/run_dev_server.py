import uvicorn
import argparse
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Run the EmbedIQ backend server in development mode"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload on code changes"
    )

    args = parser.parse_args()

    logger.info(f"Starting development server at http://{args.host}:{args.port}")
    logger.info(f"Auto-reload: {'Enabled' if args.reload else 'Disabled'}")

    # Print Auth0 configuration (without sensitive values)
    auth0_domain = os.getenv("AUTH0_DOMAIN", "")
    auth0_audience = os.getenv("AUTH0_API_AUDIENCE", "")

    logger.info(f"Auth0 Domain: {auth0_domain}")
    logger.info(f"Auth0 API Audience: {auth0_audience}")

    # Start the server
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
