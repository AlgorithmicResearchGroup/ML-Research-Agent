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
# Function to run the Docker container
run_container() {
    if [ "$#" -ne 8 ]; then
        echo "Usage: run_container <image_name> <benchmark> <provider> <gpu_ids> <task_name> <time_limit> <huggingface_token> <env_file_path>"
        echo "Example: run_container algorithmicresearch/agent:latest mini_benchmark openai 0 mini_mini_pile 2h hf_token /home/ubuntu/.env"
        return 1
    fi
    IMAGE_NAME="$1"
    BENCHMARK="$2"
    PROVIDER="$3"
    GPU_IDS="$4"
    TASK_NAME="$5"
    TIME_LIMIT="$6"
    HUGGINGFACE_TOKEN="$7"
    ENV_FILE_PATH="$8"

    echo "IMAGE_NAME: $IMAGE_NAME"
    echo "BENCHMARK: $BENCHMARK"
    echo "PROVIDER: $PROVIDER"
    echo "GPU_IDS: $GPU_IDS"
    echo "TASK_NAME: $TASK_NAME"
    echo "TIME_LIMIT: $TIME_LIMIT"
    echo "HUGGINGFACE_TOKEN: $HUGGINGFACE_TOKEN"
    echo "ENV_FILE_PATH: $ENV_FILE_PATH"

    CONTAINER_NAME="agent_${TASK_NAME}_$(date +%Y%m%d_%H%M%S)"
    HOST_OUTPUT_DIR="/home/ubuntu/agent_output/${CONTAINER_NAME}"

    # Ensure the host output directory exists
    mkdir -p "$HOST_OUTPUT_DIR"

    echo "Running Docker container using GPUs: $GPU_IDS with a $TIME_LIMIT time limit..."
    #timeout $TIME_LIMIT docker run -it \


    docker run -it \
        --name $CONTAINER_NAME \
        --gpus "device=$GPU_IDS" \
        -e NVIDIA_VISIBLE_DEVICES=$GPU_IDS \
        -e BENCHMARK=$BENCHMARK \
        -e PROVIDER=$PROVIDER \
        -e TASK_NAME=$TASK_NAME \
        -e HUGGINGFACE_TOKEN=$HUGGINGFACE_TOKEN \
        -v "$HOST_OUTPUT_DIR:/app/output" \
        --env-file $ENV_FILE_PATH \
        -v $ENV_FILE_PATH:/app/.env \
        $IMAGE_NAME

    DOCKER_PID=$!

    # Wait for the container to finish or timeout
    if ! timeout ${TIME_LIMIT}s tail --pid=$DOCKER_PID -f /dev/null; then
        echo "Container $CONTAINER_NAME reached time limit. Stopping..."
        docker stop $CONTAINER_NAME
    fi

    wait $DOCKER_PID
    CONTAINER_EXIT_CODE=$?

    if [ $CONTAINER_EXIT_CODE -eq 0 ]; then
        echo "Container $CONTAINER_NAME completed successfully"
    elif [ $CONTAINER_EXIT_CODE -eq 124 ]; then
        echo "Container $CONTAINER_NAME was terminated after reaching the 2-hour time limit"
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
if [ "$#" -ne 8 ]; then
    echo "Usage: $0 <image_name> <benchmark> <provider> <gpu_ids> <task_name> <time_limit> <huggingface_token> <env_file_path>"
    exit 1
fi

IMAGE_NAME="$1"
BENCHMARK="$2"
PROVIDER="$3"
GPU_IDS="$4"
TASK_NAME="$5"
TIME_LIMIT="$6"
HUGGINGFACE_TOKEN="$7"
ENV_FILE_PATH="$8"

# Pull the image
pull_image "$IMAGE_NAME"

# Run the container
run_container "$IMAGE_NAME" "$BENCHMARK" "$PROVIDER" "$GPU_IDS" "$TASK_NAME" "$TIME_LIMIT" "$HUGGINGFACE_TOKEN" "$ENV_FILE_PATH"

