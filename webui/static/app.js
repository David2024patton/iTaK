// ===== iTaK Dashboard — app.js =====
const API = window.location.origin;
let ws = null;

// ==================== TAB SWITCHING ====================
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelector(`.tab-btn[data-tab="${tab}"]`).classList.add('active');
    document.getElementById(`tab-${tab}`).classList.add('active');
    if (tab === 'mission') loadTasks();
    if (tab === 'resources') loadResources();
}

// ==================== WEBSOCKET ====================
function connectWS() {
    const wsUrl = `${API.replace('http', 'ws')}/ws`;
    ws = new WebSocket(wsUrl);
    ws.onopen = () => {
        document.getElementById('statusDot').style.background = 'var(--accent-green)';
        document.getElementById('statusText').textContent = 'Connected';
        addLog('system', 'WebSocket connected');
    };
    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'progress') addLog(msg.event, JSON.stringify(msg.data).slice(0, 200));
            else if (msg.type === 'response') addChatMessage('agent', msg.content);
        } catch (e) { }
    };
    ws.onclose = () => {
        document.getElementById('statusDot').style.background = 'var(--accent-red)';
        document.getElementById('statusText').textContent = 'Disconnected';
        setTimeout(connectWS, 3000);
    };
    ws.onerror = () => {
        document.getElementById('statusDot').style.background = 'var(--accent-amber)';
        document.getElementById('statusText').textContent = 'Error';
    };
}

// ==================== STATS POLLING ====================
async function fetchStats() {
    try {
        const res = await fetch(`${API}/api/stats`);
        const data = await res.json();
        const uptime = Math.floor(data.uptime_seconds || 0);
        document.getElementById('statUptime').textContent = `${Math.floor(uptime / 3600)}h ${Math.floor((uptime % 3600) / 60)}m`;
        document.getElementById('statTools').textContent = data.tools_loaded || 0;
        document.getElementById('statIterations').textContent = data.total_iterations || 0;
        const budget = data.rate_limiter?.budget_remaining;
        document.getElementById('statBudget').textContent = budget != null ? `$${budget}` : 'N/A';
        const mem = data.memory || {};
        document.getElementById('memMarkdown').textContent = mem.layer_1_files || 0;
        document.getElementById('memSqlite').textContent = (mem.layer_2_sqlite || {}).total_memories || 0;
        document.getElementById('memNeo4j').textContent = mem.layer_3_neo4j || '--';
        const wv = mem.layer_4_weaviate;
        document.getElementById('memWeaviate').textContent =
            typeof wv === 'object' ? (wv.total_memories || wv.status || '--') : (wv || '--');
    } catch (e) {
        document.getElementById('statusDot').style.background = 'var(--accent-amber)';
    }
}

// ==================== LOG STREAM ====================
function addLog(type, data) {
    const stream = document.getElementById('logStream');
    const now = new Date();
    const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
    const typeClass = type.includes('error') ? 'error' : type.includes('tool') ? 'tool' : type.includes('user') ? 'user' : type.includes('agent') ? 'agent' : 'system';
    const el = document.createElement('div');
    el.className = 'log-entry';
    el.innerHTML = `<span class="log-time">${time}</span><span class="log-type ${typeClass}">${type}</span><span class="log-data">${data}</span>`;
    stream.appendChild(el);
    stream.scrollTop = stream.scrollHeight;
    if (stream.children.length > 200) stream.removeChild(stream.firstChild);
}

// ==================== CHAT ====================
function addChatMessage(role, content) {
    const container = document.getElementById('chatMessages');
    const el = document.createElement('div');
    el.className = `chat-msg ${role}`;
    el.textContent = content;
    container.appendChild(el);
    container.scrollTop = container.scrollHeight;
}

