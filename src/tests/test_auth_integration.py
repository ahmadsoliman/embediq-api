import argparse
import httpx
import json
import sys
import asyncio

# Default URL for the backend server
DEFAULT_URL = "http://127.0.0.1:8000"


async def test_endpoints(base_url, token=None):
    """Test the auth endpoints with an optional token"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient() as client:
        # Test health endpoint (should not require authentication)
        try:
            print(f"Testing health endpoint: {base_url}/health")
            health_resp = await client.get(f"{base_url}/health", timeout=10.0)
            print(f"\n=== Health Endpoint Test ===")
            print(f"Status: {health_resp.status_code}")
            print(f"Response: {health_resp.json()}")
        except Exception as e:
            print(f"Error testing health endpoint: {str(e)}")
            return False

        # Test root endpoint (should not require authentication)
        try:
            print(f"Testing root endpoint: {base_url}/")
            root_resp = await client.get(f"{base_url}/", timeout=10.0)
            print(f"\n=== Root Endpoint Test ===")
            print(f"Status: {root_resp.status_code}")
            print(f"Response: {root_resp.json()}")
        except Exception as e:
            print(f"Error testing root endpoint: {str(e)}")

        # Test token validation endpoint
        try:
            print(f"Testing token endpoint: {base_url}/api/v1/auth/token")
            token_resp = await client.get(
                f"{base_url}/api/v1/auth/token", headers=headers, timeout=10.0
            )
            print(f"\n=== Token Validation Endpoint Test ===")
            print(f"Status: {token_resp.status_code}")
            print(
                f"Response: {json.dumps(token_resp.json(), indent=2) if token_resp.status_code < 400 else token_resp.text}"
            )
        except Exception as e:
            print(f"Error testing token validation: {str(e)}")

        # Test profile endpoint
        try:
            print(f"Testing profile endpoint: {base_url}/api/v1/auth/profile")
            profile_resp = await client.get(
                f"{base_url}/api/v1/auth/profile", headers=headers, timeout=10.0
            )
            print(f"\n=== Profile Endpoint Test ===")
            print(f"Status: {profile_resp.status_code}")
            print(
                f"Response: {json.dumps(profile_resp.json(), indent=2) if profile_resp.status_code < 400 else profile_resp.text}"
            )
        except Exception as e:
            print(f"Error testing profile endpoint: {str(e)}")

    return True


def get_auth0_test_token():
    """
    Instructions for getting an Auth0 test token
    """
    print("\n=== AUTH0 TEST TOKEN INSTRUCTIONS ===")
    print("To test with a valid Auth0 token:")
    print("1. Go to the Auth0 Dashboard: https://manage.auth0.com/")
    print("2. Select your application")
    print("3. Go to the API section and select your API")
    print("4. Navigate to the 'Test' tab")
    print("5. Use the 'OAuth2 Debug Console' to generate a test token")
    print("6. Copy the token and use it with this script's --token option")
    print("\nAlternatively, you can use the Auth0 API Explorer to generate a token:")
    print("1. Go to: https://auth0.com/docs/api/authentication")
    print("2. Find the 'Get Token' section")
    print("3. Fill in your Auth0 domain, client ID, and client secret")
    print("4. Generate a token and copy it")


def test_local_server_directly():
    """
    Simple manual test to verify server connectivity
    """
    import requests

    try:
        # Test the most basic endpoint with standard library
        print("Testing connectivity to server with requests...")
        resp = requests.get("http://127.0.0.1:8000/")
        print(f"Response status code: {resp.status_code}")
        print(f"Response content: {resp.text}")
        return True
    except Exception as e:
        print(f"Failed to connect with requests library: {str(e)}")
        return False


async def main():
    parser = argparse.ArgumentParser(
        description="Test Auth0 integration with the backend"
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Base URL for the backend (default: {DEFAULT_URL})",
    )
    parser.add_argument("--token", help="Auth0 JWT token for testing (optional)")
    parser.add_argument(
        "--token-help",
        action="store_true",
        help="Display instructions for getting an Auth0 test token",
    )
    parser.add_argument(
        "--local-test",
        action="store_true",
        help="Run a simple test to verify server connectivity",
    )

    args = parser.parse_args()

    if args.token_help:
        get_auth0_test_token()
        return

    if args.local_test:
        test_local_server_directly()
        return

    if not args.token:
        print(
            "Warning: No token provided. Authenticated endpoints will return 401 errors."
        )
        print("Run with --token-help for instructions on getting a test token.")

    success = await test_endpoints(args.url, args.token)

    if not success:
        print("Tests failed to run correctly. Ensure the server is running.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
