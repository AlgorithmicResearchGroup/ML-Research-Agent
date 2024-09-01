#!/bin/bash

# Function to build the Docker image
build_image() {
    if [ "$#" -ne 3 ]; then
        echo "Usage: build <image_name> <model_size> <provider>"
        echo "Example: build all-tasks large openai"
        return 1
    fi

    IMAGE_NAME=$1
    MODEL_SIZE=$2
    PROVIDER=$3

    TAG="${IMAGE_NAME}_${MODEL_SIZE}_${PROVIDER}"

    echo "Building Docker image with tag: agent:$TAG"
    docker build \
        --build-arg MODEL_SIZE=$MODEL_SIZE \
        --build-arg PROVIDER=$PROVIDER \
        -t agent:$TAG .

    if [ $? -eq 0 ]; then
        echo "Successfully built image: agent:$TAG"
    else
        echo "Failed to build image: agent:$TAG"
        return 1
    fi
}

# Function to run the Docker container and copy files
run_container() {
    if [ "$#" -lt 5 ]; then
        echo "Usage: run <image_name> <model_size> <provider> <gpu_ids> <task_name> [additional docker run arguments]"
        echo "Example: run all-tasks large openai 0,1 pretraining_efficiency"
        return 1
    fi

    IMAGE_NAME=$1
    MODEL_SIZE=$2
    PROVIDER=$3
    GPU_IDS=$4
    TASK_NAME=$5
    shift 5  # Remove the first 5 arguments

    TAG="${IMAGE_NAME}_${MODEL_SIZE}_${PROVIDER}"
    CONTAINER_NAME="my_gpu_app_${IMAGE_NAME}_${MODEL_SIZE}_${PROVIDER}_${TASK_NAME}"
    
    # Set the output directory to /home/paperspace/Desktop/
    HOST_OUTPUT_DIR="/home/paperspace/Desktop/${IMAGE_NAME}_${MODEL_SIZE}_${PROVIDER}_${TASK_NAME}"

    # Ensure the host output directory exists
    mkdir -p "$HOST_OUTPUT_DIR"

    # Check if a container with this name already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "Container ${CONTAINER_NAME} already exists. Removing it..."
        docker rm -f ${CONTAINER_NAME}
    fi

    echo "Running Docker container using GPUs: $GPU_IDS"
    echo "Command: docker run -it --name $CONTAINER_NAME --gpus \"device=$GPU_IDS\" -e NVIDIA_VISIBLE_DEVICES=$GPU_IDS -e MODEL_SIZE=$MODEL_SIZE -e PROVIDER=$PROVIDER -e TASK_NAME=$TASK_NAME -v \"$HOST_OUTPUT_DIR:/app/output\" $@ agent:$TAG"
    
    docker run -it \
        --name $CONTAINER_NAME \
        --gpus "device=$GPU_IDS" \
        -e NVIDIA_VISIBLE_DEVICES=$GPU_IDS \
        -e MODEL_SIZE=$MODEL_SIZE \
        -e PROVIDER=$PROVIDER \
        -e TASK_NAME=$TASK_NAME \
        -v "$HOST_OUTPUT_DIR:/app/output" \
        "$@" \
        agent:$TAG

    # Check the exit status
    CONTAINER_EXIT_CODE=$?

    if [ $CONTAINER_EXIT_CODE -eq 0 ]; then
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
case "$1" in
    build)
        shift  # Remove 'build' from the arguments
        build_image "$@"
        ;;
    run)
        shift  # Remove 'run' from the arguments
        run_container "$@"
        ;;
    *)
        echo "Usage: $0 {build|run}"
        echo "  build <image_name> <model_size> <provider> - Build the Docker image"
        echo "  run <image_name> <model_size> <provider> <gpu_ids> [additional docker run arguments] - Run the container and copy files"
        exit 1
        ;;
esac