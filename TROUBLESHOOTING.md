# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with Open-WebUI-Local-FileSync.

## Table of Contents

- [Files Not Syncing](#files-not-syncing)
- [Schedule Not Working](#schedule-not-working)
- [Upload Failures and Retries](#upload-failures-and-retries)
- [Knowledge Base Issues](#knowledge-base-issues)
- [Duplicate Content Detected Errors](#duplicate-content-detected-errors)
- [SSH Connection Issues](#ssh-connection-issues)
- [Viewing Logs](#viewing-logs)

## Files Not Syncing

If files are not being synchronized to Open WebUI, check the following:

1. **Verify API Key Configuration**
   - Check that `OPENWEBUI_API_KEY` is correctly set
   - Ensure the API key is valid and has not expired
   - Test the API key by making a manual API call

2. **Check Open WebUI URL**
   - Verify `OPENWEBUI_URL` is accessible from the container
   - Test connectivity: `docker exec openwebui-filesync curl -I $OPENWEBUI_URL`
   - Ensure there are no firewall rules blocking the connection

3. **Validate File Extensions**
   - Check file extensions match `ALLOWED_EXTENSIONS`
   - Default allowed extensions: `.md,.txt,.pdf,.doc,.docx,.json,.yaml,.yml`
   - Add additional extensions if needed

4. **Review Container Logs**
   - Check for errors: `docker logs openwebui-filesync`
   - Look for API errors, connection issues, or permission problems

5. **Check Knowledge Base Mappings**
   - If using `KNOWLEDGE_BASE_MAPPING`, verify paths match your volume mounts
   - Ensure files are in a mapped knowledge base path
   - Paths are relative to `FILES_DIR` (default `/data`)

6. **Verify Volume Mounts**
   - Confirm files are accessible inside the container:
     ```bash
     docker exec openwebui-filesync ls -la /data
     ```
   - Check file permissions (should be readable by the container user)

## Schedule Not Working

If the sync is not running at the scheduled time:

1. **Verify Timezone**
   - Check `TZ` is set correctly (e.g., `America/New_York`, `Europe/London`)
   - View available timezones: `timedatectl list-timezones`
   - Verify the current time in the container:
     ```bash
     docker exec openwebui-filesync date
     ```

2. **Check Time Format**
   - Ensure `SYNC_TIME` is in `HH:MM` format (24-hour)
   - Example: `"02:00"` for 2 AM, `"14:30"` for 2:30 PM
   - Time format must be quoted in YAML

3. **Validate Weekly Sync Day**
   - For weekly sync, ensure `SYNC_DAY` is valid
   - Accepted values: `0-6` (0=Sunday) or day names (`mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`)

4. **Check Cron Configuration**
   - View the cron configuration inside the container:
     ```bash
     docker exec openwebui-filesync cat /etc/crontabs/root
     ```
   - Verify the cron entry matches your schedule

5. **Review Cron Logs**
   - Check if cron is running: `docker exec openwebui-filesync ps aux | grep cron`
   - Review system logs for cron execution

## Upload Failures and Retries

If uploads are failing or not retrying:

1. **Check the State File**
   - Examine `/app/sync_state.json` for file status
   - Look for files with `"status": "failed"`
   - View state file: `docker exec openwebui-filesync cat /app/sync_state.json`

2. **Review Retry Configuration**
   - `MAX_RETRY_ATTEMPTS`: Default is 3
   - `RETRY_DELAY`: Default is 60 seconds
   - Increase these values if needed for slow/unreliable connections

3. **Automatic Retries**
   - Failed uploads are automatically retried on the next sync
   - Check logs for retry attempts and outcomes

4. **Manual Retry**
   - If max retries are exceeded, you can:
     - Manually remove the file entry from state file
     - Fix the underlying issue (e.g., network, permissions)
     - Wait for the next scheduled sync

5. **Increase Upload Timeout**
   - If files are taking longer to process, increase `UPLOAD_TIMEOUT`
   - Default is 300 seconds (5 minutes)
   - Larger files may need more time

6. **Check Network Connectivity**
   - Verify network between container and Open WebUI instance
   - Test with: `docker exec openwebui-filesync ping openwebui-host`
   - Check for network policies or firewall rules

7. **API Rate Limiting**
   - If syncing many files, check for API rate limits
   - Consider increasing delay between uploads
   - Check Open WebUI logs for rate limiting errors

## Knowledge Base Issues

If knowledge bases are not being created or files are not properly associated:

1. **Validate Knowledge Base Names**
   - Ensure knowledge base names don't contain special characters
   - Use alphanumeric characters, underscores, and hyphens
   - Avoid spaces (use underscores instead: `My_KB` not `My KB`)

2. **Verify Path Mappings**
   - Check paths in `KNOWLEDGE_BASE_MAPPING` match your volume mounts
   - Paths are relative to `FILES_DIR` (default `/data`)
   - Example: If you mount `./docs:/data/docs:ro`, use path `"docs"` in mapping

3. **Review Container Logs**
   - Check for knowledge base creation errors
   - Look for: "Creating knowledge base" or "Failed to create knowledge base"
   - Review API responses for details

4. **Test Knowledge Base Creation**
   - Manually test creating a knowledge base via Open WebUI interface
   - Verify API permissions allow knowledge base creation

5. **Check Configuration Priority**
   - Remember the priority order:
     1. `KNOWLEDGE_BASE_NAME` (single KB mode)
     2. `KNOWLEDGE_BASE_MAPPINGS` (JSON array)
     3. `KNOWLEDGE_BASE_MAPPING` (legacy format)
   - Ensure only one method is configured

## Duplicate Content Detected Errors

If you see "Duplicate content detected" errors:

### Automatic Backfill (Recommended)

The script automatically detects existing files in the knowledge base and updates the state file. This happens on the first sync after adding state persistence.

1. **Check Logs for Backfill Messages**
   - Look for "Backfilled state for existing file" messages
   - This confirms automatic backfill is working

2. **Verify State Persistence**
   - Ensure your state volume is mounted:
     ```yaml
     volumes:
       - ./state:/app/state
     ```
   - Check the state file exists: `docker exec openwebui-filesync ls -la /app/state`

3. **Wait for Automatic Detection**
   - On next sync, the script will detect existing files
   - State file will be updated automatically
   - Subsequent syncs will skip already-uploaded files

### Manual Resolution (If Automatic Fails)

If automatic backfill doesn't work:

1. **Reset State File**
   ```bash
   # Stop the container
   docker stop openwebui-filesync
   
   # Remove the state file (if mounted externally)
   rm ./state/sync_state.json
   
   # Or, if using default internal state, recreate the container
   docker rm openwebui-filesync
   docker-compose up -d
   ```

2. **Manual State File Update**
   - See [State File Format documentation](STATE_FORMAT.md#duplicate-content-detected-errors) for detailed steps
   - You can manually add file entries to the state file

3. **Clear Open WebUI Knowledge Base**
   - As a last resort, delete files from Open WebUI knowledge base
   - Then perform a fresh sync

### Prevention

- Always mount a volume for `/app/state` to persist state across restarts
- Don't delete the state file unless intentionally forcing a full re-sync
- Keep backups of your state file for recovery

## SSH Connection Issues

If SSH remote file ingestion is failing:

1. **Test SSH Connection**
   - Manually test SSH connection from your machine:
     ```bash
     ssh username@hostname
     ```
   - If manual connection fails, fix SSH configuration first

2. **Verify SSH Configuration**
   - Check hostname/IP address is correct
   - Verify port number (default: 22)
   - Ensure username is valid

3. **Authentication Issues**
   
   **For Password Authentication:**
   - Verify password is correct
   - Check if server allows password authentication
   - Review SSH server configuration (`PasswordAuthentication yes` in `/etc/ssh/sshd_config`)

   **For Key Authentication:**
   - Verify SSH key file is mounted correctly:
     ```bash
     docker exec openwebui-filesync ls -la /app/ssh_keys
     ```
   - Check key file permissions (should be readable)
   - Test key manually: `ssh -i ./ssh_keys/id_rsa username@hostname`
   - Ensure public key is in server's `~/.ssh/authorized_keys`

4. **Host Key Verification Failures**
   - If using strict host key checking, ensure `known_hosts` file exists
   - Add host key: `ssh-keyscan -H hostname >> ./ssh_keys/known_hosts`
   - Or use `SSH_STRICT_HOST_KEY_CHECKING=false` (less secure)

5. **Path Access Issues**
   - Verify remote paths exist and are accessible
   - Check file permissions on remote server
   - Test path access: `ssh username@hostname ls -la /remote/path`

6. **Network Issues**
   - Check firewall rules allow SSH connections
   - Verify network connectivity: `docker exec openwebui-filesync ping hostname`
   - Check SSH port is not blocked

7. **Review Container Logs**
   - Check for SSH-specific errors:
     ```bash
     docker logs openwebui-filesync | grep -i ssh
     ```
   - Look for authentication failures, timeout errors, or connection refused

## Viewing Logs

Logs are essential for troubleshooting. Here's how to view them:

### View Container Logs

```bash
# View all logs
docker logs openwebui-filesync

# Follow logs in real-time
docker logs -f openwebui-filesync

# View last 100 lines
docker logs --tail 100 openwebui-filesync

# View logs with timestamps
docker logs -t openwebui-filesync
```

### View Specific Log Patterns

```bash
# Search for errors
docker logs openwebui-filesync 2>&1 | grep -i error

# Search for SSH-related logs
docker logs openwebui-filesync 2>&1 | grep -i ssh

# Search for upload failures
docker logs openwebui-filesync 2>&1 | grep -i failed

# Search for retry attempts
docker logs openwebui-filesync 2>&1 | grep -i retry
```

### Export Logs to File

```bash
# Export all logs
docker logs openwebui-filesync > filesync-logs.txt 2>&1

# Export recent logs
docker logs --tail 1000 openwebui-filesync > recent-logs.txt 2>&1
```

### Common Log Messages

**Success Messages:**
- `Sync started at` - Sync has begun
- `Uploaded: filename` - File successfully uploaded
- `Processing complete for: filename` - File processed successfully
- `Sync completed` - Sync finished successfully

**Warning Messages:**
- `Retrying upload` - Upload failed, attempting retry
- `File not changed, skipping` - File unchanged since last sync
- `Excluded file/folder` - File/folder excluded by filter

**Error Messages:**
- `Failed to upload` - Upload failed after all retries
- `API error` - Error communicating with Open WebUI API
- `Connection refused` - Cannot connect to Open WebUI
- `Authentication failed` - Invalid API key or SSH credentials
- `Permission denied` - File permission issues

## Related Documentation

- [Configuration Guide](CONFIGURATION.md) - Complete configuration reference
- [Deployment Examples](DEPLOYMENT.md) - Example configurations
- [State File Format](STATE_FORMAT.md) - Understanding the state file
- [Quick Start Guide](QUICKSTART.md) - Getting started
