
const app = {
    currentView: 'inbox',
    user: null, // Will be set by init

    init: function () {
        this.user = window.currentUser;
        this.setupMobileMenu();
        this.navigate('inbox');
        this.connectWebSocket();
        this.log("SYSTEM LINK ESTABLISHED");
    },

    setupMobileMenu: function () {
        const btn = document.getElementById('mobile-menu-btn');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('menu-overlay');

        if (!btn || !sidebar || !overlay) return;

        const toggleMenu = () => {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('active');
        };

        const closeMenu = () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        };

        btn.addEventListener('click', toggleMenu);
        overlay.addEventListener('click', closeMenu);
    },

    navigate: function (view) {
        this.currentView = view;

        // Update Nav UI
        document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
        const btn = document.querySelector(`button[onclick="app.navigate('${view}')"]`);
        if (btn) btn.classList.add('active');

        // Mobile: Close menu on navigate
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('menu-overlay');
        if (sidebar && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        }

        // Update Title - Cyberpunk Style
        const titleMap = {
            'inbox': 'INCOMING_TRANSMISSIONS',
            'send': 'INITIATE_UPLOAD',
            'sent': 'OUTGOING_LOGS',
            'messages': 'SECURE_COMM_CHANNEL',
            'admin': 'ROOT_ACCESS_PANEL'
        };
        document.getElementById('view-title').textContent = titleMap[view] || 'SYSTEM_STATUS';

        // Load Content
        const container = document.getElementById('view-content');
        container.innerHTML = '<div class="blink mono" style="color:var(--text-dim)">// FETCHING DATA...</div>';

        if (view === 'inbox') this.loadInbox(container);
        if (view === 'send') this.renderSend(container);
        if (view === 'sent') this.loadSent(container);
        if (view === 'messages') this.loadMessages(container);
        if (view === 'admin') this.loadAdmin(container);
    },

    api: async function (url, method = 'GET', body = null) {
        const options = { method: method };
        if (body && !(body instanceof FormData)) {
            options.headers = { 'Content-Type': 'application/json' };
            options.body = JSON.stringify(body);
        } else if (body instanceof FormData) {
            options.body = body;
        }

        try {
            const res = await fetch(url, options);
            if (res.status === 401) {
                window.location.href = '/login';
                return null;
            }
            if (!res.ok) {
                throw new Error(await res.text());
            }
            return await res.json();
        } catch (e) {
            this.log(`ERROR: ${e.message}`, 'error');
            return null;
        }
    },

    log: function (msg, type = 'info') {
        const list = document.getElementById('activity-list');
        if (!list) return;

        const item = document.createElement('li');
        const now = new Date();
        const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

        item.innerHTML = `<span class="text-dim">[${time}]</span> ${msg}`;
        if (type === 'error') item.classList.add('text-error');
        if (type === 'success') item.classList.add('text-accent');

        list.insertBefore(item, list.firstChild);
        if (list.children.length > 50) list.lastChild.remove();
    },

    // VIEW: INBOX (Cards)
    loadInbox: async function (container) {
        const files = await this.api('/files/inbox');
        if (!files) {
            container.innerHTML = '<div class="text-error">SYNC_ERROR: CONNECTION_REFUSED</div>';
            return;
        }

        if (files.length === 0) {
            container.innerHTML = '<div class="text-dim" style="padding: 20px; border: 1px dashed #333; border-radius: 10px; text-align: center;">NO INCOMING TRANSMISSIONS</div>';
            return;
        }

        let html = '<div class="grid-list">';
        files.forEach(f => {
            let expiryDateStr = f.expires_at;
            if (!expiryDateStr.endsWith('Z') && !expiryDateStr.includes('+')) {
                expiryDateStr += 'Z';
            }
            html += `
            <div class="card" style="display: flex; align-items: center; justify-content: space-between; gap: 15px; padding: 20px;">
                <div style="flex-grow: 1;">
                    <div style="font-weight: bold; font-size: 1.1em; color: white; margin-bottom: 5px;">${f.display_filename}</div>
                    <div class="text-dim mono" style="font-size: 0.85em;">
                        FROM: ID_${f.sender_id} | TTL: <span class="expiry-timer text-accent" data-time="${expiryDateStr}">CALCULATING...</span>
                    </div>
                </div>
                <button class="primary" onclick="app.download(${f.id}, '${f.display_filename}')">
                    DOWNLOAD
                </button>
            </div>`;
        });
        html += '</div>';

        container.innerHTML = html;
        this.startTimers();
    },

    // VIEW: SENT (Cards)
    loadSent: async function (container) {
        const files = await this.api('/files/sent');
        if (!files) return;

        if (files.length === 0) {
            container.innerHTML = '<div class="text-dim" style="padding: 20px; border: 1px dashed #333; border-radius: 10px; text-align: center;">LOG EMPTY</div>';
            return;
        }

        let html = '<div class="grid-list">';
        files.forEach(f => {
            const statusColor = f.status === 'active' ? 'var(--accent-color)' : 'var(--text-dim)';
            html += `
            <div class="card" style="padding: 15px 20px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <div style="font-weight: bold; color: white;">${f.display_filename}</div>
                    <div class="mono" style="color: ${statusColor}; font-size: 0.8em;">[${f.status.toUpperCase()}]</div>
                </div>
                <div class="text-dim mono" style="font-size: 0.8em;">
                    TO: ID_${f.recipient_id} | SENT: ${new Date(f.created_at).toLocaleString()}
                </div>
            </div>`;
        });
        html += '</div>';
        container.innerHTML = html;
    },

    // VIEW: SEND
    renderSend: function (container) {
        container.innerHTML = `
            <div class="card" style="max-width: 600px; margin: 0 auto;">
                <form id="upload-form">
                    <div style="margin-bottom: 20px;">
                         <label class="text-dim mono" style="font-size: 0.8em; display: block; margin-bottom: 8px;">TARGET_USER</label>
                         <input type="text" name="recipient_username" required placeholder="USERNAME">
                    </div>
                    <div style="margin-bottom: 20px;">
                         <label class="text-dim mono" style="font-size: 0.8em; display: block; margin-bottom: 8px;">DATA_PAYLOAD</label>
                         <input type="file" name="file" required style="padding: 10px; background: rgba(0,0,0,0.2);">
                    </div>
                    <div style="margin-bottom: 25px;">
                         <label class="text-dim mono" style="font-size: 0.8em; display: block; margin-bottom: 8px;">TIME_TO_LIVE (MINUTES)</label>
                         <input type="number" name="expiry_minutes" value="60" min="1" required>
                    </div>
                    <button type="submit" class="primary" style="width: 100%;">INITIATE UPLOAD</button>
                </form>
                <div id="upload-status" class="mono" style="margin-top: 20px; text-align: center; min-height: 20px;"></div>
            </div>
        `;

        document.getElementById('upload-form').onsubmit = async (e) => {
            e.preventDefault();
            const btn = e.target.querySelector('button');
            const statusDiv = document.getElementById('upload-status');

            btn.disabled = true;
            btn.textContent = 'TRANSMITTING...';
            statusDiv.textContent = 'UPLOADING...';
            statusDiv.className = 'text-dim';

            const formData = new FormData(e.target);
            try {
                const res = await fetch('/files/upload', {
                    method: 'POST',
                    body: formData
                });

                if (res.ok) {
                    this.log('UPLOAD COMPLETE', 'success');
                    statusDiv.innerHTML = '<span class="text-accent">TRANSFER SUCCESSFUL</span>';
                    e.target.reset();
                } else {
                    const err = await res.json();
                    throw new Error(err.detail || 'UPLOAD FAILED');
                }
            } catch (err) {
                this.log(`UPLOAD ERROR: ${err.message}`, 'error');
                statusDiv.innerHTML = `<span class="text-error">FAILED: ${err.message}</span>`;
            } finally {
                btn.disabled = false;
                btn.textContent = 'INITIATE UPLOAD';
            }
        };
    },

    // VIEW: MESSAGES
    loadMessages: async function (container) {
        container.innerHTML = `
            <div style="display: flex; flex-direction: column; height: 100%; max-height: calc(100vh - 180px);">
                <div id="msg-stream" class="message-stream" style="flex-grow: 1; overflow-y: auto; padding: 10px; border: 1px solid var(--panel-border); border-radius: 12px; background: rgba(0,0,0,0.2); margin-bottom: 15px;">
                    <div class="text-dim mono" style="text-align: center; padding: 20px;">INITIALIZING COMM LINK...</div>
                </div>
                <div>
                    <form id="msg-form" style="display: flex; gap: 10px;">
                        <input type="text" name="recipient" placeholder="@USER" style="width: 120px;" required>
                        <input type="text" name="content" placeholder="ENTER MESSAGE..." style="flex-grow: 1;" required>
                        <button type="submit" class="primary">SEND</button>
                    </form>
                </div>
            </div>
        `;

        document.getElementById('msg-form').onsubmit = async (e) => {
            e.preventDefault();
            const form = e.target;
            const res = await this.api('/messages', 'POST', {
                recipient_username: form.recipient.value,
                content: form.content.value
            });

            if (res) {
                form.content.value = '';
                this.loadMessageStream();
            }
        };

        this.loadMessageStream();
    },

    loadMessageStream: async function () {
        const div = document.getElementById('msg-stream');
        if (!div) return;

        const msgs = await this.api('/messages');
        if (!msgs) {
            div.innerHTML = '<div class="text-error mono" style="text-align:center;">COMM LINK OFFLINE</div>';
            return;
        }

        if (msgs.length === 0) {
            div.innerHTML = '<div class="text-dim mono" style="text-align:center; padding-top: 50px;">NO COMMUNICATIONS FOUND</div>';
            return;
        }

        div.innerHTML = msgs.map(m => {
            const isMe = m.sender_username === this.user.username;
            return `<div class="message-bubble ${isMe ? 'me' : ''}">
                <div class="text-dim mono" style="font-size: 0.7em; margin-bottom: 4px;">
                    ${isMe ? `TO: ${m.recipient_username}` : `FROM: ${m.sender_username}`} | ${new Date(m.timestamp).toLocaleTimeString()}
                </div>
                <div style="line-height: 1.4;">${m.content}</div>
            </div>`;
        }).join('');

        div.scrollTop = div.scrollHeight;
    },

    download: function (id, name) {
        this.log(`INITIATING DOWNLOAD: ${name}`);
        const a = document.createElement('a');
        a.href = `/files/${id}/download`;
        a.download = name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    },

    logout: async function () {
        await this.api('/logout', 'POST');
        window.location.href = '/login';
    },

    startTimers: function () {
        if (this.timerInterval) clearInterval(this.timerInterval);
        this.timerInterval = setInterval(() => {
            document.querySelectorAll('.expiry-timer').forEach(el => {
                const end = new Date(el.dataset.time);
                const now = new Date();
                const diff = end - now;
                if (diff <= 0) {
                    el.textContent = 'EXPIRED';
                    el.classList.add('text-error');
                    el.classList.remove('text-accent');
                } else {
                    const min = Math.floor(diff / 60000);
                    const sec = Math.floor((diff % 60000) / 1000);
                    el.textContent = `${min}m ${sec}s`;
                    if (min < 5) el.classList.add('text-warning');
                }
            });
        }, 1000);
    },

    connectWebSocket: function () {
        // Future implementation
    },

    // VIEW: ADMIN
    loadAdmin: async function (container) {
        if (!this.user.is_admin) {
            container.innerHTML = '<div class="card"><div class="text-error">ACCESS DENIED: INSUFFICIENT CLEARANCE level 5 REQUIRED</div></div>';
            return;
        }

        const users = await this.api('/admin/users');
        if (!users) {
            container.innerHTML = '<div class="text-error">DATABASE CONNECTION FAILED</div>';
            return;
        }

        let html = `
        <div class="card">
            <div style="font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid var(--panel-border); padding-bottom: 10px;">ADD NEW OPERATOR</div>
            <form id="add-user-form" style="display: flex; gap: 10px; flex-wrap: wrap;">
                <input type="text" name="username" placeholder="USERNAME" required style="flex: 1; min-width: 150px;">
                <input type="text" name="password" placeholder="PASSWORD" required style="flex: 1; min-width: 150px;">
                <button type="submit" class="primary">CREATE</button>
            </form>
        </div>
        
        <div style="margin-bottom: 10px; font-weight: bold; padding-left: 5px;">PERSONNEL MANIFEST</div>
        <div class="grid-list">`;

        users.forEach(u => {
            const role = u.is_admin ? '<span class="text-accent">ADMIN</span>' : '<span class="text-dim">OPERATOR</span>';
            const action = u.id === this.user.id ?
                '<span class="text-dim">CURRENT_USER</span>' :
                `<button style="padding: 5px 10px; font-size: 0.75rem; border-color: var(--error-color); color: var(--error-color);" onclick="app.deleteUser(${u.id})">REMOVE</button>`;

            html += `
            <div class="card" style="padding: 15px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                   <div style="font-weight: bold;">${u.username} <span class="mono text-dim" style="font-size: 0.8em;">(ID:${u.id})</span></div>
                   <div style="font-size: 0.8em; margin-top: 3px;">${role}</div>
                </div>
                <div>${action}</div>
            </div>`;
        });

        html += '</div>';
        container.innerHTML = html;

        const form = document.getElementById('add-user-form');
        if (form) {
            form.onsubmit = async (e) => {
                e.preventDefault();
                const form = e.target;
                const res = await this.api('/admin/users', 'POST', {
                    username: form.username.value,
                    password: form.password.value
                });

                if (res) {
                    this.log(`USER ${res.username} CREATED`, 'success');
                    this.loadAdmin(container);
                }
            };
        }
    },

    deleteUser: async function (id) {
        if (!confirm('CONFIRM DELETION OF PERSONNEL RECORD? THIS ACTION IS IRREVERSIBLE.')) return;
        const res = await this.api(`/admin/users/${id}`, 'DELETE');
        if (res) {
            this.log('USER RECORD REMOVED', 'success');
            this.loadAdmin(document.getElementById('view-content'));
        }
    },

    // CHANGE PASSWORD MODAL
    openPasswordModal: function () {
        document.getElementById('password-modal').classList.add('active');
        document.getElementById('change-password-form').reset();
        document.getElementById('pwd-msg').textContent = '';
    },

    closePasswordModal: function () {
        document.getElementById('password-modal').classList.remove('active');
    },

    changePassword: async function (e) {
        const form = e.target;
        const btn = form.querySelector('button');
        const msg = document.getElementById('pwd-msg');

        const oldPwd = form.old_password.value;
        const newPwd = form.new_password.value;

        btn.disabled = true;
        btn.textContent = 'UPDATING...';
        msg.textContent = 'PROCESSING ENCRYPTION...';
        msg.className = 'mono text-dim';

        try {
            const res = await fetch('/auth/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ old_password: oldPwd, new_password: newPwd })
            });

            if (res.ok) {
                msg.textContent = 'CREDENTIALS UPDATED SUCCESSFULLY';
                msg.className = 'mono text-accent';
                this.log('PASSWORD UPDATED', 'success');
                setTimeout(() => {
                    this.closePasswordModal();
                    form.reset();
                }, 1500);
            } else {
                const err = await res.json();
                throw new Error(err.detail || 'UPDATE FAILED');
            }
        } catch (error) {
            msg.textContent = `ERROR: ${error.message}`;
            msg.className = 'mono text-error';
            this.log(`PASSWORD CHANGE FAILED: ${error.message}`, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'UPDATE CREDENTIALS';
        }
    }
};
