# Testing Guide for Open-WebUI-Local-FileSync Fixes

## Quick Verification Steps

### 1. Deploy and Restart
```bash
# On your server
git pull
docker restart Open-WebUI-filesync
```

### 2. Check Browser Tab Title
- Open web interface
- Tab should show "Open WebUI FileSync"

### 3. Verify No SSH Duplicates
1. Trigger a sync
2. Check logs for normalized file keys: `ssh:hostname/file.txt`
3. Trigger another sync
4. Files should be "skipped" not "uploaded"

### 4. Check Statistics
- Dashboard should show separate counts for each SSH source
- Not all files showing as "Local Files"

### 5. Verify File Metadata
- Go to Sync State tab
- Dates should be real (not 1970)
- Source column shows correct origin

### 6. Test KB Updates
- Select files in Sync State tab
- Update knowledge base
- Changes should propagate to Open WebUI

## Expected Results
 Browser tab: "Open WebUI FileSync"
 SSH files: Consistent keys across syncs
 Statistics: Accurate per-source counts  
 Dates: Real timestamps (not 1970)
 KB updates: Working in web interface
