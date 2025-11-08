# Web Interface for Configuration Management

## Overview

The Open-WebUI-Local-FileSync now includes a web-based configuration interface that allows you to manage all settings through a browser instead of editing docker-compose.yml environment variables.

**Screenshot:**

![Web Interface Configuration](https://github.com/user-attachments/assets/16be0cc1-f778-4415-b52a-afa5adfa7c38)

## Features

- **Visual Configuration Editor**: Easy-to-use web interface for all settings
- **Light/Dark Mode Toggle**: Switch between themes for comfortable viewing in any environment
- **SSH Filesystem Browser**: Browse and select files/folders from remote SSH servers
- **Sync State Management**: View, search, and manage synced files with visual status indicators
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

## New Features

### Light/Dark Mode Toggle

The web interface now includes a theme toggle for comfortable viewing in any environment.

**Light Mode:**

![Light Mode](https://github.com/user-attachments/assets/edd6f1d2-1350-4c49-8be4-0140b3ada33f)

**Dark Mode:**

![Dark Mode](https://github.com/user-attachments/assets/dec5ec6f-4fbc-4839-bf35-7a9f81ce398b)

**Features:**
- Toggle button in the header (🌙/☀️ icons)
- Smooth transitions between themes
- Theme preference saved in browser localStorage
- Automatically applies on page load

### SSH Filesystem Browser

When configuring SSH remote sources, you can now browse the remote filesystem to select files and folders.

**SSH Source with Browse Button:**

![SSH Browse](https://github.com/user-attachments/assets/4bd02680-57c9-4195-8a0f-4fface55544f)

**Features:**
- Click "Browse Files" button on any SSH source
- Interactive modal with directory navigation
- Breadcrumb navigation for easy path traversal
- Click folders to navigate, click files to select
- Selected paths automatically added to configuration
- Works with password and key-based authentication

**How to use:**
1. Add an SSH source or edit an existing one
2. Fill in host, port, username, and authentication details
3. Click "Browse Files" button
4. Navigate the remote filesystem
5. Click on a file or folder to select it
6. Click "Add Selected Path" to add it to the paths list

### Sync State Management

The new "Sync State" tab provides a comprehensive view of all synced files with management capabilities.

**Sync State Table:**

![Sync State Management](https://github.com/user-attachments/assets/b243a53a-9676-4ece-a669-fc2fcce5a948)

**Features:**
- Table view with file path, knowledge base, status, and timestamp
- Visual status indicators:
  - 🟢 Green badge for "uploaded" files
  - 🔴 Red badge for "failed" files
  - 🔵 Blue badge for "processing" files
- Search/filter by path or knowledge base name
- Multi-select with checkboxes
- Bulk operations:
  - Select All button
  - Deselect All button
  - Delete Selected (shows count)
- Individual delete buttons for each file
- Refresh button to reload data

**How to use:**
1. Click on the "Sync State" tab
2. View all synced files in the table
3. Use the search box to filter by path or knowledge base
4. Select files using checkboxes
5. Click "Delete Selected" to remove multiple files from sync state
6. Or click individual "Delete" buttons for single files
7. Click "Refresh" to reload the table

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

### Configuration Management
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration (requires JSON body)
- `GET /export_json` - Download configuration as JSON

### Sync State Management
- `GET /api/state` - Get all sync state entries with file details
- `POST /api/state/delete` - Delete sync state entries (requires JSON body with `paths` array)

### SSH Filesystem Browser
- `POST /api/ssh/browse` - Browse remote SSH filesystem (requires SSH connection details and path)

Example:

```bash
# Get current config
curl http://localhost:8000/api/config

# Update config
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d @config.json

# Get sync state
curl http://localhost:8000/api/state

# Delete sync state entries
curl -X POST http://localhost:8000/api/state/delete \
  -H "Content-Type: application/json" \
  -d '{"paths": ["path/to/file1.md", "path/to/file2.txt"]}'

# Browse SSH filesystem
curl -X POST http://localhost:8000/api/ssh/browse \
  -H "Content-Type: application/json" \
  -d '{
    "host": "example.com",
    "port": 22,
    "username": "user",
    "password": "pass",
    "path": "/home/user"
  }'
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
