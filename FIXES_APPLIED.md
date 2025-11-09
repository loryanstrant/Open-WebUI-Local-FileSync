# Fixes Applied to Open-WebUI-Local-FileSync

## Date: 2025-11-09

### Issues Fixed

#### 1. Browser Tab Title 
**Issue**: Browser tab showed "Open-WebUI FileSync Configuration"  
**Fix**: Changed to "Open WebUI FileSync" in `web.py` line 29

#### 2. Duplicate Files from SSH Sources 
**Issue**: Files synced via SSH were seen as duplicates on each sync because temporary directories had unique random suffixes (e.g., `ssh_hostname_abc123/file.txt` vs `ssh_hostname_xyz789/file.txt`)

**Root Cause**: 
- Line 1217 in `sync.py`: `tempfile.mkdtemp()` creates unique directory names
- Line 1277 in `sync.py`: `file_key = str(filepath.relative_to(FILES_DIR))` included the unique temp directory

**Fix**: Implemented normalized file keys
- Created `ssh_source_map` dictionary to track SSH source information
- Changed file_key format:
  - **SSH files**: `ssh:<hostname>/<relative_path>` (e.g., `ssh:myserver/docs/file.txt`)
  - **Local files**: `local/<relative_path>` (e.g., `local/documents/file.txt`)
- This ensures the same file from SSH has the same key across syncs

#### 3. Statistics Showing All Files as "Local" 
**Issue**: Source statistics in the dashboard showed all files as coming from "Local Files" instead of their respective SSH sources

**Fix**: 
- Added `source_type` and `source_name` fields to file state tracking
- Updated statistics calculation in `/api/status` endpoint to use tracked source information
- Now accurately counts files, conversions, and errors per source

#### 4. Knowledge Base Files Tab Issues 
**Issue**: 
- Files showed creation date as 1970 (Unix epoch 0)
- Knowledge base information not displayed correctly
- Updating KB for files didn't work

**Fixes**:
- Added comprehensive metadata tracking to file state:
  - `created_at`: File creation timestamp
  - `modified_at`: File modification timestamp  
  - `file_size`: File size in bytes
  - `filename`: Original filename
  - `source_type`: 'local' or 'ssh'
  - `source_name`: Display name of source
- Enhanced `/api/state` endpoint to return all metadata
- Improved `/api/state/update_kb` endpoint to:
  - Actually update files in Open WebUI (not just state file)
  - Create knowledge bases if they don't exist
  - Properly handle file ID to KB associations
  - Report errors for individual file updates

### Modified Files

1. **sync.py**
   - Lines ~1205-1225: Added `ssh_source_map` to track SSH source metadata
   - Lines ~1277-1307: Implemented normalized file key generation
   - Lines ~1362-1385: Added file metadata collection (size, dates)
   - Lines ~1385-1530: Updated all state saving operations to include source and metadata fields

2. **web.py**
   - Line 29: Fixed page title
   - Lines ~2665-2680: Enhanced `/api/state` endpoint to return metadata
   - Lines ~2732-2829: Completely rewrote `/api/state/update_kb` to integrate with Open WebUI API
   - Lines ~3055-3140: Fixed `/api/status` statistics calculation to use source tracking

### New State File Format

Files in the state file now include:
```json
{
  "files": {
    "ssh:hostname/path/to/file.txt": {
      "hash": "md5hash",
      "status": "uploaded",
      "file_id": "file_id_from_openwebui",
      "last_attempt": "2025-11-09T10:30:00",
      "retry_count": 0,
      "knowledge_base": "KB Name",
      "source_type": "ssh",
      "source_name": "My SSH Server",
      "file_size": 12345,
      "created_at": "2025-11-09T08:00:00",
      "modified_at": "2025-11-09T09:30:00",
      "filename": "file.txt"
    }
  }
}
```

### Migration Notes

**Backward Compatibility**: The changes are backward compatible with existing state files. Old entries without the new fields will still work, but won't show source information or accurate dates until the next sync.

**No Data Loss**: Existing files in state will be updated with new metadata on the next sync run.
