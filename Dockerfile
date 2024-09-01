# Use CUDA 12.1 base image
FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

# Accept build-time arguments
ARG TASK_NAME
ARG MODEL_SIZE
ARG PROVIDER

ENV DEBIAN_FRONTEND=noninteractive \
    TASK_NAME=$TASK_NAME \
    MODEL_SIZE=$MODEL_SIZE \
    PROVIDER=$PROVIDER \
    NVIDIA_VISIBLE_DEVICES=all

RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    git \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y python3.11 python3.11-distutils python3.11-dev \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --set python3 /usr/bin/python3.11 \
    && wget https://bootstrap.pypa.io/get-pip.py \
    && python3 get-pip.py \
    && rm get-pip.py \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*



WORKDIR /app

# Copy the Python script and requirements to the working directory
COPY . /app

# Install the required Python packages
RUN pip3 install -r requirements.txt 


# Set the NVIDIA_VISIBLE_DEVICES environment variable
# This will be overridden by the docker run command
ENV NVIDIA_VISIBLE_DEVICES=all

# Set environment variables from build args
ENV TASK_NAME=$TASK_NAME
ENV MODEL_SIZE=$MODEL_SIZE
ENV PROVIDER=$PROVIDER
ENV HUGGING_FACE_HUB_TOKEN=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

# Run the Python script
CMD ["sh", "-c", "python3 run.py --task_name ${TASK_NAME} --model_size ${MODEL_SIZE} --provider ${PROVIDER}"]