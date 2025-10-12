# State File Format

This document describes the structure of the sync state file (`sync_state.json`) for advanced users who need to understand or manually manipulate the state.

## Location

By default, the state file is located at `/app/sync_state.json` inside the container. You can customize this location using the `STATE_FILE` environment variable.

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

### State file is corrupted

If the state file becomes corrupted, it will be recreated with an empty state on the next sync. All files will be re-uploaded.

### Files stuck in "processing" status

If files remain in "processing" status indefinitely:

1. Check OpenWebUI logs for processing errors
2. Increase `UPLOAD_TIMEOUT` environment variable
3. Manually reset the file status to "failed" to force a retry

### Knowledge base IDs don't match OpenWebUI

If you manually delete or recreate knowledge bases in OpenWebUI, remove the corresponding entries from the state file to allow the sync script to recreate them.

## Best Practices

1. **Persist State**: Mount the state file or its parent directory as a volume to preserve state across container restarts
2. **Regular Backups**: Periodically backup the state file, especially before major changes
3. **Monitor Size**: The state file grows with the number of files; monitor its size in large deployments
4. **Version Control**: Consider keeping state file backups in version control (without sensitive data)
