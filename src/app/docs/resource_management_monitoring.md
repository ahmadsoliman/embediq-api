# Resource Management and Monitoring

This document provides an overview of the Resource Management and Monitoring features in the EmbedIQ backend, including system monitoring, backup utilities, and LightRAG configuration options.

## Table of Contents

1. [System Monitoring](#system-monitoring)
2. [LightRAG Performance Monitoring](#lightrag-performance-monitoring)
3. [Backup and Data Replication](#backup-and-data-replication)
4. [LightRAG Configuration](#lightrag-configuration)
5. [API Endpoints](#api-endpoints)
6. [Environment Variables](#environment-variables)

## System Monitoring

The system monitoring module tracks resource usage and provides health check information for the EmbedIQ backend.

### Features

- **CPU Monitoring**: Tracks CPU usage, load averages, and per-core utilization
- **Memory Monitoring**: Tracks memory usage, available memory, and swap usage
- **Disk Monitoring**: Tracks disk space usage, including user-specific storage
- **Network Monitoring**: Tracks network traffic, including bytes sent/received
- **Process Monitoring**: Tracks the application process, including CPU and memory usage
- **Health Checks**: Provides comprehensive health status based on resource thresholds

### Usage

The `SystemMonitor` class is the main entry point for system monitoring:

```python
from app.monitoring.system_monitor import SystemMonitor

# Create a system monitor
monitor = SystemMonitor(data_dir="/path/to/data")

# Get system metrics
metrics = monitor.get_system_metrics()

# Get health check
health = monitor.get_health_check()
```

## LightRAG Performance Monitoring

The LightRAG performance monitoring module tracks the performance of LightRAG operations, including query times, throughput, and error rates.

### Features

- **Query Monitoring**: Tracks query operation times and counts
- **Search Monitoring**: Tracks search operation times and counts
- **Insert Monitoring**: Tracks document insertion times and counts
- **Error Tracking**: Tracks operation errors
- **Performance Metrics**: Provides average, minimum, maximum, and percentile operation times
- **Throughput Calculation**: Calculates operations per second

### Usage

The `LightRAGMonitor` class is the main entry point for LightRAG performance monitoring:

```python
from app.monitoring.lightrag_monitor import get_lightrag_monitor, monitor_lightrag_operation

# Get the LightRAG monitor singleton
monitor = get_lightrag_monitor()

# Record operation times manually
monitor.record_query_time(0.1)  # 100ms query time
monitor.record_search_time(0.2)  # 200ms search time
monitor.record_insert_time(0.3)  # 300ms insert time

# Record errors
monitor.record_error()

# Get performance metrics
metrics = monitor.get_metrics()

# Reset metrics
monitor.reset_metrics()

# Use the decorator to automatically monitor operations
@monitor_lightrag_operation("query")
async def my_query_function():
    # Function implementation
    pass
```

## Backup and Data Replication

The backup and data replication module provides functionality to backup user data and database data, and to restore from backups.

### Features

- **User Data Backup**: Backs up user data directories
- **Database Backup**: Backs up the PostgreSQL database using pg_dump
- **Configuration Backup**: Backs up configuration files
- **Scheduled Backups**: Runs backups on a configurable schedule
- **Retention Policy**: Automatically cleans up old backups based on retention policy
- **Restore Functionality**: Restores user data and database from backups
- **Backup History**: Tracks backup history and status

### Usage

The `BackupService` class is the main entry point for backup and data replication:

```python
from app.backup.backup_service import get_backup_service

# Get the backup service singleton
backup_service = get_backup_service()

# Start the backup scheduler
await backup_service.start_backup_scheduler()

# Trigger a manual backup
backup_result = await backup_service.trigger_backup()

# Get backup status
status = await backup_service.get_backup_status()

# Get backup history
history = await backup_service.get_backup_history(limit=10)

# Restore from a backup
restore_result = await backup_service.restore_backup(backup_id="backup_20230101_120000")

# Stop the backup scheduler
await backup_service.stop_backup_scheduler()
```

## LightRAG Configuration

The LightRAG configuration module provides functionality to configure LightRAG parameters, including chunk sizes, embedding model parameters, and graph traversal depth.

### Features

- **User-Specific Configuration**: Supports user-specific configuration overrides
- **Default Configuration**: Provides sensible defaults for all parameters
- **Parameter Validation**: Validates configuration parameters to ensure they are within acceptable ranges
- **Runtime Configuration**: Allows changing configuration at runtime
- **Configuration Reset**: Allows resetting configuration to defaults

### Configurable Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `chunk_size` | Size of text chunks for embedding | 1000 | 100-5000 |
| `graph_traversal_depth` | Maximum depth for graph traversal | 3 | 1-5 |
| `cache_enabled` | Whether to enable caching | true | boolean |
| `cache_size` | Number of items to cache | 1000 | 10-10000 |
| `vector_dimension` | Dimension of embedding vectors | 1536 | 768-4096 |
| `max_token_size` | Maximum token size for text processing | 8192 | 1024-32768 |

### Usage

The `LightRAGConfig` class and related functions are the main entry points for LightRAG configuration:

```python
from app.config.lightrag_config import get_lightrag_config, set_lightrag_config, reset_lightrag_config

# Get configuration for a user
config = get_lightrag_config(user_id="user123")

# Update configuration for a user
new_config = set_lightrag_config(
    config={"chunk_size": 2000, "graph_traversal_depth": 4},
    user_id="user123"
)

# Reset configuration for a user
reset_lightrag_config(user_id="user123")

# Get default configuration
default_config = get_lightrag_config()

# Update default configuration
new_default_config = set_lightrag_config(
    config={"chunk_size": 1500, "cache_size": 2000}
)

# Reset all configurations to default
reset_lightrag_config()
```

## API Endpoints

### Monitoring Endpoints

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/monitoring/system` | GET | Get system metrics | Admin |
| `/api/v1/monitoring/lightrag` | GET | Get LightRAG performance metrics | Admin |
| `/api/v1/monitoring/lightrag/reset` | POST | Reset LightRAG performance metrics | Admin |
| `/api/v1/monitoring/health` | GET | Get health check | Public |
| `/api/v1/monitoring/user/{user_id}` | GET | Get metrics for a specific user | Admin |

### Backup Endpoints

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/backup/status` | GET | Get backup status | Admin |
| `/api/v1/backup/history` | GET | Get backup history | Admin |
| `/api/v1/backup/trigger` | POST | Trigger a manual backup | Admin |
| `/api/v1/backup/restore/{backup_id}` | POST | Restore from a backup | Admin |
| `/api/v1/backup/start` | POST | Start the backup scheduler | Admin |
| `/api/v1/backup/stop` | POST | Stop the backup scheduler | Admin |

### Configuration Endpoints

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/config/lightrag` | GET | Get LightRAG configuration | User |
| `/api/v1/config/lightrag` | PUT | Update LightRAG configuration | User |
| `/api/v1/config/lightrag` | DELETE | Reset LightRAG configuration | User |
| `/api/v1/config/lightrag/default` | GET | Get default LightRAG configuration | Admin |
| `/api/v1/config/lightrag/default` | PUT | Update default LightRAG configuration | Admin |
| `/api/v1/config/lightrag/default` | DELETE | Reset default LightRAG configuration | Admin |

## Environment Variables

The following environment variables can be used to configure the Resource Management and Monitoring features:

### Monitoring Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ADMIN_USER_IDS` | Comma-separated list of admin user IDs | `""` |
| `MONITORING_ENABLED` | Whether to enable monitoring | `true` |
| `MONITORING_LOG_LEVEL` | Log level for monitoring | `INFO` |

### Backup Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKUP_ENABLED` | Whether to enable backup | `true` |
| `BACKUP_DIR` | Directory to store backups | `/data/embediq/backups` |
| `BACKUP_FREQUENCY` | Backup frequency in seconds | `86400` (daily) |
| `BACKUP_RETENTION_DAYS` | Number of days to retain backups | `7` |

### LightRAG Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `CHUNK_SIZE` | Size of text chunks for embedding | `1000` |
| `GRAPH_TRAVERSAL_DEPTH` | Maximum depth for graph traversal | `3` |
| `CACHE_ENABLED` | Whether to enable caching | `true` |
| `CACHE_SIZE` | Number of items to cache | `1000` |
| `VECTOR_DIMENSION` | Dimension of embedding vectors | `1536` |
| `MAX_TOKEN_SIZE` | Maximum token size for text processing | `8192` |
