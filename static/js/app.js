const CATEGORY_NAMES = {
    'internal': '内部服务',
    'external': '外部服务',
    'database': '数据库',
    'middleware': '中间件',
    'monitoring': '监控服务',
    'consul': 'Consul服务',
    'other': '其他'
};

let resources = [];
let consulEnabled = false;

async function init() {
    await checkConsulStatus();
    await loadStats();
    await loadFilters();
    await loadResources();
    setupEventListeners();
}

async function checkConsulStatus() {
    try {
        const response = await fetch('/api/consul/status');
        const result = await response.json();
        if (result.success && result.data.enabled) {
            consulEnabled = true;
            document.getElementById('syncFromConsulBtn').style.display = 'inline-flex';
            document.getElementById('syncToConsulBtn').style.display = 'inline-flex';
        }
    } catch (e) {
        console.log('Consul not available');
    }
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const result = await response.json();
        if (result.success) {
            const stats = result.data;
            document.getElementById('statTotal').textContent = stats.total;
            document.getElementById('statOnline').textContent = stats.online;
            document.getElementById('statOffline').textContent = stats.offline;
            document.getElementById('statAvgTime').textContent = stats.avg_response_time > 0 
                ? stats.avg_response_time.toFixed(0) + 'ms' 
                : '-';
        }
    } catch (e) {
        console.error('Failed to load stats');
    }
}

async function loadFilters() {
    try {
        const [catResponse, groupResponse] = await Promise.all([
            fetch('/api/categories'),
            fetch('/api/groups')
        ]);
        const catResult = await catResponse.json();
        const groupResult = await groupResponse.json();
        const categoryFilter = document.getElementById('categoryFilter');
        catResult.data.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = CATEGORY_NAMES[cat] || cat;
            categoryFilter.appendChild(option);
        });
        const groupFilter = document.getElementById('groupFilter');
        groupResult.data.forEach(group => {
            const option = document.createElement('option');
            option.value = group;
            option.textContent = group;
            groupFilter.appendChild(option);
        });
    } catch (e) {
        console.error('Failed to load filters');
    }
}

async function loadResources() {
    const category = document.getElementById('categoryFilter').value;
    const group = document.getElementById('groupFilter').value;
    const search = document.getElementById('searchInput').value;
    let url = '/api/resources?';
    if (category) url += `category=${encodeURIComponent(category)}&`;
    if (group) url += `group=${encodeURIComponent(group)}&`;
    if (search) url += `search=${encodeURIComponent(search)}&`;
    try {
        const response = await fetch(url);
        const result = await response.json();
        if (result.success) {
            resources = result.data;
            renderResources();
        }
    } catch (e) {
        console.error('Failed to load resources');
        document.getElementById('resourcesGrid').innerHTML = '<div class="loading">加载失败</div>';
    }
}

