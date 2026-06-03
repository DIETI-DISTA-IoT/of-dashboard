# Use a base image of Python
FROM python:3.10-slim

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Set additional environment variables for Kafka connection
ENV KAFKA_BROKER="kafka:9092"
ENV TOPIC_NAME="train-sensor-data"

# Install system dependencies including Docker CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update && apt-get install -y docker-ce-cli && rm -rf /var/lib/apt/lists/*

# Upgrade pip to the latest version
RUN pip install --no-cache-dir --upgrade pip

# Full rebuild bust: pass CACHE_BUST=<timestamp> to re-run pip install AND code clone.
# Used by:  make build-dashboard-scache
ARG CACHE_BUST=1

# Install dependencies from the build context (submodule checkout on disk).
# This layer is cached when using scache-nolib; re-run only when using scache.
COPY dashboard/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Code-only bust: pass CODE_BUST=<timestamp> to re-run only the git clones, keeping pip cached.
# Used by:  make build-dashboard-scache-nolib
ARG CODE_BUST=1

RUN git clone --branch sereBench https://github.com/DIETI-DISTA-IoT/of-dashboard /app

WORKDIR /app

RUN git clone --branch sereBench https://github.com/DIETI-DISTA-IoT/of-core OpenFAIR/
# NOTE: config/ will be provided at runtime via a bind-mount (see docker-compose.yml)

EXPOSE 5000

CMD ["python", "app.py"]
