# Quick Start Guide - Knowledge Bases & Retry Logic

This guide will get you started with the new knowledge base mapping and retry logic features.

## Prerequisites

- Open WebUI instance running and accessible
- Open WebUI API key (see [main README](README.md#getting-your-open-webui-api-key))
- Docker and docker-compose installed

## Basic Setup (No Knowledge Bases)

If you just want automatic retries without knowledge base organization:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
    volumes:
      - ./files:/data:ro
    restart: unless-stopped
```

This configuration:
- ✅ Uploads files to Open WebUI
- ✅ Automatically retries failed uploads (up to 3 times)
- ✅ Waits for processing verification
- ❌ Does not organize files into knowledge bases

> 💡 **Important:** Add a state volume to persist sync information between container restarts:
> ```yaml
> volumes:
>   - ./files:/data:ro
>   - ./state:/app/state  # Persist state
> ```
> Without state persistence, the script will re-check all files on every restart. However, it **automatically backfills** state from existing knowledge base files, preventing duplicate uploads.

## With Knowledge Base Organization

To organize files into knowledge bases based on their directory:

### Approach 1: Single Knowledge Base (Simplest)

When all your files should go to one knowledge base:

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      
      # All files go to this knowledge base
      KNOWLEDGE_BASE_NAME: "MyDocumentation"
      
    volumes:
      - ./my-documents:/data:ro
    restart: unless-stopped
```

This is perfect when you have multiple directories or volumes but want them all in one knowledge base.

### Approach 2: Multiple Knowledge Bases

#### Step 1: Organize Your Files

Create a directory structure:

```
my-documents/
├── technical-docs/
│   ├── architecture.md
│   └── api-guide.md
├── user-guides/
│   ├── getting-started.md
│   └── tutorials.md
└── faqs/
    └── common-questions.md
```

#### Step 2: Create docker-compose.yml

**Option A: Using JSON Array Format (Recommended)**

```yaml
version: '3.8'

services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    container_name: openwebui-filesync
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      SYNC_SCHEDULE: daily
      SYNC_TIME: "02:00"
      
      # Map directories to knowledge bases using JSON array
      KNOWLEDGE_BASE_MAPPINGS: |
        [
          {"path": "technical-docs", "kb": "Technical_Documentation"},
          {"path": "user-guides", "kb": "User_Guides"},
          {"path": "faqs", "kb": "FAQ"}
        ]
      
    volumes:
      - ./my-documents:/data:ro
    restart: unless-stopped
```

**Option B: Using Legacy Format**

```yaml
environment:
  # Map directories to knowledge bases (comma-separated)
  KNOWLEDGE_BASE_MAPPING: "technical-docs:Technical_Documentation,user-guides:User_Guides,faqs:FAQ"
```

### Step 3: Start the Container

```bash
docker-compose up -d
```

### Step 4: Monitor the Sync

```bash
# Watch the logs
docker logs -f openwebui-filesync

# You should see:
# [2024-01-15 12:00:00] Starting file sync...
# [2024-01-15 12:00:00] Knowledge base mapping configured: 3 paths
# [2024-01-15 12:00:01] Created new knowledge base: Technical_Documentation (ID: kb-123)
# [2024-01-15 12:00:02] Created new knowledge base: User_Guides (ID: kb-456)
# [2024-01-15 12:00:03] Created new knowledge base: FAQ (ID: kb-789)
# [2024-01-15 12:00:04] ✓ Uploaded: architecture.md to KB ID: kb-123
# ...
```

## Advanced Configuration

### Custom Retry Behavior

For unreliable networks or large files that take longer to process:

```yaml
environment:
  OPENWEBUI_URL: http://openwebui:8080
  OPENWEBUI_API_KEY: your_api_key_here
  KNOWLEDGE_BASE_MAPPING: "docs:Documentation"
  
  # Retry configuration
  MAX_RETRY_ATTEMPTS: 5      # Try up to 5 times
  RETRY_DELAY: 120           # Wait 2 minutes between retries
  UPLOAD_TIMEOUT: 600        # Wait up to 10 minutes for processing
```

### Multiple Volume Mounts

If your files are in different physical locations on disk:

**Option 1: All to one knowledge base (simplest)**

```yaml
services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      KNOWLEDGE_BASE_NAME: "AllDocumentation"
    volumes:
      - /path/to/team/docs:/data/team-docs:ro
      - /path/to/customer/docs:/data/customer-docs:ro
      - /path/to/internal:/data/internal:ro
    restart: unless-stopped
```

**Option 2: Separate knowledge bases (JSON array)**

```yaml
services:
  filesync:
    image: ghcr.io/loryanstrant/open-webui-local-filesync:latest
    environment:
      OPENWEBUI_URL: http://openwebui:8080
      OPENWEBUI_API_KEY: your_api_key_here
      KNOWLEDGE_BASE_MAPPINGS: |
        [
          {"path": "team-docs", "kb": "Team_Docs"},
          {"path": "customer-docs", "kb": "Customer_Docs"},
          {"path": "internal", "kb": "Internal_KB"}
        ]
    volumes:
      - /path/to/team/docs:/data/team-docs:ro
      - /path/to/customer/docs:/data/customer-docs:ro
      - /path/to/internal:/data/internal:ro
    restart: unless-stopped
```

**Option 3: Legacy format**

```yaml
environment:
  KNOWLEDGE_BASE_MAPPING: "team-docs:Team_Docs,customer-docs:Customer_Docs,internal:Internal_KB"
    restart: unless-stopped
```

## Troubleshooting

### Check if Knowledge Bases Were Created

```bash
# View the state file
docker exec openwebui-filesync cat /app/sync_state.json | python3 -m json.tool
```

Look for the `knowledge_bases` section:
```json
{
  "knowledge_bases": {
    "Technical_Documentation": {
      "id": "kb-123",
      "created_at": "2024-01-15T12:00:00"
    }
  }
}
```

### Check Upload Status

Look at the `files` section in the state file:

```json
{
  "files": {
    "technical-docs/architecture.md": {
      "hash": "abc123...",
      "status": "uploaded",
      "file_id": "file-xyz",
      "last_attempt": "2024-01-15T12:00:00",
      "retry_count": 0,
      "knowledge_base": "Technical_Documentation"
    }
  }
}
```

Status meanings:
- `uploaded`: Successfully uploaded and processed ✅
- `processing`: Currently being processed ⏳
- `failed`: Upload or processing failed, will retry 🔄

### Common Issues

#### Issue: Files not going to correct knowledge base

**Check:**
1. Verify you're using one of the supported formats:
   - Single KB: `KNOWLEDGE_BASE_NAME: "MyKB"`
   - JSON array: `KNOWLEDGE_BASE_MAPPINGS: '[{"path": "docs", "kb": "Documentation"}]'`
   - Legacy: `KNOWLEDGE_BASE_MAPPING: "path1:kb_name1,path2:kb_name2"`
2. Ensure paths match your volume mounts
3. Paths are relative to `/data` inside the container

**Examples:**
```yaml
# ❌ Wrong - includes /data prefix
KNOWLEDGE_BASE_MAPPINGS: '[{"path": "/data/docs", "kb": "Documentation"}]'

# ✅ Correct - relative to /data
KNOWLEDGE_BASE_MAPPINGS: '[{"path": "docs", "kb": "Documentation"}]'

# ✅ Also correct - single KB mode
KNOWLEDGE_BASE_NAME: "Documentation"
KNOWLEDGE_BASE_MAPPING: "docs:Documentation"  # Relative to /data
```

#### Issue: Uploads keep failing

**Check:**
1. View logs: `docker logs openwebui-filesync`
2. Verify API key is correct
3. Check Open WebUI URL is accessible from container
4. Try increasing `UPLOAD_TIMEOUT` for large files

**Reset failed files:**
```bash
docker exec openwebui-filesync python3 << 'EOF'
import json
state_file = '/app/sync_state.json'
with open(state_file, 'r') as f:
    state = json.load(f)
for file_info in state.get('files', {}).values():
    if file_info.get('status') == 'failed':
        file_info['retry_count'] = 0
with open(state_file, 'w') as f:
    json.dump(state, f, indent=2)
print("Reset all failed files")
EOF
```

#### Issue: Knowledge bases not created

**Possible causes:**
1. OpenWebUI API doesn't support knowledge base creation
2. API key lacks permissions
3. Network connectivity issues

**Workaround:**
- Create knowledge bases manually in Open WebUI first
- The sync will find and use existing knowledge bases

## Testing Your Configuration

Before setting up the schedule, test that everything works:

```bash
# One-time sync (exits after completion)
docker run --rm \
  -e OPENWEBUI_URL=http://openwebui:8080 \
  -e OPENWEBUI_API_KEY=your_api_key_here \
  -e KNOWLEDGE_BASE_MAPPING="docs:Documentation" \
  -v ./my-documents:/data:ro \
  ghcr.io/loryanstrant/open-webui-local-filesync:latest \
  python3 /app/sync.py
```

Watch the output to ensure:
- Knowledge bases are created/found
- Files are uploaded successfully
- No errors occur

## Next Steps

- Read [EXAMPLES.md](EXAMPLES.md) for more configuration examples
- See [STATE_FORMAT.md](STATE_FORMAT.md) for detailed state file documentation
- Review [IMPLEMENTATION.md](IMPLEMENTATION.md) for technical details
- Check [FLOW_DIAGRAM.md](FLOW_DIAGRAM.md) for visual workflow documentation

## Getting Help

If you encounter issues:
1. Check container logs: `docker logs openwebui-filesync`
2. Review the [Troubleshooting](README.md#troubleshooting) section
3. Check the state file for upload status
4. Open an issue on GitHub with logs and configuration (remove sensitive data)
