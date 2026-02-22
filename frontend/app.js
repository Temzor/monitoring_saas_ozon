const API_URL = 'http://localhost:8000';
let token = localStorage.getItem('token');
let currentAuthMode = 'login';

// Check if user is logged in
if (token) {
    showDashboard();
}

function showLogin() {
    document.getElementById('auth-forms').classList.remove('hidden');
    document.getElementById('auth-title').textContent = 'Login';
    document.getElementById('auth-toggle').textContent = 'Create an account';
    currentAuthMode = 'login';
}

function showRegister() {
    document.getElementById('auth-forms').classList.remove('hidden');
    document.getElementById('auth-title').textContent = 'Register';
    document.getElementById('auth-toggle').textContent = 'Login';
    currentAuthMode = 'register';
}

function toggleAuthMode() {
    if (currentAuthMode === 'login') {
        showRegister();
    } else {
        showLogin();
    }
}

async function handleAuth(event) {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const endpoint = currentAuthMode === 'login' ? '/token' : '/register';

    try {
        const response = await fetch(API_URL + endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();

        if (response.ok) {
            token = data.access_token;
            localStorage.setItem('token', token);
            document.getElementById('auth-forms').classList.add('hidden');
            showDashboard();
        } else {
            alert(data.detail || 'Authentication failed');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function showDashboard() {
    document.getElementById('auth-buttons').classList.add('hidden');
    document.getElementById('user-info').classList.remove('hidden');
    document.getElementById('websites-container').classList.remove('hidden');

    await loadWebsites();
}

function logout() {
    localStorage.removeItem('token');
    token = null;
    document.getElementById('auth-buttons').classList.remove('hidden');
    document.getElementById('user-info').classList.add('hidden');
    document.getElementById('websites-container').classList.add('hidden');
    document.getElementById('websites-grid').innerHTML = '';
}

async function loadWebsites() {
    try {
        const response = await fetch(API_URL + '/websites', {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        const websites = await response.json();

        const grid = document.getElementById('websites-grid');
        grid.innerHTML = '';

        websites.forEach(website => {
            const card = createWebsiteCard(website);
            grid.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading websites:', error);
    }
}

function createWebsiteCard(website) {
    const card = document.createElement('div');
    card.className = 'website-card';

    const statusClass = website.last_status ? 'status-up' : 'status-down';
    const statusText = website.last_status ? 'UP' : 'DOWN';

    card.innerHTML = `
        <h3>${website.name}</h3>
        <p>${website.url}</p>
        <p>
            <span class="status-badge ${statusClass}">${statusText}</span>
        </p>
        <p>Last checked: ${website.last_checked ? new Date(website.last_checked).toLocaleString() : 'Never'}</p>
        <button class="btn" onclick="viewLogs(${website.id})">View Logs</button>
    `;

    return card;
}

function showAddWebsite() {
    document.getElementById('add-website-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('add-website-modal').classList.remove('active');
}

async function addWebsite(event) {
    event.preventDefault();

    const website = {
        name: document.getElementById('website-name').value,
        url: document.getElementById('website-url').value,
        check_interval: parseInt(document.getElementById('website-interval').value),
    };

    try {
        const response = await fetch(API_URL + '/websites', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(website),
        });

        if (response.ok) {
            closeModal();
            loadWebsites();
        } else {
            alert('Failed to add website');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function viewLogs(websiteId) {
    try {
        const response = await fetch(API_URL + `/websites/${websiteId}/logs`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        const logs = await response.json();

        const tbody = document.getElementById('logs-body');
        tbody.innerHTML = '';

        logs.forEach(log => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${new Date(log.checked_at).toLocaleString()}</td>
                <td>${log.is_up ? 'UP' : 'DOWN'}</td>
                <td>${log.response_time}ms</td>
                <td>${log.status_code || 'N/A'}</td>
            `;
        });

        document.getElementById('logs-modal').classList.add('active');
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

function closeLogsModal() {
    document.getElementById('logs-modal').classList.remove('active');
}