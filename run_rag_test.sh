#!/bin/bash

echo "Starting Docker containers if not already running..."
docker-compose up -d

# Make sure the database is ready
echo "Waiting for database to be ready..."
sleep 5

echo "Running RAG manager test in the Docker container..."
docker-compose exec backend python -m run_rag_test

# Check the exit code
if [ $? -eq 0 ]; then
    echo "Test execution completed successfully!"
else
    echo "Test execution failed. Check the logs for details."
    exit 1
fi 