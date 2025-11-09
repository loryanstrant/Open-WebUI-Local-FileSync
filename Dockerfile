FROM python:3.11-slim

# Install cron and timezone data
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org requests pyyaml paramiko flask

# Create app directory
WORKDIR /app

# Copy application files
COPY sync.py /app/sync.py
COPY config.py /app/config.py
COPY web.py /app/web.py
COPY entrypoint.sh /app/entrypoint.sh

# Make scripts executable
RUN chmod +x /app/sync.py /app/web.py /app/entrypoint.sh

# Create data directory
RUN mkdir -p /data /app/ssh_keys /app/config

# Environment variables with defaults
ENV TZ=UTC \
    SYNC_SCHEDULE=daily \
    SYNC_TIME=00:00 \
    SYNC_DAY=0 \
    FILES_DIR=/data \
    ALLOWED_EXTENSIONS=.md,.txt,.pdf,.doc,.docx,.json,.yaml,.yml,.conf,.toml \
    STATE_FILE=/app/sync_state.json \
    OPENWEBUI_URL=http://localhost:8080 \
    OPENWEBUI_API_KEY= \
    KNOWLEDGE_BASE_NAME= \
    KNOWLEDGE_BASE_MAPPINGS= \
    KNOWLEDGE_BASE_MAPPING= \
    MAX_RETRY_ATTEMPTS=3 \
    RETRY_DELAY=60 \
    UPLOAD_TIMEOUT=300 \
    SSH_REMOTE_SOURCES= \
    SSH_KEY_PATH=/app/ssh_keys \
    SSH_STRICT_HOST_KEY_CHECKING=false \
    CONFIG_FILE=/app/config/filesync-config.json \
    WEB_PORT=8000 \
    WEB_HOST=0.0.0.0

# Volume for files to sync
VOLUME ["/data", "/app/config"]

# Expose web interface port
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
