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

## Example 1a: Single Knowledge Base (Simplest)

When all your files should go to one knowledge base:

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
      # Simple: All files go to this knowledge base
      KNOWLEDGE_BASE_NAME: "Documentation"
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
- All files from all three directories go to "Documentation" KB
- Much simpler than mapping each directory separately
- Retries failed uploads up to 5 times with 2-minute delays

## Example 1b: Multiple Knowledge Bases with JSON Array

When you want different directories in different knowledge bases:

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
      # JSON array format for multiple knowledge bases
      KNOWLEDGE_BASE_MAPPINGS: |
        [
          {"path": "product-docs", "kb": "Product_Documentation"},
          {"path": "internal-wiki", "kb": "Internal_Wiki"},
          {"path": "customer-guides", "kb": "Customer_Guides"}
        ]
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
- Product documentation goes to "Product_Documentation" KB
- Internal wiki goes to "Internal_Wiki" KB
- Customer guides go to "Customer_Guides" KB
- More readable than comma-separated format
- Retries failed uploads up to 5 times with 2-minute delays

## Example 1c: Multiple Knowledge Bases (Legacy Format)

The original format still works for backward compatibility:

```yaml
environment:
  KNOWLEDGE_BASE_MAPPING: "product-docs:Product_Documentation,internal-wiki:Internal_Wiki,customer-guides:Customer_Guides"
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
      # Organize files into separate knowledge bases using JSON array
      KNOWLEDGE_BASE_MAPPINGS: |
        [
          {"path": "technical", "kb": "Technical_Docs"},
          {"path": "product", "kb": "Product_Info"},
          {"path": "support", "kb": "Support_KB"}
        ]
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

## Example 7: Home Configuration with Filters (Real-world)

This example shows a real home automation setup with multiple services, using filters to control which files are synced:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: Open-WebUI-filesync
    environment:
      OPENWEBUI_URL: https://openwebui.strant.casa
      OPENWEBUI_API_KEY: API-KEY
      TZ: Australia/Melbourne
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      STATE_FILE: /app/state/sync_state.json
      # JSON configuration with include/exclude filters
      KNOWLEDGE_BASE_MAPPINGS: |
        [
          {
            "path": "simple-wik",
            "kb": "SimpleWiki"
          },
          {
            "path": "wikidocs",
            "kb": "WikiDocs"
          },
          {
            "path": "esphome",
            "kb": "ESPHome",
            "exclude": ["*/*"],
            "include": ["includes/*"]
          },
          {
            "path": "evcc",
            "kb": "EVCC"
          },
          {
            "path": "zigbee2mqtt",
            "kb": "Zigbee2MQTT",
            "exclude": [".git/*", "*.log", "database.db"]
          },
          {
            "path": "docker-documenter-for-portainer",
            "kb": "DockerDocs",
            "exclude": ["*_2025*"]
          }
        ]
    volumes:
      - /etc/docker/simple-wik:/data/simple-wik:ro
      - /etc/docker/wikidocs:/data/wikidocs:ro
      - /etc/docker/esphome:/data/esphome:ro
      - /etc/docker/evcc:/data/evcc:ro
      - /etc/docker/zigbee2mqtt:/data/zigbee2mqtt:ro
      - /etc/docker/docker-documenter-for-portainer:/data/docker-documenter-for-portainer:ro
      # Persist state between container restarts
      - /etc/docker/openwebui-filesync:/app/state
    restart: unless-stopped
```

**This configuration demonstrates:**

1. **Simple Wiki & Wiki Docs**: No filters - all files synced
2. **ESPHome**: 
   - Excludes all subdirectories with `"exclude": ["*/*"]`
   - BUT includes the `includes` subdirectory with `"include": ["includes/*"]`
   - This is perfect for configuration files that reference includes
3. **EVCC**: No filters - all files synced
4. **Zigbee2MQTT**:
   - Excludes `.git` directory, log files, and database file
   - Only configuration files and documentation are synced
5. **Docker Documenter**:
   - Excludes any files containing `_2025` in the filename
   - Useful for excluding dated archives or temporary files

**Filter Pattern Examples:**
- `"*/*"` - All subdirectories
- `"*_2025*"` - Files containing "_2025" anywhere in name
- `".git/*"` - All files in .git directory
- `"*.log"` - All log files
- `"includes/*"` - All files in includes subdirectory (when used in include)

**Alternative: Single Knowledge Base**

If you prefer all files in one knowledge base, simply use:
```yaml
environment:
  KNOWLEDGE_BASE_NAME: "HomeConfiguration"
```
And remove the `KNOWLEDGE_BASE_MAPPINGS` section. Note that filters are only supported in the `KNOWLEDGE_BASE_MAPPINGS` format.

## Example 8: SSH Remote File Ingestion

Fetch files from remote SSH servers and sync them to Open WebUI:

### Example 8a: Single SSH Server with Password Authentication

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
      SYNC_TIME: "03:00"
      # SSH remote source with password authentication
      SSH_REMOTE_SOURCES: |
        [
          {
            "host": "192.168.1.100",
            "port": 22,
            "username": "backup_user",
            "password": "secure_password",
            "paths": ["/home/user/documents", "/home/user/notes"],
            "kb": "Remote_Documents"
          }
        ]
    volumes:
      - ./filesync-state:/app/state
    restart: unless-stopped
