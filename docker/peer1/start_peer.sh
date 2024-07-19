#!/bin/bash

echo "Starting YaCy peer..."

# Run yacy
docker-compose up -d yacy-server-1

# Wait for the yacy-server-1 container to start
echo "Waiting for yacy-server-1 to start..."
sleep 5

# Update the yacy-server-1 container configuration
docker exec yacy-server-1 sh -c "cd /opt/yacy_search_server/DATA/SETTINGS && sed -i 's/port=8090/port=8093/' yacy.conf && sed -i 's/port.ssl=8443/port.ssl=8445/' yacy.conf"

# Restart the yacy-server-1 container
echo "Restarting yacy-server-1..."
docker restart yacy-server-1

# Wait for the yacy-server-1 container to restart
echo "Waiting for yacy-server-1 to restart..."
sleep 5

# Ensure the yacy-server-1 container is running
while [ "$(docker inspect -f '{{.State.Running}}' yacy-server-1)" != "true" ]; do
    echo "Waiting for yacy-server-1 to be running..."
    sleep 2
done

# Run the rest of the containers
docker-compose up -d yacy-cf-backend-1 yacy-cf-frontend-1

echo "All services started successfully."
