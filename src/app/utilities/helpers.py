import os
import tempfile
import logging
from typing import List, Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)


def create_temp_file(content: bytes, prefix: str = "", suffix: str = "") -> str:
    """
    Create a temporary file with the given content

    Args:
        content: The content to write to the file
        prefix: Prefix for the temporary file name
        suffix: Suffix for the temporary file name (e.g., .pdf)

    Returns:
        The path to the temporary file
    """
    try:
        fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        return temp_path
    except Exception as e:
        logger.error(f"Error creating temporary file: {str(e)}")
        raise e


def ensure_user_dir(base_dir: str, user_id: str) -> str:
    """
    Ensure a user-specific directory exists

    Args:
        base_dir: The base directory
        user_id: The user ID

    Returns:
        The path to the user directory
    """
    user_dir = os.path.join(base_dir, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def generate_id() -> str:
    """
    Generate a unique ID

    Returns:
        A unique ID string
    """
    return str(uuid.uuid4())
