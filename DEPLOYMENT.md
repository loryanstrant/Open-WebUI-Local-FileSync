# Deployment Guide

This guide provides comprehensive deployment examples for Open-WebUI-Local-FileSync.

## Table of Contents

- [Quick Start Deployment](#quick-start-deployment)
- [Web Interface Deployment](#web-interface-deployment)
- [Environment Variable Deployment](#environment-variable-deployment)
- [Docker CLI Deployment](#docker-cli-deployment)
- [Common Deployment Scenarios](#common-deployment-scenarios)
- [Building Locally](#building-locally)

## Quick Start Deployment

The fastest way to get started is with the web interface:

1. Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    ports:
      - "8000:8000"  # Web interface
    volumes:
      - ./your-files:/data:ro
      - ./config:/app/config  # Persist configuration
      - ./state:/app/state    # Persist state across restarts
    restart: unless-stopped
```

2. Run the container:

```bash
docker-compose up -d
```

3. Access the web interface at `http://localhost:8000` and configure:
   - Open WebUI connection (URL and API key)
   - Sync schedule
   - File settings
   - Knowledge base mappings
   - And more!

## Web Interface Deployment

> 💡 **Recommended:** This is the easiest way to configure and manage your sync settings.

### Basic Web Interface Setup

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    ports:
      - "8000:8000"
    volumes:
      - ./files:/data:ro
      - ./config:/app/config
      - ./state:/app/state
    restart: unless-stopped
```

**Screenshot:**

![Web Interface Configuration](https://github.com/user-attachments/assets/16be0cc1-f778-4415-b52a-afa5adfa7c38)

See the [Web Interface Guide](WEB_INTERFACE.md) for detailed documentation.

## Environment Variable Deployment

If you prefer using environment variables for configuration:

### Basic Environment Variable Setup

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      TZ: America/New_York
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
    volumes:
      - ./your-files:/data:ro
      - ./state:/app/state
    restart: unless-stopped
```

## Docker CLI Deployment

Deploy using Docker CLI commands:

```bash
docker run -d \
  --name openwebui-filesync \
  -p 8000:8000 \
  -v /path/to/your/files:/data:ro \
  -v /path/to/config:/app/config \
  -v /path/to/state:/app/state \
  --restart unless-stopped \
  ghcr.io/loryanstrant/open-webui-local-filesync:latest
```

Then configure via web interface at `http://localhost:8000`.

## Common Deployment Scenarios

### Scenario 1: Basic Sync Without Knowledge Bases

Simple file synchronization without knowledge base organization:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      TZ: America/New_York
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
    volumes:
      - ./your-files:/data:ro
      - ./state:/app/state
    restart: unless-stopped
```

### Scenario 2: Single Knowledge Base

All files go to one knowledge base (perfect for unified collections):

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      TZ: America/New_York
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      KNOWLEDGE_BASE_NAME: "HomeConfiguration"
    volumes:
      - /etc/docker/simple-wik:/data/simple-wik:ro
      - /etc/docker/docker-documenter:/data/docker-documenter:ro
      - /etc/docker/esphome:/data/esphome:ro
      - /etc/docker/evcc:/data/evcc:ro
      - /etc/docker/zigbee2mqtt:/data/zigbee2mqtt:ro
      - ./state:/app/state
    restart: unless-stopped
```

This is much cleaner than the old approach when all files go to the same knowledge base!

### Scenario 3: Multiple Knowledge Bases with JSON Array

Organize files into different knowledge bases based on directory:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      TZ: America/New_York
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      KNOWLEDGE_BASE_MAPPINGS: '[{"path": "docs", "kb": "Documentation"}, {"path": "api", "kb": "API_Reference"}, {"path": "guides", "kb": "User_Guides"}]'
    volumes:
      - ./documentation:/data:ro
      - ./state:/app/state
    restart: unless-stopped
```

In this example:
- Files in `/data/docs/` → stored in "Documentation" knowledge base
- Files in `/data/api/` → stored in "API_Reference" knowledge base
- Files in `/data/guides/` → stored in "User_Guides" knowledge base

### Scenario 4: Multiple Knowledge Bases with Filters

Advanced filtering for selective file synchronization:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      TZ: America/New_York
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      KNOWLEDGE_BASE_MAPPINGS: |
        [
          {
            "path": "esphome",
            "kb": "ESPHome",
            "exclude": ["*/*"],
            "include": ["includes/*"]
          },
          {
            "path": "docker-documenter-for-portainer",
            "kb": "DockerDocs",
            "exclude": ["*_2025*"]
          },
          {
            "path": "zigbee2mqtt",
            "kb": "Zigbee2MQTT",
            "exclude": [".git/*", "*.log"]
          }
        ]
    volumes:
      - /etc/docker/esphome:/data/esphome:ro
      - /etc/docker/docker-documenter-for-portainer:/data/docker-documenter-for-portainer:ro
      - /etc/docker/zigbee2mqtt:/data/zigbee2mqtt:ro
      - ./state:/app/state
    restart: unless-stopped
```

### Scenario 5: Multiple Volumes to Different Knowledge Bases

Using JSON array format for clarity:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      KNOWLEDGE_BASE_MAPPINGS: '[{"path": "team-docs", "kb": "Team_Documentation"}, {"path": "customer-docs", "kb": "Customer_Documentation"}]'
    volumes:
      - ./team-docs:/data/team-docs:ro
      - ./customer-docs:/data/customer-docs:ro
      - ./state:/app/state
    restart: unless-stopped
```

Or using legacy format (still supported):

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      KNOWLEDGE_BASE_MAPPING: "team-docs:Team_Documentation,customer-docs:Customer_Documentation"
    volumes:
      - ./team-docs:/data/team-docs:ro
      - ./customer-docs:/data/customer-docs:ro
      - ./state:/app/state
    restart: unless-stopped
```

### Scenario 6: Hourly Sync

Sync files every hour at 30 minutes past:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      SYNC_SCHEDULE: hourly
      SYNC_TIME: "00:30"  # At 30 minutes past each hour
    volumes:
      - ./your-files:/data:ro
      - ./state:/app/state
    restart: unless-stopped
```

### Scenario 7: Weekly Sync

Sync files every Sunday at 3 AM UTC:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      TZ: UTC
      SYNC_SCHEDULE: weekly
      SYNC_TIME: "03:00"
      SYNC_DAY: "0"  # or "sun"
    volumes:
      - ./your-files:/data:ro
      - ./state:/app/state
    restart: unless-stopped
```

Or every Friday at 5 PM PST:

```yaml
environment:
  TZ: America/Los_Angeles
  SYNC_SCHEDULE: weekly
  SYNC_TIME: "17:00"
  SYNC_DAY: "5"  # or "fri"
```

### Scenario 8: SSH Remote File Ingestion (Password Auth)

Fetch files from remote servers via SSH using password authentication:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      SSH_REMOTE_SOURCES: |
        [
          {
            "host": "192.168.1.100",
            "port": 22,
            "username": "backup_user",
            "password": "secure_password",
            "paths": ["/home/user/documents", "/var/log/app.log"],
            "kb": "Remote_Backups"
          }
        ]
    volumes:
      - ./state:/app/state
    restart: unless-stopped
```

### Scenario 9: SSH Remote File Ingestion (Key Auth)

Fetch files from remote servers via SSH using SSH key authentication:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      SSH_REMOTE_SOURCES: |
        [
          {
            "host": "server.example.com",
            "username": "deploy",
            "key_filename": "deploy_key",
            "paths": ["/var/www/html/docs"],
            "kb": "Production_Docs"
          }
        ]
    volumes:
      - ./ssh_keys:/app/ssh_keys:ro
      - ./state:/app/state
    restart: unless-stopped
```

See the [docker-compose-ssh-example.yml](docker-compose-ssh-example.yml) file for a complete SSH configuration example.

### Scenario 10: Multiple SSH Sources

Connect to multiple SSH servers with different configurations:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      SSH_REMOTE_SOURCES: |
        [
          {
            "host": "dev-server.local",
            "username": "developer",
            "password": "dev_pass",
            "paths": ["/opt/app/config"],
            "kb": "Dev_Config"
          },
          {
            "host": "prod-server.com",
            "username": "prod_user",
            "key_filename": "prod_key",
            "paths": ["/etc/app/config", "/var/app/docs"],
            "kb": "Prod_Config"
          }
        ]
    volumes:
      - ./ssh_keys:/app/ssh_keys:ro
      - ./state:/app/state
    restart: unless-stopped
```

## Building Locally

If you want to build the image yourself:

```bash
# Clone the repository
git clone https://github.com/loryanstrant/Open-WebUI-Local-FileSync.git
cd Open-WebUI-Local-FileSync

# Build the image
docker build -t open-webui-local-filesync .

# Run with your custom image
docker run -d \
  --name openwebui-filesync \
  -p 8000:8000 \
  -v /path/to/your/files:/data:ro \
  -v /path/to/config:/app/config \
  -v /path/to/state:/app/state \
  --restart unless-stopped \
  open-webui-local-filesync
```

## Related Documentation

- [Configuration Guide](CONFIGURATION.md) - Complete configuration reference
- [Quick Start Guide](QUICKSTART.md) - Getting started quickly
- [Examples](EXAMPLES.md) - More comprehensive examples
- [Web Interface Guide](WEB_INTERFACE.md) - Using the web configuration interface
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
