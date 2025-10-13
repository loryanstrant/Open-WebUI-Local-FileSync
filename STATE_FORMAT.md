# State File Format

This document describes the structure of the sync state file (`sync_state.json`) for advanced users who need to understand or manually manipulate the state.

## Location

By default, the state file is located at `/app/sync_state.json` inside the container. You can customize this location using the `STATE_FILE` environment variable.

**Important:** Ensure the state file location is persisted across container restarts by mounting it as a volume.

### Automatic Initialization

The sync script automatically:
1. **Creates the state directory** if it doesn't exist
2. **Creates an empty state file** if it doesn't exist
3. **Validates permissions** before starting sync operations

If the script cannot create or access the state file, it will exit with clear error messages indicating:
- The exact path it's trying to access
- Current file/directory permissions
- Suggestions for fixing permission issues

**Example initialization log output:**
```
[2025-10-13 12:29:03] Starting file sync...
[2025-10-13 12:29:03] State directory does not exist: /app/state
[2025-10-13 12:29:03] Attempting to create directory: /app/state
[2025-10-13 12:29:03] ✓ Created state directory: /app/state
[2025-10-13 12:29:03] State file does not exist: /app/state/sync_state.json
[2025-10-13 12:29:03] Attempting to create initial state file...
[2025-10-13 12:29:03] ✓ Created initial state file: /app/state/sync_state.json
```

## Purpose

The state file tracks:
- Files that have been synced and their current status
- Knowledge bases that have been created
- Upload history and retry information

## Format

The state file is a JSON object with two main sections:

```json
{
  "files": {
    "path/to/file.txt": {
      "hash": "abc123...",
      "status": "uploaded",
      "file_id": "file-uuid-123",
      "last_attempt": "2024-01-15T12:00:00",
      "retry_count": 0,
      "knowledge_base": "Documentation"
    }
  },
  "knowledge_bases": {
    "Documentation": {
      "id": "kb-uuid-456",
      "created_at": "2024-01-15T10:00:00"
    }
  }
}
```

## Files Section

Each file entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `hash` | string | MD5 hash of the file content |
| `status` | string | Current status: `uploaded`, `processing`, or `failed` |
| `file_id` | string | (Optional) OpenWebUI file ID returned after upload |
| `last_attempt` | string | ISO 8601 timestamp of last upload attempt |
| `retry_count` | number | Number of retry attempts (resets to 0 on success) |
| `knowledge_base` | string | (Optional) Name of the associated knowledge base |
| `error` | string | (Optional) Error message if upload failed |

### File Status Values

- **`uploaded`**: File was successfully uploaded and processed
- **`processing`**: File is currently being processed by OpenWebUI
- **`failed`**: Upload or processing failed, will be retried

## Knowledge Bases Section

Each knowledge base entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | OpenWebUI knowledge base ID |
| `created_at` | string | ISO 8601 timestamp when KB was created |

## Migration from Old Format

Previous versions used a simpler format:

```json
{
  "path/to/file.txt": "abc123...",
  "path/to/other.txt": "def456..."
}
```

This format is automatically migrated to the new format on first run. The migration:
1. Wraps existing entries in a `files` section
2. Converts hash strings to objects with `hash`, `status`, and `retry_count`
3. Adds an empty `knowledge_bases` section
4. Sets all existing files to `uploaded` status

## Automatic State Backfilling

When the sync script runs, it automatically detects files that already exist in the knowledge base but are not in the state file. This handles scenarios where:
- State was not persisted between container restarts
- You're adding a new volume mount to an existing deployment
- You manually deleted the state file but files still exist in OpenWebUI

The backfill process:
1. Queries each knowledge base for existing files
2. Matches existing files with local files by filename
3. Populates the state file with these matches
4. Prevents "duplicate content detected" errors on subsequent syncs

**Example scenario:**
```yaml
# Before: State not persisted
services:
  filesync:
    volumes:
      - ./docs:/data:ro
    # No state volume mount

# After: Adding state persistence
services:
  filesync:
    volumes:
      - ./docs:/data:ro
      - ./state:/app/state  # New state volume
```

When the container restarts with the new state volume mount:
- The script finds no existing state for your files
- It queries OpenWebUI and discovers files already exist
- It backfills the state automatically
- No duplicate uploads occur

**Log output during backfill:**
```
[2024-01-15 12:00:00] Starting file sync...
[2024-01-15 12:00:00] Found 10 files to check
[2024-01-15 12:00:01] Checking for existing files in knowledge base: Documentation
[2024-01-15 12:00:01] ↻ Backfilled state for existing file: readme.md
[2024-01-15 12:00:01] ↻ Backfilled state for existing file: guide.md
[2024-01-15 12:00:01] Backfilled state for 8 existing files
[2024-01-15 12:00:01] Sync complete: 0 uploaded, 8 skipped, 0 failed, 0 retried
```

