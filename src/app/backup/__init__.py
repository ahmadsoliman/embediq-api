"""
Backup package for EmbedIQ backend.

This package provides backup and data replication utilities for user data
and database backups.
"""

from app.backup.backup_service import BackupService

__all__ = ["BackupService"]
