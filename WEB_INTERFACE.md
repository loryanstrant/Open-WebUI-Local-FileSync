# Web Interface for Configuration Management

## Overview

The Open-WebUI-Local-FileSync now includes a web-based configuration interface that allows you to manage all settings through a browser instead of editing docker-compose.yml environment variables.

**Screenshot:**

![Web Interface Configuration](https://github.com/user-attachments/assets/16be0cc1-f778-4415-b52a-afa5adfa7c38)

## Features

- **Visual Configuration Editor**: Easy-to-use web interface for all settings
- **Light/Dark Mode Toggle**: Switch between themes for comfortable viewing in any environment
- **SSH Filesystem Browser**: Browse and select files/folders from remote SSH servers
- **Advanced Sync State Management**: 
  - Multi-criteria filtering (status and knowledge base)
  - Shift-select for bulk operations
  - Change knowledge base assignments
  - Visual status indicators
- **File Management**: Direct Open WebUI file operations
  - View all files with KB associations
  - Filter and search capabilities
  - Bulk delete operations
  - Automatic sync state integration
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

### SSH Remote Sources

SSH remote sources are now displayed in a collapsible format for a cleaner interface when multiple sources are configured.

**Collapsed SSH Sources:**

![SSH Sources Collapsed by Default](https://github.com/user-attachments/assets/0d555904-632e-422c-964f-40537c595a0e)

**Features:**
- SSH sources default to collapsed state for cleaner UI
- Click the arrow to expand/collapse individual sources
- All configuration fields remain accessible when expanded

### SSH Filesystem Browser

When configuring SSH remote sources, you can now browse the remote filesystem to select files and folders with support for multiple selection.

**SSH Source with Browse Button:**

![SSH Browse](https://github.com/user-attachments/assets/4bd02680-57c9-4195-8a0f-4fface55544f)

**Multiple File Selection:**

![Multiple Selection](https://github.com/user-attachments/assets/84919612-4caf-430b-abd5-226d1b404809)

**Select All Feature:**

![Select All](https://github.com/user-attachments/assets/c07a81b1-1f65-4ae6-8e62-3da318246393)

**Features:**
- Click "Browse Files" button on any SSH source
- Interactive modal with directory navigation
- **Multiple file selection with checkboxes** - select multiple files at once
- **"Select All" and "Deselect All" buttons** - quickly select/deselect all items in current directory
- **Visual feedback** - selected items highlighted in green
- **Dynamic button text** - shows count of selected items (e.g., "Add Selected Paths (3)")
- Breadcrumb navigation for easy path traversal
- Click folders to navigate through directories
- Selected paths automatically added to configuration
- Prevents duplicate paths when adding multiple selections
- Works with password and key-based authentication

**How to use:**
1. Add an SSH source or edit an existing one
2. Fill in host, port, username, and authentication details
3. Click "Browse Files" button
4. Navigate the remote filesystem using the breadcrumb or by clicking folders
5. Select files/folders by checking their checkboxes
   - Use "Select All" to select all items in the current directory
   - Use "Deselect All" to clear all selections
6. Click "Add Selected Path" (shows count) to add all selected paths to the configuration

### Sync State Management

The "Sync State" tab provides a comprehensive view of all synced files with advanced filtering and management capabilities.

**Sync State with Enhanced Filtering:**

![Sync State Management](https://github.com/user-attachments/assets/237f4224-a685-4302-9f38-d1ca5e5aac3d)

**Features:**
- Table view with file path, knowledge base, status, and timestamp
- Visual status indicators:
  - 🟢 Green badge for "uploaded" files
  - 🔴 Red badge for "failed" files
  - 🔵 Blue badge for "processing" files
- **Advanced Filtering:**
  - **Status filter dropdown**: Filter by status (All, Uploaded, Processing, Failed)
  - **Knowledge Base filter dropdown**: Filter by specific KB or view all
  - **Multiple filters**: Apply status and KB filters simultaneously with AND logic
  - **Search by path**: Text search for file paths
- **Shift-select support**: Click first checkbox, then Shift+click last checkbox to select range
- Multi-select with checkboxes
- Bulk operations:
  - Select All button
  - Deselect All button
  - Delete Selected (shows count)
  - Change KB for multiple files
- Individual delete buttons for each file
- Refresh button to reload data

**Multiple Filters in Action:**

![Multiple Filters Applied](https://github.com/user-attachments/assets/488ce6be-8b1b-419c-989a-76270a9c0475)

**How to use:**
1. Click on the "Sync State" tab
2. View all synced files in the table
3. Use the filter dropdowns to filter by status and/or knowledge base
4. Use the search box to filter by file path
5. Select files using checkboxes:
   - Click individual checkboxes
   - Use "Select All" to select all visible files
   - Use Shift+click to select a range of files
6. Click "Delete Selected" to remove multiple files from sync state
7. Click "Change KB" to reassign files to a different knowledge base
8. Or click individual "Delete" buttons for single files
9. Click "Refresh" to reload the table

### File Management

The "File Management" tab allows you to directly manage files stored in Open WebUI, whether they were synced or uploaded manually.

**File Management Interface:**

This tab provides direct access to files in your Open WebUI instance, allowing you to manage the knowledge base without leaving the sync interface.

**Features:**
- **View all files**: Display all files from Open WebUI with their metadata
- **Knowledge Base associations**: See which KB(s) each file belongs to
- **Advanced filtering:**
  - Filter by Knowledge Base (including "Unassigned" files)
  - Search by filename
- **File information**: View filename, associated KBs, file size, and creation date
- **Shift-select support**: Select ranges of files using Shift+click
- **Bulk operations:**
  - Select All / Deselect All buttons
  - Delete multiple files at once
- **Individual file actions**: Delete button for each file
- **Sync state integration**: When files are deleted, corresponding sync state entries are automatically removed

**How to use:**
1. Click on the "File Management" tab
2. Browse all files currently in your Open WebUI instance
3. Use the Knowledge Base filter to show files from specific KBs
4. Use the search box to find files by name
5. Select files using checkboxes:
   - Click individual checkboxes
   - Use "Select All" to select all visible files
   - Use Shift+click to select a range of files
6. Click "Delete Selected" to remove multiple files from Open WebUI
7. Or click individual "Delete" buttons for single files
8. Deleted files are automatically removed from sync state
9. Click "Refresh" to reload the file list from Open WebUI

**Note:** This feature requires a valid Open WebUI URL and API key to be configured in the Configuration tab.

### Status Dashboard

The "Status" tab (default landing page) provides a comprehensive overview of your file synchronization status and statistics.

**Status Dashboard (Light Mode):**

![Status Dashboard Light](https://github.com/user-attachments/assets/aeff465a-5036-41c2-8388-16be869a28d2)

**Status Dashboard (Dark Mode):**

![Status Dashboard Dark](https://github.com/user-attachments/assets/9c2ec609-14dd-4bb6-b173-865b0c6e27e9)

**Features:**
- **Key Metrics Cards:**
  - Total Files (with synced count)
  - Knowledge Bases (total and active)
  - Failed Uploads (with pending retries)
  - File Conversions (JSON/YAML to Markdown)
- **Files per Knowledge Base**: Breakdown showing file distribution across KBs
- **Sync Sources**: Display of all sync sources with file counts, conversions, and error tracking
- **Last Sync Time**: Timestamp of the most recent sync operation
- **Force Sync Now Button**: Manually trigger a sync operation without waiting for the schedule
- **Refresh Button**: Update the statistics without reloading the page

**How to use:**
1. The Status tab is the default view when you open the web interface
2. Review the key metrics at a glance
3. Click "Force Sync Now" to trigger an immediate sync (shows results in a popup)
4. Click "↻ Refresh" to update the statistics
5. View detailed breakdowns of files per knowledge base and sync sources

### Sync Logs Viewer

The "Logs" tab provides real-time access to synchronization logs with powerful search and filtering capabilities.

**Logs Viewer:**

![Logs Tab](https://github.com/user-attachments/assets/c85cadfd-ea3a-4cc7-973b-54c899a9c5f1)

**Features:**
- **Real-time log viewing**: Display logs from `/app/sync.log`
- **Search functionality**: Filter log entries by text
- **Log level filtering**: Filter by All Levels, Errors, Warnings, or Info
- **Color-coded entries**:
  - 🔴 Red border for ERROR entries
  - 🟠 Orange border for WARNING entries
  - ⚪ Default styling for INFO entries
- **Auto-scroll**: Automatically scrolls to the latest entries
- **Clear Logs**: Remove all log entries
- **Timestamp display**: Each entry shows when it occurred

**How to use:**
1. Click on the "Logs" tab
2. View recent sync operations and any errors
3. Use the search box to find specific log entries
4. Select a log level from the dropdown to filter entries
5. Click "Refresh" to reload the latest logs
6. Click "Clear Logs" to remove all log entries (requires confirmation)

### Version Information and UI Improvements

**Version Display:**

![Version 1.5.0](https://github.com/user-attachments/assets/bc5a4cff-e59b-480a-8b11-d7021f425cd7)

The web interface now displays the version number (v1.5.0) prominently in the header next to the title, making it easy to identify which version you're running.

**UI Improvements:**
- **Corrected Heading**: Title now shows "Open WebUI FileSync" (without hyphen, "Configuration" removed)
- **GitHub Link**: Added link to the repository in the top-right header with GitHub icon
- **Improved Theme Toggle**: Now shows current mode ("Dark" when in dark mode, "Light" when in light mode) instead of the mode you'll switch to
- **Clearer Tab Names**: "File Management" renamed to "Knowledge Base Files" for better clarity

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
- `POST /api/state/update_kb` - Update knowledge base for sync state entries (requires JSON body with `paths` array and `kb_name`)
- `GET /api/knowledge_bases` - Get list of all knowledge bases from state and config

### File Management (Open WebUI)
- `GET /api/openwebui/files` - Get all files from Open WebUI with knowledge base associations
- `POST /api/openwebui/files/delete` - Delete files from Open WebUI (requires JSON body with `file_ids` array)

### Status and Monitoring
- `GET /api/status` - Get sync status dashboard statistics
- `POST /api/sync/force` - Trigger a manual sync operation
- `GET /api/logs` - Get sync logs with filtering support
- `POST /api/logs/clear` - Clear all log entries

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

# Get all files from Open WebUI
curl http://localhost:8000/api/openwebui/files

# Delete files from Open WebUI
curl -X POST http://localhost:8000/api/openwebui/files/delete \
  -H "Content-Type: application/json" \
  -d '{"file_ids": ["file_id_1", "file_id_2"]}'

# Get status dashboard statistics
curl http://localhost:8000/api/status

# Trigger manual sync
curl -X POST http://localhost:8000/api/sync/force

# Get sync logs
curl http://localhost:8000/api/logs

# Clear all logs
curl -X POST http://localhost:8000/api/logs/clear
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
