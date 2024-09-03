# Use CUDA 12.1 base image
FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

# Accept build-time arguments
ARG TASK_NAME
ARG BENCHMARK
ARG PROVIDER

ENV DEBIAN_FRONTEND=noninteractive \
    TASK_NAME=$TASK_NAME \
    BENCHMARK=$BENCHMARK \
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
RUN pip3 install -i https://test.pypi.org/simple/ agent-tasks


# Set the NVIDIA_VISIBLE_DEVICES environment variable
# This will be overridden by the docker run command
ENV NVIDIA_VISIBLE_DEVICES=all

# Set environment variables from build args
ENV TASK_NAME=$TASK_NAME
ENV BENCHMARK=$BENCHMARK
ENV PROVIDER=$PROVIDER

# Run the Python script
CMD ["sh", "-c", "python3 run.py --task_name ${TASK_NAME} --benchmark ${BENCHMARK} --provider ${PROVIDER}"]