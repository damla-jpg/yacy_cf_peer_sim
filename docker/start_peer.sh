#!/bin/bash

echo "Starting YaCy peer..."

# Run yacy
docker-compose up -d yacy-server

# Wait for the yacy-server container to start
echo "Waiting for yacy-server to start..."
sleep 5

# Update the yacy-server container configuration
docker exec yacy-server sh -c "cd /opt/yacy_search_server/DATA/SETTINGS && sed -i 's/port=8090/port=8091/' yacy.conf && sed -i 's/port.ssl=8443/port.ssl=8444/' yacy.conf"

# Restart the yacy-server container
echo "Restarting yacy-server..."
docker restart yacy-server

# Wait for the yacy-server container to restart
echo "Waiting for yacy-server to restart..."
sleep 5

# Ensure the yacy-server container is running
while [ "$(docker inspect -f '{{.State.Running}}' yacy-server)" != "true" ]; do
    echo "Waiting for yacy-server to be running..."
    sleep 2
done

# Run the rest of the containers
docker-compose up -d yacy-cf-backend yacy-cf-frontend

echo "All services started successfully."