async function sendChat() {
    const input = document.getElementById('chatInput');
    const btn = document.getElementById('chatSendBtn');
    const msg = input.value.trim();
    if (!msg) return;
    addChatMessage('user', msg);
    input.value = '';
    btn.disabled = true;
    try {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'chat', message: msg }));
        } else {
            const res = await fetch(`${API}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg }),
            });
            const data = await res.json();
            addChatMessage('agent', data.response || data.error || 'No response');
        }
    } catch (e) { addChatMessage('agent', '❌ Connection error'); }
    btn.disabled = false;
}

// ==================== MEMORY SEARCH ====================
async function searchMemory() {
    const input = document.getElementById('memoryInput');
    const query = input.value.trim();
    if (!query) return;
    const container = document.getElementById('memoryResults');
    container.innerHTML = '<div style="color:var(--text-muted);padding:12px;">Searching...</div>';
    try {
        const res = await fetch(`${API}/api/memory/search?query=${encodeURIComponent(query)}&limit=10`);
        const data = await res.json();
        if (!data.results || data.results.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted);padding:12px;">No results found.</div>';
            return;
        }
        container.innerHTML = data.results.map(r => `
            <div class="memory-item">
                <div class="memory-item-cat">${r.category || 'general'}</div>
                <div class="memory-item-content">${(r.content || '').slice(0, 300)}</div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<div style="color:var(--accent-red);padding:12px;">Search failed.</div>';
    }
}

// ======================================================
//             MISSION CONTROL — KANBAN BOARD
// ======================================================

function timeAgo(ts) {
    const diff = (Date.now() / 1000) - ts;
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

function renderTaskCard(task) {
    const card = document.createElement('div');
    card.className = 'task-card';
    card.draggable = true;
    card.dataset.taskId = task.id;
    card.ondragstart = (e) => {
        e.dataTransfer.setData('text/plain', task.id);
        card.classList.add('dragging');
    };
    card.ondragend = () => card.classList.remove('dragging');

    const stepsInfo = task.steps && task.steps.length > 0
        ? `<span>📐 ${task.steps.filter(s => s.status === 'done').length}/${task.steps.length}</span>` : '';

    card.innerHTML = `
        <div class="task-card-actions">
            <button class="task-delete-btn" onclick="deleteTask('${task.id}')" title="Delete">✕</button>
        </div>
        <div class="task-card-title">${task.title || 'Untitled'}</div>
        ${task.description ? `<div class="task-card-desc">${task.description}</div>` : ''}
        <div class="task-card-meta">
            <span class="task-priority ${task.priority}">${task.priority}</span>
            ${stepsInfo}
            <span class="task-card-id">#${task.id}</span>
        </div>
        <div class="task-card-meta" style="margin-top:6px;">
            <span class="task-card-source">via ${task.source}</span>
            <span>${timeAgo(task.created_at)}</span>
        </div>
    `;
    return card;
}

async function loadTasks() {
    try {
        const res = await fetch(`${API}/api/tasks?limit=100`);
        const data = await res.json();
        const tasks = data.tasks || [];

        const columns = { inbox: [], in_progress: [], review: [], done: [] };
        tasks.forEach(t => {
            if (columns[t.status]) columns[t.status].push(t);
            else if (t.status === 'failed') columns.inbox.push(t); // show failed in inbox
        });

        // Sort by priority
        const priOrder = { critical: 0, high: 1, medium: 2, low: 3 };
        Object.values(columns).forEach(col => col.sort((a, b) => (priOrder[a.priority] || 2) - (priOrder[b.priority] || 2)));

        // Render columns
        ['inbox', 'in_progress', 'review', 'done'].forEach(status => {
            const container = document.getElementById(`col-${status}`);
            container.innerHTML = '';
            const col = columns[status];
            document.getElementById(`colCount-${status}`).textContent = col.length;

            if (col.length === 0) {
                container.innerHTML = '<div class="kanban-empty">No tasks</div>';
            } else {
                col.forEach(t => container.appendChild(renderTaskCard(t)));
            }
        });

        // Update stats bar
        document.getElementById('mcTotal').textContent = tasks.length;
        document.getElementById('mcInbox').textContent = columns.inbox.length;
        document.getElementById('mcProgress').textContent = columns.in_progress.length;
        document.getElementById('mcReview').textContent = columns.review.length;
        document.getElementById('mcDone').textContent = columns.done.length;

    } catch (e) {
        console.error('Failed to load tasks:', e);
    }
}

// ===== Drag & Drop =====
function allowDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
}

document.addEventListener('dragleave', (e) => {
    if (e.target.classList) e.target.classList.remove('drag-over');
});

