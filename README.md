# Open-WebUI-Local-FileSync

A Docker container that periodically synchronizes files from a local mount with the Open WebUI knowledge base.

## Features

- 🔄 Automatic periodic synchronization of files to Open WebUI
- 📅 Flexible scheduling: hourly, daily, or weekly
- 🌍 Timezone support
- 📁 Multiple file format support (markdown, text, PDF, Word docs, JSON, YAML)
- 🔄 **NEW:** Automatic JSON/YAML to Markdown conversion
- 🔍 Smart sync: only uploads changed files
- 🎯 **NEW:** Include/exclude filtering for files and folders per source
- 🐳 Easy deployment with Docker
- 📚 Knowledge base organization with directory mapping
- 🔁 Automatic retry logic with configurable attempts and delays
- ✅ Upload processing verification with status tracking
- 🔄 Automatic state backfilling from existing knowledge base files
- 📝 Automatic state file initialization with permission validation

## Documentation

- 📖 [Quick Start Guide](QUICKSTART.md) - Get started with knowledge bases and retry logic
- 📚 [Examples](EXAMPLES.md) - Comprehensive examples for various deployment scenarios
- 📋 [State File Format](STATE_FORMAT.md) - Advanced state file documentation
- 🔄 [Flow Diagrams](FLOW_DIAGRAM.md) - Visual workflow documentation
- 🛠️ [Implementation Details](IMPLEMENTATION.md) - Technical implementation summary

## Quick Start

> 💡 **For more detailed examples**, see [EXAMPLES.md](EXAMPLES.md) which includes complete docker-compose configurations for various use cases.

### Using Docker Compose

1. Create a `docker-compose.yml` file:

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
      - ./filesync-state:/app/state  # Persist state across restarts
    restart: unless-stopped
```

2. Run the container:

```bash
docker-compose up -d
```

### Using Docker CLI

```bash
docker run -d \
  --name openwebui-filesync \
  -e OPENWEBUI_URL=http://openwebui:8080 \
  -e OPENWEBUI_API_KEY=your_api_key_here \
  -e TZ=America/New_York \
  -e SYNC_SCHEDULE=daily \
  -e SYNC_TIME=02:00 \
  -v /path/to/your/files:/data:ro \
  --restart unless-stopped \
  ghcr.io/loryanstrant/open-webui-local-filesync:latest
```

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENWEBUI_URL` | URL of your Open WebUI instance | `http://openwebui:8080` |
| `OPENWEBUI_API_KEY` | API key for Open WebUI authentication | `sk-...` |

### Scheduling Environment Variables

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `TZ` | Timezone for scheduling | `UTC` | Any valid timezone (e.g., `America/New_York`, `Europe/London`, `Asia/Tokyo`) |
| `SYNC_SCHEDULE` | Frequency of synchronization | `daily` | `hourly`, `daily`, `weekly` |
| `SYNC_TIME` | Time of day to run sync (HH:MM format) | `00:00` | Any valid time in 24-hour format |
| `SYNC_DAY` | Day of week for weekly sync | `0` | `0-6` (0=Sunday) or `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun` |

### File Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FILES_DIR` | Directory inside container to sync from | `/data` |
| `ALLOWED_EXTENSIONS` | Comma-separated list of file extensions to sync | `.md,.txt,.pdf,.doc,.docx,.json,.yaml,.yml` |
| `STATE_FILE` | Path to state file for tracking changes | `/app/sync_state.json` |

**Note:** JSON and YAML files are automatically converted to Markdown format during upload for better readability in the knowledge base.

### Knowledge Base Configuration

The tool supports three ways to organize files into knowledge bases:

#### Option 1: Single Knowledge Base (Simplest)

Use when all files should go to one knowledge base:

| Variable | Description | Example |
|----------|-------------|---------|
| `KNOWLEDGE_BASE_NAME` | Name of the knowledge base where all files will be stored | `MyDocumentation` |

Example:
```yaml
environment:
  KNOWLEDGE_BASE_NAME: "HomeConfiguration"
volumes:
  - ./my-files:/data:ro
```

#### Option 2: JSON Array Format (Recommended for Multiple)

Use when you have multiple directories mapped to different knowledge bases. This format also supports include/exclude filtering:

