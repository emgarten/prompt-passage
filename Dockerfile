# syntax=docker/dockerfile:1

FROM python:3.12-slim AS build
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build tools and uv
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    pip install --no-cache-dir --upgrade pip uv azure-cli && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# Install dependencies using the lock file
RUN uv pip install --system -r uv.lock && \
    pip cache purge

# Copy source and install the package
COPY src ./src
RUN pip install --no-cache-dir .

# Final slim image
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Default configuration path
ENV PROMPT_PASSAGE_CONFIG_PATH=/etc/prompt-passage.yaml
ENV AZURE_CONFIG_DIR=/root/.azure

# Copy installed packages from builder
COPY --from=build /usr/local /usr/local

EXPOSE 8095
ENTRYPOINT ["llm-proxy"]
