FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3 \
    python3-pip \
    wget \
    curl \
    libopenblas-dev \
    ninja-build \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR  /app

RUN git clone https://github.com/ggml-org/llama.cpp.git

WORKDIR /app/llama.cpp

RUN mkdir build && cd build && \
    cmake .. -DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS -DLLAMA_CURL=OFF && \
    cmake --build . --config Release

RUN mkdir /app/models

RUN cd /app/models && \
    wget -q https://huggingface.co/bartowski/Qwen2.5-Math-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-Math-1.5B-Instruct-Q5_K_S.gguf

EXPOSE 8080

CMD ["/app/llama.cpp/build/bin/llama-server", \
     "-m", "/app/models/Qwen2.5-Math-1.5B-Instruct-Q5_K_S.gguf", \
     "-c", "2048", \
     "--host", "0.0.0.0", \
     "--port", "8080"]
