#!/usr/bin/env python
"""
Simple runner script for the RAG manager test.
Run this inside the API Docker container with:
python -m run_rag_test
"""

import asyncio
import logging
from tests.test_rag_manager import test_rag_instance_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def main():
    """Run the test asynchronously"""
    print("Running RAG Manager test...")
    await test_rag_instance_manager()
    print("Test completed successfully!")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
