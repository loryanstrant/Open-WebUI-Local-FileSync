#!/usr/bin/env python3
"""
Sync local files to Open WebUI Knowledge Base
"""
import os
import sys
import glob
import hashlib
import json
import requests
import time
from pathlib import Path
from datetime import datetime

# Configuration from environment variables
OPENWEBUI_URL = os.getenv('OPENWEBUI_URL', 'http://localhost:8080')
OPENWEBUI_API_KEY = os.getenv('OPENWEBUI_API_KEY', '')
FILES_DIR = os.getenv('FILES_DIR', '/data')
ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', '.md,.txt,.pdf,.doc,.docx').split(',')
STATE_FILE = os.getenv('STATE_FILE', '/app/sync_state.json')

# Knowledge base mapping: format "path1:kb_name1,path2:kb_name2"
KNOWLEDGE_BASE_MAPPING = os.getenv('KNOWLEDGE_BASE_MAPPING', '')

# Retry configuration
MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '60'))  # seconds
UPLOAD_TIMEOUT = int(os.getenv('UPLOAD_TIMEOUT', '300'))  # seconds to wait for processing

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def parse_knowledge_base_mapping():
    """Parse knowledge base mapping from environment variable
    
    Format: "path1:kb_name1,path2:kb_name2"
    Returns dict: {Path('path1'): 'kb_name1', Path('path2'): 'kb_name2'}
    """
    mapping = {}
    if not KNOWLEDGE_BASE_MAPPING:
        return mapping
    
    try:
        for entry in KNOWLEDGE_BASE_MAPPING.split(','):
            entry = entry.strip()
            if ':' in entry:
                path, kb_name = entry.split(':', 1)
                path = path.strip()
                kb_name = kb_name.strip()
                if path and kb_name:
                    # Convert to absolute path if relative
                    abs_path = Path(FILES_DIR) / path if not Path(path).is_absolute() else Path(path)
                    mapping[abs_path] = kb_name
    except Exception as e:
        log(f"Error parsing KNOWLEDGE_BASE_MAPPING: {e}")
    
    return mapping

def get_knowledge_base_for_file(filepath, kb_mapping):
    """Determine which knowledge base a file belongs to based on mapping
    
    Args:
        filepath: Path object of the file
        kb_mapping: Dict mapping paths to knowledge base names
    
    Returns:
        Knowledge base name or None if no mapping found
    """
    if not kb_mapping:
        return None
    
    # Check if file is under any mapped path
    for mapped_path, kb_name in kb_mapping.items():
        try:
            # Check if filepath is relative to mapped_path
            filepath.relative_to(mapped_path)
            return kb_name
        except ValueError:
            # Not relative to this path, continue
            continue
    
    return None

def load_state():
    """Load previous sync state"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                
                # Check if this is the old format (flat dict with file_path: hash)
                # Old format: {"path/to/file.txt": "hash123", ...}
                # New format: {"files": {...}, "knowledge_bases": {...}}
                if 'files' not in state and 'knowledge_bases' not in state:
                    # Migrate old format to new format
                    log("Migrating old state format to new format...")
                    old_state = state.copy()
                    state = {
                        'files': {},
                        'knowledge_bases': {}
                    }
                    # Convert old entries to new format
                    for file_key, file_hash in old_state.items():
                        if isinstance(file_hash, str):  # Ensure it's a simple hash string
                            state['files'][file_key] = {
                                'hash': file_hash,
                                'status': 'uploaded',
                                'retry_count': 0
                            }
                    log(f"Migrated {len(state['files'])} file entries")
                
                # Ensure both keys exist
                if 'files' not in state:
                    state['files'] = {}
                if 'knowledge_bases' not in state:
                    state['knowledge_bases'] = {}
                
                return state
        except Exception as e:
            log(f"Error loading state file: {e}")
    
    return {
        'files': {},  # file_key -> {hash, status, last_attempt, retry_count, knowledge_base}
        'knowledge_bases': {}  # kb_name -> {id, created_at}
    }

def save_state(state):
    """Save sync state"""
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log(f"Error saving state file: {e}")

def get_file_hash(filepath):
    """Calculate MD5 hash of file"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        log(f"Error hashing file {filepath}: {e}")
        return None

def get_files_to_sync():
    """Get list of files to sync"""
    files = []
    files_dir = Path(FILES_DIR)
    
    if not files_dir.exists():
        log(f"Files directory does not exist: {FILES_DIR}")
        return files
    
    for ext in ALLOWED_EXTENSIONS:
        ext = ext.strip()
        pattern = f"**/*{ext}"
        for filepath in files_dir.glob(pattern):
            if filepath.is_file():
                files.append(filepath)
    
    return files