```

This configuration:
- Connects to SSH server at 192.168.1.100
- Uses password authentication
- Downloads files from two remote directories
- Stores all files in "Remote_Documents" knowledge base
- Runs daily at 3 AM

### Example 8b: SSH Server with Key Authentication

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
      SYNC_TIME: "00:00"
      # SSH remote source with key authentication
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
      - ./filesync-state:/app/state
    restart: unless-stopped
```

This configuration:
- Uses SSH key authentication with key file at `./ssh_keys/deploy_key`
- Syncs every hour
- SSH keys directory is mounted read-only for security

**Note:** Ensure your SSH private key file has correct permissions (600):
```bash
chmod 600 ./ssh_keys/deploy_key
```

### Example 8c: Multiple SSH Servers

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: sk-your-api-key-here
      TZ: America/Chicago
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      # Multiple SSH sources with different authentication methods
      SSH_REMOTE_SOURCES: |
        [
          {
            "host": "dev-server.local",
            "username": "developer",
            "password": "dev_password",
            "paths": ["/opt/app/config", "/opt/app/docs"],
            "kb": "Development_Docs"
          },
          {
            "host": "staging.example.com",
            "port": 2222,
            "username": "staging_user",
            "key_filename": "staging_key",
            "paths": ["/var/staging/docs"],
            "kb": "Staging_Docs"
          },
          {
            "host": "prod-server.com",
            "username": "prod_user",
            "key_filename": "prod_key",
            "password": "key_passphrase",
            "paths": ["/etc/app/config", "/var/app/docs"],
            "kb": "Production_Docs"
          }
        ]
    volumes:
      - ./ssh_keys:/app/ssh_keys:ro
      - ./filesync-state:/app/state
    restart: unless-stopped
```

This configuration demonstrates:
- Three different SSH servers
- Mix of password and key authentication
- Different ports (dev and prod use 22, staging uses 2222)
- Password field can be used as key passphrase
- Each server's files go to a different knowledge base

### Example 8d: Combined Local and SSH Sources

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
      SYNC_SCHEDULE: daily
      SYNC_TIME: "04:00"
      # Combine local and remote sources
      KNOWLEDGE_BASE_MAPPINGS: |
        [
          {"path": "local-docs", "kb": "Local_Documentation"},
          {"path": "local-config", "kb": "Local_Config"}
        ]
      SSH_REMOTE_SOURCES: |
        [
          {
            "host": "remote-server.com",
            "username": "user",
            "key_filename": "remote_key",
            "paths": ["/home/user/wiki"],
            "kb": "Remote_Wiki"
          }
        ]
    volumes:
      - ./local-docs:/data/local-docs:ro
      - ./local-config:/data/local-config:ro
      - ./ssh_keys:/app/ssh_keys:ro
      - ./filesync-state:/app/state
    restart: unless-stopped
```

This configuration:
- Syncs files from both local volumes and remote SSH server
- Local files are organized into two knowledge bases
- Remote SSH files go to a separate knowledge base
- All sources are synced in the same schedule

### SSH Troubleshooting

**Connection Issues:**
```bash
# Test SSH connection manually
docker exec -it openwebui-filesync ssh user@hostname

# Check SSH key permissions
ls -la ./ssh_keys/
# Should show: -rw------- (600) for private keys
```

**Check Logs:**
```bash
# Monitor SSH connection attempts
docker logs -f openwebui-filesync | grep -i ssh
```

**Common Issues:**
1. **Authentication Failed**: Check username, password, or key file path
2. **Connection Timeout**: Verify host is reachable and port is correct
3. **Permission Denied**: Ensure SSH key has correct permissions (600)
4. **Key Not Found**: Check `key_filename` path is correct (relative to `/app/ssh_keys`)
5. **Host Key Warning**: If you see warnings about host keys, add a `known_hosts` file (see Security section below)

### SSH Security Best Practices

**Host Key Verification:**

For production use, it's strongly recommended to use a `known_hosts` file to verify SSH server identities:

1. **Generate known_hosts file:**
```bash
# Create the SSH keys directory if it doesn't exist
mkdir -p ./ssh_keys

# Add host keys for your servers
ssh-keyscan -H server1.example.com >> ./ssh_keys/known_hosts
ssh-keyscan -H 192.168.1.100 >> ./ssh_keys/known_hosts
ssh-keyscan -H server2.example.com >> ./ssh_keys/known_hosts

# Or copy from your existing known_hosts
cp ~/.ssh/known_hosts ./ssh_keys/known_hosts
```

2. **Mount the known_hosts file:**
```yaml
volumes:
  - ./ssh_keys:/app/ssh_keys:ro
```

3. **Verify it's working:**
```bash
# Check the logs - you should see "Loading known_hosts" messages
docker logs openwebui-filesync | grep known_hosts
```

**Without known_hosts:**
- The container will use `AutoAddPolicy` which accepts any host key
- A warning will be logged on each connection
- This is less secure but may be acceptable for trusted networks
- First connection to each host is vulnerable to man-in-the-middle attacks

**SSH Key Security:**
```bash
# Ensure correct permissions on SSH keys
chmod 600 ./ssh_keys/id_rsa
chmod 644 ./ssh_keys/id_rsa.pub
chmod 644 ./ssh_keys/known_hosts
chmod 700 ./ssh_keys
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
