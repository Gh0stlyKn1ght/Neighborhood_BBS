/**
 * Admin Dashboard Module
 * Handles admin dashboard UI and interactions
 * 
 * Features:
 * - Dashboard navigation and view switching
 * - Admin profile display
 * - Admin management interface (create, list, update roles)
 * - Password change
 * - Audit log viewer
 * - Session management
 */

class AdminDashboard {
    constructor() {
        this.API_BASE = '/api/admin-management';
        this.currentView = 'dashboard';
        this.admins = [];
        this.auditLogs = [];
        
        // Ensure we're authenticated
        if (!adminAuth.isLoggedIn()) {
            window.location.href = '/admin/login';
            return;
        }
        
        this.init();
    }
    
    /**
     * Initialize dashboard
     */
    async init() {
        this.setupEventListeners();
        this.updateUserInfo();
        await this.loadDashboardData();
        
        // Listen for auth changes
        adminAuth.onChange((event) => {
            if (event === 'loggedOut') {
                window.location.href = '/admin/login';
            }
        });
    }
    
    // ========== SETUP ==========
    
    /**
     * Setup event listeners for UI elements
     */
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const view = e.currentTarget.dataset.view;
                if (view) {
                    this.switchView(view);
                }
            });
        });
        
        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
        
        // Password change
        const passwordForm = document.getElementById('passwordForm');
        if (passwordForm) {
            passwordForm.addEventListener('submit', (e) => this.handlePasswordChange(e));
        }
        
        // Admin creation
        const createAdminForm = document.getElementById('createAdminForm');
        if (createAdminForm) {
            createAdminForm.addEventListener('submit', (e) => this.handleCreateAdmin(e));
        }
        
        // Admin list
        const adminsList = document.getElementById('adminsList');
        if (adminsList) {
            adminsList.addEventListener('click', (e) => this.handleAdminListActions(e));
        }
        
        // Audit log filters
        const auditFilterBtn = document.getElementById('auditFilterBtn');
        if (auditFilterBtn) {
            auditFilterBtn.addEventListener('click', () => this.loadAuditLog());
        }
    }
    
    /**
     * Update user information display
     */
    updateUserInfo() {
        const elements = {
            username: document.getElementById('adminUsername'),
            role: document.getElementById('adminRole'),
            displayName: document.getElementById('adminDisplayName')
        };
        
        if (elements.username) elements.username.textContent = adminAuth.username;
        if (elements.role) elements.role.textContent = this.formatRole(adminAuth.role);
        if (elements.displayName) elements.displayName.textContent = adminAuth.displayName || adminAuth.username;
    }
    
    /**
     * Format role name for display
     */
    formatRole(role) {
        const roleNames = {
            'super_admin': 'Super Administrator',
            'moderator': 'Moderator',
            'approver': 'Approver',
            'viewer': 'Viewer'
        };
        return roleNames[role] || role;
    }
    
    // ========== VIEW SWITCHING ==========
    
    /**
     * Switch to different view
     */
    switchView(view) {
        // Hide all views
        document.querySelectorAll('[data-view-content]').forEach(el => {
            el.style.display = 'none';
        });
        
        // Show selected view
        const viewEl = document.querySelector(`[data-view-content="${view}"]`);
        if (viewEl) {
            viewEl.style.display = 'block';
        }
        
        // Update sidebar
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.view === view) {
                item.classList.add('active');
            }
        });
        
        this.currentView = view;
        
        // Load view-specific data
        this.loadViewData(view);
    }
    
    /**
     * Load data for specific view
     */
    async loadViewData(view) {
        try {
            switch (view) {
                case 'profile':
                    await this.loadProfile();
                    break;
                case 'admins':
                    await this.loadAdminsList();
                    break;
                case 'audit':
                    await this.loadAuditLog();
                    break;
                case 'analytics':
                    await this.loadAnalytics();
                    break;
            }
        } catch (e) {
            this.showError(`Error loading ${view}: ${adminApi.formatError(e)}`);
        }
    }
    
    // ========== DASHBOARD ==========
    
    /**
     * Load dashboard data
     */
    async loadDashboardData() {
        try {
            // Load basic stats
            const stats = {
                role: this.formatRole(adminAuth.role),
                lastLogin: new Date().toLocaleString()
            };
            
            const statsEl = document.getElementById('dashboardStats');
            if (statsEl) {
                statsEl.innerHTML = `
                    <div class="stat-item">
                        <strong>Role:</strong> ${stats.role}
                    </div>
                    <div class="stat-item">
                        <strong>Last Login:</strong> ${stats.lastLogin}
                    </div>
                `;
            }
        } catch (e) {
            console.error('Error loading dashboard data:', e);
        }
    }
    
    // ========== PROFILE MANAGEMENT ==========
    
    /**
     * Load and display admin profile
     */
    async loadProfile() {
        try {
            const admin = await adminApi.getProfile();
            
            const profileEl = document.getElementById('profileDisplay');
            if (profileEl) {
                profileEl.innerHTML = `
                    <div class="profile-field">
                        <label>Username:</label>
                        <span>${this.escapeHtml(admin.username)}</span>
                    </div>
                    <div class="profile-field">
                        <label>Display Name:</label>
                        <span>${this.escapeHtml(admin.display_name || 'Not set')}</span>
                    </div>
                    <div class="profile-field">
                        <label>Email:</label>
                        <span>${this.escapeHtml(admin.email || 'Not set')}</span>
                    </div>
                    <div class="profile-field">
                        <label>Role:</label>
                        <span>${this.formatRole(admin.role)}</span>
                    </div>
                    <div class="profile-field">
                        <label>Last Login:</label>
                        <span>${new Date(admin.last_login).toLocaleString()}</span>
                    </div>
                `;
            }
        } catch (e) {
            this.showError(`Error loading profile: ${adminApi.formatError(e)}`);
        }
    }
    
    /**
     * Handle password change
     */
    async handlePasswordChange(e) {
        e.preventDefault();
        
        const oldPassword = document.getElementById('oldPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        // Validation
        if (!oldPassword || !newPassword || !confirmPassword) {
            this.showError('All password fields are required');
            return;
        }
        
        if (newPassword !== confirmPassword) {
            this.showError('New passwords do not match');
            return;
        }
        
        if (newPassword.length < 8) {
            this.showError('New password must be at least 8 characters');
            return;
        }
        
        try {
            this.showLoading('Changing password...');
            
            const result = await adminApi.changePassword(oldPassword, newPassword);
            
            if (result.success) {
                this.showSuccess('Password changed successfully');
                e.target.reset();
            } else {
                this.showError(result.error || 'Password change failed');
            }
        } catch (e) {
            this.showError(`Error changing password: ${adminApi.formatError(e)}`);
        } finally {
            this.hideLoading();
        }
    }
    
    // ========== ADMIN MANAGEMENT (super_admin only) ==========
    
    /**
     * Load and display admins list
     */
    async loadAdminsList() {
        if (!adminAuth.hasRole('super_admin')) {
            this.showError('You do not have permission to manage admins');
            return;
        }
        
        try {
            this.showLoading('Loading admins...');
            this.admins = await adminApi.listAdmins({ limit: 100 });
            this.renderAdminsList();
        } catch (e) {
            this.showError(`Error loading admins: ${adminApi.formatError(e)}`);
        } finally {
            this.hideLoading();
        }
    }
    
    /**
     * Render admins list
     */
    renderAdminsList() {
        const container = document.getElementById('adminsTable');
        if (!container) return;
        
        if (this.admins.length === 0) {
            container.innerHTML = '<p>No admins found</p>';
            return;
        }
        
        let html = `
            <table class="admins-table">
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Display Name</th>
                        <th>Role</th>
                        <th>Email</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        this.admins.forEach(admin => {
            const isActive = admin.is_active ? 'Active' : 'Inactive';
            const isSelf = admin.admin_id === adminAuth.adminId;
            
            html += `
                <tr data-admin-id="${admin.admin_id}">
                    <td>${this.escapeHtml(admin.username)}</td>
                    <td>${this.escapeHtml(admin.display_name || '-')}</td>
                    <td>${this.formatRole(admin.role)}</td>
                    <td>${this.escapeHtml(admin.email || '-')}</td>
                    <td><span class="status ${isActive.toLowerCase()}">${isActive}</span></td>
                    <td>
                        <button class="btn-sm edit-role" ${isSelf ? 'disabled' : ''}>Edit Role</button>
                        <button class="btn-sm deactivate" ${isSelf || !admin.is_active ? 'disabled' : ''}>Deactivate</button>
                    </td>
                </tr>
            `;
        });
        
        html += `
                </tbody>
            </table>
        `;
        
        container.innerHTML = html;
    }
    
    /**
     * Handle admin list actions
     */
    async handleAdminListActions(e) {
        const btn = e.target;
        const row = btn.closest('tr');
        if (!row) return;
        
        const adminId = row.dataset.adminId;
        
        if (btn.classList.contains('edit-role')) {
            await this.handleEditRole(adminId);
        } else if (btn.classList.contains('deactivate')) {
            await this.handleDeactivateAdmin(adminId);
        }
    }
    
    /**
     * Handle edit admin role
     */
    async handleEditRole(adminId) {
        const admin = this.admins.find(a => a.admin_id === adminId);
        if (!admin) return;
        
        const roles = ['moderator', 'approver', 'viewer'];
        const newRole = prompt(
            `Change role for ${admin.username}?\n\nCurrent: ${admin.role}\n\nNew role: ${roles.join(', ')}`,
            admin.role
        );
        
        if (!newRole || newRole === admin.role) return;
        
        if (!roles.includes(newRole) && newRole !== 'super_admin') {
            this.showError('Invalid role');
            return;
        }
        
        try {
            this.showLoading('Updating role...');
            const result = await adminApi.updateAdminRole(adminId, newRole);
            
            if (result.success) {
                this.showSuccess(`Role updated to ${newRole}`);
                admin.role = newRole;
                this.renderAdminsList();
            } else {
                this.showError(result.error || 'Failed to update role');
            }
        } catch (e) {
            this.showError(`Error updating role: ${adminApi.formatError(e)}`);
        } finally {
            this.hideLoading();
        }
    }
    
    /**
     * Handle deactivate admin
     */
    async handleDeactivateAdmin(adminId) {
        const admin = this.admins.find(a => a.admin_id === adminId);
        if (!admin) return;
        
        if (!confirm(`Are you sure you want to deactivate ${admin.username}?`)) {
            return;
        }
        
        try {
            this.showLoading('Deactivating admin...');
            const result = await adminApi.deactivateAdmin(adminId);
            
            if (result.success) {
                this.showSuccess('Admin deactivated');
                admin.is_active = false;
                this.renderAdminsList();
            } else {
                this.showError(result.error || 'Failed to deactivate admin');
            }
        } catch (e) {
            this.showError(`Error deactivating admin: ${adminApi.formatError(e)}`);
        } finally {
            this.hideLoading();
        }
    }
    
    /**
     * Handle create admin
     */
    async handleCreateAdmin(e) {
        e.preventDefault();
        
        if (!adminAuth.hasRole('super_admin')) {
            this.showError('You do not have permission to create admins');
            return;
        }
        
        const username = document.getElementById('newAdminUsername').value.trim();
        const password = document.getElementById('newAdminPassword').value;
        const role = document.getElementById('newAdminRole').value;
        const displayName = document.getElementById('newAdminDisplayName').value.trim();
        const email = document.getElementById('newAdminEmail').value.trim();
        
        // Validation
        if (!username || !password || !role) {
            this.showError('Username, password, and role are required');
            return;
        }
        
        if (password.length < 8) {
            this.showError('Password must be at least 8 characters');
            return;
        }
        
        try {
            this.showLoading('Creating admin...');
            
            const result = await adminApi.createAdmin({
                username,
                password,
                role,
                displayName,
                email
            });
            
            this.showSuccess(`Admin '${username}' created successfully`);
            e.target.reset();
            
            // Reload admins list
            await this.loadAdminsList();
        } catch (e) {
            this.showError(`Error creating admin: ${adminApi.formatError(e)}`);
        } finally {
            this.hideLoading();
        }
    }
    
    // ========== AUDIT LOG ==========
    
    /**
     * Load and display audit log
     */
    async loadAuditLog() {
        if (!adminAuth.hasPermission('audit_log')) {
            this.showError('You do not have permission to view audit logs');
            return;
        }
        
        try {
            this.showLoading('Loading audit log...');
            const limit = parseInt(document.getElementById('auditLimit')?.value || '100', 10);
            this.auditLogs = await adminApi.getAuditLog({ limit });
            this.renderAuditLog();
        } catch (e) {
            this.showError(`Error loading audit log: ${adminApi.formatError(e)}`);
        } finally {
            this.hideLoading();
        }
    }
    
    /**
     * Render audit log
     */
    renderAuditLog() {
        const container = document.getElementById('auditTable');
        if (!container) return;
        
        if (this.auditLogs.length === 0) {
            container.innerHTML = '<p>No audit log entries found</p>';
            return;
        }
        
        let html = `
            <table class="audit-table">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Admin</th>
                        <th>Action</th>
                        <th>Resource</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        this.auditLogs.forEach(log => {
            const timestamp = new Date(log.timestamp).toLocaleString();
            const status = log.success ? 'Success' : 'Failed';
            
            html += `
                <tr class="${log.success ? 'success' : 'failed'}">
                    <td>${timestamp}</td>
                    <td>${this.escapeHtml(log.admin_id || '-')}</td>
                    <td>${this.escapeHtml(log.action)}</td>
                    <td>${this.escapeHtml(log.resource_type)}${log.resource_id ? ':' + this.escapeHtml(log.resource_id) : ''}</td>
                    <td><span class="status ${status.toLowerCase()}">${status}</span></td>
                </tr>
            `;
        });
        
        html += `
                </tbody>
            </table>
        `;
        
        container.innerHTML = html;
    }
    
    // ========== ANALYTICS ==========
    
    /**
     * Load analytics dashboard data
     */
    async loadAnalytics() {
        if (!adminAuth.hasPermission('audit_log')) {
            this.showError('You do not have permission to view analytics');
            return;
        }
        
        try {
            this.showLoading('Loading analytics...');
            const dashboard = await adminApi.getDashboardSummary();
            this.renderAnalytics(dashboard);
        } catch (e) {
            this.showError(`Error loading analytics: ${adminApi.formatError(e)}`);
        } finally {
            this.hideLoading();
        }
    }
    
    /**
     * Render analytics dashboard
     */
    renderAnalytics(data) {
        const container = document.getElementById('analyticsContainer');
        if (!container) return;
        
        // Format numbers with commas
        const fmt = (n) => n.toLocaleString();
        
        const admins = data.admins || {};
        const activity = data.admin_activity || {};
        const moderation = data.moderation || {};
        const access = data.access_control || {};
        const sessions = data.sessions || {};
        const content = data.content || {};
        
        let html = `
            <div class="analytics-grid">
                <!-- Admin Statistics -->
                <div class="analytics-card">
                    <h3>Admin Statistics</h3>
                    <div class="stats">
                        <div class="stat">
                            <div class="value">${fmt(admins.total || 0)}</div>
                            <div class="label">Total Admins</div>
                        </div>
                        <div class="stat">
                            <div class="value">${fmt(admins.active || 0)}</div>
                            <div class="label">Active</div>
                        </div>
                        <div class="stat">
                            <div class="value">${fmt(admins.inactive || 0)}</div>
                            <div class="label">Inactive</div>
                        </div>
                    </div>
                </div>
                
                <!-- Admin Activity -->
                <div class="analytics-card">
                    <h3>Admin Activity (Last 7 Days)</h3>
                    <div class="stats">
                        <div class="stat">
                            <div class="value">${fmt(activity.total_actions || 0)}</div>
                            <div class="label">Total Actions</div>
                        </div>
                        <div class="stat">
                            <div class="value">${Object.keys(activity.by_admin || {}).length}</div>
                            <div class="label">Active Admins</div>
                        </div>
                    </div>
                </div>
                
                <!-- Moderation Statistics -->
                <div class="analytics-card">
                    <h3>Moderation (Last 7 Days)</h3>
                    <div class="stats">
                        <div class="stat">
                            <div class="value">${fmt(moderation.total_violations || 0)}</div>
                            <div class="label">Violations</div>
                        </div>
                        <div class="stat">
                            <div class="value">${fmt(moderation.resolved || 0)}</div>
                            <div class="label">Resolved</div>
                        </div>
                        <div class="stat">
                            <div class="value">${fmt(moderation.device_bans_active || 0)}</div>
                            <div class="label">Active Bans</div>
                        </div>
                    </div>
                </div>
                
                <!-- Access Control -->
                <div class="analytics-card">
                    <h3>Access Control</h3>
                    <div class="stats">
                        <div class="stat">
                            <div class="value">${fmt(access.pending_approvals || 0)}</div>
                            <div class="label">Pending Approvals</div>
                        </div>
                        <div class="stat">
                            <div class="value">${access.approval_rate || 0}%</div>
                            <div class="label">Approval Rate</div>
                        </div>
                        <div class="stat">
                            <div class="value">${fmt(access.user_registrations || 0)}</div>
                            <div class="label">Registrations</div>
                        </div>
                    </div>
                </div>
                
                <!-- Session Statistics -->
                <div class="analytics-card">
                    <h3>Session Statistics</h3>
                    <div class="stats">
                        <div class="stat">
                            <div class="value">${fmt(sessions.active_sessions || 0)}</div>
                            <div class="label">Active Sessions</div>
                        </div>
                        <div class="stat">
                            <div class="value">${fmt(sessions.total_sessions_24h || 0)}</div>
                            <div class="label">Last 24h</div>
                        </div>
                        <div class="stat">
                            <div class="value">${(sessions.avg_session_duration_minutes || 0).toFixed(1)}m</div>
                            <div class="label">Avg Duration</div>
                        </div>
                    </div>
                </div>
                
                <!-- Content Statistics -->
                <div class="analytics-card">
                    <h3>Content (Last 7 Days)</h3>
                    <div class="stats">
                        <div class="stat">
                            <div class="value">${fmt(content.messages || 0)}</div>
                            <div class="label">Messages</div>
                        </div>
                        <div class="stat">
                            <div class="value">${fmt(content.posts || 0)}</div>
                            <div class="label">Posts</div>
                        </div>
                        <div class="stat">
                            <div class="value">${fmt(content.total_content || 0)}</div>
                            <div class="label">Total</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        this.showSuccess('Analytics loaded');
    }
    
    // ========== UTILITIES ==========
    
    /**
     * Logout
     */
    async logout() {
        if (confirm('Are you sure you want to logout?')) {
            await adminAuth.logout();
            window.location.href = '/admin/login';
        }
    }
    
    /**
     * Show error message
     */
    showError(message) {
        const container = document.getElementById('messageContainer');
        if (container) {
            container.innerHTML = `<div class="message error">${this.escapeHtml(message)}</div>`;
            setTimeout(() => {
                if (container.innerHTML === `<div class="message error">${this.escapeHtml(message)}</div>`) {
                    container.innerHTML = '';
                }
            }, 5000);
        }
    }
    
    /**
     * Show success message
     */
    showSuccess(message) {
        const container = document.getElementById('messageContainer');
        if (container) {
            container.innerHTML = `<div class="message success">${this.escapeHtml(message)}</div>`;
            setTimeout(() => {
                if (container.innerHTML === `<div class="message success">${this.escapeHtml(message)}</div>`) {
                    container.innerHTML = '';
                }
            }, 5000);
        }
    }
    
    /**
     * Show loading message
     */
    showLoading(message) {
        const container = document.getElementById('messageContainer');
        if (container) {
            container.innerHTML = `<div class="message loading">${this.escapeHtml(message)}</div>`;
        }
    }
    
    /**
     * Hide loading message
     */
    hideLoading() {
        const container = document.getElementById('messageContainer');
        if (container) {
            const loading = container.querySelector('.message.loading');
            if (loading) {
                loading.remove();
            }
        }
    }
    
    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new AdminDashboard();
});
