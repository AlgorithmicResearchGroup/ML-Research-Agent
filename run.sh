#!/bin/bash

# Function to pull the Docker image if it's not already on the machine
pull_image() {
    local IMAGE_NAME=$1
    if ! docker image inspect $IMAGE_NAME >/dev/null 2>&1; then
        echo "Image $IMAGE_NAME not found locally. Pulling from Docker Hub..."
        docker pull $IMAGE_NAME
    else
        echo "Image $IMAGE_NAME already exists locally."
    fi
}

# Function to run the Docker container with a 2-hour time limit
run_container() {
    local IMAGE_NAME=$1
    local CONTAINER_NAME=$2
    local HOST_OUTPUT_DIR=$3
    shift 3

    # Ensure the host output directory exists
    mkdir -p "$HOST_OUTPUT_DIR"

    # Check if a container with this name already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "Container ${CONTAINER_NAME} already exists. Removing it..."
        docker rm -f ${CONTAINER_NAME}
    fi

    echo "Running Docker container with a 2-hour time limit..."
    timeout 2h docker run -it \
        --name $CONTAINER_NAME \
        --gpus all \
        -e NVIDIA_VISIBLE_DEVICES=0 \
        -v "$HOST_OUTPUT_DIR:/app/output" \
        "$@" \
        $IMAGE_NAME

    # Check the exit status
    CONTAINER_EXIT_CODE=$?

    if [ $CONTAINER_EXIT_CODE -eq 124 ]; then
        echo "Container $CONTAINER_NAME timed out after 2 hours"
    elif [ $CONTAINER_EXIT_CODE -eq 0 ]; then
        echo "Container $CONTAINER_NAME completed successfully"
    else
        echo "Container $CONTAINER_NAME exited with status $CONTAINER_EXIT_CODE"
    fi

    # Copy files from container to host
    echo "Copying files from container to host..."
    docker cp $CONTAINER_NAME:/app/. "$HOST_OUTPUT_DIR"
    echo "Files copied to $HOST_OUTPUT_DIR"

    # Remove the container
    echo "Removing the container..."
    docker rm $CONTAINER_NAME
}

# Main script logic
# Main script logic
IMAGE_NAME="algorithmicresearch/agent:latest"
CONTAINER_NAME="agent_container"
HOST_OUTPUT_DIR="/home/ubuntu/agent_output"

# Check if all required arguments are provided
if [ "$#" -lt 4 ]; then
    echo "Usage: $0 <benchmark> <provider> <task_name> <env_file_path>"
    exit 1
fi

BENCHMARK="$1"
PROVIDER="$2"
TASK_NAME="$3"
ENV_FILE_PATH="$4"

# Pull the image
pull_image $IMAGE_NAME

# Run the container
run_container $IMAGE_NAME $CONTAINER_NAME $HOST_OUTPUT_DIR \
    -e BENCHMARK="$BENCHMARK" \
    -e PROVIDER="$PROVIDER" \
    -e TASK_NAME="$TASK_NAME" \
    --env-file "$ENV_FILE_PATH" \
    -v "$ENV_FILE_PATH:/app/.env"