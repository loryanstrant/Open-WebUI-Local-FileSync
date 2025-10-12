# Open-WebUI-Local-FileSync

A Docker container that periodically synchronizes files from a local mount with the Open WebUI knowledge base.

## Features

- 🔄 Automatic periodic synchronization of files to Open WebUI
- 📅 Flexible scheduling: hourly, daily, or weekly
- 🌍 Timezone support
- 📁 Multiple file format support (markdown, text, PDF, Word docs)
- 🔍 Smart sync: only uploads changed files
- 🐳 Easy deployment with Docker
- 📚 **NEW:** Knowledge base organization with directory mapping
- 🔁 **NEW:** Automatic retry logic with configurable attempts and delays
- ✅ **NEW:** Upload processing verification with status tracking

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
| `ALLOWED_EXTENSIONS` | Comma-separated list of file extensions to sync | `.md,.txt,.pdf,.doc,.docx` |
| `STATE_FILE` | Path to state file for tracking changes | `/app/sync_state.json` |

### Knowledge Base Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `KNOWLEDGE_BASE_MAPPING` | Map directory paths to knowledge base names (format: `path1:kb_name1,path2:kb_name2`) | _(empty)_ | `docs:Documentation,guides:UserGuides` |

When `KNOWLEDGE_BASE_MAPPING` is configured:
- Files are automatically organized into the specified knowledge bases
- Knowledge bases are created automatically if they don't exist
- Paths can be relative to `FILES_DIR` or absolute
- Multiple mappings are separated by commas

### Retry and Upload Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_RETRY_ATTEMPTS` | Maximum number of retry attempts for failed uploads | `3` |
| `RETRY_DELAY` | Delay in seconds between retry attempts | `60` |
| `UPLOAD_TIMEOUT` | Timeout in seconds to wait for upload processing | `300` |

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

### Sync with knowledge base organization

Organize files into different knowledge bases based on their directory:

```yaml
environment:
  OPENWEBUI_URL: http://openwebui:8080
  OPENWEBUI_API_KEY: your_api_key_here
  TZ: America/New_York
  SYNC_SCHEDULE: daily
  SYNC_TIME: "02:00"
  KNOWLEDGE_BASE_MAPPING: "docs:Documentation,api:API_Reference,guides:User_Guides"
volumes:
  - ./documentation:/data:ro
```

In this example:
- Files in `/data/docs/` → stored in "Documentation" knowledge base
- Files in `/data/api/` → stored in "API_Reference" knowledge base
- Files in `/data/guides/` → stored in "User_Guides" knowledge base

### Multiple knowledge bases with different volumes

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
      KNOWLEDGE_BASE_MAPPING: "team-docs:Team_Documentation,customer-docs:Customer_Documentation"
    volumes:
      - ./team-docs:/data/team-docs:ro
      - ./customer-docs:/data/customer-docs:ro
    restart: unless-stopped
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

## Getting Your Open WebUI API Key

1. Log in to your Open WebUI instance
2. Navigate to Settings → Account
3. Generate or copy your API key
4. Use this key for the `OPENWEBUI_API_KEY` environment variable

## Volumes

- `/data` - Mount your local directory containing files to sync (read-only recommended)

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

## License

MIT License - see [LICENSE](LICENSE) file for details
