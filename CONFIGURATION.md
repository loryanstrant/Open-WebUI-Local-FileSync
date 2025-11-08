# Configuration Guide

This guide covers all configuration options for Open-WebUI-Local-FileSync.

## Table of Contents

- [Web Interface Configuration](#web-interface-configuration)
- [Environment Variables](#environment-variables)
  - [Required Variables](#required-environment-variables)
  - [Scheduling Variables](#scheduling-environment-variables)
  - [File Configuration](#file-configuration-variables)
  - [Knowledge Base Configuration](#knowledge-base-configuration)
  - [Retry and Upload Configuration](#retry-and-upload-configuration)
  - [SSH Remote File Ingestion](#ssh-remote-file-ingestion)
- [Volumes](#volumes)

## Web Interface Configuration

> 💡 **Recommended:** Use the [Web Interface](WEB_INTERFACE.md) for the easiest configuration experience!

The web interface provides a visual editor for all configuration options without needing to manage complex environment variables or YAML files.

**Screenshot:**

![Web Interface Configuration](https://github.com/user-attachments/assets/16be0cc1-f778-4415-b52a-afa5adfa7c38)

Access the web interface at `http://localhost:8000` (or your configured port) to manage:
- Open WebUI connection settings
- Sync schedules
- File settings and allowed extensions
- Knowledge base mappings with include/exclude filters
- SSH remote sources
- Retry and timeout settings

See the [Web Interface Guide](WEB_INTERFACE.md) for detailed documentation.

## Environment Variables

If you prefer using environment variables instead of the web interface, all settings can be configured via docker-compose or CLI.

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENWEBUI_URL` | URL of your Open WebUI instance | `http://openwebui:8080` |
| `OPENWEBUI_API_KEY` | API key for Open WebUI authentication | `sk-...` |

**Getting Your Open WebUI API Key:**
1. Log in to your Open WebUI instance
2. Navigate to Settings → Account
3. Generate or copy your API key
4. Use this key for the `OPENWEBUI_API_KEY` environment variable

### Scheduling Environment Variables

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `TZ` | Timezone for scheduling | `UTC` | Any valid timezone (e.g., `America/New_York`, `Europe/London`, `Asia/Tokyo`) |
| `SYNC_SCHEDULE` | Frequency of synchronization | `daily` | `hourly`, `daily`, `weekly` |
| `SYNC_TIME` | Time of day to run sync (HH:MM format) | `00:00` | Any valid time in 24-hour format |
| `SYNC_DAY` | Day of week for weekly sync | `0` | `0-6` (0=Sunday) or `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun` |

**Examples:**

Daily sync at 2 AM EST:
```yaml
environment:
  TZ: America/New_York
  SYNC_SCHEDULE: daily
  SYNC_TIME: "02:00"
```

Hourly sync:
```yaml
environment:
  SYNC_SCHEDULE: hourly
  SYNC_TIME: "00:30"  # At 30 minutes past each hour
```

Weekly sync every Sunday at 3 AM UTC:
```yaml
environment:
  TZ: UTC
  SYNC_SCHEDULE: weekly
  SYNC_TIME: "03:00"
  SYNC_DAY: "0"  # or "sun"
```

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

## Volumes

- `/data` - Mount your local directory containing files to sync (read-only recommended)
- `/app/state` - **Recommended:** Mount a volume to persist the sync state file across container restarts
- `/app/config` - Mount a volume to persist web interface configuration
- `/app/ssh_keys` - Mount a directory containing SSH private keys for remote file ingestion

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

## Related Documentation

- [Quick Start Guide](QUICKSTART.md) - Get started quickly
- [Deployment Examples](DEPLOYMENT.md) - Complete deployment scenarios
- [Web Interface Guide](WEB_INTERFACE.md) - Using the web configuration interface
- [State File Format](STATE_FORMAT.md) - Advanced state file documentation
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