| Variable | Description | Example |
|----------|-------------|---------|
| `KNOWLEDGE_BASE_MAPPINGS` | JSON array of path-to-KB mappings with optional filters | See below |

**Basic Example (without filters):**
```yaml
environment:
  KNOWLEDGE_BASE_MAPPINGS: '[{"path": "docs", "kb": "Documentation"}, {"path": "api", "kb": "API_Reference"}]'
volumes:
  - ./documentation:/data:ro
```

**Advanced Example (with include/exclude filters):**
```yaml
environment:
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
```

**Filter Configuration:**
- `exclude`: Array of patterns to exclude files/folders
  - Supports glob patterns (`*`, `?`)
  - Supports substring matching (e.g., `"_2025"` excludes files with `_2025` in name)
  - Examples: `["*/*"]` excludes all subdirectories, `["*.log"]` excludes log files
- `include`: Array of patterns to include (overrides exclusions)
  - Same pattern matching as exclude
  - Useful for excluding subdirectories but including specific ones
  - Example: Exclude `*/*` but include `includes/*`

**Filter Examples:**
1. **Exclude subdirectories but include specific folder:**
   ```json
   {"path": "esphome", "kb": "ESPHome", "exclude": ["*/*"], "include": ["includes/*"]}
   ```
   This excludes all subdirectories except the `includes` subdirectory.

2. **Exclude files with specific pattern in name:**
   ```json
   {"path": "docker-docs", "kb": "DockerDocs", "exclude": ["*_2025*"]}
   ```
   This excludes any files containing `_2025` in the filename.

3. **Exclude multiple patterns:**
   ```json
   {"path": "project", "kb": "Project", "exclude": [".git/*", "*.log", "temp/*", "*_backup*"]}
   ```
   This excludes git files, log files, temp directory, and backup files.

#### Option 3: Legacy Format (Still Supported)

Original comma-separated format:

| Variable | Description | Example |
|----------|-------------|---------|
| `KNOWLEDGE_BASE_MAPPING` | Comma-separated path:kb pairs | `docs:Documentation,guides:UserGuides` |

Example:
```yaml
environment:
  KNOWLEDGE_BASE_MAPPING: "docs:Documentation,api:API_Reference,guides:User_Guides"
```

**Priority Order:**
1. `KNOWLEDGE_BASE_NAME` (single KB mode) - takes precedence if set
2. `KNOWLEDGE_BASE_MAPPINGS` (JSON array) - used if no single KB name
3. `KNOWLEDGE_BASE_MAPPING` (legacy) - fallback for backward compatibility

**Notes:**
- Knowledge bases are created automatically if they don't exist
- Paths can be relative to `FILES_DIR` or absolute
- When using single KB mode, all files from all paths go to the same knowledge base

### Retry and Upload Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_RETRY_ATTEMPTS` | Maximum number of retry attempts for failed uploads | `3` |
| `RETRY_DELAY` | Delay in seconds between retry attempts | `60` |
| `UPLOAD_TIMEOUT` | Timeout in seconds to wait for upload processing | `300` |

### SSH Remote File Ingestion

Fetch files from remote servers via SSH and sync them to Open WebUI. This feature allows you to:
- Connect to multiple remote SSH servers
- Specify multiple remote paths per server
- Use password or SSH key authentication
- Map remote files to specific knowledge bases

| Variable | Description | Default |
|----------|-------------|---------|
| `SSH_REMOTE_SOURCES` | JSON array of SSH connection configurations (see below) | `""` (disabled) |
| `SSH_KEY_PATH` | Directory containing SSH private keys for authentication | `/app/ssh_keys` |
| `SSH_STRICT_HOST_KEY_CHECKING` | Enforce host key verification (requires known_hosts file) | `false` |

**SSH_REMOTE_SOURCES Format:**

```json
[
  {
    "host": "hostname or IP address",
    "port": 22,
    "username": "ssh_username",
    "password": "password_if_using_password_auth",
    "key_filename": "id_rsa",
    "paths": ["/remote/path1", "/remote/path2"],
    "kb": "Knowledge_Base_Name"
  }
]
```