async function dropTask(e, newStatus) {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    const taskId = e.dataTransfer.getData('text/plain');
    if (!taskId) return;
    try {
        await fetch(`${API}/api/tasks/${taskId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus }),
        });
        loadTasks();
    } catch (e) { console.error('Failed to move task:', e); }
}

// ===== Task CRUD =====
function openNewTaskModal() {
    document.getElementById('newTaskModal').classList.add('open');
    document.getElementById('newTaskTitle').focus();
}

function closeModal(e) {
    if (e && e.target !== e.currentTarget) return;
    document.getElementById('newTaskModal').classList.remove('open');
}

async function createTask(e) {
    e.preventDefault();
    const title = document.getElementById('newTaskTitle').value.trim();
    const description = document.getElementById('newTaskDesc').value.trim();
    const priority = document.getElementById('newTaskPriority').value;
    if (!title) return;
    try {
        await fetch(`${API}/api/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description, priority }),
        });
        document.getElementById('newTaskTitle').value = '';
        document.getElementById('newTaskDesc').value = '';
        document.getElementById('newTaskPriority').value = 'medium';
        closeModal();
        loadTasks();
    } catch (e) { console.error('Failed to create task:', e); }
}

async function deleteTask(taskId) {
    if (!confirm('Delete this task?')) return;
    try {
        await fetch(`${API}/api/tasks/${taskId}`, { method: 'DELETE' });
        loadTasks();
    } catch (e) { console.error('Failed to delete task:', e); }
}

// ===== Keyboard shortcuts =====
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
        closeResourceModal();
    }
});

// ======================================================
//             RESOURCES TAB - SKILLS, TOOLS, MCPs
// ======================================================

let currentResourceType = 'skills';
let currentEditingResource = null;

function switchResourceType(type) {
    currentResourceType = type;
    document.querySelectorAll('.resource-type-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.resource-section').forEach(s => s.classList.remove('active'));
    document.querySelector(`.resource-type-btn[data-type="${type}"]`).classList.add('active');
    document.getElementById(`section-${type}`).classList.add('active');
    loadResourceType(type);
}

function loadResources() {
    loadResourceType(currentResourceType);
}

async function loadResourceType(type) {
    if (type === 'skills') await loadSkills();
    else if (type === 'tools') await loadTools();
    else if (type === 'mcps') await loadMCPs();
}

