#!/usr/bin/env python3
"""
Web interface for managing Open-WebUI-Local-FileSync configuration
"""
import os
import json
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from config import get_config, save_config_to_file, export_env_to_config_file, DEFAULT_CONFIG_FILE

app = Flask(__name__)

# HTML Template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Open-WebUI FileSync Configuration</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 6px;
            border-left: 4px solid #4CAF50;
        }
        
        .section h2 {
            color: #333;
            margin-bottom: 15px;
            font-size: 20px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: 500;
            font-size: 14px;
        }
        
        input[type="text"],
        input[type="number"],
        select,
        textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            font-family: inherit;
        }
        
        textarea {
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            min-height: 120px;
            resize: vertical;
        }
        
        input[type="checkbox"] {
            margin-right: 8px;
        }
        
        button {
            background: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #45a049;
        }
        
        button.secondary {
            background: #2196F3;
        }
        
        button.secondary:hover {
            background: #0b7dda;
        }
        
        button.danger {
            background: #f44336;
        }
        
        button.danger:hover {
            background: #da190b;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        .mapping-item,
        .ssh-source-item,
        .volume-item {
            background: white;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 10px;
            border: 1px solid #e0e0e0;
        }
        
        .mapping-item button,
        .ssh-source-item button,
        .volume-item button {
            padding: 6px 12px;
            font-size: 12px;
        }
        
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .help-text {
            font-size: 12px;
            color: #888;
            margin-top: 4px;
        }
        
        .inline-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        @media (max-width: 768px) {
            .inline-group {
                grid-template-columns: 1fr;
            }
        }
        
        .array-field {
            margin-bottom: 10px;
        }
        
        .array-field input {
            margin-bottom: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Open-WebUI FileSync Configuration</h1>
        <p class="subtitle">Manage your file synchronization settings</p>
        
        {% if message %}
        <div class="alert alert-success">
            {{ message }}
        </div>
        {% endif %}
        
        {% if info %}
        <div class="alert alert-info">
            {{ info }}
        </div>
        {% endif %}
        
        <form method="POST" action="/save">
            
            <!-- Open WebUI Settings -->
            <div class="section">
                <h2>Open WebUI Connection</h2>
                <div class="form-group">
                    <label for="openwebui_url">Open WebUI URL:</label>
                    <input type="text" id="openwebui_url" name="openwebui_url" 
                           value="{{ config.openwebui.url }}" required>
                    <div class="help-text">URL of your Open WebUI instance (e.g., http://openwebui:8080)</div>
                </div>
                <div class="form-group">
                    <label for="openwebui_api_key">API Key:</label>
                    <input type="text" id="openwebui_api_key" name="openwebui_api_key" 
                           value="{{ config.openwebui.api_key }}" required>
                    <div class="help-text">API key from Open WebUI Settings → Account</div>
                </div>
            </div>
            
            <!-- Sync Schedule Settings -->
            <div class="section">
                <h2>Sync Schedule</h2>
                <div class="inline-group">
                    <div class="form-group">
                        <label for="sync_schedule">Schedule:</label>
                        <select id="sync_schedule" name="sync_schedule">
                            <option value="hourly" {% if config.sync.schedule == 'hourly' %}selected{% endif %}>Hourly</option>
                            <option value="daily" {% if config.sync.schedule == 'daily' %}selected{% endif %}>Daily</option>
                            <option value="weekly" {% if config.sync.schedule == 'weekly' %}selected{% endif %}>Weekly</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="sync_time">Time (HH:MM):</label>
                        <input type="text" id="sync_time" name="sync_time" 
                               value="{{ config.sync.time }}" pattern="[0-9]{2}:[0-9]{2}">
                    </div>
                </div>
                <div class="inline-group">
                    <div class="form-group">
                        <label for="sync_day">Day (for weekly):</label>
                        <input type="text" id="sync_day" name="sync_day" 
                               value="{{ config.sync.day }}">
                        <div class="help-text">0-6 (0=Sunday) or mon, tue, wed, etc.</div>
                    </div>
                    <div class="form-group">
                        <label for="sync_timezone">Timezone:</label>
                        <input type="text" id="sync_timezone" name="sync_timezone" 
                               value="{{ config.sync.timezone }}">
                        <div class="help-text">e.g., UTC, America/New_York, Europe/London</div>
                    </div>
                </div>
            </div>
            
            <!-- File Settings -->
            <div class="section">
                <h2>File Settings</h2>
                <div class="form-group">
                    <label for="files_directory">Files Directory:</label>
                    <input type="text" id="files_directory" name="files_directory" 
                           value="{{ config.files.directory }}">
                    <div class="help-text">Directory inside container to sync from (default: /data)</div>
                </div>
                <div class="form-group">
                    <label for="files_allowed_extensions">Allowed Extensions:</label>
                    <input type="text" id="files_allowed_extensions" name="files_allowed_extensions" 
                           value="{{ ','.join(config.files.allowed_extensions) }}">
                    <div class="help-text">Comma-separated list (e.g., .md,.txt,.pdf,.doc,.docx)</div>
                </div>
                <div class="form-group">
                    <label for="files_state_file">State File Path:</label>
                    <input type="text" id="files_state_file" name="files_state_file" 
                           value="{{ config.files.state_file }}">
                </div>
            </div>
            
            <!-- Knowledge Base Settings -->
            <div class="section">
                <h2>Knowledge Base Configuration</h2>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="kb_single_mode" name="kb_single_mode" 
                               {% if config.knowledge_bases.single_kb_mode %}checked{% endif %}>
                        Single Knowledge Base Mode (all files go to one KB)
                    </label>
                </div>
                <div class="form-group" id="single_kb_name_group">
                    <label for="kb_single_name">Knowledge Base Name:</label>
                    <input type="text" id="kb_single_name" name="kb_single_name" 
                           value="{{ config.knowledge_bases.single_kb_name }}">
                </div>
                <div class="form-group" id="kb_mappings_group">
                    <label>Knowledge Base Mappings:</label>
                    <div id="kb_mappings_container">
                        {% for mapping in config.knowledge_bases.mappings %}
                        <div class="mapping-item">
                            <input type="text" placeholder="Path" name="kb_mapping_path[]" value="{{ mapping.path }}">
                            <input type="text" placeholder="KB Name" name="kb_mapping_kb[]" value="{{ mapping.kb }}">
                            <textarea placeholder='Exclude patterns (JSON array, e.g., ["*.log", ".git/*"])' 
                                      name="kb_mapping_exclude[]">{{ mapping.exclude | tojson if mapping.exclude else '' }}</textarea>
                            <textarea placeholder='Include patterns (JSON array, e.g., ["includes/*"])' 
                                      name="kb_mapping_include[]">{{ mapping.include | tojson if mapping.include else '' }}</textarea>
                            <button type="button" class="danger" onclick="this.parentElement.remove()">Remove</button>
                        </div>
                        {% endfor %}
                    </div>
                    <button type="button" class="secondary" onclick="addKBMapping()">Add Mapping</button>
                </div>
            </div>
            
            <!-- Volume Configuration -->
            <div class="section">
                <h2>Volume Mounts (Documentation Only)</h2>
                <p class="help-text">Note: These are for reference only. Actual volume mounts must be configured in docker-compose.yml</p>
                <div id="volumes_container">
                    {% for volume in config.volumes %}
                    <div class="volume-item">
                        <input type="text" placeholder="Host Path" name="volume_host[]" value="{{ volume.host }}">
                        <input type="text" placeholder="Container Path" name="volume_container[]" value="{{ volume.container }}">
                        <label>
                            <input type="checkbox" name="volume_readonly[]" {% if volume.readonly %}checked{% endif %}>
                            Read-only
                        </label>
                        <button type="button" class="danger" onclick="this.parentElement.remove()">Remove</button>
                    </div>
                    {% endfor %}
                </div>
                <button type="button" class="secondary" onclick="addVolume()">Add Volume</button>
            </div>
            
            <!-- SSH Settings -->
            <div class="section">
                <h2>SSH Remote Sources</h2>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="ssh_enabled" name="ssh_enabled" 
                               {% if config.ssh.enabled %}checked{% endif %}>
                        Enable SSH Remote File Ingestion
                    </label>
                </div>
                <div class="form-group">
                    <label for="ssh_key_path">SSH Keys Directory:</label>
                    <input type="text" id="ssh_key_path" name="ssh_key_path" 
                           value="{{ config.ssh.key_path }}">
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="ssh_strict_host_key" 
                               {% if config.ssh.strict_host_key_checking %}checked{% endif %}>
                        Strict Host Key Checking
                    </label>
                </div>
                <div id="ssh_sources_container">
                    {% for source in config.ssh.sources %}
                    <div class="ssh-source-item">
                        <input type="text" placeholder="Host" name="ssh_host[]" value="{{ source.host }}">
                        <input type="number" placeholder="Port" name="ssh_port[]" value="{{ source.port | default(22) }}">
                        <input type="text" placeholder="Username" name="ssh_username[]" value="{{ source.username }}">
                        <input type="text" placeholder="Password (optional)" name="ssh_password[]" value="{{ source.password | default('') }}">
                        <input type="text" placeholder="Key Filename (optional)" name="ssh_key_filename[]" value="{{ source.key_filename | default('') }}">
                        <textarea placeholder='Remote Paths (JSON array, e.g., ["/path1", "/path2"])' 
                                  name="ssh_paths[]">{{ source.paths | tojson }}</textarea>
                        <input type="text" placeholder="Knowledge Base Name (optional)" name="ssh_kb[]" value="{{ source.kb | default('') }}">
                        <button type="button" class="danger" onclick="this.parentElement.remove()">Remove</button>
                    </div>
                    {% endfor %}
                </div>
                <button type="button" class="secondary" onclick="addSSHSource()">Add SSH Source</button>
            </div>
            
            <!-- Retry Settings -->
            <div class="section">
                <h2>Retry & Upload Settings</h2>
                <div class="inline-group">
                    <div class="form-group">
                        <label for="retry_max_attempts">Max Retry Attempts:</label>
                        <input type="number" id="retry_max_attempts" name="retry_max_attempts" 
                               value="{{ config.retry.max_attempts }}" min="1" max="10">
                    </div>
                    <div class="form-group">
                        <label for="retry_delay">Retry Delay (seconds):</label>
                        <input type="number" id="retry_delay" name="retry_delay" 
                               value="{{ config.retry.delay }}" min="1">
                    </div>
                </div>
                <div class="form-group">
                    <label for="retry_upload_timeout">Upload Timeout (seconds):</label>
                    <input type="number" id="retry_upload_timeout" name="retry_upload_timeout" 
                           value="{{ config.retry.upload_timeout }}" min="30">
                </div>
            </div>
            
            <div class="button-group">
                <button type="submit">Save Configuration</button>
                <button type="button" class="secondary" onclick="window.location.href='/export_json'">Download JSON</button>
            </div>
        </form>
    </div>
    
    <script>
        function addKBMapping() {
            const container = document.getElementById('kb_mappings_container');
            const item = document.createElement('div');
            item.className = 'mapping-item';
            item.innerHTML = `
                <input type="text" placeholder="Path" name="kb_mapping_path[]">
                <input type="text" placeholder="KB Name" name="kb_mapping_kb[]">
                <textarea placeholder='Exclude patterns (JSON array, e.g., ["*.log", ".git/*"])' name="kb_mapping_exclude[]"></textarea>
                <textarea placeholder='Include patterns (JSON array, e.g., ["includes/*"])' name="kb_mapping_include[]"></textarea>
                <button type="button" class="danger" onclick="this.parentElement.remove()">Remove</button>
            `;
            container.appendChild(item);
        }
        
        function addVolume() {
            const container = document.getElementById('volumes_container');
            const item = document.createElement('div');
            item.className = 'volume-item';
            item.innerHTML = `
                <input type="text" placeholder="Host Path" name="volume_host[]">
                <input type="text" placeholder="Container Path" name="volume_container[]">
                <label>
                    <input type="checkbox" name="volume_readonly[]">
                    Read-only
                </label>
                <button type="button" class="danger" onclick="this.parentElement.remove()">Remove</button>
            `;
            container.appendChild(item);
        }
        
        function addSSHSource() {
            const container = document.getElementById('ssh_sources_container');
            const item = document.createElement('div');
            item.className = 'ssh-source-item';
            item.innerHTML = `
                <input type="text" placeholder="Host" name="ssh_host[]">
                <input type="number" placeholder="Port" name="ssh_port[]" value="22">
                <input type="text" placeholder="Username" name="ssh_username[]">
                <input type="text" placeholder="Password (optional)" name="ssh_password[]">
                <input type="text" placeholder="Key Filename (optional)" name="ssh_key_filename[]">
                <textarea placeholder='Remote Paths (JSON array, e.g., ["/path1", "/path2"])' name="ssh_paths[]"></textarea>
                <input type="text" placeholder="Knowledge Base Name (optional)" name="ssh_kb[]">
                <button type="button" class="danger" onclick="this.parentElement.remove()">Remove</button>
            `;
            container.appendChild(item);
        }
        
        // Toggle KB configuration based on single mode checkbox
        document.getElementById('kb_single_mode').addEventListener('change', function() {
            const singleGroup = document.getElementById('single_kb_name_group');
            const mappingsGroup = document.getElementById('kb_mappings_group');
            if (this.checked) {
                singleGroup.style.display = 'block';
                mappingsGroup.style.display = 'none';
            } else {
                singleGroup.style.display = 'none';
                mappingsGroup.style.display = 'block';
            }
        });
        
        // Initialize visibility on load
        window.addEventListener('load', function() {
            const checkbox = document.getElementById('kb_single_mode');
            const event = new Event('change');
            checkbox.dispatchEvent(event);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main configuration page"""
    config = get_config()
    message = request.args.get('message')
    info = request.args.get('info')
    return render_template_string(HTML_TEMPLATE, config=config, message=message, info=info)

@app.route('/save', methods=['POST'])
def save():
    """Save configuration"""
    try:
        # Build config from form data
        config = {
            'openwebui': {
                'url': request.form.get('openwebui_url'),
                'api_key': request.form.get('openwebui_api_key')
            },
            'sync': {
                'schedule': request.form.get('sync_schedule'),
                'time': request.form.get('sync_time'),
                'day': request.form.get('sync_day'),
                'timezone': request.form.get('sync_timezone')
            },
            'files': {
                'directory': request.form.get('files_directory'),
                'allowed_extensions': [ext.strip() for ext in request.form.get('files_allowed_extensions', '').split(',')],
                'state_file': request.form.get('files_state_file')
            },
            'knowledge_bases': {
                'single_kb_mode': 'kb_single_mode' in request.form,
                'single_kb_name': request.form.get('kb_single_name', ''),
                'mappings': []
            },
            'retry': {
                'max_attempts': int(request.form.get('retry_max_attempts', 3)),
                'delay': int(request.form.get('retry_delay', 60)),
                'upload_timeout': int(request.form.get('retry_upload_timeout', 300))
            },
            'ssh': {
                'enabled': 'ssh_enabled' in request.form,
                'key_path': request.form.get('ssh_key_path'),
                'strict_host_key_checking': 'ssh_strict_host_key' in request.form,
                'sources': []
            },
            'volumes': []
        }
        
        # Parse KB mappings
        kb_paths = request.form.getlist('kb_mapping_path[]')
        kb_kbs = request.form.getlist('kb_mapping_kb[]')
        kb_excludes = request.form.getlist('kb_mapping_exclude[]')
        kb_includes = request.form.getlist('kb_mapping_include[]')
        
        for i, (path, kb) in enumerate(zip(kb_paths, kb_kbs)):
            if path and kb:
                mapping = {'path': path, 'kb': kb}
                
                # Parse exclude patterns
                if i < len(kb_excludes) and kb_excludes[i]:
                    try:
                        exclude = json.loads(kb_excludes[i])
                        if isinstance(exclude, list):
                            mapping['exclude'] = exclude
                    except:
                        pass
                
                # Parse include patterns
                if i < len(kb_includes) and kb_includes[i]:
                    try:
                        include = json.loads(kb_includes[i])
                        if isinstance(include, list):
                            mapping['include'] = include
                    except:
                        pass
                
                config['knowledge_bases']['mappings'].append(mapping)
        
        # Parse volumes
        volume_hosts = request.form.getlist('volume_host[]')
        volume_containers = request.form.getlist('volume_container[]')
        volume_readonlys = request.form.getlist('volume_readonly[]')
        
        for i, (host, container) in enumerate(zip(volume_hosts, volume_containers)):
            if host and container:
                config['volumes'].append({
                    'host': host,
                    'container': container,
                    'readonly': str(i) in volume_readonlys
                })
        
        # Parse SSH sources
        ssh_hosts = request.form.getlist('ssh_host[]')
        ssh_ports = request.form.getlist('ssh_port[]')
        ssh_usernames = request.form.getlist('ssh_username[]')
        ssh_passwords = request.form.getlist('ssh_password[]')
        ssh_key_filenames = request.form.getlist('ssh_key_filename[]')
        ssh_paths_list = request.form.getlist('ssh_paths[]')
        ssh_kbs = request.form.getlist('ssh_kb[]')
        
        for i, host in enumerate(ssh_hosts):
            if host and i < len(ssh_usernames) and ssh_usernames[i]:
                source = {
                    'host': host,
                    'port': int(ssh_ports[i]) if i < len(ssh_ports) and ssh_ports[i] else 22,
                    'username': ssh_usernames[i]
                }
                
                if i < len(ssh_passwords) and ssh_passwords[i]:
                    source['password'] = ssh_passwords[i]
                
                if i < len(ssh_key_filenames) and ssh_key_filenames[i]:
                    source['key_filename'] = ssh_key_filenames[i]
                
                if i < len(ssh_paths_list) and ssh_paths_list[i]:
                    try:
                        paths = json.loads(ssh_paths_list[i])
                        if isinstance(paths, list):
                            source['paths'] = paths
                        else:
                            source['paths'] = [ssh_paths_list[i]]
                    except:
                        source['paths'] = [ssh_paths_list[i]]
                else:
                    source['paths'] = []
                
                if i < len(ssh_kbs) and ssh_kbs[i]:
                    source['kb'] = ssh_kbs[i]
                
                config['ssh']['sources'].append(source)
        
        # Save to file
        if save_config_to_file(config):
            return redirect(url_for('index', message='Configuration saved successfully!'))
        else:
            return redirect(url_for('index', info='Failed to save configuration. Check permissions.'))
    
    except Exception as e:
        # Log the error but don't expose details to user
        print(f"Error saving configuration: {e}")
        return redirect(url_for('index', info='Error saving configuration. Check logs for details.'))

@app.route('/export_json')
def export_json():
    """Export configuration as JSON download"""
    config = get_config()
    return jsonify(config)

@app.route('/api/config', methods=['GET'])
def get_config_api():
    """API endpoint to get configuration"""
    config = get_config()
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def update_config_api():
    """API endpoint to update configuration"""
    try:
        config = request.get_json()
        if save_config_to_file(config):
            return jsonify({'success': True, 'message': 'Configuration saved'})
        else:
            return jsonify({'success': False, 'message': 'Failed to save configuration'}), 500
    except Exception as e:
        # Log the error but don't expose details to user
        print(f"Error updating config: {e}")
        return jsonify({'success': False, 'message': 'Error saving configuration'}), 400

@app.route('/migrate')
def migrate():
    """Migrate environment variables to config file"""
    if export_env_to_config_file():
        return redirect(url_for('index', message='Environment variables migrated to config file successfully!'))
    else:
        return redirect(url_for('index', info='Failed to migrate environment variables.'))

def main():
    """Run the web interface"""
    port = int(os.getenv('WEB_PORT', '8000'))
    host = os.getenv('WEB_HOST', '0.0.0.0')
    
    print(f"Starting web interface on {host}:{port}")
    print(f"Config file location: {DEFAULT_CONFIG_FILE}")
    
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    main()