**Configuration Fields:**
- `host` (required): Hostname or IP address of the SSH server
- `port` (optional): SSH port, defaults to 22
- `username` (required): SSH username
- `password` (optional): Password for password-based authentication
- `key_filename` (optional): Filename of SSH private key (relative to `SSH_KEY_PATH` or absolute path)
- `paths` (required): Array of remote file paths or directories to fetch
- `kb` (optional): Knowledge base name for these files (uses default mapping if not specified)

**Authentication Methods:**
1. **Password Authentication**: Provide `password` field
2. **SSH Key Authentication**: Provide `key_filename` field (and optionally `password` for key passphrase)

**Example: Password Authentication**
```yaml
environment:
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
```

**Example: SSH Key Authentication**
```yaml
environment:
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
```

**Example: Multiple SSH Sources**
```yaml
environment:
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
```

**Security: SSH Host Key Verification**

For improved security, you can provide a `known_hosts` file to verify SSH server identities:

```yaml
volumes:
  - ./ssh_keys:/app/ssh_keys:ro
```

Create a `known_hosts` file in your `./ssh_keys/` directory:
```bash
# Get the host key
ssh-keyscan -H server.example.com >> ./ssh_keys/known_hosts

# Or copy from your ~/.ssh/known_hosts
cp ~/.ssh/known_hosts ./ssh_keys/known_hosts
```

**Host Key Checking Modes:**

1. **Default Mode** (`SSH_STRICT_HOST_KEY_CHECKING=false`):
   - If `known_hosts` exists: Uses it for verification (secure)
   - If `known_hosts` missing: Falls back to AutoAddPolicy with warnings
   - Suitable for most use cases where convenience is needed

2. **Strict Mode** (`SSH_STRICT_HOST_KEY_CHECKING=true`):
   - **Requires** a `known_hosts` file
   - Connections fail if host key cannot be verified
   - Maximum security, recommended for production environments
   - Example:
   ```yaml
   environment:
     SSH_STRICT_HOST_KEY_CHECKING: "true"
   volumes:
     - ./ssh_keys:/app/ssh_keys:ro
   ```

**Notes:**
- Files are downloaded to temporary directories and processed like local files
- SSH-fetched files respect `ALLOWED_EXTENSIONS` configuration
- Temporary files are automatically cleaned up after sync
- Each SSH source can target a different knowledge base
- SSH connections timeout after 30 seconds
- Directories are recursively downloaded (up to 10 levels deep)
- Host key verification: Place a `known_hosts` file in the SSH keys directory for enhanced security

## Examples

### Basic sync without knowledge bases

```yaml
environment:
  OPENWEBUI_URL: http://openwebui:8080
  OPENWEBUI_API_KEY: your_api_key_here
  TZ: America/New_York
  SYNC_SCHEDULE: daily
  SYNC_TIME: "02:00"
volumes:
  - ./your-files:/data:ro
```

### Single knowledge base (all files to one KB)

Perfect when you have one collection and multiple directories:

```yaml
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
  # Persist state between container restarts
  - /etc/docker/openwebui-filesync:/app/state
```

This is much cleaner than the old approach when all files go to the same knowledge base!

### Multiple knowledge bases with JSON array format

For organizing files into different knowledge bases based on directory:

```yaml
environment:
  OPENWEBUI_URL: http://openwebui:8080
  OPENWEBUI_API_KEY: your_api_key_here
  TZ: America/New_York
  SYNC_SCHEDULE: daily
  SYNC_TIME: "02:00"
  KNOWLEDGE_BASE_MAPPINGS: '[{"path": "docs", "kb": "Documentation"}, {"path": "api", "kb": "API_Reference"}, {"path": "guides", "kb": "User_Guides"}]'
volumes:
  - ./documentation:/data:ro
```

In this example:
- Files in `/data/docs/` → stored in "Documentation" knowledge base
- Files in `/data/api/` → stored in "API_Reference" knowledge base
- Files in `/data/guides/` → stored in "User_Guides" knowledge base

### Multiple volumes mapped to different knowledge bases

Using JSON array format for clarity:

```yaml
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
    restart: unless-stopped
```

Or using legacy format (still supported):

```yaml
environment:
  KNOWLEDGE_BASE_MAPPING: "team-docs:Team_Documentation,customer-docs:Customer_Documentation"
```

