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

## Example 1a: Knowledge Base Organization

Sync files into organized knowledge bases based on directory structure:

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
      KNOWLEDGE_BASE_MAPPING: "product-docs:Product_Documentation,internal-wiki:Internal_Wiki,customer-guides:Customer_Guides"
      ALLOWED_EXTENSIONS: .md,.txt,.pdf
      MAX_RETRY_ATTEMPTS: 5
      RETRY_DELAY: 120
    volumes:
      - ./documentation/product-docs:/data/product-docs:ro
      - ./documentation/internal-wiki:/data/internal-wiki:ro
      - ./documentation/customer-guides:/data/customer-guides:ro
    restart: unless-stopped
```

This configuration:
- Maps three different directories to three knowledge bases
- Product documentation goes to "Product_Documentation" KB
- Internal wiki goes to "Internal_Wiki" KB
- Customer guides go to "Customer_Guides" KB
- Retries failed uploads up to 5 times with 2-minute delays

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

## Example 5: Complete Stack with Open WebUI and Knowledge Bases

Running both Open WebUI and the file sync container together with organized knowledge bases:

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
      # Organize files into separate knowledge bases
      KNOWLEDGE_BASE_MAPPING: "technical:Technical_Docs,product:Product_Info,support:Support_KB"
      # Configure retry behavior
      MAX_RETRY_ATTEMPTS: 5
      RETRY_DELAY: 120
      UPLOAD_TIMEOUT: 600
    volumes:
      - ./documentation/technical:/data/technical:ro
      - ./documentation/product:/data/product:ro
      - ./documentation/support:/data/support:ro
    restart: unless-stopped

volumes:
  openwebui-data:
  ollama-data:
```

This setup:
- Runs Open WebUI with Ollama backend
- Syncs files from three different directories to three knowledge bases
- Configures robust retry logic (5 attempts, 2-minute delays)
- Allows 10 minutes for file processing

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
