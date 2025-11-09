#!/usr/bin/env python3
"""
Web interface for managing Open-WebUI-Local-FileSync configuration
"""
import os
import json
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from config import get_config, save_config_to_file, export_env_to_config_file, DEFAULT_CONFIG_FILE
from pathlib import Path

# Version information
VERSION = "1.0.0"

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

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
        :root {
            --bg-primary: #f5f5f5;
            --bg-secondary: white;
            --bg-tertiary: #f9f9f9;
            --text-primary: #333;
            --text-secondary: #555;
            --text-tertiary: #666;
            --text-muted: #888;
            --border-color: #ddd;
            --border-color-light: #e0e0e0;
            --accent-color: #4CAF50;
            --accent-hover: #45a049;
            --secondary-color: #2196F3;
            --secondary-hover: #0b7dda;
            --danger-color: #f44336;
            --danger-hover: #da190b;
            --success-bg: #d4edda;
            --success-text: #155724;
            --success-border: #c3e6cb;
            --info-bg: #d1ecf1;
            --info-text: #0c5460;
            --info-border: #bee5eb;
            --shadow: rgba(0,0,0,0.1);
        }
        
        [data-theme="dark"] {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #383838;
            --text-primary: #e0e0e0;
            --text-secondary: #c0c0c0;
            --text-tertiary: #a0a0a0;
            --text-muted: #888;
            --border-color: #444;
            --border-color-light: #555;
            --accent-color: #66BB6A;
            --accent-hover: #57a75b;
            --secondary-color: #42A5F5;
            --secondary-hover: #2196F3;
            --danger-color: #EF5350;
            --danger-hover: #e53935;
            --success-bg: #1b5e20;
            --success-text: #a5d6a7;
            --success-border: #2e7d32;
            --info-bg: #01579b;
            --info-text: #81d4fa;
            --info-border: #0277bd;
            --shadow: rgba(0,0,0,0.3);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            padding: 20px;
            line-height: 1.6;
            transition: background-color 0.3s, color 0.3s;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: var(--bg-secondary);
            border-radius: 8px;
            box-shadow: 0 2px 4px var(--shadow);
            padding: 30px;
            transition: background-color 0.3s, box-shadow 0.3s;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .header-left {
            flex: 1;
        }
        
        .header-right {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        h1 {
            color: var(--text-primary);
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: var(--text-tertiary);
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .version {
            color: var(--text-muted);
            font-size: 12px;
            font-weight: normal;
        }
        
        .github-link {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 8px 12px;
            border-radius: 4px;
            transition: all 0.3s;
        }
        
        .github-link:hover {
            color: var(--text-primary);
            background: var(--bg-tertiary);
        }
        
        .nav-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 0;
        }
        
        .nav-tab {
            padding: 10px 20px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: var(--text-secondary);
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
            transition: all 0.3s;
        }
        
        .nav-tab:hover {
            color: var(--accent-color);
        }
        
        .nav-tab.active {
            color: var(--accent-color);
            border-bottom-color: var(--accent-color);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .theme-toggle {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .theme-toggle:hover {
            background: var(--border-color);
        }
        
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background: var(--bg-tertiary);
            border-radius: 6px;
            border-left: 4px solid var(--accent-color);
            transition: background-color 0.3s;
        }
        
        .section h2 {
            color: var(--text-primary);
            margin-bottom: 15px;
            font-size: 20px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 14px;
        }
        
        input[type="text"],
        input[type="number"],
        select,
        textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 14px;
            font-family: inherit;
            background: var(--bg-secondary);
            color: var(--text-primary);
            transition: border-color 0.3s, background-color 0.3s, color 0.3s;
        }
        
        input[type="text"]:focus,
        input[type="number"]:focus,
        select:focus,
        textarea:focus {
            outline: none;
            border-color: var(--accent-color);
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
            background: var(--accent-color);
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
            background: var(--accent-hover);
        }
        
        button.secondary {
            background: var(--secondary-color);
        }
        
        button.secondary:hover {
            background: var(--secondary-hover);
        }
        
        button.danger {
            background: var(--danger-color);
        }
        
        button.danger:hover {
            background: var(--danger-hover);
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        .mapping-item,
        .ssh-source-item,
        .volume-item {
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 10px;
            border: 1px solid var(--border-color-light);
            transition: background-color 0.3s, border-color 0.3s;
        }
        
        .ssh-source-item {
            border-left: 3px solid var(--secondary-color);
        }
        
        .ssh-source-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            padding: 5px;
            margin: -10px -10px 10px -10px;
            border-radius: 4px;
        }
        
        .ssh-source-header:hover {
            background: var(--bg-tertiary);
        }
        
        .ssh-source-title {
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .ssh-source-toggle {
            font-size: 18px;
            transition: transform 0.3s;
        }
        
        .ssh-source-toggle.collapsed {
            transform: rotate(-90deg);
        }
        
        .ssh-source-content {
            max-height: 2000px;
            overflow: hidden;
            transition: max-height 0.3s ease-out, opacity 0.3s ease-out;
            opacity: 1;
        }
        
        .ssh-source-content.collapsed {
            max-height: 0;
            opacity: 0;
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
            background: var(--success-bg);
            color: var(--success-text);
            border: 1px solid var(--success-border);
        }
        
        .alert-info {
            background: var(--info-bg);
            color: var(--info-text);
            border: 1px solid var(--info-border);
        }
        
        .help-text {
            font-size: 12px;
            color: var(--text-muted);
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
        
        /* Sync State Table Styles */
        .state-table-container {
            overflow-x: auto;
            margin-top: 20px;
        }
        
        .state-table {
            width: 100%;
            border-collapse: collapse;
            background: var(--bg-secondary);
            table-layout: auto;
        }
        
        .state-table th,
        .state-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .state-table th {
            background: var(--bg-tertiary);
            font-weight: 600;
            color: var(--text-primary);
            position: sticky;
            top: 0;
            cursor: pointer;
            user-select: none;
        }
        
        .state-table th:hover {
            background: var(--border-color);
        }
        
        .state-table th.sortable::after {
            content: ' ⇅';
            opacity: 0.3;
            font-size: 0.8em;
        }
        
        .state-table th.sort-asc::after {
            content: ' ↑';
            opacity: 1;
        }
        
        .state-table th.sort-desc::after {
            content: ' ↓';
            opacity: 1;
        }
        
        .state-table td.file-path {
            max-width: 300px;
            word-break: break-all;
            white-space: normal;
        }
        
        .state-table td.kb-name {
            max-width: 150px;
        }
        
        .state-table td.actions {
            white-space: nowrap;
        }
        
        .state-table tr:hover {
            background: var(--bg-tertiary);
        }
        
        @media (max-width: 768px) {
            .state-table td.file-path {
                max-width: 150px;
            }
            
            .state-table td.kb-name {
                max-width: 100px;
            }
        }
        
        .state-status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .state-status.uploaded {
            background: var(--success-bg);
            color: var(--success-text);
        }
        
        .state-status.failed {
            background: var(--danger-color);
            color: white;
        }
        
        .state-status.processing {
            background: var(--info-bg);
            color: var(--info-text);
        }
        
        .state-controls {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .state-search {
            flex: 1;
            min-width: 200px;
        }
        
        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background-color: var(--bg-secondary);
            margin: auto;
            padding: 20px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            width: 80%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .modal-header h2 {
            margin: 0;
            color: var(--text-primary);
        }
        
        .close {
            color: var(--text-muted);
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            background: none;
            border: none;
            padding: 0;
        }
        
        .close:hover,
        .close:focus {
            color: var(--text-primary);
        }
        
        .file-browser {
            border: 1px solid var(--border-color);
            border-radius: 4px;
            max-height: 400px;
            overflow-y: auto;
            background: var(--bg-secondary);
        }
        
        .file-item {
            padding: 10px;
            border-bottom: 1px solid var(--border-color-light);
            display: flex;
            align-items: center;
            gap: 8px;
            transition: background 0.2s;
        }
        
        .file-item:hover {
            background: var(--bg-tertiary);
        }
        
        .file-item.selected {
            background: var(--accent-color);
            color: white;
        }
        
        .file-item-checkbox {
            cursor: pointer;
            margin-right: 4px;
        }
        
        .file-item-content {
            display: flex;
            align-items: center;
            gap: 8px;
            flex: 1;
            cursor: pointer;
        }
        
        .file-icon {
            font-size: 18px;
        }
        
        .breadcrumb {
            padding: 10px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            margin-bottom: 10px;
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        .breadcrumb-item {
            cursor: pointer;
            color: var(--secondary-color);
        }
        
        .breadcrumb-item:hover {
            text-decoration: underline;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: var(--text-muted);
        }
        
        /* Status Dashboard Styles */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: var(--bg-tertiary);
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid var(--accent-color);
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px var(--shadow);
        }
        
        .stat-card.warning {
            border-left-color: #ff9800;
        }
        
        .stat-card.error {
            border-left-color: var(--danger-color);
        }
        
        .stat-card.success {
            border-left-color: var(--accent-color);
        }
        
        .stat-label {
            font-size: 14px;
            color: var(--text-tertiary);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: var(--text-primary);
            margin-bottom: 4px;
        }
        
        .stat-detail {
            font-size: 12px;
            color: var(--text-muted);
        }
        
        .kb-list {
            list-style: none;
            padding: 0;
        }
        
        .kb-item {
            padding: 10px;
            margin-bottom: 8px;
            background: var(--bg-secondary);
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .kb-name {
            font-weight: 500;
            color: var(--text-primary);
        }
        
        .kb-count {
            color: var(--text-muted);
            font-size: 14px;
        }
        
        .source-list {
            list-style: none;
            padding: 0;
        }
        
        .source-item {
            padding: 10px;
            margin-bottom: 8px;
            background: var(--bg-secondary);
            border-radius: 4px;
        }
        
        .source-name {
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 4px;
        }
        
        .source-stats {
            font-size: 12px;
            color: var(--text-muted);
            display: flex;
            gap: 15px;
        }
        
        .log-entry {
            margin-bottom: 8px;
            padding: 8px;
            border-radius: 4px;
            background: var(--bg-secondary);
            word-wrap: break-word;
        }
        
        .log-entry.error {
            border-left: 3px solid var(--danger-color);
            background: rgba(244, 67, 54, 0.1);
        }
        
        .log-entry.warning {
            border-left: 3px solid #ff9800;
            background: rgba(255, 152, 0, 0.1);
        }
        
        .log-entry.info {
            border-left: 3px solid var(--secondary-color);
        }
        
        .log-timestamp {
            color: var(--text-muted);
            font-size: 11px;
            margin-right: 8px;
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .spinning {
            display: inline-block;
            animation: spin 1s linear infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1>Open WebUI FileSync <span class="version">v{{ version }}</span></h1>
                <p class="subtitle">Manage your file synchronization settings</p>
            </div>
            <div class="header-right">
                <a href="https://github.com/loryanstrant/Open-WebUI-Local-FileSync" target="_blank" class="github-link" title="View on GitHub">
                    <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                    </svg>
                    GitHub
                </a>
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">
                    <span id="theme-icon">🌙</span>
                    <span id="theme-text">Dark</span>
                </button>
            </div>
        </div>
        
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
        
        <!-- Navigation Tabs -->
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="switchTab('status')">Status</button>
            <button class="nav-tab" onclick="switchTab('config')">Configuration</button>
            <button class="nav-tab" onclick="switchTab('state')">Sync State</button>
            <button class="nav-tab" onclick="switchTab('files')">Knowledge Base Files</button>
            <button class="nav-tab" onclick="switchTab('logs')">Logs</button>
        </div>
        
        <!-- Status Tab -->
        <div id="status-tab" class="tab-content active">
            <div class="section">
                <h2>Sync Status Dashboard</h2>
                <p class="help-text" style="margin-bottom: 15px;">
                    Overview of your file synchronization status and statistics.
                </p>
                
                <div class="button-group" style="margin-bottom: 20px;">
                    <button class="secondary" onclick="forceSyncNow()">
                        <span id="sync-btn-icon">🔄</span> Force Sync Now
                    </button>
                    <button class="secondary" onclick="refreshStatusDashboard()">↻ Refresh</button>
                </div>
                
                <div id="status-dashboard">
                    <div class="loading">Loading status...</div>
                </div>
            </div>
        </div>
        
        <!-- Configuration Tab -->
        <div id="config-tab" class="tab-content">
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
                    <div class="help-text">Comma-separated list (e.g., .md,.txt,.pdf,.doc,.docx,.json,.yaml,.yml,.conf)</div>
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
                <div class="help-text" style="margin-bottom: 15px;">Use exclude/include patterns to filter which files are synced. Patterns support wildcards (* and ?) and substring matching.</div>
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
                            <input type="text" placeholder="Path (can be a directory or specific file)" name="kb_mapping_path[]" value="{{ mapping.path }}">
                            <input type="text" placeholder="KB Name" name="kb_mapping_kb[]" value="{{ mapping.kb }}">
                            <textarea placeholder='Exclude patterns (JSON array, e.g., ["*.log", ".git/*", "*_backup*"])' 
                                      name="kb_mapping_exclude[]">{{ mapping.exclude | tojson if mapping.exclude else '' }}</textarea>
                            <textarea placeholder='Include patterns (JSON array, e.g., ["includes/*", "config.conf"])' 
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
                <p class="help-text">To filter which files are synced from volumes, use the Knowledge Base Configuration section below with include/exclude patterns.</p>
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
                <div class="help-text" style="margin-bottom: 15px;">Fetch files from remote servers. Paths can be directories or specific files. Use exclude/include patterns to filter files.</div>
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
                        <div class="ssh-source-header" onclick="toggleSSHSource(this)">
                            <div class="ssh-source-title">
                                <span class="ssh-source-toggle collapsed">▼</span>
                                <span>{{ source.name if source.name else (source.host + '@' + (source.username if source.username else 'unknown')) }}</span>
                            </div>
                        </div>
                        <div class="ssh-source-content collapsed">
                            <input type="text" placeholder="Name/Description (e.g., Production Server)" name="ssh_name[]" value="{{ source.name | default('') }}">
                            <input type="text" placeholder="Host" name="ssh_host[]" value="{{ source.host }}">
                            <input type="number" placeholder="Port" name="ssh_port[]" value="{{ source.port | default(22) }}">
                            <input type="text" placeholder="Username" name="ssh_username[]" value="{{ source.username }}">
                            <input type="text" placeholder="Password (optional)" name="ssh_password[]" value="{{ source.password | default('') }}">
                            <input type="text" placeholder="Key Filename (optional)" name="ssh_key_filename[]" value="{{ source.key_filename | default('') }}">
                            <textarea placeholder='Remote Paths - directories or files (JSON array, e.g., ["/etc/app", "/config/app.conf"])' 
                                      name="ssh_paths[]">{{ source.paths | tojson }}</textarea>
                            <button type="button" class="secondary" onclick="browseSSH(this)">Browse Files</button>
                            <input type="text" placeholder="Knowledge Base Name (optional)" name="ssh_kb[]" value="{{ source.kb | default('') }}">
                            <textarea placeholder='Exclude patterns (JSON array, e.g., ["*.log", ".git/*", "*_backup*"])' 
                                      name="ssh_exclude[]">{{ source.exclude | tojson if source.exclude else '' }}</textarea>
                            <textarea placeholder='Include patterns - overrides exclusions (JSON array, e.g., ["includes/*", "*.conf"])' 
                                      name="ssh_include[]">{{ source.include | tojson if source.include else '' }}</textarea>
                            <button type="button" class="danger" onclick="this.parentElement.parentElement.remove()">Remove</button>
                        </div>
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
        
        <!-- Sync State Tab -->
        <div id="state-tab" class="tab-content">
            <div class="section">
                <h2>Sync State Management</h2>
                <p class="help-text" style="margin-bottom: 15px;">
                    View and manage files that have been synced to Open WebUI. 
                    You can remove individual files, change knowledge bases, or select multiple items for bulk operations.
                </p>
                
                <div class="state-controls">
                    <input type="text" id="state-search" class="state-search" placeholder="Search by path..." onkeyup="filterStateTable()">
                    <select id="status-filter" style="padding: 8px; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary);" onchange="filterStateTable()">
                        <option value="">All Statuses</option>
                        <option value="uploaded">Uploaded</option>
                        <option value="processing">Processing</option>
                        <option value="failed">Failed</option>
                    </select>
                    <select id="kb-filter" style="padding: 8px; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary);" onchange="filterStateTable()">
                        <option value="">All Knowledge Bases</option>
                    </select>
                    <button onclick="selectAllState()">Select All</button>
                    <button onclick="deselectAllState()">Deselect All</button>
                    <select id="kb-select" style="padding: 8px; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary);">
                        <option value="">Select KB...</option>
                    </select>
                    <button class="secondary" onclick="changeSelectedKB()" id="change-kb-btn" disabled>Change KB</button>
                    <button class="danger" onclick="deleteSelectedState()" id="delete-selected-btn" disabled>Delete Selected</button>
                    <button class="secondary" onclick="refreshStateTable()">Refresh</button>
                </div>
                
                <div class="state-table-container">
                    <table class="state-table" id="state-table">
                        <thead>
                            <tr>
                                <th><input type="checkbox" id="select-all-checkbox" onchange="toggleSelectAll()"></th>
                                <th class="sortable" onclick="sortStateTable('path')">File Path</th>
                                <th class="sortable" onclick="sortStateTable('kb')">Knowledge Base</th>
                                <th class="sortable" onclick="sortStateTable('status')">Status</th>
                                <th class="sortable" onclick="sortStateTable('date')">Last Updated</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="state-table-body">
                            <tr>
                                <td colspan="6" class="loading">Loading sync state...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- File Management Tab -->
        <div id="files-tab" class="tab-content">
            <div class="section">
                <h2>Knowledge Base File Management</h2>
                <p class="help-text" style="margin-bottom: 15px;">
                    Manage files and knowledge bases in Open WebUI. View, search, and delete files directly from the knowledge base.
                </p>
                
                <div class="state-controls">
                    <input type="text" id="files-search" class="state-search" placeholder="Search by filename..." onkeyup="filterFilesTable()">
                    <select id="files-kb-filter" style="padding: 8px; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary);" onchange="filterFilesTable()">
                        <option value="">All Knowledge Bases</option>
                    </select>
                    <button onclick="selectAllFiles()">Select All</button>
                    <button onclick="deselectAllFiles()">Deselect All</button>
                    <button class="danger" onclick="deleteSelectedFiles()" id="delete-files-btn" disabled>Delete Selected</button>
                    <button class="secondary" onclick="refreshFilesTable()">Refresh</button>
                </div>
                
                <div class="state-table-container">
                    <table class="state-table" id="files-table">
                        <thead>
                            <tr>
                                <th><input type="checkbox" id="select-all-files-checkbox" onchange="toggleSelectAllFiles()"></th>
                                <th class="sortable" onclick="sortFilesTable('filename')">Filename</th>
                                <th class="sortable" onclick="sortFilesTable('kb')">Knowledge Base</th>
                                <th class="sortable" onclick="sortFilesTable('size')">Size</th>
                                <th class="sortable" onclick="sortFilesTable('date')">Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="files-table-body">
                            <tr>
                                <td colspan="6" class="loading">Loading files...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Logs Tab -->
        <div id="logs-tab" class="tab-content">
            <div class="section">
                <h2>Sync Logs</h2>
                <p class="help-text" style="margin-bottom: 15px;">
                    View synchronization logs and errors. Use the search box to filter log entries.
                </p>
                
                <div class="state-controls">
                    <input type="text" id="logs-search" class="state-search" placeholder="Search logs..." onkeyup="filterLogs()">
                    <select id="logs-level-filter" style="padding: 8px; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary);" onchange="filterLogs()">
                        <option value="">All Levels</option>
                        <option value="ERROR">Errors</option>
                        <option value="WARNING">Warnings</option>
                        <option value="INFO">Info</option>
                    </select>
                    <button class="secondary" onclick="refreshLogs()">Refresh</button>
                    <button class="danger" onclick="clearLogs()">Clear Logs</button>
                </div>
                
                <div class="state-table-container">
                    <div id="logs-container" style="background: var(--bg-tertiary); padding: 15px; border-radius: 4px; max-height: 600px; overflow-y: auto; font-family: 'Monaco', 'Menlo', 'Courier New', monospace; font-size: 13px; line-height: 1.5;">
                        <div class="loading">Loading logs...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- SSH File Browser Modal -->
    <div id="ssh-browser-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Browse SSH Files</h2>
                <button class="close" onclick="closeSSHBrowser()">&times;</button>
            </div>
            <div class="breadcrumb" id="ssh-breadcrumb">
                <span class="breadcrumb-item" onclick="navigateSSHPath('/')">Root</span>
            </div>
            <div style="margin-bottom: 10px; display: flex; gap: 10px;">
                <button type="button" class="secondary" style="padding: 6px 12px; font-size: 12px;" onclick="selectAllInCurrentDirectory()">Select All</button>
                <button type="button" class="secondary" style="padding: 6px 12px; font-size: 12px;" onclick="deselectAllSSH()">Deselect All</button>
            </div>
            <div class="file-browser" id="file-browser">
                <div class="loading">Connecting...</div>
            </div>
            <div class="button-group" style="margin-top: 15px;">
                <button class="secondary" id="add-selected-path-btn" onclick="addSelectedPath()">Add Selected Path</button>
                <button onclick="closeSSHBrowser()">Cancel</button>
            </div>
        </div>
    </div>
    
    <script>
        // Theme Management
        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            updateThemeButton(newTheme);
        }
        
        function updateThemeButton(theme) {
            const icon = document.getElementById('theme-icon');
            const text = document.getElementById('theme-text');
            
            if (theme === 'dark') {
                icon.textContent = '🌙';
                text.textContent = 'Dark';
            } else {
                icon.textContent = '☀️';
                text.textContent = 'Light';
            }
        }
        
        function initTheme() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            updateThemeButton(savedTheme);
        }
        
        // Tab Management
        function switchTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active class from all nav tabs
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            
            // Set active nav tab
            event.target.classList.add('active');
            
            // Load appropriate content
            if (tabName === 'status') {
                loadStatusDashboard();
            } else if (tabName === 'state') {
                loadStateTable();
            } else if (tabName === 'files') {
                loadFilesTable();
            } else if (tabName === 'logs') {
                loadLogs();
            }
        }
        
        // Sync State Management
        let stateData = [];
        let selectedState = new Set();
        let sortColumn = null;
        let sortDirection = 'asc';
        
        async function loadStateTable() {
            const tbody = document.getElementById('state-table-body');
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Loading sync state...</td></tr>';
            
            try {
                const response = await fetch('/api/state');
                const data = await response.json();
                stateData = data.files || [];
                
                // Load knowledge bases for dropdown
                await loadKnowledgeBases();
                
                renderStateTable();
            } catch (error) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--danger-color);">Error loading sync state</td></tr>';
                console.error('Error loading state:', error);
            }
        }
        
        async function loadKnowledgeBases() {
            try {
                const response = await fetch('/api/knowledge_bases');
                const data = await response.json();
                const kbSelect = document.getElementById('kb-select');
                const kbFilter = document.getElementById('kb-filter');
                
                // Clear existing options except the first one
                kbSelect.innerHTML = '<option value="">Select KB...</option>';
                kbFilter.innerHTML = '<option value="">All Knowledge Bases</option>';
                
                // Add knowledge bases
                if (data.knowledge_bases && data.knowledge_bases.length > 0) {
                    data.knowledge_bases.forEach(kb => {
                        // For kb-select (change KB dropdown)
                        const option = document.createElement('option');
                        option.value = kb;
                        option.textContent = kb;
                        kbSelect.appendChild(option);
                        
                        // For kb-filter (filter dropdown)
                        const filterOption = document.createElement('option');
                        filterOption.value = kb;
                        filterOption.textContent = kb;
                        kbFilter.appendChild(filterOption);
                    });
                }
                
                // Add option to clear KB (only for kb-select)
                const clearOption = document.createElement('option');
                clearOption.value = '__clear__';
                clearOption.textContent = '(Remove KB Assignment)';
                kbSelect.appendChild(clearOption);
            } catch (error) {
                console.error('Error loading knowledge bases:', error);
            }
        }
        
        function sortStateTable(column) {
            // Toggle sort direction if clicking same column
            if (sortColumn === column) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                sortColumn = column;
                sortDirection = 'asc';
            }
            
            // Sort data
            stateData.sort((a, b) => {
                let valA, valB;
                
                switch(column) {
                    case 'path':
                        valA = a.path.toLowerCase();
                        valB = b.path.toLowerCase();
                        break;
                    case 'kb':
                        valA = (a.kb || '').toLowerCase();
                        valB = (b.kb || '').toLowerCase();
                        break;
                    case 'status':
                        valA = a.status.toLowerCase();
                        valB = b.status.toLowerCase();
                        break;
                    case 'date':
                        valA = a.last_attempt || '';
                        valB = b.last_attempt || '';
                        break;
                    default:
                        return 0;
                }
                
                if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
                if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
                return 0;
            });
            
            // Update sort indicators
            document.querySelectorAll('.state-table th.sortable').forEach(th => {
                th.classList.remove('sort-asc', 'sort-desc');
            });
            
            const headerMap = {
                'path': 1,
                'kb': 2,
                'status': 3,
                'date': 4
            };
            
            const thIndex = headerMap[column];
            if (thIndex) {
                const th = document.querySelectorAll('.state-table th.sortable')[thIndex - 1];
                if (th) {
                    th.classList.add(sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
                }
            }
            
            renderStateTable();
        }
        
        function renderStateTable() {
            const tbody = document.getElementById('state-table-body');
            const searchTerm = document.getElementById('state-search').value.toLowerCase();
            const statusFilter = document.getElementById('status-filter').value;
            const kbFilter = document.getElementById('kb-filter').value;
            
            const filteredData = stateData.filter(item => {
                // Apply search filter
                const matchesSearch = !searchTerm || item.path.toLowerCase().includes(searchTerm);
                
                // Apply status filter
                const matchesStatus = !statusFilter || item.status === statusFilter;
                
                // Apply KB filter
                const matchesKB = !kbFilter || item.kb === kbFilter;
                
                return matchesSearch && matchesStatus && matchesKB;
            });
            
            if (filteredData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No synced files found</td></tr>';
                return;
            }
            
            tbody.innerHTML = filteredData.map(item => `
                <tr>
                    <td><input type="checkbox" class="state-checkbox" value="${escapeHtml(item.path)}" onclick="handleStateCheckboxClick(event, this)" onchange="updateSelectedState()"></td>
                    <td class="file-path">${escapeHtml(item.path)}</td>
                    <td class="kb-name">${item.kb ? escapeHtml(item.kb) : '-'}</td>
                    <td><span class="state-status ${item.status}">${item.status}</span></td>
                    <td>${item.last_attempt ? new Date(item.last_attempt).toLocaleString() : '-'}</td>
                    <td><button class="danger" onclick="deleteStateItem('${escapeHtml(item.path)}')">Delete</button></td>
                </tr>
            `).join('');
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function filterStateTable() {
            renderStateTable();
        }
        
        function refreshStateTable() {
            selectedState.clear();
            document.getElementById('select-all-checkbox').checked = false;
            updateActionButtons();
            loadStateTable();
        }
        
        function toggleSelectAll() {
            const checked = document.getElementById('select-all-checkbox').checked;
            document.querySelectorAll('.state-checkbox').forEach(cb => {
                cb.checked = checked;
            });
            updateSelectedState();
        }
        
        function selectAllState() {
            document.getElementById('select-all-checkbox').checked = true;
            toggleSelectAll();
        }
        
        function deselectAllState() {
            document.getElementById('select-all-checkbox').checked = false;
            toggleSelectAll();
        }
        
        function updateSelectedState() {
            selectedState.clear();
            document.querySelectorAll('.state-checkbox:checked').forEach(cb => {
                selectedState.add(cb.value);
            });
            updateActionButtons();
        }
        
        // Shift-select support for sync state
        let lastCheckedState = null;
        
        function handleStateCheckboxClick(event, checkbox) {
            if (!lastCheckedState) {
                lastCheckedState = checkbox;
                return;
            }
            
            if (event.shiftKey) {
                const checkboxes = Array.from(document.querySelectorAll('.state-checkbox'));
                const start = checkboxes.indexOf(lastCheckedState);
                const end = checkboxes.indexOf(checkbox);
                const range = checkboxes.slice(Math.min(start, end), Math.max(start, end) + 1);
                
                range.forEach(cb => {
                    cb.checked = checkbox.checked;
                });
                
                updateSelectedState();
            }
            
            lastCheckedState = checkbox;
        }
        
        function updateActionButtons() {
            const deleteBtn = document.getElementById('delete-selected-btn');
            const changeKbBtn = document.getElementById('change-kb-btn');
            const count = selectedState.size;
            
            deleteBtn.disabled = count === 0;
            deleteBtn.textContent = `Delete Selected (${count})`;
            
            changeKbBtn.disabled = count === 0;
            changeKbBtn.textContent = count > 0 ? `Change KB (${count})` : 'Change KB';
        }
        
        async function changeSelectedKB() {
            if (selectedState.size === 0) return;
            
            const kbSelect = document.getElementById('kb-select');
            const kbName = kbSelect.value;
            
            if (!kbName) {
                alert('Please select a knowledge base first');
                return;
            }
            
            const kbDisplayName = kbName === '__clear__' ? 'no knowledge base' : kbName;
            const actualKbName = kbName === '__clear__' ? '' : kbName;
            
            if (!confirm(`Change knowledge base for ${selectedState.size} item(s) to "${kbDisplayName}"?`)) {
                return;
            }
            
            try {
                const response = await fetch('/api/state/update_kb', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        paths: Array.from(selectedState),
                        kb_name: actualKbName
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    selectedState.clear();
                    refreshStateTable();
                    alert(`Successfully updated ${result.updated_count} item(s)`);
                } else {
                    alert('Failed to update KB: ' + result.message);
                }
            } catch (error) {
                alert('Error updating KB: ' + error.message);
                console.error('Error:', error);
            }
        }
        
        async function deleteStateItem(path) {
            if (!confirm(`Are you sure you want to remove "${path}" from the sync state?`)) {
                return;
            }
            
            try {
                const response = await fetch('/api/state/delete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({paths: [path]})
                });
                
                const result = await response.json();
                if (result.success) {
                    refreshStateTable();
                } else {
                    alert('Failed to delete item: ' + result.message);
                }
            } catch (error) {
                alert('Error deleting item: ' + error.message);
                console.error('Error:', error);
            }
        }
        
        async function deleteSelectedState() {
            if (selectedState.size === 0) return;
            
            if (!confirm(`Are you sure you want to remove ${selectedState.size} item(s) from the sync state?`)) {
                return;
            }
            
            try {
                const response = await fetch('/api/state/delete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({paths: Array.from(selectedState)})
                });
                
                const result = await response.json();
                if (result.success) {
                    selectedState.clear();
                    refreshStateTable();
                } else {
                    alert('Failed to delete items: ' + result.message);
                }
            } catch (error) {
                alert('Error deleting items: ' + error.message);
                console.error('Error:', error);
            }
        }
        
        // File Management (Open WebUI Files)
        let filesData = [];
        let selectedFiles = new Set();
        let filesSortColumn = null;
        let filesSortDirection = 'asc';
        
        async function loadFilesTable() {
            const tbody = document.getElementById('files-table-body');
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Loading files from Open WebUI...</td></tr>';
            
            try {
                const response = await fetch('/api/openwebui/files');
                const data = await response.json();
                
                if (!data.success) {
                    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--danger-color);">${data.error || 'Error loading files'}</td></tr>`;
                    return;
                }
                
                filesData = data.files || [];
                
                // Load KB filter options
                await loadFilesKnowledgeBases();
                
                renderFilesTable();
            } catch (error) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--danger-color);">Error loading files</td></tr>';
                console.error('Error loading files:', error);
            }
        }
        
        async function loadFilesKnowledgeBases() {
            try {
                const kbFilter = document.getElementById('files-kb-filter');
                kbFilter.innerHTML = '<option value="">All Knowledge Bases</option>';
                
                // Get unique KB names from files
                const kbSet = new Set();
                filesData.forEach(file => {
                    if (file.knowledge_bases && file.knowledge_bases.length > 0) {
                        file.knowledge_bases.forEach(kb => kbSet.add(kb));
                    }
                });
                
                // Add to filter dropdown
                Array.from(kbSet).sort().forEach(kb => {
                    const option = document.createElement('option');
                    option.value = kb;
                    option.textContent = kb;
                    kbFilter.appendChild(option);
                });
                
                // Add "Unassigned" option
                const unassignedOption = document.createElement('option');
                unassignedOption.value = '__none__';
                unassignedOption.textContent = '(Unassigned)';
                kbFilter.appendChild(unassignedOption);
            } catch (error) {
                console.error('Error loading knowledge bases:', error);
            }
        }
        
        function renderFilesTable() {
            const tbody = document.getElementById('files-table-body');
            const searchTerm = document.getElementById('files-search').value.toLowerCase();
            const kbFilter = document.getElementById('files-kb-filter').value;
            
            const filteredData = filesData.filter(item => {
                // Apply search filter
                const matchesSearch = !searchTerm || item.filename.toLowerCase().includes(searchTerm);
                
                // Apply KB filter
                let matchesKB = true;
                if (kbFilter) {
                    if (kbFilter === '__none__') {
                        matchesKB = !item.knowledge_bases || item.knowledge_bases.length === 0;
                    } else {
                        matchesKB = item.knowledge_bases && item.knowledge_bases.includes(kbFilter);
                    }
                }
                
                return matchesSearch && matchesKB;
            });
            
            if (filteredData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No files found</td></tr>';
                return;
            }
            
            tbody.innerHTML = filteredData.map(item => `
                <tr>
                    <td><input type="checkbox" class="files-checkbox" value="${escapeHtml(item.id)}" onclick="handleFilesCheckboxClick(event, this)" onchange="updateSelectedFiles()"></td>
                    <td class="file-path">${escapeHtml(item.filename)}</td>
                    <td class="kb-name">${item.knowledge_bases && item.knowledge_bases.length > 0 ? escapeHtml(item.knowledge_bases.join(', ')) : '-'}</td>
                    <td>${formatFileSize(item.size)}</td>
                    <td>${item.created_at ? new Date(item.created_at).toLocaleString() : '-'}</td>
                    <td><button class="danger" onclick="deleteFileItem('${escapeHtml(item.id)}', '${escapeHtml(item.filename)}')">Delete</button></td>
                </tr>
            `).join('');
        }
        
        // Shift-select support for files
        let lastCheckedFile = null;
        
        function handleFilesCheckboxClick(event, checkbox) {
            if (!lastCheckedFile) {
                lastCheckedFile = checkbox;
                return;
            }
            
            if (event.shiftKey) {
                const checkboxes = Array.from(document.querySelectorAll('.files-checkbox'));
                const start = checkboxes.indexOf(lastCheckedFile);
                const end = checkboxes.indexOf(checkbox);
                const range = checkboxes.slice(Math.min(start, end), Math.max(start, end) + 1);
                
                range.forEach(cb => {
                    cb.checked = checkbox.checked;
                });
                
                updateSelectedFiles();
            }
            
            lastCheckedFile = checkbox;
        }
        
        function formatFileSize(bytes) {
            if (!bytes || bytes === 0) return '-';
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(1024));
            return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
        }
        
        function filterFilesTable() {
            renderFilesTable();
        }
        
        function refreshFilesTable() {
            selectedFiles.clear();
            document.getElementById('select-all-files-checkbox').checked = false;
            updateFilesActionButtons();
            loadFilesTable();
        }
        
        function toggleSelectAllFiles() {
            const checked = document.getElementById('select-all-files-checkbox').checked;
            document.querySelectorAll('.files-checkbox').forEach(cb => {
                cb.checked = checked;
            });
            updateSelectedFiles();
        }
        
        function selectAllFiles() {
            document.getElementById('select-all-files-checkbox').checked = true;
            toggleSelectAllFiles();
        }
        
        function deselectAllFiles() {
            document.getElementById('select-all-files-checkbox').checked = false;
            toggleSelectAllFiles();
        }
        
        function updateSelectedFiles() {
            selectedFiles.clear();
            document.querySelectorAll('.files-checkbox:checked').forEach(cb => {
                selectedFiles.add(cb.value);
            });
            updateFilesActionButtons();
        }
        
        function updateFilesActionButtons() {
            const deleteBtn = document.getElementById('delete-files-btn');
            const count = selectedFiles.size;
            
            deleteBtn.disabled = count === 0;
            deleteBtn.textContent = `Delete Selected (${count})`;
        }
        
        async function deleteFileItem(fileId, filename) {
            if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
                return;
            }
            
            try {
                const response = await fetch('/api/openwebui/files/delete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({file_ids: [fileId]})
                });
                
                const result = await response.json();
                if (result.success) {
                    refreshFilesTable();
                    alert(`Successfully deleted file`);
                } else {
                    alert('Failed to delete file: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Error deleting file: ' + error.message);
                console.error('Error:', error);
            }
        }
        
        async function deleteSelectedFiles() {
            if (selectedFiles.size === 0) return;
            
            if (!confirm(`Are you sure you want to delete ${selectedFiles.size} file(s)?`)) {
                return;
            }
            
            try {
                const response = await fetch('/api/openwebui/files/delete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({file_ids: Array.from(selectedFiles)})
                });
                
                const result = await response.json();
                if (result.success) {
                    selectedFiles.clear();
                    refreshFilesTable();
                    alert(`Successfully deleted ${result.deleted_count} of ${result.total} file(s)`);
                } else {
                    alert('Failed to delete files: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Error deleting files: ' + error.message);
                console.error('Error:', error);
            }
        }
        
        function sortFilesTable(column) {
            // Toggle sort direction if clicking same column
            if (filesSortColumn === column) {
                filesSortDirection = filesSortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                filesSortColumn = column;
                filesSortDirection = 'asc';
            }
            
            // Sort data
            filesData.sort((a, b) => {
                let valA, valB;
                
                switch(column) {
                    case 'filename':
                        valA = a.filename.toLowerCase();
                        valB = b.filename.toLowerCase();
                        break;
                    case 'kb':
                        valA = (a.knowledge_bases && a.knowledge_bases.length > 0 ? a.knowledge_bases.join(',') : '').toLowerCase();
                        valB = (b.knowledge_bases && b.knowledge_bases.length > 0 ? b.knowledge_bases.join(',') : '').toLowerCase();
                        break;
                    case 'size':
                        valA = a.size || 0;
                        valB = b.size || 0;
                        break;
                    case 'date':
                        valA = a.created_at || '';
                        valB = b.created_at || '';
                        break;
                    default:
                        return 0;
                }
                
                if (valA < valB) return filesSortDirection === 'asc' ? -1 : 1;
                if (valA > valB) return filesSortDirection === 'asc' ? 1 : -1;
                return 0;
            });
            
            renderFilesTable();
        }
        
        // SSH File Browser
        let currentSSHSource = null;
        let currentSSHPath = '/';
        let selectedSSHPaths = new Set();
        
        function browseSSH(button) {
            const sshItem = button.closest('.ssh-source-item');
            const host = sshItem.querySelector('input[name="ssh_host[]"]').value;
            const port = sshItem.querySelector('input[name="ssh_port[]"]').value;
            const username = sshItem.querySelector('input[name="ssh_username[]"]').value;
            const password = sshItem.querySelector('input[name="ssh_password[]"]').value;
            const keyFilename = sshItem.querySelector('input[name="ssh_key_filename[]"]').value;
            
            if (!host || !username) {
                alert('Please enter host and username first');
                return;
            }
            
            currentSSHSource = {
                sshItem: sshItem,
                host: host,
                port: port || 22,
                username: username,
                password: password,
                key_filename: keyFilename
            };
            
            currentSSHPath = '/';
            document.getElementById('ssh-browser-modal').classList.add('active');
            loadSSHDirectory('/');
        }
        
        async function loadSSHDirectory(path) {
            const browser = document.getElementById('file-browser');
            browser.innerHTML = '<div class="loading">Loading...</div>';
            
            try {
                const response = await fetch('/api/ssh/browse', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        host: currentSSHSource.host,
                        port: currentSSHSource.port,
                        username: currentSSHSource.username,
                        password: currentSSHSource.password,
                        key_filename: currentSSHSource.key_filename,
                        path: path
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    renderSSHDirectory(data.items, path);
                    updateSSHBreadcrumb(path);
                } else {
                    browser.innerHTML = `<div class="loading" style="color: var(--danger-color);">${data.error}</div>`;
                }
            } catch (error) {
                browser.innerHTML = `<div class="loading" style="color: var(--danger-color);">Error: ${error.message}</div>`;
                console.error('Error:', error);
            }
        }
        
        function renderSSHDirectory(items, path) {
            const browser = document.getElementById('file-browser');
            
            if (items.length === 0) {
                browser.innerHTML = '<div class="loading">Empty directory</div>';
                return;
            }
            
            browser.innerHTML = items.map(item => {
                const icon = item.is_dir ? '📁' : '📄';
                const itemPath = path.endsWith('/') ? path + item.name : path + '/' + item.name;
                const isSelected = selectedSSHPaths.has(itemPath);
                const selectedClass = isSelected ? 'selected' : '';
                
                return `
                    <div class="file-item ${selectedClass}">
                        <input type="checkbox" 
                               class="file-item-checkbox" 
                               data-path="${escapeHtml(itemPath)}" 
                               ${isSelected ? 'checked' : ''}
                               onchange="toggleSSHItemSelection('${escapeHtml(itemPath)}', this.checked)">
                        <div class="file-item-content" onclick="${item.is_dir ? `navigateSSHPath('${escapeHtml(itemPath)}')` : ''}">
                            <span class="file-icon">${icon}</span>
                            <span>${escapeHtml(item.name)}</span>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function updateSSHBreadcrumb(path) {
            const breadcrumb = document.getElementById('ssh-breadcrumb');
            const parts = path.split('/').filter(p => p);
            
            let html = '<span class="breadcrumb-item" onclick="navigateSSHPath(\'/\')">Root</span>';
            let currentPath = '';
            
            parts.forEach(part => {
                currentPath += '/' + part;
                html += ` / <span class="breadcrumb-item" onclick="navigateSSHPath('${currentPath}')">${escapeHtml(part)}</span>`;
            });
            
            breadcrumb.innerHTML = html;
        }
        
        function navigateSSHPath(path) {
            currentSSHPath = path;
            loadSSHDirectory(path);
        }
        
        function toggleSSHItemSelection(path, isChecked) {
            if (isChecked) {
                selectedSSHPaths.add(path);
            } else {
                selectedSSHPaths.delete(path);
            }
            updateSelectedPathsButton();
            // Update visual state
            const checkbox = document.querySelector(`input[data-path="${path}"]`);
            if (checkbox) {
                const fileItem = checkbox.closest('.file-item');
                if (isChecked) {
                    fileItem.classList.add('selected');
                } else {
                    fileItem.classList.remove('selected');
                }
            }
        }
        
        function updateSelectedPathsButton() {
            const button = document.querySelector('#add-selected-path-btn');
            if (button) {
                const count = selectedSSHPaths.size;
                if (count > 0) {
                    button.textContent = `Add Selected Path${count > 1 ? 's' : ''} (${count})`;
                } else {
                    button.textContent = 'Add Selected Path';
                }
            }
        }
        
        function selectAllInCurrentDirectory() {
            document.querySelectorAll('.file-item-checkbox').forEach(checkbox => {
                const path = checkbox.getAttribute('data-path');
                checkbox.checked = true;
                selectedSSHPaths.add(path);
                checkbox.closest('.file-item').classList.add('selected');
            });
            updateSelectedPathsButton();
        }
        
        function deselectAllSSH() {
            document.querySelectorAll('.file-item-checkbox').forEach(checkbox => {
                checkbox.checked = false;
                checkbox.closest('.file-item').classList.remove('selected');
            });
            selectedSSHPaths.clear();
            updateSelectedPathsButton();
        }
        
        function selectSSHItem(path) {
            // This function is kept for backward compatibility but is no longer used
            selectedSSHPaths.clear();
            selectedSSHPaths.add(path);
            updateSelectedPathsButton();
        }
        
        function addSelectedPath() {
            if (selectedSSHPaths.size === 0 && currentSSHPath === '/') {
                alert('Please select at least one file or directory');
                return;
            }
            
            // If nothing selected, add current directory
            const pathsToAdd = selectedSSHPaths.size > 0 ? 
                Array.from(selectedSSHPaths) : 
                [currentSSHPath];
            
            const pathsTextarea = currentSSHSource.sshItem.querySelector('textarea[name="ssh_paths[]"]');
            
            try {
                let paths = [];
                const currentValue = pathsTextarea.value.trim();
                if (currentValue) {
                    paths = JSON.parse(currentValue);
                }
                
                if (!Array.isArray(paths)) {
                    paths = [];
                }
                
                // Add all selected paths, avoiding duplicates
                pathsToAdd.forEach(pathToAdd => {
                    if (!paths.includes(pathToAdd)) {
                        paths.push(pathToAdd);
                    }
                });
                
                pathsTextarea.value = JSON.stringify(paths, null, 2);
                
                closeSSHBrowser();
            } catch (error) {
                alert('Error adding path: ' + error.message);
            }
        }
        
        function closeSSHBrowser() {
            document.getElementById('ssh-browser-modal').classList.remove('active');
            currentSSHSource = null;
            currentSSHPath = '/';
            selectedSSHPaths.clear();
        }
        
        function addKBMapping() {
            const container = document.getElementById('kb_mappings_container');
            const item = document.createElement('div');
            item.className = 'mapping-item';
            item.innerHTML = `
                <input type="text" placeholder="Path (can be a directory or specific file)" name="kb_mapping_path[]">
                <input type="text" placeholder="KB Name" name="kb_mapping_kb[]">
                <textarea placeholder='Exclude patterns (JSON array, e.g., ["*.log", ".git/*", "*_backup*"])' name="kb_mapping_exclude[]"></textarea>
                <textarea placeholder='Include patterns (JSON array, e.g., ["includes/*", "config.conf"])' name="kb_mapping_include[]"></textarea>
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
                <div class="ssh-source-header" onclick="toggleSSHSource(this)">
                    <div class="ssh-source-title">
                        <span class="ssh-source-toggle">▼</span>
                        <span>New SSH Source</span>
                    </div>
                </div>
                <div class="ssh-source-content">
                    <input type="text" placeholder="Name/Description (e.g., Production Server)" name="ssh_name[]">
                    <input type="text" placeholder="Host" name="ssh_host[]">
                    <input type="number" placeholder="Port" name="ssh_port[]" value="22">
                    <input type="text" placeholder="Username" name="ssh_username[]">
                    <input type="text" placeholder="Password (optional)" name="ssh_password[]">
                    <input type="text" placeholder="Key Filename (optional)" name="ssh_key_filename[]">
                    <textarea placeholder='Remote Paths - directories or files (JSON array, e.g., ["/etc/app", "/config/app.conf"])' name="ssh_paths[]"></textarea>
                    <button type="button" class="secondary" onclick="browseSSH(this)">Browse Files</button>
                    <input type="text" placeholder="Knowledge Base Name (optional)" name="ssh_kb[]">
                    <textarea placeholder='Exclude patterns (JSON array, e.g., ["*.log", ".git/*", "*_backup*"])' name="ssh_exclude[]"></textarea>
                    <textarea placeholder='Include patterns - overrides exclusions (JSON array, e.g., ["includes/*", "*.conf"])' name="ssh_include[]"></textarea>
                    <button type="button" class="danger" onclick="this.parentElement.parentElement.remove()">Remove</button>
                </div>
            `;
            container.appendChild(item);
        }
        
        function toggleSSHSource(header) {
            const content = header.nextElementSibling;
            const toggle = header.querySelector('.ssh-source-toggle');
            
            if (content.classList.contains('collapsed')) {
                content.classList.remove('collapsed');
                toggle.classList.remove('collapsed');
            } else {
                content.classList.add('collapsed');
                toggle.classList.add('collapsed');
            }
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
        
        // Status Dashboard Functions
        async function loadStatusDashboard() {
            const dashboard = document.getElementById('status-dashboard');
            dashboard.innerHTML = '<div class="loading">Loading status...</div>';
            
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                if (data.success) {
                    renderStatusDashboard(data);
                } else {
                    dashboard.innerHTML = '<div style="text-align: center; color: var(--danger-color);">Error loading status</div>';
                }
            } catch (error) {
                dashboard.innerHTML = '<div style="text-align: center; color: var(--danger-color);">Error loading status</div>';
                console.error('Error loading status:', error);
            }
        }
        
        function renderStatusDashboard(data) {
            const dashboard = document.getElementById('status-dashboard');
            
            const html = `
                <div class="stats-grid">
                    <div class="stat-card success">
                        <div class="stat-label">Total Files</div>
                        <div class="stat-value">${data.total_files || 0}</div>
                        <div class="stat-detail">${data.synced_files || 0} synced</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Knowledge Bases</div>
                        <div class="stat-value">${data.total_kbs || 0}</div>
                        <div class="stat-detail">${data.active_kbs || 0} active</div>
                    </div>
                    
                    <div class="stat-card ${data.failed_files > 0 ? 'error' : ''}">
                        <div class="stat-label">Failed Uploads</div>
                        <div class="stat-value">${data.failed_files || 0}</div>
                        <div class="stat-detail">${data.pending_retries || 0} pending retry</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Conversions</div>
                        <div class="stat-value">${data.total_conversions || 0}</div>
                        <div class="stat-detail">JSON/YAML to MD</div>
                    </div>
                </div>
                
                ${data.kb_stats && data.kb_stats.length > 0 ? `
                <div class="section">
                    <h2>Files per Knowledge Base</h2>
                    <ul class="kb-list">
                        ${data.kb_stats.map(kb => `
                            <li class="kb-item">
                                <span class="kb-name">${escapeHtml(kb.name || 'Unassigned')}</span>
                                <span class="kb-count">${kb.file_count} files</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
                ` : ''}
                
                ${data.source_stats && data.source_stats.length > 0 ? `
                <div class="section">
                    <h2>Sync Sources</h2>
                    <ul class="source-list">
                        ${data.source_stats.map(source => `
                            <li class="source-item">
                                <div class="source-name">${escapeHtml(source.name)}</div>
                                <div class="source-stats">
                                    <span>📁 ${source.files} files</span>
                                    ${source.conversions > 0 ? `<span>🔄 ${source.conversions} converted</span>` : ''}
                                    ${source.errors > 0 ? `<span style="color: var(--danger-color);">❌ ${source.errors} errors</span>` : ''}
                                </div>
                            </li>
                        `).join('')}
                    </ul>
                </div>
                ` : ''}
                
                ${data.last_sync ? `
                <div style="margin-top: 20px; padding: 15px; background: var(--bg-tertiary); border-radius: 4px;">
                    <div style="color: var(--text-secondary); font-size: 14px;">
                        <strong>Last Sync:</strong> ${new Date(data.last_sync).toLocaleString()}
                    </div>
                    ${data.next_sync ? `
                        <div style="color: var(--text-muted); font-size: 12px; margin-top: 5px;">
                            <strong>Next Scheduled:</strong> ${new Date(data.next_sync).toLocaleString()}
                        </div>
                    ` : ''}
                </div>
                ` : ''}
            `;
            
            dashboard.innerHTML = html;
        }
        
        function refreshStatusDashboard() {
            loadStatusDashboard();
        }
        
        async function forceSyncNow() {
            const btn = event.target.closest('button');
            const icon = document.getElementById('sync-btn-icon');
            const originalText = btn.innerHTML;
            
            btn.disabled = true;
            icon.classList.add('spinning');
            btn.innerHTML = '<span class="spinning">🔄</span> Syncing...';
            
            try {
                const response = await fetch('/api/sync/force', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Sync completed successfully!\\n\\n' +
                          'Uploaded: ' + (result.uploaded || 0) + '\\n' +
                          'Skipped: ' + (result.skipped || 0) + '\\n' +
                          'Failed: ' + (result.failed || 0));
                    refreshStatusDashboard();
                } else {
                    alert('Sync failed: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Error triggering sync: ' + error.message);
                console.error('Error:', error);
            } finally {
                btn.disabled = false;
                icon.classList.remove('spinning');
                btn.innerHTML = originalText;
            }
        }
        
        // Logs Functions
        let logsData = [];
        
        async function loadLogs() {
            const container = document.getElementById('logs-container');
            container.innerHTML = '<div class="loading">Loading logs...</div>';
            
            try {
                const response = await fetch('/api/logs');
                const data = await response.json();
                
                if (data.success) {
                    logsData = data.logs || [];
                    renderLogs();
                } else {
                    container.innerHTML = '<div style="text-align: center; color: var(--danger-color);">Error loading logs</div>';
                }
            } catch (error) {
                container.innerHTML = '<div style="text-align: center; color: var(--danger-color);">Error loading logs</div>';
                console.error('Error loading logs:', error);
            }
        }
        
        function renderLogs() {
            const container = document.getElementById('logs-container');
            const searchTerm = document.getElementById('logs-search').value.toLowerCase();
            const levelFilter = document.getElementById('logs-level-filter').value;
            
            const filteredLogs = logsData.filter(log => {
                const matchesSearch = !searchTerm || log.message.toLowerCase().includes(searchTerm);
                const matchesLevel = !levelFilter || log.level === levelFilter;
                return matchesSearch && matchesLevel;
            });
            
            if (filteredLogs.length === 0) {
                container.innerHTML = '<div style="text-align: center; color: var(--text-muted);">No logs found</div>';
                return;
            }
            
            const html = filteredLogs.map(log => {
                const levelClass = log.level ? log.level.toLowerCase() : 'info';
                return `
                    <div class="log-entry ${levelClass}">
                        <span class="log-timestamp">${log.timestamp ? new Date(log.timestamp).toLocaleString() : ''}</span>
                        <span>${escapeHtml(log.message)}</span>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = html;
            // Auto-scroll to bottom
            container.scrollTop = container.scrollHeight;
        }
        
        function filterLogs() {
            renderLogs();
        }
        
        function refreshLogs() {
            loadLogs();
        }
        
        async function clearLogs() {
            if (!confirm('Are you sure you want to clear all logs?')) {
                return;
            }
            
            try {
                const response = await fetch('/api/logs/clear', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const result = await response.json();
                
                if (result.success) {
                    logsData = [];
                    renderLogs();
                } else {
                    alert('Failed to clear logs: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Error clearing logs: ' + error.message);
                console.error('Error:', error);
            }
        }
        
        // Initialize visibility on load
        window.addEventListener('load', function() {
            // Initialize theme
            initTheme();
            
            // Initialize KB single mode visibility
            const checkbox = document.getElementById('kb_single_mode');
            const event = new Event('change');
            checkbox.dispatchEvent(event);
            
            // Load status dashboard on initial page load
            loadStatusDashboard();
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
    return render_template_string(HTML_TEMPLATE, config=config, message=message, info=info, version=VERSION)

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
        ssh_names = request.form.getlist('ssh_name[]')
        ssh_hosts = request.form.getlist('ssh_host[]')
        ssh_ports = request.form.getlist('ssh_port[]')
        ssh_usernames = request.form.getlist('ssh_username[]')
        ssh_passwords = request.form.getlist('ssh_password[]')
        ssh_key_filenames = request.form.getlist('ssh_key_filename[]')
        ssh_paths_list = request.form.getlist('ssh_paths[]')
        ssh_kbs = request.form.getlist('ssh_kb[]')
        ssh_excludes = request.form.getlist('ssh_exclude[]')
        ssh_includes = request.form.getlist('ssh_include[]')
        
        for i, host in enumerate(ssh_hosts):
            if host and i < len(ssh_usernames) and ssh_usernames[i]:
                source = {
                    'host': host,
                    'port': int(ssh_ports[i]) if i < len(ssh_ports) and ssh_ports[i] else 22,
                    'username': ssh_usernames[i]
                }
                
                # Add name/description if provided
                if i < len(ssh_names) and ssh_names[i]:
                    source['name'] = ssh_names[i]
                
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
                
                # Parse exclude patterns
                if i < len(ssh_excludes) and ssh_excludes[i]:
                    try:
                        exclude = json.loads(ssh_excludes[i])
                        if isinstance(exclude, list):
                            source['exclude'] = exclude
                    except:
                        pass
                
                # Parse include patterns
                if i < len(ssh_includes) and ssh_includes[i]:
                    try:
                        include = json.loads(ssh_includes[i])
                        if isinstance(include, list):
                            source['include'] = include
                    except:
                        pass
                
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

@app.route('/api/state', methods=['GET'])
def get_state():
    """API endpoint to get sync state"""
    try:
        config = get_config()
        state_file = config['files']['state_file']
        
        if not os.path.exists(state_file):
            return jsonify({'files': []})
        
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        # Convert state to list format for table display
        files = []
        for path, info in state.get('files', {}).items():
            files.append({
                'path': path,
                'status': info.get('status', 'unknown'),
                'kb': info.get('knowledge_base', ''),
                'last_attempt': info.get('last_attempt', ''),
                'hash': info.get('hash', '')
            })
        
        return jsonify({'files': files})
    except Exception as e:
        print(f"Error loading state: {e}")
        return jsonify({'error': 'Failed to load sync state'}), 500

@app.route('/api/state/delete', methods=['POST'])
def delete_state():
    """API endpoint to delete sync state entries"""
    try:
        data = request.get_json()
        paths = data.get('paths', [])
        
        if not paths:
            return jsonify({'success': False, 'message': 'No paths provided'}), 400
        
        config = get_config()
        state_file = config['files']['state_file']
        
        if not os.path.exists(state_file):
            return jsonify({'success': False, 'message': 'State file not found'}), 404
        
        # Load state
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        # Remove specified paths
        deleted_count = 0
        for path in paths:
            if path in state.get('files', {}):
                del state['files'][path]
                deleted_count += 1
        
        # Save updated state
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        return jsonify({
            'success': True, 
            'message': f'Deleted {deleted_count} item(s)',
            'deleted_count': deleted_count
        })
    except Exception as e:
        print(f"Error deleting state: {e}")
        return jsonify({'success': False, 'message': 'Failed to delete sync state entries'}), 500

@app.route('/api/state/update_kb', methods=['POST'])
def update_kb():
    """API endpoint to update knowledge base for multiple files"""
    try:
        data = request.get_json()
        paths = data.get('paths', [])
        kb_name = data.get('kb_name', '')
        
        if not paths:
            return jsonify({'success': False, 'message': 'No paths provided'}), 400
        
        config = get_config()
        state_file = config['files']['state_file']
        
        if not os.path.exists(state_file):
            return jsonify({'success': False, 'message': 'State file not found'}), 404
        
        # Load state
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        # Update knowledge base for specified paths
        updated_count = 0
        for path in paths:
            if path in state.get('files', {}):
                state['files'][path]['knowledge_base'] = kb_name
                updated_count += 1
        
        # Save updated state
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        return jsonify({
            'success': True, 
            'message': f'Updated {updated_count} item(s)',
            'updated_count': updated_count
        })
    except Exception as e:
        print(f"Error updating KB: {e}")
        return jsonify({'success': False, 'message': 'Failed to update knowledge base'}), 500

@app.route('/api/knowledge_bases', methods=['GET'])
def get_knowledge_bases():
    """API endpoint to get list of knowledge bases from state"""
    try:
        config = get_config()
        state_file = config['files']['state_file']
        
        if not os.path.exists(state_file):
            return jsonify({'knowledge_bases': []})
        
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        # Get unique knowledge bases from state
        kb_set = set()
        for path, info in state.get('files', {}).items():
            kb = info.get('knowledge_base', '')
            if kb:
                kb_set.add(kb)
        
        # Also add knowledge bases from config
        if config['knowledge_bases']['single_kb_mode']:
            kb_name = config['knowledge_bases']['single_kb_name']
            if kb_name:
                kb_set.add(kb_name)
        else:
            for mapping in config['knowledge_bases']['mappings']:
                kb = mapping.get('kb', '')
                if kb:
                    kb_set.add(kb)
        
        # Convert to sorted list
        kb_list = sorted(list(kb_set))
        
        return jsonify({'knowledge_bases': kb_list})
    except Exception as e:
        print(f"Error getting knowledge bases: {e}")
        return jsonify({'error': 'Failed to get knowledge bases'}), 500

@app.route('/api/ssh/browse', methods=['POST'])
def browse_ssh():
    """API endpoint to browse SSH filesystem"""
    if not PARAMIKO_AVAILABLE:
        return jsonify({'success': False, 'error': 'SSH functionality not available'}), 400
    
    try:
        data = request.get_json()
        host = data.get('host')
        port = data.get('port', 22)
        username = data.get('username')
        password = data.get('password')
        key_filename = data.get('key_filename')
        path = data.get('path', '/')
        
        if not host or not username:
            return jsonify({'success': False, 'error': 'Host and username required'}), 400
        
        # Resolve key path if relative
        config = get_config()
        ssh_key_path = config['ssh']['key_path']
        
        # Validate and resolve key path to prevent path injection
        validated_key_path = None
        if key_filename:
            if not os.path.isabs(key_filename):
                temp_key_path = os.path.join(ssh_key_path, key_filename)
            else:
                temp_key_path = key_filename
            
            # Normalize the path and verify it's within the SSH key directory
            temp_key_path = os.path.normpath(temp_key_path)
            ssh_key_path_abs = os.path.normpath(os.path.abspath(ssh_key_path))
            
            # Ensure the key file path is within the allowed SSH key directory
            if temp_key_path.startswith(ssh_key_path_abs + os.sep) or temp_key_path == ssh_key_path_abs:
                validated_key_path = temp_key_path
            else:
                return jsonify({'success': False, 'error': 'Invalid key file path'}), 400
        
        # Connect to SSH
        ssh_client = paramiko.SSHClient()
        # WARNING: AutoAddPolicy accepts any host key without verification
        # This is necessary for SSH browsing functionality but is a security risk
        # lgtm[py/paramiko-missing-host-key-validation]
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        connect_kwargs = {
            'hostname': host,
            'port': port,
            'username': username,
            'timeout': 30
        }
        
        if validated_key_path and os.path.exists(validated_key_path):
            connect_kwargs['key_filename'] = validated_key_path
            if password:
                connect_kwargs['passphrase'] = password
        elif password:
            connect_kwargs['password'] = password
        else:
            return jsonify({'success': False, 'error': 'No authentication method provided'}), 400
        
        ssh_client.connect(**connect_kwargs)
        sftp_client = ssh_client.open_sftp()
        
        # List directory
        items = []
        try:
            for entry in sftp_client.listdir_attr(path):
                import stat as stat_module
                items.append({
                    'name': entry.filename,
                    'is_dir': stat_module.S_ISDIR(entry.st_mode),
                    'size': entry.st_size,
                    'mtime': entry.st_mtime
                })
            
            # Sort: directories first, then files
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        except Exception as e:
            print(f"Error listing directory: {e}")
            return jsonify({'success': False, 'error': 'Failed to list directory'}), 400
        finally:
            sftp_client.close()
            ssh_client.close()
        
        return jsonify({'success': True, 'items': items, 'path': path})
    except paramiko.AuthenticationException:
        return jsonify({'success': False, 'error': 'Authentication failed'}), 401
    except paramiko.SSHException as e:
        print(f"SSH error: {e}")
        return jsonify({'success': False, 'error': 'SSH connection error'}), 500
    except Exception as e:
        print(f"Error browsing SSH: {e}")
        return jsonify({'success': False, 'error': 'Failed to browse SSH filesystem'}), 500

@app.route('/api/openwebui/files', methods=['GET'])
def get_openwebui_files():
    """API endpoint to get all files from Open WebUI"""
    try:
        import requests
        
        config = get_config()
        openwebui_url = config['openwebui']['url']
        api_key = config['openwebui']['api_key']
        
        if not openwebui_url or not api_key:
            return jsonify({'success': False, 'error': 'Open WebUI URL and API key required'}), 400
        
        # Get all files from Open WebUI
        headers = {'Authorization': f'Bearer {api_key}'}
        response = requests.get(f'{openwebui_url}/api/v1/files/', headers=headers)
        
        if response.status_code != 200:
            return jsonify({'success': False, 'error': f'Failed to fetch files: {response.status_code}'}), 500
        
        files_data = response.json()
        
        # Get knowledge bases to map file IDs to KB names
        kb_response = requests.get(f'{openwebui_url}/api/v1/knowledge/', headers=headers)
        kb_mapping = {}
        
        if kb_response.status_code == 200:
            kb_data = kb_response.json()
            # Create mapping of file_id to knowledge base name
            for kb in kb_data:
                kb_name = kb.get('name', '')
                for file_id in kb.get('file_ids', []):
                    if file_id not in kb_mapping:
                        kb_mapping[file_id] = []
                    kb_mapping[file_id].append(kb_name)
        
        # Enhance files data with KB information
        enhanced_files = []
        for file_item in files_data:
            file_id = file_item.get('id', '')
            enhanced_files.append({
                'id': file_id,
                'filename': file_item.get('filename', file_item.get('meta', {}).get('name', 'Unknown')),
                'size': file_item.get('meta', {}).get('size', 0),
                'created_at': file_item.get('created_at', ''),
                'knowledge_bases': kb_mapping.get(file_id, [])
            })
        
        return jsonify({'success': True, 'files': enhanced_files})
    except Exception as e:
        print(f"Error getting Open WebUI files: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch files from Open WebUI'}), 500

@app.route('/api/openwebui/files/delete', methods=['POST'])
def delete_openwebui_files():
    """API endpoint to delete files from Open WebUI"""
    try:
        import requests
        
        data = request.get_json()
        file_ids = data.get('file_ids', [])
        
        if not file_ids:
            return jsonify({'success': False, 'message': 'No file IDs provided'}), 400
        
        config = get_config()
        openwebui_url = config['openwebui']['url']
        api_key = config['openwebui']['api_key']
        
        if not openwebui_url or not api_key:
            return jsonify({'success': False, 'error': 'Open WebUI URL and API key required'}), 400
        
        headers = {'Authorization': f'Bearer {api_key}'}
        deleted_count = 0
        errors = []
        
        for file_id in file_ids:
            try:
                response = requests.delete(f'{openwebui_url}/api/v1/files/{file_id}', headers=headers)
                if response.status_code in [200, 204]:
                    deleted_count += 1
                    # Update sync state to mark as deleted
                    update_sync_state_on_delete(file_id)
                else:
                    errors.append(f'File {file_id}: {response.status_code}')
            except Exception as e:
                errors.append(f'File {file_id}: Error deleting file')
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'total': len(file_ids),
            'errors': errors
        })
    except Exception as e:
        print(f"Error deleting Open WebUI files: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete files'}), 500

def update_sync_state_on_delete(file_id):
    """Update sync state when a file is deleted from Open WebUI"""
    try:
        config = get_config()
        state_file = config['files']['state_file']
        
        if not os.path.exists(state_file):
            return
        
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        # Find and remove entries with matching file_id
        files_to_remove = []
        for path, info in state.get('files', {}).items():
            if info.get('file_id') == file_id:
                files_to_remove.append(path)
        
        for path in files_to_remove:
            del state['files'][path]
        
        # Save updated state
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Error updating sync state on delete: {e}")

@app.route('/api/status', methods=['GET'])
def get_status():
    """API endpoint to get sync status dashboard data"""
    try:
        config = get_config()
        state_file = config['files']['state_file']
        
        # Default stats
        stats = {
            'success': True,
            'total_files': 0,
            'synced_files': 0,
            'failed_files': 0,
            'pending_retries': 0,
            'total_conversions': 0,
            'total_kbs': 0,
            'active_kbs': 0,
            'kb_stats': [],
            'source_stats': [],
            'last_sync': None,
            'next_sync': None
        }
        
        # Load state file
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            files_dict = state.get('files', {})
            stats['total_files'] = len(files_dict)
            
            # Count by status
            kb_file_counts = {}
            for path, info in files_dict.items():
                status = info.get('status', 'unknown')
                if status == 'uploaded':
                    stats['synced_files'] += 1
                elif status == 'failed':
                    stats['failed_files'] += 1
                    retry_count = info.get('retry_count', 0)
                    max_retries = config['retry']['max_attempts']
                    if retry_count < max_retries:
                        stats['pending_retries'] += 1
                
                # Count conversions (files with .json, .yaml, .yml, .conf extensions that were uploaded)
                if status == 'uploaded':
                    ext = os.path.splitext(path)[1].lower()
                    if ext in ['.json', '.yaml', '.yml', '.conf']:
                        stats['total_conversions'] += 1
                
                # Count files per KB
                kb_name = info.get('knowledge_base', '')
                if kb_name:
                    kb_file_counts[kb_name] = kb_file_counts.get(kb_name, 0) + 1
                else:
                    kb_file_counts['Unassigned'] = kb_file_counts.get('Unassigned', 0) + 1
                
                # Get last sync time (most recent last_attempt)
                last_attempt = info.get('last_attempt')
                if last_attempt:
                    if not stats['last_sync'] or last_attempt > stats['last_sync']:
                        stats['last_sync'] = last_attempt
            
            # KB stats
            stats['total_kbs'] = len(state.get('knowledge_bases', {}))
            stats['active_kbs'] = len([kb for kb in kb_file_counts.keys() if kb != 'Unassigned'])
            stats['kb_stats'] = [{'name': kb, 'file_count': count} for kb, count in sorted(kb_file_counts.items(), key=lambda x: x[1], reverse=True)]
        
        # Source stats
        sources = []
        
        # Local files source
        files_dir = config['files']['directory']
        if os.path.exists(files_dir):
            sources.append({
                'name': f'Local Files ({files_dir})',
                'files': stats['synced_files'],
                'conversions': stats['total_conversions'],
                'errors': stats['failed_files']
            })
        
        # SSH sources
        if config['ssh']['enabled'] and config['ssh']['sources']:
            for ssh_source in config['ssh']['sources']:
                ssh_name = ssh_source.get('name', ssh_source.get('host', 'Unknown'))
                sources.append({
                    'name': f'SSH: {ssh_name}',
                    'files': 0,  # Would need to track per-source
                    'conversions': 0,
                    'errors': 0
                })
        
        stats['source_stats'] = sources
        
        return jsonify(stats)
    except Exception as e:
        print(f"Error getting status: {e}")
        return jsonify({'success': False, 'error': 'Failed to load status'}), 500

@app.route('/api/sync/force', methods=['POST'])
def force_sync():
    """API endpoint to trigger a manual sync"""
    try:
        import subprocess
        import sys
        
        # Run sync.py as a subprocess
        result = subprocess.run(
            [sys.executable, '/app/sync.py'],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        # Parse output for stats
        output = result.stdout
        uploaded = 0
        skipped = 0
        failed = 0
        
        # Look for the summary line: "Sync complete: X uploaded, Y skipped, Z failed..."
        import re
        match = re.search(r'Sync complete: (\d+) uploaded, (\d+) skipped, (\d+) failed', output)
        if match:
            uploaded = int(match.group(1))
            skipped = int(match.group(2))
            failed = int(match.group(3))
        
        return jsonify({
            'success': result.returncode == 0,
            'uploaded': uploaded,
            'skipped': skipped,
            'failed': failed,
            'output': output if result.returncode != 0 else None
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Sync timed out'}), 500
    except Exception as e:
        print(f"Error forcing sync: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """API endpoint to get sync logs"""
    try:
        logs = []
        log_file = '/app/sync.log'
        
        # Check if log file exists
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Parse log lines
                for line in lines[-500:]:  # Last 500 lines
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Try to parse timestamp and level from log format: [YYYY-MM-DD HH:MM:SS] message
                    import re
                    match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (.+)', line)
                    if match:
                        timestamp = match.group(1)
                        message = match.group(2)
                        
                        # Determine log level
                        level = 'INFO'
                        if 'ERROR' in message or '✗' in message:
                            level = 'ERROR'
                        elif 'WARNING' in message or '⚠' in message:
                            level = 'WARNING'
                        
                        logs.append({
                            'timestamp': timestamp,
                            'level': level,
                            'message': message
                        })
                    else:
                        # No timestamp, add as-is
                        logs.append({
                            'timestamp': None,
                            'level': 'INFO',
                            'message': line
                        })
        else:
            # No log file, return empty
            logs.append({
                'timestamp': None,
                'level': 'INFO',
                'message': 'No logs available yet. Logs will appear after the first sync.'
            })
        
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        print(f"Error getting logs: {e}")
        return jsonify({'success': False, 'error': 'Failed to load logs'}), 500

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """API endpoint to clear logs"""
    try:
        log_file = '/app/sync.log'
        
        if os.path.exists(log_file):
            # Clear the log file
            with open(log_file, 'w') as f:
                f.write('')
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error clearing logs: {e}")
        return jsonify({'success': False, 'error': 'Failed to clear logs'}), 500

def main():
    """Run the web interface"""
    port = int(os.getenv('WEB_PORT', '8000'))
    host = os.getenv('WEB_HOST', '0.0.0.0')
    
    print(f"Starting web interface on {host}:{port}")
    print(f"Config file location: {DEFAULT_CONFIG_FILE}")
    
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    main()
