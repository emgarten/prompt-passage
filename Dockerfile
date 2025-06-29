FROM mcr.microsoft.com/azurelinux/base/python:3.12
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHON_PATH="/app/src:/app/src/prompt_passage"

RUN set -eux; \
    rpm --import https://packages.microsoft.com/keys/microsoft.asc && \
    printf "[azure-cli]\nname=Azure CLI\nbaseurl=https://packages.microsoft.com/yumrepos/azure-cli\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc\n" \
        > /etc/yum.repos.d/azure-cli.repo && \
    tdnf -y update && \
    tdnf -y install azure-cli ca-certificates-microsoft && \
    tdnf clean all && \
    rm -rf /var/cache/tdnf

# Default configuration path
ENV PROMPT_PASSAGE_CONFIG_PATH=/etc/prompt-passage.yaml
ENV AZURE_CONFIG_DIR=/root/.azure

# Install uv
RUN pip install uv

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# Install dependencies using the lock file
RUN uv export --no-dev -o requirements.txt
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy source
COPY src ./src

EXPOSE 8095
CMD ["python3", "-m", "src.prompt_passage.cli"]
