// Front-end dashboard utilities
document.addEventListener('DOMContentLoaded', () => {
    // Socket.io Connection
    const socket = io();
    const connectionDot = document.getElementById('connectionDot');
    const connectionText = document.getElementById('connectionText');

    socket.on('connect', () => {
        if (connectionDot) connectionDot.classList.add('online');
        if (connectionText) connectionText.textContent = 'Connected';
    });

    socket.on('disconnect', () => {
        if (connectionDot) connectionDot.classList.remove('online');
        if (connectionText) connectionText.textContent = 'Offline';
    });

    socket.on('dashboard_update', (data) => {
        // Trigger live refresh
        if (data.stats) {
            updateStats(data.stats);
        }
        if (data.log) {
            prependLog(data.log);
        }
    });

    // Client-side search filters
    const searchBar = document.getElementById('tableSearch');
    if (searchBar) {
        searchBar.addEventListener('keyup', (e) => {
            const term = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('table tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }
});

// Toast System
function showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    
    // Border colors
    if (type === 'success') toast.style.borderLeftColor = 'var(--accent-emerald)';
    if (type === 'danger') toast.style.borderLeftColor = 'var(--accent-rose)';
    if (type === 'warning') toast.style.borderLeftColor = 'var(--accent-amber)';
    
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Generate Keys via Modal
function openGenerateModal() {
    const overlay = document.getElementById('generateModalOverlay');
    if (overlay) overlay.classList.add('active');
}

function closeGenerateModal() {
    const overlay = document.getElementById('generateModalOverlay');
    if (overlay) overlay.classList.remove('active');
}

function generateKeysSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Keys generated successfully!', 'success');
            
            // Show generated keys in output area
            const listArea = document.getElementById('generatedKeysList');
            if (listArea) {
                listArea.innerHTML = '';
                data.keys.forEach(key => {
                    const row = document.createElement('div');
                    row.style.display = 'flex';
                    row.style.justifyContent = 'space-between';
                    row.style.marginBottom = '0.5rem';
                    row.style.background = 'var(--bg-tertiary)';
                    row.style.padding = '0.5rem';
                    row.style.borderRadius = '0.25rem';
                    row.innerHTML = `
                        <code style="color:var(--accent-blue)">${key}</code>
                        <button class="btn btn-ghost" style="padding:0.25rem 0.5rem" onclick="copyText('${key}')">Copy</button>
                    `;
                    listArea.appendChild(row);
                });
                
                document.getElementById('generatedKeysOutput').style.display = 'block';
            }
        } else {
            showToast(data.message || 'Failed to generate keys.', 'danger');
        }
    })
    .catch(err => {
        console.error(err);
        showToast('Error sending generation request.', 'danger');
    });
}

function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Key copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Could not copy text: ', err);
    });
}

function testWebhook(endpoint) {
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'danger');
        }
    })
    .catch(err => {
        showToast('Webhook testing failed.', 'danger');
    });
}

function getCsrfToken() {
    const element = document.querySelector('input[name="csrf_token"]');
    return element ? element.value : '';
}

function updateStats(stats) {
    const map = {
        'total-keys-val': stats.total_keys,
        'active-keys-val': stats.active_keys,
        'total-users-val': stats.total_users,
        'events-today-val': stats.events_today
    };
    for (const [id, val] of Object.entries(map)) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    }
}

function prependLog(log) {
    const feed = document.getElementById('activityFeed');
    if (feed) {
        const li = document.createElement('li');
        li.className = 'activity-item';
        li.innerHTML = `
            <strong>${log.event_type}</strong>: ${log.details}
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.25rem">${log.created_at}</div>
        `;
        feed.insertBefore(li, feed.firstChild);
        if (feed.children.length > 20) {
            feed.lastChild.remove();
        }
    }
}
