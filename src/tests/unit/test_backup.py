"""
Unit tests for backup module.
"""

import pytest
import os
import shutil
import tempfile
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import time
from datetime import datetime

from app.backup.backup_service import BackupService, get_backup_service


class TestBackupService:
    """Tests for BackupService class"""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        data_dir = tempfile.mkdtemp()
        backup_dir = tempfile.mkdtemp()

        # Create some test data
        user1_dir = os.path.join(data_dir, "user1")
        user2_dir = os.path.join(data_dir, "user2")
        os.makedirs(user1_dir)
        os.makedirs(user2_dir)

        # Create some test files
        with open(os.path.join(user1_dir, "test1.txt"), "w") as f:
            f.write("Test file 1")
        with open(os.path.join(user2_dir, "test2.txt"), "w") as f:
            f.write("Test file 2")

        yield data_dir, backup_dir

        # Clean up
        shutil.rmtree(data_dir, ignore_errors=True)
        shutil.rmtree(backup_dir, ignore_errors=True)

    def test_init(self, temp_dirs):
        """Test initialization"""
        data_dir, backup_dir = temp_dirs
        service = BackupService(
            data_dir=data_dir,
            backup_dir=backup_dir,
            backup_frequency=3600,
            retention_days=7,
            database_url="postgresql://user:pass@localhost:5432/db",
        )

        assert service.data_dir == data_dir
        assert service.backup_dir == backup_dir
        assert service.backup_frequency == 3600
        assert service.retention_days == 7
        assert service.database_url == "postgresql://user:pass@localhost:5432/db"
        assert service.backup_task is None
        assert service.last_backup_time is None
        assert len(service.backup_history) == 0
        assert service.backup_status["status"] == "idle"

        # Check that backup directories were created
        assert os.path.exists(os.path.join(backup_dir, "user_data"))
        assert os.path.exists(os.path.join(backup_dir, "database"))
        assert os.path.exists(os.path.join(backup_dir, "config"))

    @pytest.mark.asyncio
    async def test_copy_directory(self, temp_dirs):
        """Test _copy_directory method"""
        data_dir, backup_dir = temp_dirs
        service = BackupService(data_dir=data_dir, backup_dir=backup_dir)

        # Create source and destination directories
        src = os.path.join(data_dir, "user1")
        dst = os.path.join(backup_dir, "user1_backup")
        os.makedirs(dst, exist_ok=True)

        # Copy directory
        size = await service._copy_directory(src, dst)

        # Check that files were copied
        assert os.path.exists(os.path.join(dst, "test1.txt"))
        assert size > 0

        # Check file content
        with open(os.path.join(dst, "test1.txt"), "r") as f:
            content = f.read()
            assert content == "Test file 1"

    def test_parse_database_url(self, temp_dirs):
        """Test _parse_database_url method"""
        data_dir, backup_dir = temp_dirs
        service = BackupService(data_dir=data_dir, backup_dir=backup_dir)

        # Test with full URL
        url = "postgresql://user:pass@localhost:5432/db"
        result = service._parse_database_url(url)

        assert result["user"] == "user"
        assert result["password"] == "pass"
        assert result["host"] == "localhost"
        assert result["port"] == "5432"
        assert result["database"] == "db"

        # Test without protocol
        url = "user:pass@localhost:5432/db"
        result = service._parse_database_url(url)

        assert result["user"] == "user"
        assert result["password"] == "pass"
        assert result["host"] == "localhost"
        assert result["port"] == "5432"
        assert result["database"] == "db"

        # Test without password
        url = "user@localhost:5432/db"
        result = service._parse_database_url(url)

        assert result["user"] == "user"
        assert result["password"] == ""
        assert result["host"] == "localhost"
        assert result["port"] == "5432"
        assert result["database"] == "db"

        # Test without port
        url = "user:pass@localhost/db"
        result = service._parse_database_url(url)

        assert result["user"] == "user"
        assert result["password"] == "pass"
        assert result["host"] == "localhost"
        assert result["port"] == "5432"  # Default port
        assert result["database"] == "db"

        # Test invalid URL
        url = "invalid"
        result = service._parse_database_url(url)

        assert result is None

    @pytest.mark.asyncio
    async def test_backup_user_data(self, temp_dirs):
        """Test _backup_user_data method"""
        data_dir, backup_dir = temp_dirs
        service = BackupService(data_dir=data_dir, backup_dir=backup_dir)

        # Run backup
        result = await service._backup_user_data("test_backup")

        # Check result
        assert result["status"] == "success"
        assert result["user_count"] == 2
        assert result["total_size_bytes"] > 0
        assert "user_results" in result
        assert "user1" in result["user_results"]
        assert "user2" in result["user_results"]
        assert result["user_results"]["user1"]["status"] == "success"
        assert result["user_results"]["user2"]["status"] == "success"

        # Check that backup files were created
        backup_path = os.path.join(backup_dir, "user_data", "test_backup")
        assert os.path.exists(os.path.join(backup_path, "user1", "test1.txt"))
        assert os.path.exists(os.path.join(backup_path, "user2", "test2.txt"))

    @pytest.mark.asyncio
    async def test_backup_config(self, temp_dirs):
        """Test _backup_config method"""
        data_dir, backup_dir = temp_dirs
        service = BackupService(data_dir=data_dir, backup_dir=backup_dir)

        # Create a test config file
        config_file = os.path.join(os.getcwd(), ".env")
        with open(config_file, "w") as f:
            f.write("TEST=value")

        try:
            # Run backup
            result = await service._backup_config("test_backup")

            # Check result
            assert result["status"] == "success"
            assert "file_results" in result
            assert ".env" in result["file_results"]

            # Check that backup file was created
            backup_path = os.path.join(backup_dir, "config", "test_backup")
            assert os.path.exists(os.path.join(backup_path, ".env"))

            # Check file content
            with open(os.path.join(backup_path, ".env"), "r") as f:
                content = f.read()
                assert content == "TEST=value"
        finally:
            # Clean up
            if os.path.exists(config_file):
                os.remove(config_file)

    @pytest.mark.asyncio
    async def test_get_backup_status(self, temp_dirs):
        """Test get_backup_status method"""
        data_dir, backup_dir = temp_dirs
        service = BackupService(data_dir=data_dir, backup_dir=backup_dir)

        # Get status
        status = await service.get_backup_status()

        # Check status
        assert "status" in status
        assert "enabled" in status
        assert "frequency" in status
        assert "retention_days" in status
        assert "backup_count" in status
        assert status["status"] == "idle"

    @pytest.mark.asyncio
    async def test_start_stop_backup_scheduler(self, temp_dirs):
        """Test start_backup_scheduler and stop_backup_scheduler methods"""
        data_dir, backup_dir = temp_dirs

        # Create service with short backup frequency
        service = BackupService(
            data_dir=data_dir,
            backup_dir=backup_dir,
            backup_frequency=1,  # 1 second
        )

        # Mock run_backup to avoid actual backup
        service.run_backup = AsyncMock(return_value={"status": "success"})

        # Start scheduler
        with patch("app.backup.backup_service.BACKUP_ENABLED", True):
            await service.start_backup_scheduler()

            # Check that scheduler was started
            assert service.backup_task is not None
            assert service.backup_status["status"] == "scheduled"

            # Wait for scheduler to run
            await asyncio.sleep(2)

            # Check that run_backup was called
            assert service.run_backup.called

            # Stop scheduler
            await service.stop_backup_scheduler()

            # Check that scheduler was stopped
            assert service.backup_task is None
            assert service.backup_status["status"] == "idle"

    def test_get_backup_service_singleton(self):
        """Test get_backup_service function"""
        # Mock the BackupService class to avoid file system operations
        with patch("app.backup.backup_service.BackupService") as mock_service:
            # Configure the mock to return a specific instance
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance

            # Get service
            service1 = get_backup_service()

            # Get service again
            service2 = get_backup_service()

            # Check that both references point to the same object
            assert service1 is service2

            # Verify that BackupService constructor was called only once
            assert mock_service.call_count == 1