def create_or_get_knowledge_base(kb_name, state):
    """Create or get a knowledge base by name
    
    Args:
        kb_name: Name of the knowledge base
        state: Current state dict
    
    Returns:
        Knowledge base ID or None if failed
    """
    # Check if we already have this knowledge base in state
    if 'knowledge_bases' not in state:
        state['knowledge_bases'] = {}
    
    if kb_name in state['knowledge_bases']:
        kb_id = state['knowledge_bases'][kb_name].get('id')
        if kb_id:
            log(f"Using existing knowledge base: {kb_name} (ID: {kb_id})")
            return kb_id
    
    # Try to create or get the knowledge base
    url = f"{OPENWEBUI_URL.rstrip('/')}/api/v1/knowledge/"
    headers = {
        'Authorization': f'Bearer {OPENWEBUI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        # First try to list existing knowledge bases
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            kbs = response.json()
            # Look for existing knowledge base with this name
            if isinstance(kbs, list):
                for kb in kbs:
                    if kb.get('name') == kb_name:
                        kb_id = kb.get('id')
                        log(f"Found existing knowledge base: {kb_name} (ID: {kb_id})")
                        state['knowledge_bases'][kb_name] = {
                            'id': kb_id,
                            'created_at': datetime.now().isoformat()
                        }
                        return kb_id
        
        # If not found, try to create it
        data = {
            'name': kb_name,
            'description': f'Auto-created knowledge base for {kb_name}'
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code in [200, 201]:
            result = response.json()
            kb_id = result.get('id')
            log(f"Created new knowledge base: {kb_name} (ID: {kb_id})")
            state['knowledge_bases'][kb_name] = {
                'id': kb_id,
                'created_at': datetime.now().isoformat()
            }
            return kb_id
        else:
            log(f"Failed to create knowledge base {kb_name}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        log(f"Error creating/getting knowledge base {kb_name}: {e}")
        return None

def upload_file_to_openwebui(filepath, file_hash, kb_id=None):
    """Upload a file to Open WebUI Knowledge Base
    
    Args:
        filepath: Path to the file to upload
        file_hash: MD5 hash of the file
        kb_id: Optional knowledge base ID to associate file with
    
    Returns:
        Tuple of (success: bool, file_id: str or None)
    """
    url = f"{OPENWEBUI_URL.rstrip('/')}/api/v1/files/"
    
    headers = {
        'Authorization': f'Bearer {OPENWEBUI_API_KEY}'
    }
    
    try:
        with open(filepath, 'rb') as f:
            files = {
                'file': (filepath.name, f, 'application/octet-stream')
            }
            
            # Add knowledge base ID if provided
            data = {}
            if kb_id:
                data['knowledge_base_id'] = kb_id
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                file_id = result.get('id')
                log(f"✓ Uploaded: {filepath.name}" + (f" to KB ID: {kb_id}" if kb_id else ""))
                return True, file_id
            else:
                log(f"✗ Failed to upload {filepath.name}: {response.status_code} - {response.text}")
                return False, None
    except Exception as e:
        log(f"✗ Error uploading {filepath.name}: {e}")
        return False, None

def check_upload_status(file_id):
    """Check if an uploaded file has been processed successfully
    
    Args:
        file_id: ID of the uploaded file
    
    Returns:
        Status string: 'processed', 'processing', 'failed', or 'unknown'
    """
    if not file_id:
        return 'unknown'
    
    url = f"{OPENWEBUI_URL.rstrip('/')}/api/v1/files/{file_id}"
    headers = {
        'Authorization': f'Bearer {OPENWEBUI_API_KEY}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status', 'unknown')
            # Map possible status values
            if status in ['completed', 'processed', 'ready']:
                return 'processed'
            elif status in ['processing', 'pending', 'uploading']:
                return 'processing'
            elif status in ['failed', 'error']:
                return 'failed'
            else:
                return 'unknown'
        else:
            log(f"Could not check status for file ID {file_id}: {response.status_code}")
            return 'unknown'
    except Exception as e:
        log(f"Error checking upload status for file ID {file_id}: {e}")
        return 'unknown'

def wait_for_upload_processing(file_id, timeout=UPLOAD_TIMEOUT):
    """Wait for an uploaded file to be processed
    
    Args:
        file_id: ID of the uploaded file
        timeout: Maximum time to wait in seconds
    
    Returns:
        True if processed successfully, False otherwise
    """
    if not file_id:
        return False
    
    start_time = time.time()
    check_interval = 5  # Check every 5 seconds
    
    while time.time() - start_time < timeout:
        status = check_upload_status(file_id)
        
        if status == 'processed':
            return True
        elif status == 'failed':
            log(f"File processing failed for ID: {file_id}")
            return False
        elif status == 'processing':
            time.sleep(check_interval)
        else:
            # Unknown status, assume it's done
            return True
    
    log(f"Timeout waiting for file processing (ID: {file_id})")
    return False

def sync_files():
    """Main sync function"""
    log("Starting file sync...")
    
    if not OPENWEBUI_API_KEY:
        log("ERROR: OPENWEBUI_API_KEY not set")
        sys.exit(1)
    
    state = load_state()
    
    # Ensure state structure exists
    if 'files' not in state:
        state['files'] = {}
    if 'knowledge_bases' not in state:
        state['knowledge_bases'] = {}
    
    # Parse knowledge base mapping
    kb_mapping = parse_knowledge_base_mapping()
    if kb_mapping:
        log(f"Knowledge base mapping configured: {len(kb_mapping)} paths")
    
    files = get_files_to_sync()
    log(f"Found {len(files)} files to check")
    
    uploaded = 0
    skipped = 0
    failed = 0
    retried = 0
    
    for filepath in files:
        file_key = str(filepath.relative_to(FILES_DIR))
        file_hash = get_file_hash(filepath)
        
        if file_hash is None:
            failed += 1
            continue
        
        # Get file state
        file_state = state['files'].get(file_key, {})
        
        # Check if file has changed
        if file_state.get('hash') == file_hash and file_state.get('status') == 'uploaded':
            skipped += 1
            continue
        
        # Check if we need to retry a failed upload
        if file_state.get('status') == 'failed':
            retry_count = file_state.get('retry_count', 0)
            last_attempt = file_state.get('last_attempt')
            
            if retry_count >= MAX_RETRY_ATTEMPTS:
                log(f"⊘ Max retries reached for {filepath.name}, skipping")
                skipped += 1
                continue
            
            # Check if enough time has passed since last attempt
            if last_attempt:
                try:
                    last_time = datetime.fromisoformat(last_attempt)
                    elapsed = (datetime.now() - last_time).total_seconds()
                    if elapsed < RETRY_DELAY:
                        log(f"⏳ Too soon to retry {filepath.name}, waiting {int(RETRY_DELAY - elapsed)}s more")
                        skipped += 1
                        continue
                except Exception:
                    pass  # If we can't parse time, just proceed with retry
            
            retried += 1
            log(f"Retrying upload ({retry_count + 1}/{MAX_RETRY_ATTEMPTS}): {filepath.name}")
        
        # Determine knowledge base for this file
        kb_name = get_knowledge_base_for_file(filepath, kb_mapping)
        kb_id = None
        
        if kb_name:
            kb_id = create_or_get_knowledge_base(kb_name, state)
            if not kb_id:
                log(f"✗ Could not create/get knowledge base {kb_name} for {filepath.name}")
                # Update state to track failure
                state['files'][file_key] = {
                    'hash': file_hash,
                    'status': 'failed',
                    'last_attempt': datetime.now().isoformat(),
                    'retry_count': file_state.get('retry_count', 0) + 1,
                    'knowledge_base': kb_name,
                    'error': 'Failed to create/get knowledge base'
                }
                failed += 1
                continue
        
        # Upload file
        success, file_id = upload_file_to_openwebui(filepath, file_hash, kb_id)
        
        if success:
            # Wait for processing if we got a file ID
            if file_id:
                log(f"⏳ Waiting for {filepath.name} to be processed...")
                processing_success = wait_for_upload_processing(file_id)
                
                if processing_success:
                    state['files'][file_key] = {
                        'hash': file_hash,
                        'status': 'uploaded',
                        'file_id': file_id,
                        'last_attempt': datetime.now().isoformat(),
                        'retry_count': 0,
                        'knowledge_base': kb_name
                    }
                    uploaded += 1
                else:
                    # Processing failed
                    state['files'][file_key] = {
                        'hash': file_hash,
                        'status': 'failed',
                        'file_id': file_id,
                        'last_attempt': datetime.now().isoformat(),
                        'retry_count': file_state.get('retry_count', 0) + 1,
                        'knowledge_base': kb_name,
                        'error': 'Processing failed'
                    }
                    failed += 1
            else:
                # No file ID returned, assume success
                state['files'][file_key] = {
                    'hash': file_hash,
                    'status': 'uploaded',
                    'last_attempt': datetime.now().isoformat(),
                    'retry_count': 0,
                    'knowledge_base': kb_name
                }
                uploaded += 1
        else:
            # Upload failed
            state['files'][file_key] = {
                'hash': file_hash,
                'status': 'failed',
                'last_attempt': datetime.now().isoformat(),
                'retry_count': file_state.get('retry_count', 0) + 1,
                'knowledge_base': kb_name,
                'error': 'Upload failed'
            }
            failed += 1
    
    # Save updated state
    save_state(state)
    
    log(f"Sync complete: {uploaded} uploaded, {skipped} skipped, {failed} failed, {retried} retried")

if __name__ == '__main__':
    sync_files()
