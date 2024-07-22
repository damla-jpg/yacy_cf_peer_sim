#!/bin/bash

echo "Starting YaCy peer..."

if [ -z "$1" ]; then
    echo "Please provide the path to the YaCy peer."
    exit 1
fi

# Change to the given path
echo "Given path: $1"

cd $1
echo "The current working directory is:"
pwd

# If $2 is not empty, and is 2
if [ ! -z "$2" ] && [ "$2" == "0" ]; then
    echo "Closing the container..."

    # Stop the containers after 5 minutes
    docker-compose stop
else
    echo "Starting the first peer..."

    # Run yacy
    docker-compose up -d yacy-server-5

    # Wait for the yacy-server-5 container to start
    echo "Waiting for yacy-server-5 to start..."
    sleep 5

    # Update the yacy-server-5 container configuration
    docker exec yacy-server-5 sh -c "cd /opt/yacy_search_server/DATA/SETTINGS && sed -i 's/port=8090/port=8097/' yacy.conf && sed -i 's/port.ssl=8443/port.ssl=8449/' yacy.conf"

    # Restart the yacy-server-5 container
    echo "Restarting yacy-server-5..."
    docker restart yacy-server-5

    # Wait for the yacy-server-5 container to restart
    echo "Waiting for yacy-server-5 to restart..."
    sleep 5

    # Ensure the yacy-server-5 container is running
    while [ "$(docker inspect -f '{{.State.Running}}' yacy-server-5)" != "true" ]; do
        echo "Waiting for yacy-server-5 to be running..."
        sleep 2
    done

    # Run the rest of the containers
    docker-compose up -d yacy-cf-backend-5 yacy-cf-frontend-5

    echo "All services started successfully."
fi