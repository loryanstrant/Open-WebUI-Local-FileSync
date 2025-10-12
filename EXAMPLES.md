# Example Usage

This document provides practical examples for deploying the Open WebUI File Sync container.

## Example 1: Basic Daily Sync

Sync markdown files from a local directory daily at 2 AM:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: sk-your-api-key-here
      TZ: America/New_York
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      ALLOWED_EXTENSIONS: .md
    volumes:
      - ./markdown-docs:/data:ro
    restart: unless-stopped
```

## Example 2: Hourly Sync with Multiple File Types

Sync every hour at 15 minutes past the hour:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: sk-your-api-key-here
      TZ: UTC
      SYNC_SCHEDULE: hourly
      SYNC_TIME: "00:15"
      ALLOWED_EXTENSIONS: .md,.txt,.pdf,.doc,.docx
    volumes:
      - ./documents:/data:ro
    restart: unless-stopped
```

## Example 3: Weekly Sync on Sundays

Sync every Sunday at midnight:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: sk-your-api-key-here
      TZ: America/Los_Angeles
      SYNC_SCHEDULE: weekly
      SYNC_TIME: "00:00"
      SYNC_DAY: "0"  # 0 = Sunday
    volumes:
      - ./weekly-reports:/data:ro
    restart: unless-stopped
```

## Example 4: Weekly Sync on Fridays (End of Week)

Sync every Friday at 5 PM:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: sk-your-api-key-here
      TZ: Europe/London
      SYNC_SCHEDULE: weekly
      SYNC_TIME: "17:00"
      SYNC_DAY: "fri"  # Can also use "5"
    volumes:
      - ./weekly-updates:/data:ro
    restart: unless-stopped
```

## Example 5: Complete Stack with Open WebUI

Running both Open WebUI and the file sync container together:

```yaml
version: '3.8'

services:
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: openwebui
    ports:
      - "8080:8080"
    volumes:
      - openwebui-data:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    volumes:
      - ollama-data:/root/.ollama
    restart: unless-stopped

  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    depends_on:
      - openwebui
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: sk-your-api-key-here
      TZ: UTC
      SYNC_SCHEDULE: daily
      SYNC_TIME: "03:00"
    volumes:
      - ./knowledge-base:/data:ro
    restart: unless-stopped

volumes:
  openwebui-data:
  ollama-data:
```

## Example 6: Using Docker CLI

```bash
docker run -d \
  --name openwebui-filesync \
  -e OPENWEBUI_URL=http://192.168.1.100:8080 \
  -e OPENWEBUI_API_KEY=sk-your-api-key-here \
  -e TZ=America/Chicago \
  -e SYNC_SCHEDULE=daily \
  -e SYNC_TIME=01:00 \
  -e ALLOWED_EXTENSIONS=.md,.txt \
  -v /home/user/documents:/data:ro \
  --restart unless-stopped \
  ghcr.io/loryanstrant/open-webui-local-filesync:latest
```

## Monitoring and Logs

To view the sync logs:

```bash
# Follow logs in real-time
docker logs -f openwebui-filesync

# View last 100 lines
docker logs --tail 100 openwebui-filesync

# View logs with timestamps
docker logs -t openwebui-filesync
```

## Testing Your Configuration

Before setting up the schedule, you can test that files will be synced correctly:

```bash
# Run a one-time sync (container will exit after initial sync completes)
docker run --rm \
  -e OPENWEBUI_URL=http://your-openwebui:8080 \
  -e OPENWEBUI_API_KEY=sk-your-api-key \
  -v /path/to/files:/data:ro \
  ghcr.io/loryanstrant/open-webui-local-filesync:latest \
  python3 /app/sync.py
```

## Timezone Examples

Common timezone values:

- `UTC` - Coordinated Universal Time
- `America/New_York` - Eastern Time (US & Canada)
- `America/Chicago` - Central Time (US & Canada)
- `America/Denver` - Mountain Time (US & Canada)
- `America/Los_Angeles` - Pacific Time (US & Canada)
- `Europe/London` - British Time
- `Europe/Paris` - Central European Time
- `Asia/Tokyo` - Japan Time
- `Australia/Sydney` - Australian Eastern Time

For a complete list of timezones, see: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

## Day of Week Reference

For weekly syncs using `SYNC_DAY`:

| Number | Name | Alternative |
|--------|------|-------------|
| 0 | Sunday | `sun` |
| 1 | Monday | `mon` |
| 2 | Tuesday | `tue` |
| 3 | Wednesday | `wed` |
| 4 | Thursday | `thu` |
| 5 | Friday | `fri` |
| 6 | Saturday | `sat` |
