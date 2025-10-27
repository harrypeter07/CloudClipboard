from fastapi import FastAPI, HTTPException, Form, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
import logging
from database import init_db, rooms_collection, users_collection, clipboard_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def create_web_routes(app: FastAPI):
    """Add comprehensive web routes to the FastAPI app"""
    
    @app.get("/", response_class=HTMLResponse)
    async def web_dashboard():
        """Main web dashboard for CloudClipboard with room-based viewing and upload features"""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CloudClipboard - Cross-Device Clipboard Sync</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    overflow: hidden;
                }
                
                .header {
                    background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }
                
                .header h1 {
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }
                
                .header p {
                    font-size: 1.2em;
                    opacity: 0.9;
                }
                
                .tabs {
                    display: flex;
                    background: #f8f9fa;
                    border-bottom: 1px solid #e9ecef;
                }
                
                .tab {
                    flex: 1;
                    padding: 15px 20px;
                    background: #e9ecef;
                    border: none;
                    cursor: pointer;
                    font-size: 16px;
                    transition: background 0.3s;
                }
                
                .tab.active {
                    background: white;
                    border-bottom: 3px solid #3498db;
                }
                
                .tab:hover {
                    background: #dee2e6;
                }
                
                .tab-content {
                    display: none;
                    padding: 30px;
                }
                
                .tab-content.active {
                    display: block;
                }
                
                .room-input {
                    display: flex;
                    gap: 15px;
                    align-items: center;
                    justify-content: center;
                    flex-wrap: wrap;
                    margin-bottom: 30px;
                }
                
                .room-input input {
                    padding: 12px 20px;
                    border: 2px solid #e9ecef;
                    border-radius: 8px;
                    font-size: 16px;
                    min-width: 200px;
                    transition: border-color 0.3s;
                }
                
                .room-input input:focus {
                    outline: none;
                    border-color: #3498db;
                }
                
                .room-input button {
                    background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                    color: white;
                    border: none;
                    padding: 12px 25px;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: transform 0.2s;
                }
                
                .room-input button:hover {
                    transform: translateY(-2px);
                }
                
                .upload-section {
                    background: #f8f9fa;
                    padding: 25px;
                    border-radius: 12px;
                    margin-bottom: 30px;
                    border: 2px dashed #dee2e6;
                }
                
                .upload-section h3 {
                    margin-bottom: 20px;
                    color: #2c3e50;
                }
                
                .upload-form {
                    display: grid;
                    gap: 15px;
                }
                
                .upload-form input, .upload-form textarea {
                    padding: 12px;
                    border: 2px solid #e9ecef;
                    border-radius: 8px;
                    font-size: 14px;
                }
                
                .upload-form textarea {
                    min-height: 100px;
                    resize: vertical;
                }
                
                .upload-form button {
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                    border: none;
                    padding: 12px 25px;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: transform 0.2s;
                }
                
                .upload-form button:hover {
                    transform: translateY(-2px);
                }
                
                .stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                
                .stat-card {
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 25px;
                    border-radius: 12px;
                    text-align: center;
                    border: 1px solid #dee2e6;
                }
                
                .stat-card h3 {
                    font-size: 2.5em;
                    color: #2c3e50;
                    margin-bottom: 10px;
                }
                
                .stat-card p {
                    color: #6c757d;
                    font-size: 1.1em;
                }
                
                .loading {
                    text-align: center;
                    padding: 50px;
                    font-size: 1.2em;
                    color: #6c757d;
                }
                
                .error {
                    background: #f8d7da;
                    color: #721c24;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    margin: 20px 0;
                }
                
                .success {
                    background: #d4edda;
                    color: #155724;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    margin: 20px 0;
                }
                
                .no-data {
                    text-align: center;
                    padding: 50px;
                    color: #6c757d;
                }
                
                .no-data h3 {
                    margin-bottom: 15px;
                    font-size: 1.5em;
                }
                
                .clipboard-items {
                    display: grid;
                    gap: 20px;
                }
                
                .item-card {
                    background: white;
                    border: 1px solid #e9ecef;
                    border-radius: 12px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    transition: transform 0.2s, box-shadow 0.2s;
                }
                
                .item-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                }
                
                .item-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                }
                
                .item-type {
                    background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                    color: white;
                    padding: 5px 12px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    font-weight: bold;
                }
                
                .item-time {
                    color: #6c757d;
                    font-size: 0.9em;
                }
                
                .item-user {
                    color: #2c3e50;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                
                .item-content {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                    font-family: 'Courier New', monospace;
                    white-space: pre-wrap;
                    word-break: break-word;
                }
                
                .item-image {
                    max-width: 100%;
                    max-height: 300px;
                    border-radius: 8px;
                    margin-top: 10px;
                }
                
                .copy-btn {
                    background: #6c757d;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 12px;
                    margin-top: 10px;
                }
                
                .copy-btn:hover {
                    background: #5a6268;
                }
                
                @media (max-width: 768px) {
                    .room-input {
                        flex-direction: column;
                    }
                    
                    .room-input input {
                        min-width: 100%;
                    }
                    
                    .stats {
                        grid-template-columns: repeat(2, 1fr);
                    }
                    
                    .tabs {
                        flex-direction: column;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>☁️ CloudClipboard</h1>
                    <p>Cross-Device Clipboard Synchronization Platform</p>
                </div>
                
                <div class="tabs">
                    <button class="tab active" onclick="showTab('view')">📊 View Room Data</button>
                    <button class="tab" onclick="showTab('upload')">📤 Upload Content</button>
                    <button class="tab" onclick="showTab('help')">❓ Help & Instructions</button>
                </div>
                
                <div id="view" class="tab-content active">
                    <div class="room-input">
                        <input type="text" id="roomId" placeholder="Enter Room ID (or 'hassan' for all data)" />
                        <button onclick="loadRoomData()">📊 Load Room Data</button>
                        <button onclick="toggleAutoRefresh()" id="autoRefreshBtn">⏸️ Auto Refresh OFF</button>
                    </div>
                    
                    <div id="stats" class="stats" style="display: none;">
                        <div class="stat-card">
                            <h3 id="totalItems">0</h3>
                            <p>Total Items</p>
                        </div>
                        <div class="stat-card">
                            <h3 id="totalUsers">0</h3>
                            <p>Active Users</p>
                        </div>
                        <div class="stat-card">
                            <h3 id="textItems">0</h3>
                            <p>Text Items</p>
                        </div>
                        <div class="stat-card">
                            <h3 id="fileItems">0</h3>
                            <p>File Items</p>
                        </div>
                    </div>
                    
                    <div id="content">
                        <div class="no-data">
                            <h3>🔍 Enter a Room ID to view data</h3>
                            <p>Use the input field above to load clipboard data for any room</p>
                        </div>
                    </div>
                </div>
                
                <div id="upload" class="tab-content">
                    <div class="upload-section">
                        <h3>📤 Upload Content to Room</h3>
                        <form class="upload-form" id="uploadForm">
                            <input type="text" id="uploadRoomId" placeholder="Room ID" required>
                            <input type="text" id="uploadUsername" placeholder="Your Username" required>
                            <textarea id="uploadText" placeholder="Enter text content to upload..."></textarea>
                            <input type="file" id="uploadFile" accept="image/*,.txt,.pdf,.doc,.docx">
                            <button type="submit">📤 Upload Content</button>
                        </form>
                    </div>
                    <div id="uploadResult"></div>
                </div>
                
                <div id="help" class="tab-content">
                    <div style="padding: 20px;">
                        <h3>🚀 How to Use CloudClipboard</h3>
                        <div style="margin: 20px 0;">
                            <h4>📱 Desktop App Features:</h4>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                <li><strong>Ctrl+Shift+V:</strong> Show overlay with recent clipboard items</li>
                                <li><strong>Ctrl+7:</strong> Toggle ghost mode (secret copying)</li>
                                <li><strong>Ctrl+Shift+7:</strong> Paste last item from database</li>
                            </ul>
                        </div>
                        <div style="margin: 20px 0;">
                            <h4>🌐 Web Interface Features:</h4>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                <li><strong>View Room Data:</strong> Enter Room ID to see all clipboard items</li>
                                <li><strong>Upload Content:</strong> Add text or images to any room</li>
                                <li><strong>Cross-Device Sync:</strong> Items uploaded here appear in desktop app</li>
                            </ul>
                        </div>
                        <div style="margin: 20px 0;">
                            <h4>🔄 Synchronization:</h4>
                            <p>When you copy something on one device, it automatically syncs to all other devices in the same room. Use Ctrl+V on any device to paste the latest content.</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                let currentRoomId = '';
                let autoRefreshInterval = null;
                
                function toggleAutoRefresh() {
                    const btn = document.getElementById('autoRefreshBtn');
                    if (autoRefreshInterval) {
                        clearInterval(autoRefreshInterval);
                        autoRefreshInterval = null;
                        btn.textContent = '⏸️ Auto Refresh OFF';
                        btn.style.backgroundColor = '#6c757d';
                    } else {
                        if (currentRoomId) {
                            autoRefreshInterval = setInterval(() => {
                                loadRoomData();
                            }, 5000); // Refresh every 5 seconds
                            btn.textContent = '▶️ Auto Refresh ON';
                            btn.style.backgroundColor = '#28a745';
                        } else {
                            alert('Please load room data first');
                        }
                    }
                }
                
                function showTab(tabName) {
                    // Hide all tab contents
                    document.querySelectorAll('.tab-content').forEach(content => {
                        content.classList.remove('active');
                    });
                    
                    // Remove active class from all tabs
                    document.querySelectorAll('.tab').forEach(tab => {
                        tab.classList.remove('active');
                    });
                    
                    // Show selected tab content
                    document.getElementById(tabName).classList.add('active');
                    
                    // Add active class to clicked tab
                    event.target.classList.add('active');
                }
                
                async function loadRoomData() {
                    const roomId = document.getElementById('roomId').value.trim();
                    if (!roomId) {
                        alert('Please enter a Room ID');
                        return;
                    }
                    
                    currentRoomId = roomId;
                    const contentDiv = document.getElementById('content');
                    contentDiv.innerHTML = '<div class="loading">🔄 Loading room data...</div>';
                    
                    try {
                        // Load room info
                        const roomResponse = await fetch(`/api/room/info/${roomId}`);
                        if (!roomResponse.ok) {
                            throw new Error('Room not found or access denied');
                        }
                        const roomData = await roomResponse.json();
                        
                        // Load clipboard history
                        const historyResponse = await fetch(`/api/clipboard/history/${roomId}`);
                        const historyData = await historyResponse.ok ? await historyResponse.json() : { items: [] };
                        
                        // Update stats
                        document.getElementById('totalItems').textContent = roomData.total_items || 0;
                        document.getElementById('totalUsers').textContent = roomData.members?.length || 0;
                        document.getElementById('textItems').textContent = historyData.items?.filter(item => item.type === 'text').length || 0;
                        document.getElementById('fileItems').textContent = historyData.items?.filter(item => item.type !== 'text').length || 0;
                        document.getElementById('stats').style.display = 'grid';
                        
                        // Display items
                        displayItems(historyData.items || []);
                        
                    } catch (error) {
                        contentDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                    }
                }
                
                function displayItems(items) {
                    const contentDiv = document.getElementById('content');
                    
                    if (items.length === 0) {
                        contentDiv.innerHTML = '<div class="no-data"><h3>📭 No clipboard items found</h3><p>This room has no clipboard history yet</p></div>';
                        return;
                    }
                    
                    let html = '<div class="clipboard-items">';
                    
                    items.forEach(item => {
                        const typeIcon = {
                            'text': '📝',
                            'image': '🖼️',
                            'file': '📄',
                            'folder': '📁'
                        }[item.type] || '📋';
                        
                        let content = '';
                        if (item.type === 'text') {
                            content = item.content.substring(0, 200) + (item.content.length > 200 ? '...' : '');
                        } else if (item.type === 'image') {
                            // Display base64 image directly
                            const mimeType = item.metadata?.mime_type || 'image/png';
                            content = `<img src="data:${mimeType};base64,${item.content}" class="item-image" alt="Uploaded image">`;
                        } else {
                            content = `${item.type.toUpperCase()}: ${item.filename || 'Unknown'}`;
                        }
                        
                        html += `
                            <div class="item-card">
                                <div class="item-header">
                                    <span class="item-type">${typeIcon} ${item.type.toUpperCase()}</span>
                                    <span class="item-time">${new Date(item.timestamp).toLocaleString()}</span>
                                </div>
                                <div class="item-user">👤 ${item.username}</div>
                                <div class="item-content">${content}</div>
                                <button class="copy-btn" onclick="copyItem('${item.id}', '${item.type}')">📋 Copy to Clipboard</button>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                    contentDiv.innerHTML = html;
                }
                
            async function copyItem(itemId, itemType) {
                try {
                    const response = await fetch(`/api/clipboard/download/${itemId}`);
                    if (response.ok) {
                        if (itemType === 'text') {
                            const data = await response.json();
                            await navigator.clipboard.writeText(data.content);
                            alert('✅ Text copied to clipboard!');
                        } else if (itemType === 'image') {
                            // For images, copy the base64 data URL
                            const blob = await response.blob();
                            const reader = new FileReader();
                            reader.onload = function() {
                                navigator.clipboard.writeText(reader.result);
                                alert('✅ Image data URL copied to clipboard!');
                            };
                            reader.readAsDataURL(blob);
                        } else {
                            // For files, copy the URL
                            const blob = await response.blob();
                            await navigator.clipboard.writeText(window.location.origin + `/api/clipboard/download/${itemId}`);
                            alert('✅ File URL copied to clipboard!');
                        }
                    } else {
                        alert('❌ Failed to copy item');
                    }
                } catch (error) {
                    alert('❌ Error copying item: ' + error.message);
                }
            }
                
                // Upload form handling
                document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const roomId = document.getElementById('uploadRoomId').value.trim();
                    const username = document.getElementById('uploadUsername').value.trim();
                    const textContent = document.getElementById('uploadText').value.trim();
                    const fileInput = document.getElementById('uploadFile');
                    const resultDiv = document.getElementById('uploadResult');
                    
                    if (!roomId || !username) {
                        resultDiv.innerHTML = '<div class="error">❌ Please fill in Room ID and Username</div>';
                        return;
                    }
                    
                    if (!textContent && !fileInput.files[0]) {
                        resultDiv.innerHTML = '<div class="error">❌ Please enter text or select a file</div>';
                        return;
                    }
                    
                    try {
                        if (textContent) {
                            // Upload text
                            const response = await fetch('/api/clipboard/text', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    room_id: roomId,
                                    username: username,
                                    content: textContent
                                })
                            });
                            
                            if (response.ok) {
                                resultDiv.innerHTML = '<div class="success">✅ Text uploaded successfully!</div>';
                                document.getElementById('uploadText').value = '';
                            } else {
                                throw new Error('Failed to upload text');
                            }
                        }
                        
                        if (fileInput.files[0]) {
                            // Upload file/image
                            const formData = new FormData();
                            formData.append('room_id', roomId);
                            formData.append('username', username);
                            formData.append('file', fileInput.files[0]);
                            
                            const endpoint = fileInput.files[0].type.startsWith('image/') ? '/api/clipboard/image' : '/api/clipboard/file';
                            const response = await fetch(endpoint, {
                                method: 'POST',
                                body: formData
                            });
                            
                            if (response.ok) {
                                resultDiv.innerHTML = '<div class="success">✅ File uploaded successfully!</div>';
                                fileInput.value = '';
                            } else {
                                throw new Error('Failed to upload file');
                            }
                        }
                        
                        // Auto-refresh room data if viewing the same room
                        if (currentRoomId === roomId) {
                            setTimeout(() => loadRoomData(), 1000);
                        }
                        
                    } catch (error) {
                        resultDiv.innerHTML = `<div class="error">❌ Upload failed: ${error.message}</div>`;
                    }
                });
                
                // Allow Enter key to load data
                document.getElementById('roomId').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        loadRoomData();
                    }
                });
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
