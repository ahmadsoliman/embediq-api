"""
Backup service for EmbedIQ backend.

This module provides functionality to backup user data directories and
database data, and to replicate data across availability zones.
"""

import os
import shutil
import logging
import time
import datetime
import asyncio
import subprocess
import glob
import json
from typing import Dict, Any, List, Optional, Tuple
import threading
from pathlib import Path

from app.config.app_config import (
    DATA_DIR,
    BACKUP_DIR,
    BACKUP_ENABLED,
    BACKUP_FREQUENCY,
    BACKUP_RETENTION_DAYS,
    DATABASE_URL,
)

logger = logging.getLogger(__name__)


class BackupService:
    """
    Service for backing up user data and database data.
    """

    def __init__(
        self,
        data_dir: str = DATA_DIR,
        backup_dir: str = BACKUP_DIR,
        backup_frequency: int = BACKUP_FREQUENCY,
        retention_days: int = BACKUP_RETENTION_DAYS,
        database_url: str = DATABASE_URL,
    ):
        """
        Initialize the backup service.

        Args:
            data_dir: The data directory to backup
            backup_dir: The directory to store backups
            backup_frequency: Backup frequency in seconds
            retention_days: Number of days to retain backups
            database_url: Database connection URL
        """
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        self.backup_frequency = backup_frequency
        self.retention_days = retention_days
        self.database_url = database_url
        self.backup_task = None
        self.stop_event = threading.Event()
        self.last_backup_time = None
        self.backup_history = []
        self.backup_status = {
            "status": "idle",
            "last_backup": None,
            "next_backup": None,
        }

        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)

        # Create subdirectories for different backup types
        os.makedirs(os.path.join(self.backup_dir, "user_data"), exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, "database"), exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, "config"), exist_ok=True)

        logger.info(
            f"BackupService initialized with data_dir={data_dir}, "
            f"backup_dir={backup_dir}, frequency={backup_frequency}s, "
            f"retention={retention_days} days"
        )

    async def start_backup_scheduler(self):
        """
        Start the backup scheduler.

        This method starts a background task that runs backups at the
        configured frequency.
        """
        if not BACKUP_ENABLED:
            logger.info("Backup is disabled. Scheduler not started.")
            return

        if self.backup_task is not None:
            logger.warning("Backup scheduler is already running")
            return

        logger.info("Starting backup scheduler")
        self.stop_event.clear()
        self.backup_task = asyncio.create_task(self._backup_scheduler())
        self.backup_status["status"] = "scheduled"
        self.backup_status["next_backup"] = time.time() + self.backup_frequency

    async def stop_backup_scheduler(self):
        """
        Stop the backup scheduler.
        """
        if self.backup_task is None:
            logger.warning("Backup scheduler is not running")
            return

        logger.info("Stopping backup scheduler")
        self.stop_event.set()
        await self.backup_task
        self.backup_task = None
        self.backup_status["status"] = "idle"
        self.backup_status["next_backup"] = None

    async def _backup_scheduler(self):
        """
        Background task for scheduled backups.
        """
        try:
            while not self.stop_event.is_set():
                # Run a backup
                logger.info("Running scheduled backup")
                self.backup_status["status"] = "running"

                try:
                    await self.run_backup()
                    self.backup_status["status"] = "scheduled"
                    self.backup_status["last_backup"] = time.time()
                    self.backup_status["next_backup"] = (
                        time.time() + self.backup_frequency
                    )
                except Exception as e:
                    logger.error(f"Scheduled backup failed: {e}")
                    self.backup_status["status"] = "error"
                    self.backup_status["error"] = str(e)

                # Wait for the next backup time
                for _ in range(self.backup_frequency):
                    if self.stop_event.is_set():
                        break
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Backup scheduler task cancelled")
            self.backup_status["status"] = "idle"
            self.backup_status["next_backup"] = None
        except Exception as e:
            logger.error(f"Error in backup scheduler: {e}")
            self.backup_status["status"] = "error"
            self.backup_status["error"] = str(e)

    async def run_backup(self) -> Dict[str, Any]:
        """
        Run a full backup of user data and database.

        Returns:
            Dictionary containing backup results
        """
        start_time = time.time()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"backup_{timestamp}"

        logger.info(f"Starting backup {backup_id}")

        results = {
            "backup_id": backup_id,
            "timestamp": timestamp,
            "start_time": start_time,
            "user_data": None,
            "database": None,
            "config": None,
        }

        try:
            # Backup user data
            user_data_result = await self._backup_user_data(backup_id)
            results["user_data"] = user_data_result

            # Backup database
            db_result = await self._backup_database(backup_id)
            results["database"] = db_result

            # Backup configuration
            config_result = await self._backup_config(backup_id)
            results["config"] = config_result

            # Clean up old backups
            await self._cleanup_old_backups()

            # Record backup in history
            end_time = time.time()
            results["end_time"] = end_time
            results["duration"] = end_time - start_time
            results["status"] = "success"

            self.backup_history.append(results)
            self.last_backup_time = end_time

            logger.info(
                f"Backup {backup_id} completed successfully in {results['duration']:.2f}s"
            )
            return results

        except Exception as e:
            logger.error(f"Backup {backup_id} failed: {e}")
            results["status"] = "error"
            results["error"] = str(e)
            results["end_time"] = time.time()
            results["duration"] = results["end_time"] - start_time

            self.backup_history.append(results)
            return results

    async def _backup_user_data(self, backup_id: str) -> Dict[str, Any]:
        """
        Backup user data directories.

        Args:
            backup_id: The backup ID

        Returns:
            Dictionary containing backup results
        """
        start_time = time.time()

        # Create backup directory
        backup_path = os.path.join(self.backup_dir, "user_data", backup_id)
        os.makedirs(backup_path, exist_ok=True)

        # Get list of user directories
        user_dirs = []
        for item in os.listdir(self.data_dir):
            item_path = os.path.join(self.data_dir, item)
            if os.path.isdir(item_path):
                user_dirs.append(item)

        # Backup each user directory
        user_results = {}
        total_size = 0

        for user_id in user_dirs:
            user_dir = os.path.join(self.data_dir, user_id)
            user_backup_dir = os.path.join(backup_path, user_id)

            try:
                # Create user backup directory
                os.makedirs(user_backup_dir, exist_ok=True)

                # Copy user data
                size = await self._copy_directory(user_dir, user_backup_dir)

                user_results[user_id] = {
                    "status": "success",
                    "size_bytes": size,
                }
                total_size += size
            except Exception as e:
                logger.error(f"Error backing up user {user_id}: {e}")
                user_results[user_id] = {
                    "status": "error",
                    "error": str(e),
                }

        end_time = time.time()

        return {
            "status": "success",
            "path": backup_path,
            "user_count": len(user_dirs),
            "total_size_bytes": total_size,
            "duration": end_time - start_time,
            "user_results": user_results,
        }

    async def _backup_database(self, backup_id: str) -> Dict[str, Any]:
        """
        Backup database using pg_dump.

        Args:
            backup_id: The backup ID

        Returns:
            Dictionary containing backup results
        """
        start_time = time.time()

        # Create backup directory
        backup_path = os.path.join(self.backup_dir, "database", backup_id)
        os.makedirs(backup_path, exist_ok=True)

        # Parse database URL
        db_parts = self._parse_database_url(self.database_url)

        if not db_parts:
            return {
                "status": "error",
                "error": "Invalid database URL",
            }

        # Create backup file path
        backup_file = os.path.join(backup_path, f"{db_parts['database']}.sql")

        try:
            # Build pg_dump command
            cmd = [
                "pg_dump",
                "-h",
                db_parts["host"],
                "-p",
                db_parts["port"],
                "-U",
                db_parts["user"],
                "-d",
                db_parts["database"],
                "-f",
                backup_file,
                "--format=p",  # Plain text format
                "--no-owner",  # Don't include ownership commands
                "--no-privileges",  # Don't include privilege commands
            ]

            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_parts["password"]

            # Run pg_dump
            logger.info(f"Running pg_dump to {backup_file}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"pg_dump failed: {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg,
                    "returncode": process.returncode,
                }

            # Get backup file size
            size = os.path.getsize(backup_file)

            end_time = time.time()

            return {
                "status": "success",
                "path": backup_file,
                "size_bytes": size,
                "duration": end_time - start_time,
            }
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def _backup_config(self, backup_id: str) -> Dict[str, Any]:
        """
        Backup configuration files.

        Args:
            backup_id: The backup ID

        Returns:
            Dictionary containing backup results
        """
        start_time = time.time()

        # Create backup directory
        backup_path = os.path.join(self.backup_dir, "config", backup_id)
        os.makedirs(backup_path, exist_ok=True)

        # Get list of configuration files
        config_files = [
            ".env",
            "docker-compose.yml",
            "requirements.txt",
        ]

        # Backup each configuration file
        config_results = {}
        total_size = 0

        for config_file in config_files:
            src_path = os.path.join(os.getcwd(), config_file)
            dst_path = os.path.join(backup_path, config_file)

            try:
                if os.path.exists(src_path):
                    # Copy configuration file
                    shutil.copy2(src_path, dst_path)

                    # Get file size
                    size = os.path.getsize(dst_path)

                    config_results[config_file] = {
                        "status": "success",
                        "size_bytes": size,
                    }
                    total_size += size
                else:
                    config_results[config_file] = {
                        "status": "skipped",
                        "reason": "File not found",
                    }
            except Exception as e:
                logger.error(f"Error backing up config file {config_file}: {e}")
                config_results[config_file] = {
                    "status": "error",
                    "error": str(e),
                }

        end_time = time.time()

        return {
            "status": "success",
            "path": backup_path,
            "file_count": len(config_results),
            "total_size_bytes": total_size,
            "duration": end_time - start_time,
            "file_results": config_results,
        }

    async def _cleanup_old_backups(self) -> Dict[str, Any]:
        """
        Clean up old backups based on retention policy.

        Returns:
            Dictionary containing cleanup results
        """
        if self.retention_days <= 0:
            logger.info("Backup retention is disabled, skipping cleanup")
            return {"status": "skipped", "reason": "Retention disabled"}

        logger.info(f"Cleaning up backups older than {self.retention_days} days")

        # Calculate cutoff time
        cutoff_time = time.time() - (self.retention_days * 86400)

        # Get list of backup directories
        backup_types = ["user_data", "database", "config"]
        removed_count = 0

        for backup_type in backup_types:
            backup_type_dir = os.path.join(self.backup_dir, backup_type)

            if not os.path.exists(backup_type_dir):
                continue

            for backup_dir in os.listdir(backup_type_dir):
                backup_path = os.path.join(backup_type_dir, backup_dir)

                if not os.path.isdir(backup_path):
                    continue

                # Get directory modification time
                mtime = os.path.getmtime(backup_path)

                # Remove if older than cutoff
                if mtime < cutoff_time:
                    logger.info(f"Removing old backup: {backup_path}")
                    try:
                        shutil.rmtree(backup_path)
                        removed_count += 1
                    except Exception as e:
                        logger.error(f"Error removing old backup {backup_path}: {e}")

        return {
            "status": "success",
            "removed_count": removed_count,
            "cutoff_time": cutoff_time,
        }

    async def _copy_directory(self, src: str, dst: str) -> int:
        """
        Copy a directory recursively.

        Args:
            src: Source directory
            dst: Destination directory

        Returns:
            Total size of copied files in bytes
        """
        total_size = 0

        # Use shutil.copytree for directories
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)

            if os.path.isdir(s):
                os.makedirs(d, exist_ok=True)
                size = await self._copy_directory(s, d)
                total_size += size
            else:
                shutil.copy2(s, d)
                total_size += os.path.getsize(d)

        return total_size

    def _parse_database_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Parse a database URL into components.

        Args:
            url: Database URL (e.g., postgresql://user:pass@host:port/dbname)

        Returns:
            Dictionary containing database components or None if invalid
        """
        try:
            # Remove protocol
            if "://" in url:
                url = url.split("://")[1]

            # Split user:pass@host:port/dbname
            auth_host, database = url.split("/")

            # Split user:pass@host:port
            if "@" in auth_host:
                auth, host = auth_host.split("@")
            else:
                auth = ""
                host = auth_host

            # Split user:pass
            if ":" in auth:
                user, password = auth.split(":")
            else:
                user = auth
                password = ""

            # Split host:port
            if ":" in host:
                host, port = host.split(":")
            else:
                port = "5432"  # Default PostgreSQL port

            return {
                "user": user,
                "password": password,
                "host": host,
                "port": port,
                "database": database,
            }
        except Exception as e:
            logger.error(f"Error parsing database URL: {e}")
            return None

    async def get_backup_status(self) -> Dict[str, Any]:
        """
        Get the current backup status.

        Returns:
            Dictionary containing backup status
        """
        return {
            **self.backup_status,
            "enabled": BACKUP_ENABLED,
            "frequency": self.backup_frequency,
            "retention_days": self.retention_days,
            "backup_count": len(self.backup_history),
            "last_backup_time": self.last_backup_time,
        }

    async def get_backup_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the backup history.

        Args:
            limit: Maximum number of history items to return

        Returns:
            List of backup history items
        """
        return self.backup_history[-limit:]

    async def trigger_backup(self) -> Dict[str, Any]:
        """
        Trigger a manual backup.

        Returns:
            Dictionary containing backup results
        """
        logger.info("Triggering manual backup")
        return await self.run_backup()

    async def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Restore from a backup.

        Args:
            backup_id: The backup ID to restore from

        Returns:
            Dictionary containing restore results
        """
        logger.info(f"Restoring from backup {backup_id}")

        # Check if backup exists
        user_data_path = os.path.join(self.backup_dir, "user_data", backup_id)
        database_path = os.path.join(self.backup_dir, "database", backup_id)

        if not os.path.exists(user_data_path) or not os.path.exists(database_path):
            return {
                "status": "error",
                "error": f"Backup {backup_id} not found",
            }

        results = {
            "backup_id": backup_id,
            "start_time": time.time(),
            "user_data": None,
            "database": None,
        }

        try:
            # Restore user data
            user_data_result = await self._restore_user_data(backup_id)
            results["user_data"] = user_data_result

            # Restore database
            db_result = await self._restore_database(backup_id)
            results["database"] = db_result

            # Record restore in history
            end_time = time.time()
            results["end_time"] = end_time
            results["duration"] = end_time - results["start_time"]
            results["status"] = "success"

            logger.info(f"Restore from backup {backup_id} completed successfully")
            return results

        except Exception as e:
            logger.error(f"Restore from backup {backup_id} failed: {e}")
            results["status"] = "error"
            results["error"] = str(e)
            results["end_time"] = time.time()
            results["duration"] = results["end_time"] - results["start_time"]

            return results

    async def _restore_user_data(self, backup_id: str) -> Dict[str, Any]:
        """
        Restore user data from backup.

        Args:
            backup_id: The backup ID to restore from

        Returns:
            Dictionary containing restore results
        """
        start_time = time.time()

        # Get backup path
        backup_path = os.path.join(self.backup_dir, "user_data", backup_id)

        if not os.path.exists(backup_path):
            return {
                "status": "error",
                "error": f"User data backup {backup_id} not found",
            }

        # Get list of user directories in backup
        user_dirs = []
        for item in os.listdir(backup_path):
            item_path = os.path.join(backup_path, item)
            if os.path.isdir(item_path):
                user_dirs.append(item)

        # Restore each user directory
        user_results = {}
        total_size = 0

        for user_id in user_dirs:
            user_backup_dir = os.path.join(backup_path, user_id)
            user_dir = os.path.join(self.data_dir, user_id)

            try:
                # Create user directory if it doesn't exist
                os.makedirs(user_dir, exist_ok=True)

                # Copy user data
                size = await self._copy_directory(user_backup_dir, user_dir)

                user_results[user_id] = {
                    "status": "success",
                    "size_bytes": size,
                }
                total_size += size
            except Exception as e:
                logger.error(f"Error restoring user {user_id}: {e}")
                user_results[user_id] = {
                    "status": "error",
                    "error": str(e),
                }

        end_time = time.time()

        return {
            "status": "success",
            "user_count": len(user_dirs),
            "total_size_bytes": total_size,
            "duration": end_time - start_time,
            "user_results": user_results,
        }

    async def _restore_database(self, backup_id: str) -> Dict[str, Any]:
        """
        Restore database from backup.

        Args:
            backup_id: The backup ID to restore from

        Returns:
            Dictionary containing restore results
        """
        start_time = time.time()

        # Get backup directory
        backup_path = os.path.join(self.backup_dir, "database", backup_id)

        if not os.path.exists(backup_path):
            return {
                "status": "error",
                "error": f"Database backup {backup_id} not found",
            }

        # Parse database URL
        db_parts = self._parse_database_url(self.database_url)

        if not db_parts:
            return {
                "status": "error",
                "error": "Invalid database URL",
            }

        # Find backup file
        backup_files = glob.glob(os.path.join(backup_path, "*.sql"))

        if not backup_files:
            return {
                "status": "error",
                "error": "No database backup file found",
            }

        backup_file = backup_files[0]

        try:
            # Build psql command
            cmd = [
                "psql",
                "-h",
                db_parts["host"],
                "-p",
                db_parts["port"],
                "-U",
                db_parts["user"],
                "-d",
                db_parts["database"],
                "-f",
                backup_file,
            ]

            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_parts["password"]

            # Run psql
            logger.info(f"Running psql to restore from {backup_file}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"psql restore failed: {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg,
                    "returncode": process.returncode,
                }

            end_time = time.time()

            return {
                "status": "success",
                "file": backup_file,
                "size_bytes": os.path.getsize(backup_file),
                "duration": end_time - start_time,
            }
        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return {
                "status": "error",
                "error": str(e),
            }


# Singleton instance
_backup_service = None


def get_backup_service() -> BackupService:
    """
    Get or create the backup service singleton.

    Returns:
        The backup service singleton
    """
    global _backup_service
    if _backup_service is None:
        _backup_service = BackupService()
    return _backup_service
