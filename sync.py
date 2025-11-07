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
import re
import tempfile
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None

try:
    import paramiko
except ImportError:
    paramiko = None

# Configuration from environment variables
OPENWEBUI_URL = os.getenv('OPENWEBUI_URL', 'http://localhost:8080')
OPENWEBUI_API_KEY = os.getenv('OPENWEBUI_API_KEY', '')
FILES_DIR = os.getenv('FILES_DIR', '/data')
ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', '.md,.txt,.pdf,.doc,.docx,.json,.yaml,.yml').split(',')
STATE_FILE = os.getenv('STATE_FILE', '/app/sync_state.json')

# Knowledge base mapping: format "path1:kb_name1,path2:kb_name2"
KNOWLEDGE_BASE_MAPPING = os.getenv('KNOWLEDGE_BASE_MAPPING', '')
# Single knowledge base name (all files go to this KB)
KNOWLEDGE_BASE_NAME = os.getenv('KNOWLEDGE_BASE_NAME', '')
# JSON array format: [{"path": "path1", "kb": "kb_name1"}, ...]
KNOWLEDGE_BASE_MAPPINGS = os.getenv('KNOWLEDGE_BASE_MAPPINGS', '')

# Retry configuration
MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '60'))  # seconds
UPLOAD_TIMEOUT = int(os.getenv('UPLOAD_TIMEOUT', '300'))  # seconds to wait for processing

# SSH Remote Sources Configuration
# JSON array format: [{"host": "hostname", "port": 22, "username": "user", "password": "pass", "paths": ["/path1", "/path2"], "kb": "KB_Name"}, ...]
SSH_REMOTE_SOURCES = os.getenv('SSH_REMOTE_SOURCES', '')
SSH_KEY_PATH = os.getenv('SSH_KEY_PATH', '/app/ssh_keys')

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def parse_ssh_remote_sources():
    """Parse SSH remote sources from environment variable
    
    Returns:
        List of dicts with SSH connection details:
        [
            {
                "host": "hostname or IP",
                "port": 22,
                "username": "user",
                "password": "password" (optional),
                "key_filename": "path/to/key" (optional),
                "paths": ["/remote/path1", "/remote/path2"],
                "kb": "Knowledge_Base_Name" (optional)
            },
            ...
        ]
    """
    if not SSH_REMOTE_SOURCES:
        return []
    
    try:
        sources = json.loads(SSH_REMOTE_SOURCES)
        if not isinstance(sources, list):
            log("WARNING: SSH_REMOTE_SOURCES must be a JSON array")
            return []
        
        # Validate and normalize each source
        validated_sources = []
        for i, source in enumerate(sources):
            if not isinstance(source, dict):
                log(f"WARNING: SSH source {i} is not a valid object, skipping")
                continue
            
            if 'host' not in source or 'username' not in source or 'paths' not in source:
                log(f"WARNING: SSH source {i} missing required fields (host, username, paths), skipping")
                continue
            
            # Set defaults
            source.setdefault('port', 22)
            
            # Ensure paths is a list
            if isinstance(source['paths'], str):
                source['paths'] = [source['paths']]
            elif not isinstance(source['paths'], list):
                log(f"WARNING: SSH source {i} has invalid 'paths' format, skipping")
                continue
            
            # Check authentication method
            has_password = 'password' in source and source['password']
            has_key = 'key_filename' in source and source['key_filename']
            
            if not has_password and not has_key:
                log(f"WARNING: SSH source {i} has no authentication method (password or key_filename), skipping")
                continue
            
            # Resolve key_filename path if relative
            if has_key:
                key_path = source['key_filename']
                if not os.path.isabs(key_path):
                    # If relative, assume it's in SSH_KEY_PATH directory
                    source['key_filename'] = os.path.join(SSH_KEY_PATH, key_path)
            
            validated_sources.append(source)
        
        return validated_sources
    
    except json.JSONDecodeError as e:
        log(f"ERROR: Failed to parse SSH_REMOTE_SOURCES JSON: {e}")
        return []
    except Exception as e:
        log(f"ERROR: Failed to process SSH_REMOTE_SOURCES: {e}")
        return []