// ===== SKILLS =====
async function loadSkills() {
    const container = document.getElementById('skillsList');
    container.innerHTML = '<div class="resource-loading">Loading skills...</div>';
    try {
        const res = await fetch(`${API}/api/resources/skills`);
        const data = await res.json();
        const skills = data.skills || [];
        if (skills.length === 0) {
            container.innerHTML = '<div class="resource-loading">No skills found. Create your first skill!</div>';
            return;
        }
        container.innerHTML = skills.map(skill => `
            <div class="resource-item" onclick="editSkill('${skill.name}')">
                <div class="resource-item-header">
                    <div class="resource-item-name">📚 ${skill.title || skill.name}</div>
                    <div class="resource-item-actions">
                        <button class="resource-item-btn delete" onclick="event.stopPropagation(); deleteSkill('${skill.name}')">Delete</button>
                    </div>
                </div>
                <div class="resource-item-meta">
                    <span>📄 ${skill.filename}</span>
                    <span>${(skill.size / 1024).toFixed(1)} KB</span>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<div class="resource-loading">Failed to load skills.</div>';
        console.error('Failed to load skills:', e);
    }
}

async function editSkill(name) {
    try {
        const res = await fetch(`${API}/api/resources/skills/${name}`);
        const data = await res.json();
        currentEditingResource = { type: 'skill', name: name };
        showResourceEditor('Edit Skill: ' + name, data.content, false);
    } catch (e) {
        console.error('Failed to load skill:', e);
    }
}

async function deleteSkill(name) {
    if (!confirm(`Delete skill "${name}"?`)) return;
    try {
        await fetch(`${API}/api/resources/skills/${name}`, { method: 'DELETE' });
        loadSkills();
    } catch (e) {
        console.error('Failed to delete skill:', e);
    }
}

// ===== TOOLS =====
async function loadTools() {
    const container = document.getElementById('toolsList');
    container.innerHTML = '<div class="resource-loading">Loading tools...</div>';
    try {
        const res = await fetch(`${API}/api/resources/tools`);
        const data = await res.json();
        const tools = data.tools || [];
        if (tools.length === 0) {
            container.innerHTML = '<div class="resource-loading">No tools found.</div>';
            return;
        }
        container.innerHTML = tools.map(tool => `
            <div class="resource-item" onclick="editTool('${tool.name}')">
                <div class="resource-item-header">
                    <div class="resource-item-name">🔧 ${tool.name}</div>
                    <div class="resource-item-actions">
                        <button class="resource-item-btn delete" onclick="event.stopPropagation(); deleteTool('${tool.name}')">Delete</button>
                    </div>
                </div>
                <div class="resource-item-desc">${tool.description || 'No description'}</div>
                <div class="resource-item-meta">
                    <span>📄 ${tool.filename}</span>
                    <span>${(tool.size / 1024).toFixed(1)} KB</span>
                    <span>${tool.has_prompt ? '✓ Has prompt' : '⚠️ No prompt'}</span>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<div class="resource-loading">Failed to load tools.</div>';
        console.error('Failed to load tools:', e);
    }
}

async function editTool(name) {
    try {
        const res = await fetch(`${API}/api/resources/tools/${name}`);
        const data = await res.json();
        currentEditingResource = { type: 'tool', name: name };
        showToolEditor('Edit Tool: ' + name, data.code, data.prompt);
    } catch (e) {
        console.error('Failed to load tool:', e);
    }
}

async function deleteTool(name) {
    if (!confirm(`Delete tool "${name}"?`)) return;
    try {
        await fetch(`${API}/api/resources/tools/${name}`, { method: 'DELETE' });
        loadTools();
    } catch (e) {
        console.error('Failed to delete tool:', e);
    }
}

// ===== MCPs =====
async function loadMCPs() {
    const container = document.getElementById('mcpsList');
    container.innerHTML = '<div class="resource-loading">Loading MCP servers...</div>';
    try {
        const res = await fetch(`${API}/api/resources/mcps`);
        const data = await res.json();
        const mcps = data.mcps || [];
        if (mcps.length === 0) {
            container.innerHTML = '<div class="resource-loading">No MCP servers configured. Add them in config.json.</div>';
            return;
        }
        container.innerHTML = mcps.map(mcp => `
            <div class="resource-item">
                <div class="resource-item-header">
                    <div class="resource-item-name">🔌 ${mcp.name}</div>
                    <span class="mcp-status ${mcp.connected ? 'connected' : 'disconnected'}">
                        ${mcp.connected ? 'Connected' : 'Disconnected'}
                    </span>
                </div>
                <div class="resource-item-meta">
                    <span>${mcp.tool_count} tools available</span>
                </div>
                ${mcp.tools && mcp.tools.length > 0 ? `
                    <div class="mcp-tools-list">
                        ${mcp.tools.slice(0, 5).map(t => `
                            <div class="mcp-tool-item">🔧 ${t.name}${t.description ? ': ' + t.description.slice(0, 80) : ''}</div>
                        `).join('')}
                        ${mcp.tools.length > 5 ? `<div class="mcp-tool-item">... and ${mcp.tools.length - 5} more</div>` : ''}
                    </div>
                ` : ''}
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<div class="resource-loading">Failed to load MCP servers.</div>';
        console.error('Failed to load MCPs:', e);
    }
}

// ===== RESOURCE MODALS =====
function openNewResourceModal(type) {
    currentEditingResource = { type: type, name: null };
    if (type === 'skill') {
        showResourceEditor('Create New Skill', '# Skill: New Skill\nCategory: general\nTags: [tag1, tag2]\n\n## When to Use\n\n## Steps\n\n## Examples\n', true);
    } else if (type === 'tool') {
        const template = `"""
iTaK Tool: New Tool - Description here.
"""

from tools.base import BaseTool, ToolResult


class NewTool(BaseTool):
    """Tool description for LLM."""

    name = "new_tool"
    description = "Short description"

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        return ToolResult(output="Result here")
`;
        const promptTemplate = `# Tool: new_tool

## When to Use

## Arguments

## Examples
`;
        showToolEditor('Create New Tool', template, promptTemplate);
    }
}

function showResourceEditor(title, content, isNew) {
    document.getElementById('resourceModalTitle').textContent = title;
    const modalContent = document.getElementById('resourceModalContent');
    modalContent.innerHTML = `
        <div class="editor-container">
            ${isNew ? `
                <div>
                    <label class="form-label">Name</label>
                    <input type="text" class="form-input" id="resourceName" placeholder="resource_name" required>
                </div>
            ` : ''}
            <div>
                <label class="form-label">Content</label>
                <textarea class="editor-textarea" id="resourceContent">${content || ''}</textarea>
            </div>
            <div class="editor-actions">
                <button class="chat-btn" onclick="closeResourceModal()">Cancel</button>
                <button class="chat-btn" onclick="saveResource()">${isNew ? 'Create' : 'Save'}</button>
            </div>
        </div>
    `;
    document.getElementById('resourceModal').classList.add('open');
}

function showToolEditor(title, code, prompt) {
    document.getElementById('resourceModalTitle').textContent = title;
    const modalContent = document.getElementById('resourceModalContent');
    const isNew = currentEditingResource.name === null;
    modalContent.innerHTML = `
        <div class="editor-container">
            ${isNew ? `
                <div>
                    <label class="form-label">Tool Name (e.g., my_tool)</label>
                    <input type="text" class="form-input" id="toolName" placeholder="my_tool" required>
                </div>
            ` : ''}
            <div class="tool-editor-split">
                <div class="editor-section">
                    <label>Python Code</label>
                    <textarea class="editor-textarea" id="toolCode">${code || ''}</textarea>
                </div>
                <div class="editor-section">
                    <label>Prompt (optional)</label>
                    <textarea class="editor-textarea" id="toolPrompt">${prompt || ''}</textarea>
                </div>
            </div>
            <div class="editor-actions">
                <button class="chat-btn" onclick="closeResourceModal()">Cancel</button>
                <button class="chat-btn" onclick="saveTool()">${isNew ? 'Create' : 'Save'}</button>
            </div>
        </div>
    `;
    document.getElementById('resourceModal').classList.add('open');
}

function closeResourceModal(e) {
    if (e && e.target !== e.currentTarget) return;
    document.getElementById('resourceModal').classList.remove('open');
    currentEditingResource = null;
}

async function saveResource() {
    const content = document.getElementById('resourceContent').value;
    if (currentEditingResource.type === 'skill') {
        const name = currentEditingResource.name || document.getElementById('resourceName')?.value;
        if (!name) {
            alert('Please enter a skill name');
            return;
        }
        try {
            const method = currentEditingResource.name ? 'PUT' : 'POST';
            const url = currentEditingResource.name 
                ? `${API}/api/resources/skills/${name}`
                : `${API}/api/resources/skills`;
            await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, content }),
            });
            closeResourceModal();
            loadSkills();
        } catch (e) {
            alert('Failed to save skill: ' + e.message);
        }
    }
}

async function saveTool() {
    const code = document.getElementById('toolCode').value;
    const prompt = document.getElementById('toolPrompt').value;
    const name = currentEditingResource.name || document.getElementById('toolName')?.value;
    if (!name) {
        alert('Please enter a tool name');
        return;
    }
    try {
        const method = currentEditingResource.name ? 'PUT' : 'POST';
        const url = currentEditingResource.name 
            ? `${API}/api/resources/tools/${name}`
            : `${API}/api/resources/tools`;
        await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, code, prompt }),
        });
        closeResourceModal();
        loadTools();
    } catch (e) {
        alert('Failed to save tool: ' + e.message);
    }
}

// ==================== INIT ====================
document.getElementById('chatInput').addEventListener('keydown', (e) => { if (e.key === 'Enter') sendChat(); });
document.getElementById('memoryInput').addEventListener('keydown', (e) => { if (e.key === 'Enter') searchMemory(); });

connectWS();
fetchStats();
setInterval(fetchStats, 10000);

// Fetch initial logs
fetch(`${API}/api/logs?limit=20`).then(r => r.json()).then(data => {
    if (data.logs) {
        data.logs.reverse().forEach(log => {
            addLog(log.event_type || 'system', typeof log.data === 'string' ? log.data : JSON.stringify(log.data).slice(0, 200));
        });
    }
}).catch(() => { });
