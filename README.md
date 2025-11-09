# Open-WebUI-Local-FileSync

A Docker container that periodically synchronizes files from a local mount with the Open WebUI knowledge base.

## ✨ NEW: Web-Based Configuration Interface

**No more messy docker-compose files!** Configure everything through an easy-to-use web interface.

![Web Interface](https://github.com/user-attachments/assets/16be0cc1-f778-4415-b52a-afa5adfa7c38)

**Status Dashboard - Monitor your sync operations:**

![Status Dashboard](https://github.com/user-attachments/assets/aeff465a-5036-41c2-8388-16be869a28d2)

**Real-time Logs - Track sync activity:**

![Logs Viewer](https://github.com/user-attachments/assets/c85cadfd-ea3a-4cc7-973b-54c899a9c5f1)

### Latest Updates
- 📊 **Status Dashboard**: Comprehensive overview with key metrics, force sync button, and detailed statistics (v1.5.0)
- 📝 **Logs Viewer**: Real-time log viewing with search and filtering by log level (v1.5.0)
- 🏷️ **Version Display**: Shows version number (v1.5.0) in the header
- 🎨 **UI Improvements**: Corrected heading, GitHub link, improved theme toggle showing current mode (v1.5.0)
- 🔍 **Multi-Criteria Filtering**: Filter sync state by status AND knowledge base simultaneously
- ⚡ **Shift-Select**: Select ranges of items with Shift+click for bulk operations
- 📁 **File Management Tab**: Directly manage files in Open WebUI - view, filter, search, and delete files
- 🔄 **Sync Integration**: File deletions automatically update sync state
- 🌓 **Light/Dark Mode**: Toggle between themes for comfortable viewing
- 📂 **SSH Browser**: Browse remote filesystems to select files and folders
- 📊 **State Management**: View and manage synced files with visual status indicators

Quick setup:
```yaml
services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    ports:
      - "8000:8000"
    volumes:
      - ./files:/data:ro
      - ./config:/app/config
      - ./state:/app/state
```
Then access `http://localhost:8000` to configure all settings!

## Features

- 🖥️ **Web-based configuration interface** - no more complex environment variables!
- 📊 **NEW v1.5:** Status Dashboard - comprehensive overview of sync operations with force sync button
- 📝 **NEW v1.5:** Logs Viewer - real-time log viewing with search and filtering
- 🏷️ **NEW v1.5:** Version tracking and display
- 🔍 **Multi-criteria filtering** - filter by status AND knowledge base simultaneously
- ⚡ **Shift-select support** - select ranges of items for bulk operations
- 📁 **File Management tab** - directly manage Open WebUI files with filtering and bulk operations
- 🔄 **Sync state integration** - file deletions automatically reflected in sync state
- 🌓 **Light/Dark mode toggle** - improved to show current mode
- 📂 **SSH filesystem browser** - with multiple file selection for easy file selection
- 📊 **Advanced sync state management** - with visual status indicators and filtering
- 🔄 Automatic periodic synchronization of files to Open WebUI
- 📅 Flexible scheduling: hourly, daily, or weekly
- 🌍 Timezone support
- 📁 Multiple file format support (markdown, text, PDF, Word docs, JSON, YAML, TOML, configuration files, and any text-based files)
- 🔄 Automatic text file detection and conversion to Markdown
- 🔍 Smart sync: only uploads changed files
- 🎯 Include/exclude filtering for files and folders per source (volume mounts and SSH)
- 📂 Support for exact file paths or directory filtering
- 🐳 Easy deployment with Docker
- 📚 Knowledge base organization with directory mapping
- 🔁 Automatic retry logic with configurable attempts and delays
- ✅ Upload processing verification with status tracking
- 🔄 Automatic state backfilling from existing knowledge base files
- 📝 Automatic state file initialization with permission validation
- 🔐 SSH remote file ingestion with password and key authentication
- 🛡️ SSH host key verification support for enhanced security
- 🎛️ Fine-grained file filtering with glob patterns and substring matching

## 📚 Documentation

### Getting Started
- 🚀 **[Quick Start Guide](QUICKSTART.md)** - Get up and running quickly
- 🌐 **[Web Interface Guide](WEB_INTERFACE.md)** - Use the web-based configuration (recommended)
- 🚢 **[Deployment Guide](DEPLOYMENT.md)** - Complete deployment scenarios and examples

### Configuration & Usage
- ⚙️ **[Configuration Guide](CONFIGURATION.md)** - All configuration options and environment variables
- 📚 **[Examples](EXAMPLES.md)** - Comprehensive examples for various use cases

### Troubleshooting & Advanced
- 🔧 **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions
- 📋 **[State File Format](STATE_FORMAT.md)** - Advanced state file documentation
- 🔄 **[Flow Diagrams](FLOW_DIAGRAM.md)** - Visual workflow documentation
- 🛠️ **[Implementation Details](IMPLEMENTATION.md)** - Technical implementation summary

## Quick Start

> 💡 **Recommended:** Use the [Web Interface](WEB_INTERFACE.md) for the easiest configuration experience!
> 
> 📚 **For more examples**, see the [Deployment Guide](DEPLOYMENT.md) which includes complete docker-compose configurations for various use cases.
> 
> 📡 **For SSH remote file ingestion**, see [docker-compose-ssh-example.yml](docker-compose-ssh-example.yml) for a ready-to-use configuration.

### Using Docker Compose with Web Interface (Recommended)

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

3. **Access the web interface** at `http://localhost:8000` and configure:
   - Open WebUI connection (URL and API key)
   - Sync schedule
   - File settings
   - Knowledge base mappings
   - And more!

### Using Docker Compose with Environment Variables (Legacy)

You can still use environment variables for configuration. See the [Configuration Guide](CONFIGURATION.md) for all available options.

Basic example:

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

See the [Deployment Guide](DEPLOYMENT.md) for more examples.

### Using Docker CLI

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

For more deployment options, see the [Deployment Guide](DEPLOYMENT.md).

## How It Works

1. The container starts and runs an initial sync immediately
2. A cron job is configured based on your schedule settings
3. At each scheduled time, the sync script:
   - Scans the `/data` directory for files with allowed extensions
   - Calculates MD5 hashes to detect changes
   - Uploads new or changed files to Open WebUI via the API
   - Associates files with knowledge bases (if configured)
   - Waits for uploads to be processed successfully
   - Retries failed uploads with exponential backoff
   - Stores file hashes and status to avoid re-uploading unchanged files

### Upload Staging and Retry Logic

The sync script implements robust error handling:

- **Status Tracking**: Each file upload is tracked with states: `uploaded`, `processing`, `failed`
- **Processing Verification**: After upload, the script waits up to 5 minutes (configurable) to verify the file was processed
- **Automatic Retries**: Failed uploads are automatically retried (up to 3 attempts by default)
- **Retry Delay**: Configurable delay (default 60 seconds) between retry attempts
- **State Persistence**: Upload status is saved between sync runs to handle failures gracefully

### Automatic Text File Detection and Conversion

The sync tool automatically detects text files and converts them to Markdown format before upload:

- **Universal Text Detection**: Any text-based file (regardless of extension) is automatically detected and converted
- **Structured Format Recognition**: JSON, YAML, TOML files are parsed and converted to structured markdown with proper formatting
- **Configuration Files**: Files with .conf extension or configuration-like content are wrapped in code blocks
- **Generic Text Files**: Plain text files, logs, scripts, and other text content are converted with appropriate formatting
- **Markdown Passthrough**: Existing markdown files (.md, .markdown) are uploaded as-is without conversion
- **Binary Files**: Non-text files (PDF, images, etc.) are uploaded without modification
- **Smart Formatting**: Code-like content is automatically wrapped in code blocks for syntax highlighting
- **Temporary Conversion**: Converted files are created temporarily and cleaned up after upload
- **Original Files Preserved**: Your original files remain unchanged on your filesystem

**Example Structured Format Conversion (JSON/YAML/TOML):**

A JSON file like this:
```json
{
  "name": "MyApp",
  "version": "1.0.0",
  "settings": {
    "enabled": true,
    "timeout": 30
  }
}
```

Is converted to Markdown:
```markdown
# myapp.json

- **name:** MyApp
- **version:** 1.0.0
- **settings:**
  - **enabled:** True
  - **timeout:** 30
```

**Example CONF File Conversion:**

A configuration file like `app.conf` is converted to:
```markdown
# app.conf

\`\`\`
[database]
host = localhost
port = 5432

[logging]
level = INFO
\`\`\`
```

**Example Generic Text File Conversion:**

A log file or script like `deployment.log` (with no specific extension) is automatically detected as text and converted:
```markdown
# deployment.log

\`\`\`
2024-01-15 10:30:00 Starting deployment
2024-01-15 10:30:15 Pulling latest image
2024-01-15 10:30:45 Deployment complete
\`\`\`
```

This makes all text-based files readable and searchable in the Open WebUI knowledge base, regardless of their file extension.

For detailed configuration options, see the [Configuration Guide](CONFIGURATION.md).

## Volumes and State Management

- `/data` - Mount your local directory containing files to sync (read-only recommended)
- `/app/state` - **Recommended:** Mount a volume to persist the sync state file across container restarts

### State File Persistence

To avoid duplicate content errors and maintain sync history across container restarts, mount a volume for the state file:

```yaml
volumes:
  - ./your-files:/data:ro
  - ./filesync-state:/app/state  # Persist state file
```

Or use the `STATE_FILE` environment variable to customize the location:

```yaml
environment:
  STATE_FILE: /app/state/sync_state.json
volumes:
  - ./your-files:/data:ro
  - ./filesync-state:/app/state
```

**Benefits of persisting state:**
- Prevents duplicate uploads when container restarts
- Maintains knowledge base associations
- Preserves retry attempts and upload history
- Faster sync times (only new/changed files are uploaded)

**Note:** The sync script automatically creates the state directory and file if they don't exist, with full permission validation.

For detailed volume configuration, see the [Configuration Guide](CONFIGURATION.md#volumes).

## Migrating from Previous Versions

If you're upgrading from a version before the knowledge base and retry logic features, your existing state file will be automatically migrated. However, be aware:

- **Old state format**: Previously, state was a simple `{file_path: hash}` mapping
- **New state format**: State now includes detailed tracking: `{files: {...}, knowledge_bases: {...}}`
- **Automatic migration**: On first run, files with the old format will be automatically detected and work correctly
- **State file location**: If you're mounting a custom state file path, ensure it persists across container restarts

To manually reset the state file (force re-upload of all files):

```bash
# Stop the container
docker stop openwebui-filesync

# Remove the state file (if mounted externally)
rm ./state/sync_state.json

# Or, if using default internal state, recreate the container
docker rm openwebui-filesync
docker-compose up -d
```

## Logs

View container logs to monitor sync operations:

```bash
docker logs -f openwebui-filesync
```

For detailed troubleshooting, see the [Troubleshooting Guide](TROUBLESHOOTING.md).

## License

MIT License - see [LICENSE](LICENSE) file for details