## Manual State Manipulation

### Reset All Files

To force re-upload of all files:

```bash
docker exec openwebui-filesync rm /app/sync_state.json
# Or if you have a mounted volume:
rm ./state/sync_state.json
```

### Reset Failed Files

To retry all failed uploads on the next sync:

```bash
docker exec openwebui-filesync python3 << 'EOF'
import json
import os

STATE_FILE = os.getenv('STATE_FILE', '/app/sync_state.json')

with open(STATE_FILE, 'r') as f:
    state = json.load(f)

# Reset retry count for failed files
for file_key, file_info in state.get('files', {}).items():
    if file_info.get('status') == 'failed':
        file_info['retry_count'] = 0

with open(STATE_FILE, 'w') as f:
    json.dump(state, f, indent=2)

print("Reset retry count for all failed files")
EOF
```

### View Current State

To view the current state:

```bash
docker exec openwebui-filesync cat /app/sync_state.json | python3 -m json.tool
```

### Remove Specific File from State

To force re-upload of a specific file:

```bash
docker exec openwebui-filesync python3 << 'EOF'
import json
import os

STATE_FILE = os.getenv('STATE_FILE', '/app/sync_state.json')
FILE_TO_REMOVE = 'docs/readme.md'  # Change this

with open(STATE_FILE, 'r') as f:
    state = json.load(f)

if FILE_TO_REMOVE in state.get('files', {}):
    del state['files'][FILE_TO_REMOVE]
    print(f"Removed {FILE_TO_REMOVE} from state")
else:
    print(f"{FILE_TO_REMOVE} not found in state")

with open(STATE_FILE, 'w') as f:
    json.dump(state, f, indent=2)
EOF
```

## Backup and Restore

### Backup State

```bash
docker cp openwebui-filesync:/app/sync_state.json ./sync_state_backup.json
```

### Restore State

```bash
docker cp ./sync_state_backup.json openwebui-filesync:/app/sync_state.json
```

## Troubleshooting

### State file permissions errors

If you see errors like:
```
[2025-10-13 12:29:03] ✗ ERROR: State directory is not writable: /app/state
[2025-10-13 12:29:03]   Current permissions: 755
[2025-10-13 12:29:03]   Please ensure the container has write permissions to this location
```

**Cause:** The container doesn't have write permissions to the state directory.

**Solution:**

1. **Check your volume mount** in docker-compose.yml:
   ```yaml
   volumes:
     - ./state:/app/state  # Local directory must be writable
   ```

2. **Fix directory permissions** on the host:
   ```bash
   sudo chmod -R 777 ./state  # Or use appropriate ownership/permissions
   ```

3. **Alternative: Use a named volume** instead of a bind mount:
   ```yaml
   volumes:
     - filesync-state:/app/state
   
   volumes:
     filesync-state:
   ```

### State file is corrupted

If the state file becomes corrupted, it will be recreated with an empty state on the next sync. All files will be re-uploaded.

### Files stuck in "processing" status

If files remain in "processing" status indefinitely:

1. Check OpenWebUI logs for processing errors
2. Increase `UPLOAD_TIMEOUT` environment variable
3. Manually reset the file status to "failed" to force a retry

### Knowledge base IDs don't match OpenWebUI

If you manually delete or recreate knowledge bases in OpenWebUI, remove the corresponding entries from the state file to allow the sync script to recreate them.

### Duplicate content detected errors

If you see errors like:
```
✗ Failed to add file to knowledge base: 400 - {"detail":"400: Duplicate content detected. Please provide unique content to proceed."}
```

**Cause:** Files already exist in OpenWebUI but the state file doesn't know about them.

**Solution:** The script now automatically detects and backfills state for existing files. If you still see these errors:

1. **Wait for the next sync cycle** - The backfill happens automatically on the first run
2. **Check the logs** - Look for "Backfilled state for existing file" messages
3. **Verify state persistence** - Ensure your state volume is properly mounted:
   ```yaml
   volumes:
     - ./state:/app/state
   ```
4. **Manual fix** - If needed, remove the specific file from state to force a check:
   ```bash
   docker exec openwebui-filesync rm /app/sync_state.json
   ```

After the next sync, the state will be automatically backfilled from the knowledge base.

## Best Practices

1. **Persist State**: Mount the state file or its parent directory as a volume to preserve state across container restarts
2. **Regular Backups**: Periodically backup the state file, especially before major changes
3. **Monitor Size**: The state file grows with the number of files; monitor its size in large deployments
4. **Version Control**: Consider keeping state file backups in version control (without sensitive data)
