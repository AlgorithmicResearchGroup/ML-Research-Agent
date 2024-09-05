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

# Function to run the Docker container
run_container() {
    if [ "$#" -lt 6 ]; then
        echo "Usage: run_container <image_name> <benchmark> <provider> <gpu_ids> <task_name> <time_limit> [additional docker run arguments]"
        echo "Example: run_container algorithmicresearch/agent:latest mini_benchmark openai 0 mini_mini_pile 2h /home/ubuntu/.env"
        return 1
    fi
    IMAGE_NAME=$1
    BENCHMARK=$2
    PROVIDER=$3
    GPU_IDS=$4
    TASK_NAME=$5
    TIME_LIMIT=$6
    ENV_FILE_PATH=$7
    shift 7  
    CONTAINER_NAME="agent_${TASK_NAME}_$(date +%Y%m%d_%H%M%S)"
    HOST_OUTPUT_DIR="/home/ubuntu/agent_output/${CONTAINER_NAME}"
    
    # Ensure the host output directory exists
    mkdir -p "$HOST_OUTPUT_DIR"
    
    echo "Running Docker container using GPUs: $GPU_IDS with a $TIME_LIMIT time limit..."
    docker run -d \
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

    echo "Started container $CONTAINER_NAME on GPU $GPU_IDS"
}

# Main script logic
IMAGE_NAME="algorithmicresearch/agent:latest"
BENCHMARK="mini_benchmark"  # You may want to customize this
PROVIDER="openai"  # You may want to customize this
TIME_LIMIT="2h"
ENV_FILE_PATH="/home/ubuntu/.env"  # Adjust this path as needed

# Pull the image
pull_image $IMAGE_NAME

# Array of tasks to run
TASKS=(
    "mini_llm_efficiency"
    "mini_baby_lm"
    "mini_mini_pile" 
    "mini_budget_inference" 
    "mini_llm_merging"
    "mini_math_reasoning" 
    # Add or remove tasks as needed
)

# Get the number of available GPUs
NUM_GPUS=$(nvidia-smi -L | wc -l)

# Get the number of tasks
NUM_TASKS=${#TASKS[@]}

# Determine how many containers to run
NUM_CONTAINERS=$(( NUM_TASKS < NUM_GPUS ? NUM_TASKS : NUM_GPUS ))

echo "Number of available GPUs: $NUM_GPUS"
echo "Number of tasks: $NUM_TASKS"
echo "Number of containers to run: $NUM_CONTAINERS"

# Run containers
for i in $(seq 0 $((NUM_CONTAINERS - 1))); do
    run_container $IMAGE_NAME $BENCHMARK $PROVIDER $i ${TASKS[$i]} $TIME_LIMIT $ENV_FILE_PATH &
done

# Wait for all background processes to finish
wait

echo "All containers have been started. Use 'docker ps' to check their status."