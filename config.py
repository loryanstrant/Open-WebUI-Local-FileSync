#!/usr/bin/env python3
"""
Configuration manager for Open-WebUI-Local-FileSync
Handles loading config from file or environment variables
"""
import os
import json
from pathlib import Path

# Default configuration file path
DEFAULT_CONFIG_FILE = os.getenv('CONFIG_FILE', '/app/config/filesync-config.json')

def get_default_config():
    """Get default configuration structure"""
    return {
        'openwebui': {
            'url': 'http://localhost:8080',
            'api_key': ''
        },
        'sync': {
            'schedule': 'daily',
            'time': '00:00',
            'day': '0',
            'timezone': 'UTC'
        },
        'files': {
            'directory': '/data',
            'allowed_extensions': ['.md', '.txt', '.pdf', '.doc', '.docx', '.json', '.yaml', '.yml', '.conf'],
            'state_file': '/app/sync_state.json'
        },
        'knowledge_bases': {
            'single_kb_mode': False,
            'single_kb_name': '',
            'mappings': []
        },
        'retry': {
            'max_attempts': 3,
            'delay': 60,
            'upload_timeout': 300
        },
        'ssh': {
            'enabled': False,
            'key_path': '/app/ssh_keys',
            'strict_host_key_checking': False,
            'sources': []
        },
        'volumes': []
    }

def load_config_from_file(config_file=None):
    """Load configuration from JSON file
    
    Args:
        config_file: Path to config file, defaults to DEFAULT_CONFIG_FILE
    
    Returns:
        Dict with configuration or default config if file doesn't exist
    """
    config_path = config_file or DEFAULT_CONFIG_FILE
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                default = get_default_config()
                # Deep merge
                for key in default:
                    if key not in config:
                        config[key] = default[key]
                    elif isinstance(default[key], dict):
                        for subkey in default[key]:
                            if subkey not in config[key]:
                                config[key][subkey] = default[key][subkey]
                return config
        except Exception as e:
            print(f"Error loading config file {config_path}: {e}")
            return get_default_config()
    else:
        return get_default_config()

def save_config_to_file(config, config_file=None):
    """Save configuration to JSON file
    
    Args:
        config: Configuration dict to save
        config_file: Path to config file, defaults to DEFAULT_CONFIG_FILE
    
    Returns:
        True if successful, False otherwise
    """
    config_path = config_file or DEFAULT_CONFIG_FILE
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config file {config_path}: {e}")
        return False

def load_config_from_env():
    """Load configuration from environment variables (legacy mode)
    
    Returns:
        Dict with configuration from environment
    """
    config = get_default_config()
    
    # OpenWebUI settings
    config['openwebui']['url'] = os.getenv('OPENWEBUI_URL', 'http://localhost:8080')
    config['openwebui']['api_key'] = os.getenv('OPENWEBUI_API_KEY', '')
    
    # Sync settings
    config['sync']['schedule'] = os.getenv('SYNC_SCHEDULE', 'daily')
    config['sync']['time'] = os.getenv('SYNC_TIME', '00:00')
    config['sync']['day'] = os.getenv('SYNC_DAY', '0')
    config['sync']['timezone'] = os.getenv('TZ', 'UTC')
    
    # File settings
    config['files']['directory'] = os.getenv('FILES_DIR', '/data')
    allowed_ext = os.getenv('ALLOWED_EXTENSIONS', '.md,.txt,.pdf,.doc,.docx,.json,.yaml,.yml,.conf')
    config['files']['allowed_extensions'] = [ext.strip() for ext in allowed_ext.split(',')]
    config['files']['state_file'] = os.getenv('STATE_FILE', '/app/sync_state.json')
    
    # Knowledge base settings
    kb_name = os.getenv('KNOWLEDGE_BASE_NAME', '')
    if kb_name:
        config['knowledge_bases']['single_kb_mode'] = True
        config['knowledge_bases']['single_kb_name'] = kb_name
    else:
        config['knowledge_bases']['single_kb_mode'] = False
        
        # Try JSON array format
        kb_mappings_json = os.getenv('KNOWLEDGE_BASE_MAPPINGS', '')
        if kb_mappings_json:
            try:
                mappings = json.loads(kb_mappings_json)
                if isinstance(mappings, list):
                    config['knowledge_bases']['mappings'] = mappings
            except:
                pass
        
        # Try legacy format
        if not config['knowledge_bases']['mappings']:
            kb_mapping = os.getenv('KNOWLEDGE_BASE_MAPPING', '')
            if kb_mapping:
                mappings = []
                for entry in kb_mapping.split(','):
                    if ':' in entry:
                        path, kb = entry.split(':', 1)
                        mappings.append({'path': path.strip(), 'kb': kb.strip()})
                config['knowledge_bases']['mappings'] = mappings
    
    # Retry settings
    config['retry']['max_attempts'] = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    config['retry']['delay'] = int(os.getenv('RETRY_DELAY', '60'))
    config['retry']['upload_timeout'] = int(os.getenv('UPLOAD_TIMEOUT', '300'))
    
    # SSH settings
    ssh_sources_json = os.getenv('SSH_REMOTE_SOURCES', '')
    if ssh_sources_json:
        try:
            sources = json.loads(ssh_sources_json)
            if isinstance(sources, list) and sources:
                config['ssh']['enabled'] = True
                config['ssh']['sources'] = sources
        except:
            pass
    
    config['ssh']['key_path'] = os.getenv('SSH_KEY_PATH', '/app/ssh_keys')
    config['ssh']['strict_host_key_checking'] = os.getenv('SSH_STRICT_HOST_KEY_CHECKING', 'false').lower() == 'true'
    
    return config

def get_config():
    """Get configuration from file or environment variables
    
    Priority:
    1. Config file (if exists and CONFIG_FILE env var is set or default exists)
    2. Environment variables (legacy mode)
    
    Returns:
        Dict with configuration
    """
    config_file = os.getenv('CONFIG_FILE', DEFAULT_CONFIG_FILE)
    
    # Check if config file exists
    if os.path.exists(config_file):
        print(f"Loading configuration from file: {config_file}")
        return load_config_from_file(config_file)
    else:
        print("Loading configuration from environment variables")
        return load_config_from_env()

def export_env_to_config_file():
    """One-time migration: export environment variables to config file
    
    Returns:
        True if successful, False otherwise
    """
    config = load_config_from_env()
    return save_config_to_file(config)
