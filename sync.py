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
from pathlib import Path
from datetime import datetime

# Configuration from environment variables
OPENWEBUI_URL = os.getenv('OPENWEBUI_URL', 'http://localhost:8080')
OPENWEBUI_API_KEY = os.getenv('OPENWEBUI_API_KEY', '')
FILES_DIR = os.getenv('FILES_DIR', '/data')
ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', '.md,.txt,.pdf,.doc,.docx').split(',')
STATE_FILE = os.getenv('STATE_FILE', '/app/sync_state.json')

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def load_state():
    """Load previous sync state"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            log(f"Error loading state file: {e}")
    return {}

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

def upload_file_to_openwebui(filepath, file_hash):
    """Upload a file to Open WebUI Knowledge Base"""
    url = f"{OPENWEBUI_URL.rstrip('/')}/api/v1/files/"
    
    headers = {
        'Authorization': f'Bearer {OPENWEBUI_API_KEY}'
    }
    
    try:
        with open(filepath, 'rb') as f:
            files = {
                'file': (filepath.name, f, 'application/octet-stream')
            }
            
            response = requests.post(url, headers=headers, files=files, timeout=30)
            
            if response.status_code in [200, 201]:
                log(f"✓ Uploaded: {filepath.name}")
                return True
            else:
                log(f"✗ Failed to upload {filepath.name}: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        log(f"✗ Error uploading {filepath.name}: {e}")
        return False

def sync_files():
    """Main sync function"""
    log("Starting file sync...")
    
    if not OPENWEBUI_API_KEY:
        log("ERROR: OPENWEBUI_API_KEY not set")
        sys.exit(1)
    
    state = load_state()
    files = get_files_to_sync()
    
    log(f"Found {len(files)} files to check")
    
    uploaded = 0
    skipped = 0
    failed = 0
    
    for filepath in files:
        file_key = str(filepath.relative_to(FILES_DIR))
        file_hash = get_file_hash(filepath)
        
        if file_hash is None:
            failed += 1
            continue
        
        # Check if file has changed
        if file_key in state and state[file_key] == file_hash:
            skipped += 1
            continue
        
        # Upload file
        if upload_file_to_openwebui(filepath, file_hash):
            state[file_key] = file_hash
            uploaded += 1
        else:
            failed += 1
    
    # Save updated state
    save_state(state)
    
    log(f"Sync complete: {uploaded} uploaded, {skipped} skipped, {failed} failed")

if __name__ == '__main__':
    sync_files()
