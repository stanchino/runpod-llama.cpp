# ================================
# Stage 1: Model Preparation
# ================================
FROM ghcr.io/ggml-org/llama.cpp:light-cuda AS model-downloader

WORKDIR /app
# Make sure /build/models exists even if nothing is downloaded
RUN mkdir -p /app/models

# Accept model-related args/envs
ARG MODEL_NAME
# Download the model to reuse it in the runtime image
RUN /app/llama-cli --hf-repo ${MODEL_NAME} -no-cnv -c 10 -n 2 -p "hi"

# =================================
# Stage 2: Prepare production image
# =================================
FROM ghcr.io/ggml-org/llama.cpp:server-cuda AS builder

RUN apt-get update && apt-get install -y python3 python3-venv \
 && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /app/.venv 
# Python packages (RunPod SDK + utilities)
RUN /app/.venv/bin/python3 -m pip install --no-cache-dir --upgrade pip && \
    /app/.venv/bin/python3 -m pip install --no-cache-dir \
        runpod \
        fastapi \
        requests \
        psutil

WORKDIR /app
COPY src /app

# Create non-root user
# RUN groupadd -r llama && useradd -r -g llama -u 1001 llamauser

# Copy built binary and models
# COPY --from=builder /app/llama-server /usr/local/bin/llama-server
FROM builder AS runtime
COPY --from=builder /app /app
# COPY --from=model-downloader /root/.cache/llama.cpp /root/.cache/llama.cpp

ARG MODEL_NAME
ENV MODEL_NAME=${MODEL_NAME}

# Env
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV GGML_CUDA_NO_PINNED=0
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
ENV PYTHONUNBUFFERED=1
ENV HF_HUB_ENABLE_HF_TRANSFER=1

EXPOSE ${PORT:-80}

# Health check for RunPod compatibility
# HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
#   CMD curl -f http://localhost:${PORT}/ping || exit 1

# ENV CUDA_VISIBLE_DEVICES=0
# Run as non-root after files are in place

# Prefer an explicit entrypoint (avoids NVIDIA entrypoint arg mishaps)
ENTRYPOINT ["/app/.venv/bin/python3", "/app/handler.py"]
# ENTRYPOINT ["/app/llama-server", "--list-devices"]
#ENTRYPOINT ["/bin/bash"]
