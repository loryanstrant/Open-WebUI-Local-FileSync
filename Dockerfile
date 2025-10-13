FROM python:3.11-slim

# Install cron and timezone data
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org requests

# Create app directory
WORKDIR /app

# Copy application files
COPY sync.py /app/sync.py
COPY entrypoint.sh /app/entrypoint.sh

# Make scripts executable
RUN chmod +x /app/sync.py /app/entrypoint.sh

# Create data directory
RUN mkdir -p /data

# Environment variables with defaults
ENV TZ=UTC \
    SYNC_SCHEDULE=daily \
    SYNC_TIME=00:00 \
    SYNC_DAY=0 \
    FILES_DIR=/data \
    ALLOWED_EXTENSIONS=.md,.txt,.pdf,.doc,.docx \
    STATE_FILE=/app/sync_state.json \
    OPENWEBUI_URL=http://localhost:8080 \
    OPENWEBUI_API_KEY= \
    KNOWLEDGE_BASE_NAME= \
    KNOWLEDGE_BASE_MAPPINGS= \
    KNOWLEDGE_BASE_MAPPING= \
    MAX_RETRY_ATTEMPTS=3 \
    RETRY_DELAY=60 \
    UPLOAD_TIMEOUT=300

# Volume for files to sync
VOLUME ["/data"]

ENTRYPOINT ["/app/entrypoint.sh"]