def fetch_files_from_ssh(ssh_source, temp_dir):
    """Fetch files from a remote SSH server
    
    Args:
        ssh_source: Dict with SSH connection details (host, port, username, password/key_filename, paths, kb)
        temp_dir: Path object pointing to temporary directory for downloaded files
    
    Returns:
        Tuple of (success: bool, downloaded_files: list of Path objects, kb_name: str or None)
    """
    if paramiko is None:
        log("ERROR: paramiko library not installed, cannot fetch files via SSH")
        return False, [], None
    
    host = ssh_source['host']
    port = ssh_source.get('port', 22)
    username = ssh_source['username']
    password = ssh_source.get('password')
    key_filename = ssh_source.get('key_filename')
    remote_paths = ssh_source['paths']
    kb_name = ssh_source.get('kb')
    
    log(f"Connecting to SSH server: {username}@{host}:{port}")
    
    ssh_client = None
    sftp_client = None
    downloaded_files = []
    
    try:
        # Create SSH client
        ssh_client = paramiko.SSHClient()
        
        # Try to load known_hosts file if it exists
        known_hosts_path = os.path.join(SSH_KEY_PATH, 'known_hosts')
        if os.path.exists(known_hosts_path):
            log(f"Loading known_hosts from: {known_hosts_path}")
            ssh_client.load_host_keys(known_hosts_path)
            ssh_client.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            # WARNING: AutoAddPolicy accepts any host key without verification
            # This is a security risk but often necessary for automation
            log(f"⚠ WARNING: No known_hosts file found at {known_hosts_path}")
            log(f"⚠ WARNING: Using AutoAddPolicy - host keys will not be verified")
            log(f"⚠ For better security, mount a known_hosts file to {known_hosts_path}")
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect with appropriate authentication method
        connect_kwargs = {
            'hostname': host,
            'port': port,
            'username': username,
            'timeout': 30
        }
        
        if key_filename:
            # Key-based authentication
            if not os.path.exists(key_filename):
                log(f"ERROR: SSH key file not found: {key_filename}")
                return False, [], kb_name
            
            log(f"Using SSH key authentication: {key_filename}")
            connect_kwargs['key_filename'] = key_filename
            
            # If a passphrase is provided in the password field, use it
            if password:
                connect_kwargs['passphrase'] = password
        else:
            # Password authentication
            log("Using password authentication")
            connect_kwargs['password'] = password
        
        ssh_client.connect(**connect_kwargs)
        log(f"✓ Connected to {host}")
        
        # Open SFTP session
        sftp_client = ssh_client.open_sftp()
        
        # Process each remote path
        for remote_path in remote_paths:
            log(f"Fetching files from remote path: {remote_path}")
            
            try:
                # Check if remote_path is a file or directory
                remote_stat = sftp_client.stat(remote_path)
                
                # Import stat module for file type checking
                import stat as stat_module
                
                if stat_module.S_ISREG(remote_stat.st_mode):
                    # It's a file - download it directly
                    downloaded = _download_ssh_file(sftp_client, remote_path, temp_dir, host)
                    if downloaded:
                        downloaded_files.extend(downloaded)
                elif stat_module.S_ISDIR(remote_stat.st_mode):
                    # It's a directory - recursively download files
                    downloaded = _download_ssh_directory(sftp_client, remote_path, temp_dir, host)
                    if downloaded:
                        downloaded_files.extend(downloaded)
                else:
                    log(f"⚠ Remote path is neither file nor directory: {remote_path}")
            
            except FileNotFoundError:
                log(f"✗ Remote path not found: {remote_path}")
            except Exception as e:
                log(f"✗ Error processing remote path {remote_path}: {e}")
        
        log(f"✓ Downloaded {len(downloaded_files)} files from {host}")
        return True, downloaded_files, kb_name
    
    except paramiko.AuthenticationException:
        log(f"✗ SSH authentication failed for {username}@{host}")
        return False, [], kb_name
    except paramiko.SSHException as e:
        log(f"✗ SSH connection error to {host}: {e}")
        return False, [], kb_name
    except Exception as e:
        log(f"✗ Error fetching files from {host}: {e}")
        return False, [], kb_name
    finally:
        # Clean up connections
        if sftp_client:
            try:
                sftp_client.close()
            except:
                pass
        if ssh_client:
            try:
                ssh_client.close()
            except:
                pass

