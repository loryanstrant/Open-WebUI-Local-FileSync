# Sync Flow Diagram

This document illustrates the enhanced sync flow with knowledge base mapping and retry logic.

## High-Level Architecture

```
┌─────────────────┐
│  Docker Host    │
│                 │
│  ┌───────────┐  │      ┌──────────────────┐
│  │ Files Dir │  │      │   Open WebUI     │
│  │           │  │      │                  │
│  │ /docs ────┼──┼──────▶ Documentation KB │
│  │ /api ─────┼──┼──────▶ API Reference KB │
│  │ /guides ──┼──┼──────▶ User Guides KB   │
│  └───────────┘  │      └──────────────────┘
│                 │
│  ┌───────────┐  │
│  │State File │  │
│  │ (JSON)    │  │
│  └───────────┘  │
└─────────────────┘
```

## Detailed Sync Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        SYNC PROCESS                              │
└─────────────────────────────────────────────────────────────────┘

1. INITIALIZATION
   ├─ Load environment configuration
   ├─ Parse KNOWLEDGE_BASE_MAPPING
   ├─ Load state from JSON file
   └─ Migrate old state format if needed

2. FILE DISCOVERY
   ├─ Scan FILES_DIR for files
   ├─ Filter by ALLOWED_EXTENSIONS
   └─ Build list of files to check

3. FOR EACH FILE:
   │
   ├─ Calculate MD5 hash
   │
   ├─ Check state:
   │  ├─ Is hash unchanged AND status = 'uploaded'?
   │  │  └─ SKIP (already synced)
   │  │
   │  ├─ Is status = 'failed' AND retry_count >= MAX_RETRY_ATTEMPTS?
   │  │  └─ SKIP (max retries reached)
   │  │
   │  ├─ Is status = 'failed' AND retry_count < MAX_RETRY_ATTEMPTS?
   │  │  ├─ Has RETRY_DELAY elapsed since last_attempt?
   │  │  │  ├─ YES → Continue to upload
   │  │  │  └─ NO → SKIP (too soon to retry)
   │  │  └─ Continue to upload
   │  │
   │  └─ New file or hash changed
   │     └─ Continue to upload
   │
   ├─ UPLOAD PROCESS:
   │  │
   │  ├─ Determine knowledge base from path
   │  │  ├─ Match file path against KNOWLEDGE_BASE_MAPPING
   │  │  └─ Get or create knowledge base via API
   │  │
   │  ├─ Upload file to Open WebUI
   │  │  ├─ POST /api/v1/files/
   │  │  ├─ Include knowledge_base_id if applicable
   │  │  └─ Receive file_id in response
   │  │
   │  ├─ PROCESSING VERIFICATION:
   │  │  ├─ Loop for up to UPLOAD_TIMEOUT seconds:
   │  │  │  ├─ GET /api/v1/files/{file_id}
   │  │  │  ├─ Check status:
   │  │  │  │  ├─ 'processed' → SUCCESS
   │  │  │  │  ├─ 'failed' → FAILURE
   │  │  │  │  ├─ 'processing' → Wait 5s and retry
   │  │  │  │  └─ 'unknown' → Assume success
   │  │  │  └─ Timeout reached → FAILURE
   │  │  └─ Return success/failure
   │  │
   │  ├─ ADD TO KNOWLEDGE BASE (if kb_id present):
   │  │  ├─ POST /api/v1/knowledge/{kb_id}/file/add
   │  │  ├─ Body: {file_id: <file_id>}
   │  │  ├─ If SUCCESS → Continue
   │  │  └─ If FAILURE → Mark as failed, will retry
   │  │
   │  └─ UPDATE STATE:
   │     ├─ If SUCCESS:
   │     │  ├─ status = 'uploaded'
   │     │  ├─ retry_count = 0
   │     │  ├─ Store file_id
   │     │  ├─ Store knowledge_base name
   │     │  └─ Store last_attempt timestamp
   │     │
   │     └─ If FAILURE:
   │        ├─ status = 'failed'
   │        ├─ retry_count += 1
   │        ├─ Store error message
   │        ├─ Store last_attempt timestamp
   │        └─ Will retry on next sync (if under max attempts)
   │
   └─ Continue to next file

4. FINALIZATION
   ├─ Save updated state to JSON file
   └─ Log summary (uploaded, skipped, failed, retried)
```

## State Transitions

```
┌──────────┐
│   NEW    │  First time seeing this file
│   FILE   │
└────┬─────┘
     │
     ▼
