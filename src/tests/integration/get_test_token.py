#!/usr/bin/env python
"""
Helper script to obtain a test authentication token for integration tests.

This script uses the Auth0 OAuth endpoint to generate a test token
using client credentials grant for integration tests.
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default Auth0 configuration from environment variables
DEFAULT_AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "dev-embediq.us.auth0.com")
DEFAULT_AUTH0_CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "")
DEFAULT_AUTH0_CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET", "")
DEFAULT_AUTH0_AUDIENCE = os.environ.get("AUTH0_API_AUDIENCE", "https://api.embediq.dev")


def get_auth_token(domain, client_id, client_secret, audience):
    """Get an Auth0 access token using client credentials grant"""
    url = f"https://{domain}/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
        "grant_type": "client_credentials",
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["access_token"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get a test authentication token for integration tests"
    )
    parser.add_argument("--domain", default=DEFAULT_AUTH0_DOMAIN, help="Auth0 domain")
    parser.add_argument(
        "--client-id", default=DEFAULT_AUTH0_CLIENT_ID, help="Auth0 client ID"
    )
    parser.add_argument(
        "--client-secret",
        default=DEFAULT_AUTH0_CLIENT_SECRET,
        help="Auth0 client secret",
    )
    parser.add_argument(
        "--audience", default=DEFAULT_AUTH0_AUDIENCE, help="API audience"
    )

    args = parser.parse_args()

    # Validate required args
    if not args.client_id or not args.client_secret:
        logger.error("Missing required arguments: client-id and client-secret")
        parser.print_help()
        sys.exit(1)

    # Get token
    try:
        logger.info(f"Getting token for {args.domain} with audience {args.audience}")
        token = get_auth_token(
            args.domain, args.client_id, args.client_secret, args.audience
        )

        # Export the token
        print(f"\n# Add this to your .env file or export it:")
        print(f"export TEST_AUTH_TOKEN='{token}'")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