def _download_ssh_file(sftp_client, remote_filepath, local_dir, host):
    """Download a single file from SSH server
    
    Args:
        sftp_client: Active SFTP client
        remote_filepath: Path to remote file
        local_dir: Path object for local directory
        host: Hostname for logging
    
    Returns:
        List containing Path object of downloaded file, or empty list if failed
    """
    try:
        # Get file extension
        file_ext = os.path.splitext(remote_filepath)[1].lower()
        
        # Check if extension is allowed
        if file_ext not in ALLOWED_EXTENSIONS:
            return []
        
        # Create local filename (preserve filename, create subdirs if needed)
        filename = os.path.basename(remote_filepath)
        local_filepath = local_dir / filename
        
        # Ensure local directory exists
        local_filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Download file
        sftp_client.get(remote_filepath, str(local_filepath))
        log(f"  ↓ Downloaded: {filename}")
        
        return [local_filepath]
    
    except Exception as e:
        log(f"  ✗ Failed to download {remote_filepath}: {e}")
        return []

def _download_ssh_directory(sftp_client, remote_dirpath, local_dir, host, _depth=0):
    """Recursively download files from SSH directory
    
    Args:
        sftp_client: Active SFTP client
        remote_dirpath: Path to remote directory
        local_dir: Path object for local directory
        host: Hostname for logging
        _depth: Recursion depth (internal use)
    
    Returns:
        List of Path objects of downloaded files
    """
    # Prevent excessive recursion
    if _depth > 10:
        log(f"  ⚠ Maximum recursion depth reached for {remote_dirpath}")
        return []
    
    downloaded_files = []
    
    try:
        # List directory contents
        for entry in sftp_client.listdir_attr(remote_dirpath):
            # Import stat module for file type checking
            import stat as stat_module
            
            remote_path = os.path.join(remote_dirpath, entry.filename).replace('\\', '/')
            
            if stat_module.S_ISREG(entry.st_mode):
                # It's a file - download it
                files = _download_ssh_file(sftp_client, remote_path, local_dir, host)
                downloaded_files.extend(files)
            elif stat_module.S_ISDIR(entry.st_mode):
                # It's a subdirectory - recurse into it
                subdir_files = _download_ssh_directory(sftp_client, remote_path, local_dir, host, _depth + 1)
                downloaded_files.extend(subdir_files)
    
    except Exception as e:
        log(f"  ✗ Error listing directory {remote_dirpath}: {e}")
    
    return downloaded_files

def convert_json_to_markdown(json_data, filename):
    """Convert JSON data to formatted Markdown
    
    Args:
        json_data: Parsed JSON object
        filename: Original filename for title
    
    Returns:
        Markdown formatted string
    """
    lines = [f"# {filename}\n"]
    
    def format_value(value, indent=0):
        """Recursively format JSON values to Markdown"""
        prefix = "  " * indent
        result = []
        
        if isinstance(value, dict):
            for key, val in value.items():
                if isinstance(val, (dict, list)):
                    result.append(f"{prefix}- **{key}:**")
                    result.extend(format_value(val, indent + 1))
                else:
                    result.append(f"{prefix}- **{key}:** {val}")
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, (dict, list)):
                    result.append(f"{prefix}- Item {i + 1}:")
                    result.extend(format_value(item, indent + 1))
                else:
                    result.append(f"{prefix}- {item}")
        else:
            result.append(f"{prefix}{value}")
        
        return result
    
    lines.extend(format_value(json_data))
    return "\n".join(lines)

def convert_yaml_to_markdown(yaml_data, filename):
    """Convert YAML data to formatted Markdown
    
    Args:
        yaml_data: Parsed YAML object
        filename: Original filename for title
    
    Returns:
        Markdown formatted string
    """
    # YAML and JSON have similar structures, reuse the JSON converter
    return convert_json_to_markdown(yaml_data, filename)