┌──────────────┐     Upload      ┌────────────┐
│   PENDING    │ ──────────────▶ │ PROCESSING │
│              │                 │            │
└──────────────┘                 └─────┬──────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
            ┌───────────┐      ┌──────────┐      ┌──────────┐
            │ UPLOADED  │      │  FAILED  │      │ TIMEOUT  │
            │ (success) │      │(retry<3) │      │(retry<3) │
            └───────────┘      └────┬─────┘      └────┬─────┘
                                    │                  │
                                    ▼                  ▼
                            ┌────────────────────────────┐
                            │  Wait RETRY_DELAY seconds  │
                            └──────────┬─────────────────┘
                                       │
                            retry_count < MAX_RETRY_ATTEMPTS?
                                       │
                        ┌──────────────┼──────────────┐
                        │              │              │
                       YES             NO             │
                        │              │              │
                        ▼              ▼              │
                ┌────────────┐  ┌──────────┐         │
                │   RETRY    │  │ SKIPPED  │         │
                │ (re-upload)│  │(maxed out)│        │
                └────────────┘  └──────────┘         │
                        │                            │
                        └────────────────────────────┘
```

## Knowledge Base Resolution

```
File Path: /data/docs/api/authentication.md

Step 1: Parse KNOWLEDGE_BASE_MAPPING
        "docs:Documentation,api:API_Reference"
        
        Mappings:
        - /data/docs → Documentation
        - /data/api  → API_Reference

Step 2: Find Best Match
        File: /data/docs/api/authentication.md
        
        Check /data/docs: ✓ Match
        Check /data/api:  ✗ No match (not relative to this path)
        
        Result: Documentation

Step 3: Get or Create KB
        ├─ Check state.knowledge_bases['Documentation']
        ├─ If not found:
        │  ├─ GET /api/v1/knowledge/
        │  ├─ Search for existing 'Documentation' KB
        │  └─ If not found, POST /api/v1/knowledge/
        └─ Store KB ID in state

Step 4: Upload File
        POST /api/v1/files/
        Body: {file: <binary>, knowledge_base_id: "kb-123"}

Step 5: Add File to Knowledge Base Collection
        POST /api/v1/knowledge/{kb_id}/file/add
        Body: {file_id: "file-uuid"}
```

## Error Handling

```
Upload Error Types:

1. Network Error
   ├─ Connection refused
   ├─ Timeout
   └─ DNS resolution failure
   
   Action: Mark as 'failed', will retry

2. HTTP Error
   ├─ 400 Bad Request → Mark as 'failed', will retry
   ├─ 401 Unauthorized → Log error, mark as 'failed', will retry
   ├─ 404 Not Found → Mark as 'failed', will retry
   ├─ 500 Server Error → Mark as 'failed', will retry
   └─ Other → Mark as 'failed', will retry

3. Processing Error
   ├─ File rejected by Open WebUI
   ├─ Unsupported format
   └─ Processing timeout
   
   Action: Mark as 'failed', will retry

4. Knowledge Base Error
   ├─ Cannot create KB
   └─ Cannot find KB
   
   Action: Mark as 'failed', log error, will retry
```

## Example Timeline

```
Time    Event
-----   -----
00:00   Sync starts
00:00   Load state (50 files previously synced)
00:00   Scan /data directory (52 files found)
00:01   File 1: readme.md → Already uploaded, skip
00:01   File 2: new-doc.md → New file, upload to 'Documentation' KB
00:02   File 3: failed-file.md → Previously failed (retry 1/3), upload
00:03   File 4: old-failed.md → Max retries reached, skip
        ...
00:30   All files processed
00:30   Save state
00:30   Log: 2 uploaded, 48 skipped, 1 failed, 1 retried
```

## Configuration Impact

### Without Knowledge Base Mapping
- Files uploaded to default Open WebUI location
- No KB organization
- Still benefits from retry logic

### With Knowledge Base Mapping
- Files automatically organized by directory
- Knowledge bases created if needed
- Better organization in Open WebUI

### Retry Configuration Impact

| Setting | Low (1 attempt, 30s delay) | Default (3 attempts, 60s delay) | High (5 attempts, 120s delay) |
|---------|---------------------------|----------------------------------|-------------------------------|
| Transient errors | May fail | Usually succeeds | Very likely to succeed |
| Network issues | Likely fails | Usually succeeds | Very likely to succeed |
| Sync duration | Fastest | Moderate | Slowest |
| Resource usage | Lowest | Moderate | Higher |
| Best for | Stable networks | General use | Unreliable networks |
```