function renderResources() {
    const grid = document.getElementById('resourcesGrid');
    if (resources.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i data-lucide="folder-open"></i>
                <p>暂无资源，点击右上角添加</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }
    grid.innerHTML = resources.map(resource => {
        const healthStatus = resource.health_status;
        let statusClass = 'status-unknown';
        let statusText = '未知';
        let checkTime = '';
        if (healthStatus) {
            if (healthStatus.status === 'online') {
                statusClass = 'status-online';
                statusText = '在线 ' + (healthStatus.response_time ? healthStatus.response_time.toFixed(0) + 'ms' : '');
            } else {
                statusClass = 'status-offline';
                statusText = '离线';
            }
            if (healthStatus.checked_at) {
                checkTime = formatTime(healthStatus.checked_at);
            }
        }
        const tags = resource.tags ? resource.tags.split(',').filter(t => t.trim()) : [];
        const consulBadge = resource.consul_enabled ? '<span class="tag tag-consul">已同步</span>' : '';
        return `
            <div class="resource-card" data-id="${resource.id}">
                <div class="resource-actions">
                    <button class="btn btn-sm" onclick="event.stopPropagation(); editResource(${resource.id})" title="编辑">
                        <i data-lucide="edit-2"></i>
                    </button>
                </div>
                <div class="resource-header">
                    <div class="resource-title">${escapeHtml(resource.name)}</div>
                    <span class="resource-category category-${resource.category}">${CATEGORY_NAMES[resource.category] || resource.category}</span>
                </div>
                <div class="resource-url">${escapeHtml(resource.url)}</div>
                ${resource.description ? `<div class="resource-description">${escapeHtml(resource.description)}</div>` : ''}
                <div class="resource-tags">${consulBadge}${tags.map(tag => `<span class="tag">${escapeHtml(tag.trim())}</span>`).join('')}</div>
                <div class="resource-footer">
                    <div class="resource-status ${statusClass}">
                        <span class="status-dot"></span>
                        <span>${statusText}</span>
                        ${checkTime ? `<span class="check-time">${checkTime}</span>` : ''}
                    </div>
                    <button class="btn btn-secondary btn-sm" onclick="openResource(${resource.id})">
                        <i data-lucide="external-link"></i>
                        访问
                    </button>
                </div>
            </div>
        `;
    }).join('');
    lucide.createIcons();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTime(datetimeStr) {
    if (!datetimeStr) return '';
    const date = new Date(datetimeStr.replace(' ', 'T') + ':00');
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return '刚刚';
    if (diff < 3600) return Math.floor(diff / 60) + '分钟前';
    if (diff < 86400) return Math.floor(diff / 3600) + '小时前';
    return datetimeStr;
}

function setupEventListeners() {
    document.getElementById('addBtn').addEventListener('click', () => {
        window.location.href = '/add';
    });
    document.getElementById('syncToConsulBtn').addEventListener('click', syncToConsul);
    document.getElementById('syncFromConsulBtn').addEventListener('click', syncFromConsul);
    document.getElementById('searchInput').addEventListener('input', debounce(loadResources, 300));
    document.getElementById('categoryFilter').addEventListener('change', loadResources);
    document.getElementById('groupFilter').addEventListener('change', loadResources);
    document.getElementById('resourcesGrid').addEventListener('click', (e) => {
        const card = e.target.closest('.resource-card');
        if (card && !e.target.closest('.btn') && !e.target.closest('.resource-actions')) {
            openResource(card.dataset.id);
        }
    });
}

function debounce(fn, delay) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn.apply(this, args), delay);
    };
}

function openResource(id) {
    const resource = resources.find(r => r.id === id);
    if (resource) {
        window.open(resource.url, '_blank');
    }
}

function editResource(id) {
    window.location.href = `/edit/${id}`;
}

async function syncToConsul() {
    const btn = document.getElementById('syncToConsulBtn');
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader"></i> 同步中...';
    lucide.createIcons();
    try {
        const response = await fetch('/api/consul/sync-to-consul', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        });
        const result = await response.json();
        if (result.success) {
            const msg = result.data.failed.length > 0 
                ? `成功同步 ${result.data.synced} 个，失败 ${result.data.failed.length} 个: ${result.data.failed.join(', ')}`
                : `成功同步 ${result.data.synced} 个服务到 Consul`;
            alert(msg);
            loadResources();
        } else {
            alert('同步失败: ' + result.error);
        }
    } catch (e) {
        alert('同步失败: ' + e.message);
    }
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="upload"></i> 同步到Consul';
    lucide.createIcons();
}

async function syncFromConsul() {
    const btn = document.getElementById('syncFromConsulBtn');
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader"></i> 导入中...';
    lucide.createIcons();
    try {
        const response = await fetch('/api/consul/sync-from-consul', {method: 'POST'});
        const result = await response.json();
        if (result.success) {
            alert(`成功从 Consul 导入 ${result.data.synced} 个服务`);
            loadResources();
            loadStats();
        } else {
            alert('导入失败: ' + result.error);
        }
    } catch (e) {
        alert('导入失败: ' + e.message);
    }
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="download"></i> 导入Consul';
    lucide.createIcons();
}

document.addEventListener('DOMContentLoaded', init);