def should_process_file(filepath, filters, mapped_path=None):
    """Check if a file should be processed based on include/exclude filters
    
    Args:
        filepath: Path object of the file to check
        filters: Dict with 'exclude' and 'include' pattern lists
        mapped_path: Path object of the mapped knowledge base path (for relative pattern matching)
    
    Returns:
        True if file should be processed, False if it should be skipped
    """
    if not filters:
        return True
    
    # Get relative path for pattern matching
    # If mapped_path is provided, get path relative to that; otherwise use FILES_DIR
    if mapped_path:
        try:
            rel_path = str(filepath.relative_to(mapped_path))
        except ValueError:
            # Fallback to FILES_DIR
            try:
                rel_path = str(filepath.relative_to(FILES_DIR))
            except ValueError:
                rel_path = str(filepath)
    else:
        try:
            rel_path = str(filepath.relative_to(FILES_DIR))
        except ValueError:
            rel_path = str(filepath)
    
    # Check exclude patterns first
    exclude_patterns = filters.get('exclude', [])
    for pattern in exclude_patterns:
        # Support glob patterns and substring matching
        if '*' in pattern or '?' in pattern:
            # Glob pattern - use relative path for matching
            if Path(rel_path).match(pattern):
                # Check if any include pattern overrides this exclusion
                include_patterns = filters.get('include', [])
                for inc_pattern in include_patterns:
                    if '*' in inc_pattern or '?' in inc_pattern:
                        if Path(rel_path).match(inc_pattern):
                            return True
                    else:
                        # Substring match for include
                        if inc_pattern in rel_path or inc_pattern in filepath.name:
                            return True
                return False
        else:
            # Substring match for exclude
            if pattern in rel_path or pattern in filepath.name:
                # Check if any include pattern overrides
                include_patterns = filters.get('include', [])
                for inc_pattern in include_patterns:
                    if '*' in inc_pattern or '?' in inc_pattern:
                        if Path(rel_path).match(inc_pattern):
                            return True
                    else:
                        if inc_pattern in rel_path or inc_pattern in filepath.name:
                            return True
                return False
    
    # If no exclusions matched, file should be processed
    return True

def convert_file_to_markdown(filepath):
    """Convert JSON/YAML files to Markdown format
    
    Args:
        filepath: Path to the file
    
    Returns:
        Tuple of (success: bool, converted_filepath: Path or None, is_temp: bool)
        - success: Whether conversion was successful or not needed
        - converted_filepath: Path to the converted file (temp file) or original if no conversion
        - is_temp: True if a temporary file was created that needs cleanup
    """
    ext = filepath.suffix.lower()
    
    # Only convert JSON and YAML files
    if ext not in ['.json', '.yaml', '.yml']:
        return True, filepath, False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse based on extension
        if ext == '.json':
            try:
                data = json.loads(content)
                markdown_content = convert_json_to_markdown(data, filepath.name)
            except json.JSONDecodeError as e:
                log(f"⚠ Failed to parse JSON file {filepath.name}: {e}")
                return False, None, False
        elif ext in ['.yaml', '.yml']:
            if yaml is None:
                log(f"⚠ PyYAML not installed, cannot convert {filepath.name}")
                return True, filepath, False
            try:
                data = yaml.safe_load(content)
                markdown_content = convert_yaml_to_markdown(data, filepath.name)
            except yaml.YAMLError as e:
                log(f"⚠ Failed to parse YAML file {filepath.name}: {e}")
                return False, None, False
        
        # Create temporary markdown file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.md', prefix=f"{filepath.stem}_")
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
                temp_file.write(markdown_content)
            log(f"✓ Converted {filepath.name} to Markdown")
            return True, Path(temp_path), True
        except Exception as e:
            log(f"✗ Error writing converted file: {e}")
            os.close(temp_fd)
            try:
                os.unlink(temp_path)
            except:
                pass
            return False, None, False
            
    except Exception as e:
        log(f"✗ Error converting {filepath.name}: {e}")
        return False, None, False

