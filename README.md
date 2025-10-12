# Open-WebUI-Local-FileSync

A Docker container that periodically synchronizes files from a local mount with the Open WebUI knowledge base.

## Features

- 🔄 Automatic periodic synchronization of files to Open WebUI
- 📅 Flexible scheduling: hourly, daily, or weekly
- 🌍 Timezone support
- 📁 Multiple file format support (markdown, text, PDF, Word docs)
- 🔍 Smart sync: only uploads changed files
- 🐳 Easy deployment with Docker

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

## Examples

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
   - Stores file hashes to avoid re-uploading unchanged files

## Getting Your Open WebUI API Key

1. Log in to your Open WebUI instance
2. Navigate to Settings → Account
3. Generate or copy your API key
4. Use this key for the `OPENWEBUI_API_KEY` environment variable

## Volumes

- `/data` - Mount your local directory containing files to sync (read-only recommended)

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

### Schedule not working

1. Verify timezone is set correctly with `TZ`
2. Check time format is `HH:MM` (24-hour)
3. For weekly sync, ensure `SYNC_DAY` is valid (0-6 or day name)

## License

MIT License - see [LICENSE](LICENSE) file for details
