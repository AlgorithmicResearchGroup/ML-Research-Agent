Build Single Versatile Docker Image

#!/bin/bash

# Fixed variables
IMAGE_NAME="all-tasks"
MODEL_SIZE="x-small"
PROVIDER="anthropic"

# Build a single, versatile container
echo "Building a single, versatile container for all tasks..."
echo "Image name: $IMAGE_NAME"
echo "Model size: $MODEL_SIZE"
echo "Provider: $PROVIDER"
echo "----------------------------------------"

./manage_docker.sh build "$IMAGE_NAME" "$MODEL_SIZE" "$PROVIDER"

if [ $? -eq 0 ]; then
    echo "Successfully built container for all tasks"
    echo "----------------------------------------"
    echo "You can now run different tasks using:"
    echo "./manage_docker.sh run $IMAGE_NAME $MODEL_SIZE $PROVIDER <gpu_ids> <time_limit> -e TASK_NAME=<task_name>"
    echo "Example:"
    echo "./manage_docker.sh run $IMAGE_NAME $MODEL_SIZE $PROVIDER 0 2h -e TASK_NAME=pretraining_efficiency"
else
    echo "Failed to build container"
    exit 1
fi