def verify_state_file_access():
    """Verify that the state file directory exists and is writable
    
    Returns:
        True if state file can be created/accessed, False otherwise
    """
    state_dir = os.path.dirname(STATE_FILE)
    
    # Check if directory exists
    if not os.path.exists(state_dir):
        log(f"State directory does not exist: {state_dir}")
        log(f"Attempting to create directory: {state_dir}")
        try:
            os.makedirs(state_dir, exist_ok=True)
            log(f"✓ Created state directory: {state_dir}")
        except Exception as e:
            log(f"✗ ERROR: Cannot create state directory {state_dir}: {e}")
            log(f"  Please ensure the container has write permissions to this location")
            return False
    
    # Check if directory is writable
    if not os.access(state_dir, os.W_OK):
        log(f"✗ ERROR: State directory is not writable: {state_dir}")
        log(f"  Current permissions: {oct(os.stat(state_dir).st_mode)[-3:]}")
        log(f"  Please ensure the container has write permissions to this location")
        return False
    
    # Check if state file exists
    if not os.path.exists(STATE_FILE):
        log(f"State file does not exist: {STATE_FILE}")
        log(f"Attempting to create initial state file...")
        try:
            # Create initial empty state
            initial_state = {
                'files': {},
                'knowledge_bases': {}
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(initial_state, f, indent=2)
            log(f"✓ Created initial state file: {STATE_FILE}")
        except Exception as e:
            log(f"✗ ERROR: Cannot create state file {STATE_FILE}: {e}")
            log(f"  Please ensure the container has write permissions to this location")
            return False
    else:
        # State file exists, check if it's readable and writable
        if not os.access(STATE_FILE, os.R_OK):
            log(f"✗ ERROR: State file is not readable: {STATE_FILE}")
            log(f"  Current permissions: {oct(os.stat(STATE_FILE).st_mode)[-3:]}")
            log(f"  Please ensure the container has read permissions to this file")
            return False
        
        if not os.access(STATE_FILE, os.W_OK):
            log(f"✗ ERROR: State file is not writable: {STATE_FILE}")
            log(f"  Current permissions: {oct(os.stat(STATE_FILE).st_mode)[-3:]}")
            log(f"  Please ensure the container has write permissions to this file")
            return False
        
        log(f"✓ State file exists and is accessible: {STATE_FILE}")
    
    return True

def parse_knowledge_base_mapping():
    """Parse knowledge base mapping from environment variables
    
    Supports three formats:
    1. Single KB (KNOWLEDGE_BASE_NAME): All files go to one knowledge base
    2. JSON array (KNOWLEDGE_BASE_MAPPINGS): [{"path": "path1", "kb": "kb_name1", "exclude": [...], "include": [...]}, ...]
    3. Legacy (KNOWLEDGE_BASE_MAPPING): "path1:kb_name1,path2:kb_name2"
    
    Returns tuple: (mapping_dict, filters_dict)
    - mapping_dict: {Path('path1'): 'kb_name1', Path('path2'): 'kb_name2'}
    - filters_dict: {Path('path1'): {'exclude': [...], 'include': [...]}, ...}
    Returns (None, {}) if single KB mode (all files go to KNOWLEDGE_BASE_NAME)
    """
    # Priority 1: Single knowledge base - all files go to this KB
    if KNOWLEDGE_BASE_NAME:
        log(f"Using single knowledge base mode: {KNOWLEDGE_BASE_NAME}")
        return None, {}  # Special case: None means use single KB for all files
    
    mapping = {}
    filters = {}
    
    # Priority 2: JSON array format
    if KNOWLEDGE_BASE_MAPPINGS:
        try:
            mappings_data = json.loads(KNOWLEDGE_BASE_MAPPINGS)
            if isinstance(mappings_data, list):
                for entry in mappings_data:
                    if isinstance(entry, dict) and 'path' in entry and 'kb' in entry:
                        path = entry['path'].strip()
                        kb_name = entry['kb'].strip()
                        if path and kb_name:
                            # Convert to absolute path if relative
                            abs_path = Path(FILES_DIR) / path if not Path(path).is_absolute() else Path(path)
                            mapping[abs_path] = kb_name
                            
                            # Parse filters if present
                            path_filters = {}
                            if 'exclude' in entry and isinstance(entry['exclude'], list):
                                path_filters['exclude'] = entry['exclude']
                            if 'include' in entry and isinstance(entry['include'], list):
                                path_filters['include'] = entry['include']
                            
                            if path_filters:
                                filters[abs_path] = path_filters
                
                log(f"Loaded {len(mapping)} mappings from KNOWLEDGE_BASE_MAPPINGS JSON array")
                if filters:
                    log(f"Loaded filters for {len(filters)} paths")
                return mapping, filters
            else:
                log("WARNING: KNOWLEDGE_BASE_MAPPINGS must be a JSON array")
        except json.JSONDecodeError as e:
            log(f"Error parsing KNOWLEDGE_BASE_MAPPINGS JSON: {e}")
        except Exception as e:
            log(f"Error processing KNOWLEDGE_BASE_MAPPINGS: {e}")
    
    # Priority 3: Legacy comma-separated format
    if KNOWLEDGE_BASE_MAPPING:
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
            if mapping:
                log(f"Loaded {len(mapping)} mappings from KNOWLEDGE_BASE_MAPPING (legacy format)")
        except Exception as e:
            log(f"Error parsing KNOWLEDGE_BASE_MAPPING: {e}")
    
    return (mapping if mapping else {}, filters)

def get_knowledge_base_for_file(filepath, kb_mapping, kb_filters):
    """Determine which knowledge base a file belongs to based on mapping
    
    Args:
        filepath: Path object of the file
        kb_mapping: Dict mapping paths to knowledge base names, or None for single KB mode
        kb_filters: Dict mapping paths to filter configurations
    
    Returns:
        Tuple of (knowledge_base_name, filters_dict, mapped_path) or (None, None, None) if no mapping found
    """
    # Special case: single KB mode (all files go to KNOWLEDGE_BASE_NAME)
    if kb_mapping is None and KNOWLEDGE_BASE_NAME:
        return KNOWLEDGE_BASE_NAME, {}, None
    
    if not kb_mapping:
        return None, {}, None
    
    # Check if file is under any mapped path
    for mapped_path, kb_name in kb_mapping.items():
        try:
            # Check if filepath is relative to mapped_path
            filepath.relative_to(mapped_path)
            # Get filters for this path if they exist
            filters = kb_filters.get(mapped_path, {})
            return kb_name, filters, mapped_path
        except ValueError:
            # Not relative to this path, continue
            continue
    
    return None, {}, None

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

def add_file_to_knowledge_base(kb_id, file_id):
    """Add an uploaded file to a knowledge base collection
    
    Args:
        kb_id: Knowledge base ID
        file_id: ID of the uploaded file
    
    Returns:
        True if successfully added, False otherwise
    """
    if not kb_id or not file_id:
        return False
    
    url = f"{OPENWEBUI_URL.rstrip('/')}/api/v1/knowledge/{kb_id}/file/add"
    headers = {
        'Authorization': f'Bearer {OPENWEBUI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'file_id': file_id
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code in [200, 201]:
            log(f"✓ Added file {file_id} to knowledge base {kb_id}")
            return True
        else:
            log(f"✗ Failed to add file {file_id} to knowledge base {kb_id}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log(f"✗ Error adding file {file_id} to knowledge base {kb_id}: {e}")
        return False

def get_knowledge_base_files(kb_id):
    """Get list of files in a knowledge base
    
    Args:
        kb_id: Knowledge base ID
    
    Returns:
        List of file dicts with 'id', 'filename', 'hash' etc., or empty list if failed
    """
    if not kb_id:
        return []
    
    url = f"{OPENWEBUI_URL.rstrip('/')}/api/v1/knowledge/{kb_id}"
    headers = {
        'Authorization': f'Bearer {OPENWEBUI_API_KEY}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            # The knowledge base response may have a 'files' field with file details
            files = result.get('files', [])
            return files if isinstance(files, list) else []
        else:
            log(f"Could not get files for knowledge base {kb_id}: {response.status_code}")
            return []
    except Exception as e:
        log(f"Error getting files for knowledge base {kb_id}: {e}")
        return []

def backfill_state_from_knowledge_base(kb_name, kb_id, local_files, state):
    """Backfill sync state by checking which local files already exist in the knowledge base
    
    Args:
        kb_name: Name of the knowledge base
        kb_id: Knowledge base ID
        local_files: List of local file paths to check
        state: Current state dict
    
    Returns:
        Number of files backfilled
    """
    if not kb_id or not local_files:
        return 0
    
    log(f"Checking for existing files in knowledge base: {kb_name}")
    
    # Get existing files from knowledge base
    kb_files = get_knowledge_base_files(kb_id)
    if not kb_files:
        log(f"No existing files found in knowledge base {kb_name} or unable to retrieve")
        return 0
    
    # Create a mapping of filename to file info for quick lookup
    kb_files_map = {}
    for kb_file in kb_files:
        if isinstance(kb_file, dict):
            filename = kb_file.get('filename') or kb_file.get('name')
            if filename:
                kb_files_map[filename] = kb_file
    
    backfilled_count = 0
    
    for filepath in local_files:
        file_key = str(filepath.relative_to(FILES_DIR))
        
        # Skip if already in state
        if file_key in state['files']:
            file_state = state['files'][file_key]
            # Only skip if status is uploaded - if failed, we may want to retry
            if file_state.get('status') == 'uploaded':
                continue
        
        # Check if file exists in knowledge base by filename
        filename = filepath.name
        if filename in kb_files_map:
            kb_file = kb_files_map[filename]
            file_id = kb_file.get('id')
            
            # Only backfill if we have a valid file ID
            if not file_id:
                continue
            
            # Get local file hash to store in state
            file_hash = get_file_hash(filepath)
            if file_hash is None:
                continue
            
            # Backfill the state
            state['files'][file_key] = {
                'hash': file_hash,
                'status': 'uploaded',
                'file_id': file_id,
                'last_attempt': datetime.now().isoformat(),
                'retry_count': 0,
                'knowledge_base': kb_name
            }
            backfilled_count += 1
            log(f"↻ Backfilled state for existing file: {filename}")
    
    return backfilled_count

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
    
    # Verify state file access before proceeding
    if not verify_state_file_access():
        log("ERROR: Cannot access state file. Sync cannot proceed.")
        log(f"Please check that the volume mount for state directory is correct")
        log(f"Expected state file location: {STATE_FILE}")
        sys.exit(1)
    
    state = load_state()
    
    # Ensure state structure exists
    if 'files' not in state:
        state['files'] = {}
    if 'knowledge_bases' not in state:
        state['knowledge_bases'] = {}
    
    # Parse knowledge base mapping
    kb_mapping, kb_filters = parse_knowledge_base_mapping()
    if kb_mapping is None and KNOWLEDGE_BASE_NAME:
        log(f"Single knowledge base mode: all files will go to '{KNOWLEDGE_BASE_NAME}'")
    elif kb_mapping:
        log(f"Knowledge base mapping configured: {len(kb_mapping)} paths")
    
    # Fetch files from SSH remote sources if configured
    ssh_sources = parse_ssh_remote_sources()
    ssh_temp_dirs = []  # Keep track of temp directories to clean up later
    
    if ssh_sources:
        log(f"Found {len(ssh_sources)} SSH remote source(s) configured")
        
        for ssh_source in ssh_sources:
            host = ssh_source.get('host', 'unknown')
            log(f"Processing SSH source: {host}")
            
            # Create a temporary directory for this SSH source
            temp_dir = Path(tempfile.mkdtemp(prefix=f"ssh_{host}_", dir=FILES_DIR))
            ssh_temp_dirs.append(temp_dir)
            
            # Fetch files from SSH
            success, downloaded_files, ssh_kb_name = fetch_files_from_ssh(ssh_source, temp_dir)
            
            if success and downloaded_files:
                log(f"✓ Successfully fetched {len(downloaded_files)} files from {host}")
                
                # If this SSH source has a specific KB configured, create/update KB mapping
                if ssh_kb_name:
                    if kb_mapping is None:
                        # Create a new mapping dict if in single KB mode
                        kb_mapping = {}
                    # Map the temp directory to the SSH source's KB
                    kb_mapping[temp_dir] = ssh_kb_name
                    log(f"Mapped SSH files from {host} to knowledge base: {ssh_kb_name}")
            elif not success:
                log(f"✗ Failed to fetch files from {host}")
    
    files = get_files_to_sync()
    log(f"Found {len(files)} files to check")
    
    # Backfill state from existing knowledge base files
    # This handles the case where state was not persisted but files already exist
    backfilled_total = 0
    if kb_mapping is None and KNOWLEDGE_BASE_NAME:
        # Single KB mode - backfill from the single knowledge base
        kb_id = create_or_get_knowledge_base(KNOWLEDGE_BASE_NAME, state)
        if kb_id:
            backfilled_total = backfill_state_from_knowledge_base(KNOWLEDGE_BASE_NAME, kb_id, files, state)
    elif kb_mapping:
        # Multiple KB mode - backfill from each knowledge base
        kb_groups = {}
        for filepath in files:
            kb_name, file_filters, kb_mapped_path = get_knowledge_base_for_file(filepath, kb_mapping, kb_filters)
            if kb_name:
                if kb_name not in kb_groups:
                    kb_groups[kb_name] = []
                kb_groups[kb_name].append(filepath)
        
        for kb_name, kb_files in kb_groups.items():
            kb_id = create_or_get_knowledge_base(kb_name, state)
            if kb_id:
                backfilled_count = backfill_state_from_knowledge_base(kb_name, kb_id, kb_files, state)
                backfilled_total += backfilled_count
    
    if backfilled_total > 0:
        log(f"Backfilled state for {backfilled_total} existing files")
        # Save state after backfilling
        save_state(state)
    
    uploaded = 0
    skipped = 0
    failed = 0
    retried = 0
    filtered = 0
    converted = 0
    
    for filepath in files:
        file_key = str(filepath.relative_to(FILES_DIR))
        
        # Determine knowledge base and filters for this file
        kb_name, file_filters, kb_mapped_path = get_knowledge_base_for_file(filepath, kb_mapping, kb_filters)
        
        # Check if file should be processed based on filters
        if not should_process_file(filepath, file_filters, kb_mapped_path):
            log(f"⊗ Filtered: {filepath.name}")
            filtered += 1
            continue
        
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
        
        # Convert JSON/YAML to Markdown if needed
        conversion_success, upload_filepath, is_temp = convert_file_to_markdown(filepath)
        
        if not conversion_success:
            log(f"✗ Failed to convert {filepath.name}, skipping")
            state['files'][file_key] = {
                'hash': file_hash,
                'status': 'failed',
                'last_attempt': datetime.now().isoformat(),
                'retry_count': file_state.get('retry_count', 0) + 1,
                'knowledge_base': kb_name,
                'error': 'Conversion failed'
            }
            failed += 1
            continue
        
        if is_temp:
            converted += 1
        
        # Determine knowledge base for this file (kb_name already determined above)
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
                # Clean up temp file if created
                if is_temp:
                    try:
                        upload_filepath.unlink()
                    except:
                        pass
                continue
        
        # Upload file (use converted file if available)
        success, file_id = upload_file_to_openwebui(upload_filepath, file_hash, kb_id)
        
        # Clean up temp file after upload
        if is_temp:
            try:
                upload_filepath.unlink()
            except Exception as e:
                log(f"⚠ Could not clean up temp file: {e}")
        
        if success:
            # Wait for processing if we got a file ID
            if file_id:
                log(f"⏳ Waiting for {filepath.name} to be processed...")
                processing_success = wait_for_upload_processing(file_id)
                
                if processing_success:
                    # Add file to knowledge base collection if kb_id is present
                    kb_add_success = True
                    if kb_id:
                        kb_add_success = add_file_to_knowledge_base(kb_id, file_id)
                    
                    if kb_add_success:
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
                        # Failed to add to knowledge base
                        state['files'][file_key] = {
                            'hash': file_hash,
                            'status': 'failed',
                            'file_id': file_id,
                            'last_attempt': datetime.now().isoformat(),
                            'retry_count': file_state.get('retry_count', 0) + 1,
                            'knowledge_base': kb_name,
                            'error': 'Failed to add to knowledge base collection'
                        }
                        failed += 1
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
    
    # Clean up temporary SSH directories
    if ssh_temp_dirs:
        log("Cleaning up temporary SSH directories...")
        for temp_dir in ssh_temp_dirs:
            try:
                if temp_dir.exists():
                    import shutil
                    shutil.rmtree(temp_dir)
                    log(f"✓ Removed temp directory: {temp_dir.name}")
            except Exception as e:
                log(f"⚠ Could not remove temp directory {temp_dir.name}: {e}")
    
    log(f"Sync complete: {uploaded} uploaded, {skipped} skipped, {failed} failed, {retried} retried, {filtered} filtered, {converted} converted")

if __name__ == '__main__':
    sync_files()
