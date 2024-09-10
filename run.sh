

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
    if [ "$#" -lt 6 ]; then
        echo "Usage: run_container <image_name> <benchmark> <provider> <gpu_ids> <task_name> [additional docker run arguments]"
        echo "Example: run_container algorithmicresearch/agent:latest mini_benchmark openai 0 mini_mini_pile /home/ubuntu/.env"
        return 1
    fi
    IMAGE_NAME=$1
    BENCHMARK=$2
    PROVIDER=$3
    GPU_IDS=$4
    TASK_NAME=$5
    ENV_FILE_PATH=$6
    shift 7  

    CONTAINER_NAME="agent_${TASK_NAME}_$(date +%Y%m%d_%H%M%S)"
    HOST_OUTPUT_DIR="/home/ubuntu/agent_output/${CONTAINER_NAME}"

    # Ensure the host output directory exists
    mkdir -p "$HOST_OUTPUT_DIR"

    echo "Running Docker container using GPUs: $GPU_IDS"
    #timeout $TIME_LIMIT docker run -it \


    docker run -it \
        --name $CONTAINER_NAME \
        --gpus "device=$GPU_IDS" \
        -e NVIDIA_VISIBLE_DEVICES=$GPU_IDS \
        -e BENCHMARK=$BENCHMARK \
        -e PROVIDER=$PROVIDER \
        -e TASK_NAME=$TASK_NAME \
        -v "$HOST_OUTPUT_DIR:/app/output" \
        --env-file $ENV_FILE_PATH \
        -v $ENV_FILE_PATH:/app/.env \
        $IMAGE_NAME


    # Copy files from container to host
    echo "Copying files from container to host..."
    docker exec $CONTAINER_NAME rm /app/.env  # Remove .env from container
    docker cp $CONTAINER_NAME:/app/. "$HOST_OUTPUT_DIR"
    echo "Files copied to $HOST_OUTPUT_DIR"

}

# Main script logic
IMAGE_NAME="algorithmicresearch/agent:latest"
BENCHMARK=$2
PROVIDER=$3
GPU_IDS=$4
TASK_NAME=$5
ENV_FILE_PATH=$6
# Pull the image
pull_image $IMAGE_NAME

# Run the container
run_container $IMAGE_NAME $BENCHMARK $PROVIDER $GPU_IDS $TASK_NAME $ENV_FILE_PATH