### Daily sync at 2 AM EST

```yaml
environment:
  TZ: America/New_York
  SYNC_SCHEDULE: daily
  SYNC_TIME: "02:00"
```

### Hourly sync

```yaml
environment:
  SYNC_SCHEDULE: hourly
  SYNC_TIME: "00:30"  # At 30 minutes past each hour
```

### Weekly sync every Sunday at 3 AM UTC

```yaml
environment:
  TZ: UTC
  SYNC_SCHEDULE: weekly
  SYNC_TIME: "03:00"
  SYNC_DAY: "0"  # or "sun"
```

### Weekly sync every Friday at 5 PM PST

```yaml
environment:
  TZ: America/Los_Angeles
  SYNC_SCHEDULE: weekly
  SYNC_TIME: "17:00"
  SYNC_DAY: "5"  # or "fri"
```

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

### JSON and YAML File Conversion

JSON and YAML files are automatically converted to Markdown format before upload:

- **Automatic Detection**: Files with `.json`, `.yaml`, or `.yml` extensions are automatically detected
- **Markdown Conversion**: Content is converted to a readable Markdown format with proper formatting
- **Structured Display**: Nested objects and arrays are displayed with proper indentation
- **Temporary Files**: Converted files are created temporarily, uploaded, and then cleaned up
- **No Original File Changes**: Original files remain unchanged on your filesystem

**Example Conversion:**

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

This makes configuration files much more readable in the Open WebUI knowledge base.

## Getting Your Open WebUI API Key

1. Log in to your Open WebUI instance
2. Navigate to Settings → Account
3. Generate or copy your API key
4. Use this key for the `OPENWEBUI_API_KEY` environment variable

## Volumes

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

## Advanced Documentation

- [State File Format](STATE_FORMAT.md) - Detailed documentation on the sync state file structure and manual manipulation
- [Examples](EXAMPLES.md) - Comprehensive examples for various deployment scenarios

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

## Building Locally

If you want to build the image yourself:

```bash
git clone https://github.com/loryanstrant/Open-WebUI-Local-FileSync.git
cd Open-WebUI-Local-FileSync
docker build -t open-webui-local-filesync .
```

## Logs

View container logs to monitor sync operations:

```bash
docker logs -f openwebui-filesync
```

## Troubleshooting

### Files not syncing

1. Check that `OPENWEBUI_API_KEY` is correctly set
2. Verify `OPENWEBUI_URL` is accessible from the container
3. Check file extensions match `ALLOWED_EXTENSIONS`
4. Review container logs for errors
5. Check if files are in a mapped knowledge base path (if using `KNOWLEDGE_BASE_MAPPING`)

### Schedule not working

1. Verify timezone is set correctly with `TZ`
2. Check time format is `HH:MM` (24-hour)
3. For weekly sync, ensure `SYNC_DAY` is valid (0-6 or day name)

### Upload failures and retries

1. Check the state file (`/app/sync_state.json`) for file status
2. Failed uploads will be retried automatically on the next sync
3. If max retries are exceeded, manually remove the file entry from state file or fix the underlying issue
4. Increase `UPLOAD_TIMEOUT` if files are taking longer to process
5. Check network connectivity between container and Open WebUI instance

### Knowledge base issues

1. Ensure knowledge base names don't contain special characters
2. Verify paths in `KNOWLEDGE_BASE_MAPPING` match your volume mounts
3. Check container logs for knowledge base creation errors
4. Paths are relative to `FILES_DIR` (default `/data`)

### Duplicate content detected errors

If you see "Duplicate content detected" errors:

1. **Automatic backfill**: The script automatically detects existing files in the knowledge base and updates the state file. This happens on the first sync after adding state persistence.
2. **Check logs**: Look for "Backfilled state for existing file" messages to confirm the backfill is working
3. **Verify state persistence**: Ensure your state volume is mounted:
   ```yaml
   volumes:
     - ./state:/app/state
   ```
4. If issues persist, see the [State File Format documentation](STATE_FORMAT.md#duplicate-content-detected-errors) for detailed troubleshooting steps.

## License

MIT License - see [LICENSE](LICENSE) file for details
