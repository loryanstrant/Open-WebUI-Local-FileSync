# Web Interface for Configuration Management

## Overview

The Open-WebUI-Local-FileSync now includes a web-based configuration interface that allows you to manage all settings through a browser instead of editing docker-compose.yml environment variables.

**Screenshot:**

![Web Interface Configuration](https://github.com/user-attachments/assets/16be0cc1-f778-4415-b52a-afa5adfa7c38)

## Features

- **Visual Configuration Editor**: Easy-to-use web interface for all settings
- **Persistent Configuration**: Saves to a JSON file in the container's volume
- **Live Updates**: Changes take effect on the next sync cycle
- **Configuration Export**: Download your configuration as JSON
- **Migration Tool**: Convert environment variable configuration to config file

## Quick Start

### Using the Web Interface

1. **Start the container with minimal environment variables:**

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    ports:
      - "8000:8000"  # Web interface
    volumes:
      - ./files:/data:ro
      - ./config:/app/config  # Persist configuration
      - ./state:/app/state    # Persist state
    restart: unless-stopped
```

2. **Access the web interface:**

   Open your browser to `http://localhost:8000`

3. **Configure your sync settings:**
   - Open WebUI connection details (URL and API key)
   - Sync schedule (hourly, daily, weekly)
   - File settings and allowed extensions
   - Knowledge base mappings
   - SSH remote sources (optional)
   - Retry and upload settings

4. **Save and restart:**

   Click "Save Configuration" to persist your settings. The configuration will be used on the next sync cycle.

## Configuration File

The web interface saves configuration to `/app/config/filesync-config.json` inside the container. This file is persisted through the volume mount at `./config:/app/config`.

### Configuration File Format

```json
{
  "openwebui": {
    "url": "http://openwebui:8080",
    "api_key": "your_api_key"
  },
  "sync": {
    "schedule": "daily",
    "time": "00:00",
    "day": "0",
    "timezone": "UTC"
  },
  "files": {
    "directory": "/data",
    "allowed_extensions": [".md", ".txt", ".pdf", ".doc", ".docx", ".json", ".yaml", ".yml"],
    "state_file": "/app/sync_state.json"
  },
  "knowledge_bases": {
    "single_kb_mode": false,
    "single_kb_name": "",
    "mappings": [
      {
        "path": "docs",
        "kb": "Documentation",
        "exclude": ["*.log"],
        "include": []
      }
    ]
  },
  "retry": {
    "max_attempts": 3,
    "delay": 60,
    "upload_timeout": 300
  },
  "ssh": {
    "enabled": false,
    "key_path": "/app/ssh_keys",
    "strict_host_key_checking": false,
    "sources": []
  },
  "volumes": []
}
```

## Migrating from Environment Variables

If you have an existing deployment using environment variables, you can migrate to the config file:

1. Start the container with your existing environment variables
2. Access the web interface at `http://localhost:8000/migrate`
3. Your environment variables will be converted to the config file
4. Update your docker-compose.yml to remove environment variables (except WEB_PORT if needed)

## API Endpoints

The web interface also provides REST API endpoints for programmatic configuration management:

- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration (requires JSON body)
- `GET /export_json` - Download configuration as JSON

Example:

```bash
# Get current config
curl http://localhost:8000/api/config

# Update config
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d @config.json
```

## Environment Variables (Web Interface)

The following environment variables control the web interface itself:

| Variable | Description | Default |
|----------|-------------|---------|
| `WEB_PORT` | Port for web interface | `8000` |
| `WEB_HOST` | Host to bind web server | `0.0.0.0` |
| `CONFIG_FILE` | Path to config file | `/app/config/filesync-config.json` |

## Backward Compatibility

The container maintains full backward compatibility with environment variable configuration. If no config file exists, the container will use environment variables as before. This allows you to:

- Continue using existing deployments without changes
- Gradually migrate to the web interface
- Use a mix of both (config file takes precedence)

## Security Considerations

- The web interface does not include authentication by default
- It's recommended to:
  - Keep the web interface on a private network
  - Use a reverse proxy with authentication if exposing externally
  - Restrict access using firewall rules
  - Use HTTPS/TLS when accessing remotely

## Troubleshooting

### Web Interface Not Accessible

1. Check that port 8000 is exposed in docker-compose.yml:
   ```yaml
   ports:
     - "8000:8000"
   ```

2. Check container logs:
   ```bash
   docker logs openwebui-filesync
   ```

3. Verify the web server started:
   ```bash
   docker exec openwebui-filesync ps aux | grep web.py
   ```

### Configuration Not Persisting

Ensure the config volume is mounted:
```yaml
volumes:
  - ./config:/app/config
```

Check permissions on the host directory:
```bash
ls -la ./config
```

### Changes Not Taking Effect

The sync process runs on the configured schedule. To trigger an immediate sync after configuration changes:

```bash
docker exec openwebui-filesync /usr/local/bin/python3 /app/sync.py
```

Or restart the container:
```bash
docker restart openwebui-filesync
```
