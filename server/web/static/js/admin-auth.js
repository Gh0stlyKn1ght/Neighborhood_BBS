/**
 * Admin Authentication Module
 * Handles admin login, logout, token management, and session state
 * 
 * Features:
 * - Token-based authentication
 * - Token persistence in localStorage
 * - Automatic token validation on page load
 * - Session timeout handling
 * - Login/logout flows
 */

class AdminAuth {
    constructor() {
        this.token = null;
        this.adminId = null;
        this.username = null;
        this.role = null;
        this.displayName = null;
        this.expiresAt = null;
        this.listeners = [];
        
        // Configuration
        this.API_BASE = '/api/admin-management';
        this.TOKEN_KEY = 'admin_token';
        this.ADMIN_KEY = 'admin_info';
        this.CHECK_INTERVAL = 5 * 60 * 1000; // Check token every 5 minutes
        
        this.loadFromStorage();
        this.startTokenCheckInterval();
    }
    
    /**
     * Load authentication data from localStorage
     */
    loadFromStorage() {
        const token = localStorage.getItem(this.TOKEN_KEY);
        const adminInfo = localStorage.getItem(this.ADMIN_KEY);
        
        if (token && adminInfo) {
            try {
                const info = JSON.parse(adminInfo);
                this.token = token;
                this.adminId = info.admin_id;
                this.username = info.username;
                this.role = info.role;
                this.displayName = info.display_name;
                this.expiresAt = new Date(info.expires_at);
                
                // Check if token is expired
                if (this.isExpired()) {
                    this.logout();
                }
            } catch (e) {
                console.error('Error loading admin info from storage:', e);
                this.logout();
            }
        }
    }
    
    /**
     * Check if current token is expired
     */
    isExpired() {
        if (!this.expiresAt) return true;
        return new Date() > this.expiresAt;
    }
    
    /**
     * Check if admin is logged in
     */
    isLoggedIn() {
        return this.token && !this.isExpired();
    }
    
    /**
     * Save authentication data to localStorage
     */
    saveToStorage() {
        if (this.token) {
            localStorage.setItem(this.TOKEN_KEY, this.token);
            
            const adminInfo = {
                admin_id: this.adminId,
                username: this.username,
                role: this.role,
                display_name: this.displayName,
                expires_at: this.expiresAt.toISOString()
            };
            localStorage.setItem(this.ADMIN_KEY, JSON.stringify(adminInfo));
        }
    }
    
    /**
     * Login with username and password
     * 
     * @param {string} username - Admin username
     * @param {string} password - Admin password
     * @returns {Promise<{success: boolean, error?: string}>}
     */
    async login(username, password) {
        try {
            const response = await fetch(`${this.API_BASE}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                return {
                    success: false,
                    error: data.error || 'Login failed'
                };
            }
            
            // Store authentication data
            this.token = data.token;
            this.adminId = data.admin_id;
            this.username = data.username;
            this.role = data.role;
            this.displayName = data.display_name;
            this.expiresAt = new Date(data.expires_at);
            
            this.saveToStorage();
            this.notifyListeners('loggedIn');
            
            return {
                success: true,
                message: data.message
            };
        } catch (e) {
            console.error('Login error:', e);
            return {
                success: false,
                error: 'Network error during login'
            };
        }
    }
    
    /**
     * Logout and clear authentication
     */
    async logout() {
        try {
            if (this.token) {
                // Notify API of logout
                await fetch(`${this.API_BASE}/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                }).catch(e => console.warn('Error notifying API of logout:', e));
            }
        } catch (e) {
            console.error('Logout error:', e);
        } finally {
            // Clear local state
            this.token = null;
            this.adminId = null;
            this.username = null;
            this.role = null;
            this.displayName = null;
            this.expiresAt = null;
            
            // Clear storage
            localStorage.removeItem(this.TOKEN_KEY);
            localStorage.removeItem(this.ADMIN_KEY);
            
            this.notifyListeners('loggedOut');
        }
    }
    
    /**
     * Validate current token with API
     * 
     * @returns {Promise<boolean>} - True if token is valid
     */
    async validateToken() {
        if (!this.token) return false;
        
        try {
            const response = await fetch(`${this.API_BASE}/validate-token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token: this.token
                })
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.logout();
                }
                return false;
            }
            
            return true;
        } catch (e) {
            console.error('Token validation error:', e);
            return false;
        }
    }
    
    /**
     * Check if admin has specific permission
     * 
     * @param {string} permission - Permission to check
     * @returns {boolean}
     */
    hasPermission(permission) {
        // Permission check will be done via API
        // This is a placeholder for role-based checks
        const rolePermissions = {
            'super_admin': ['*'],
            'moderator': ['moderate_content', 'manage_moderation', 'ban_devices', 'view_analytics'],
            'approver': ['approve_access', 'reject_access', 'view_pending', 'view_approval_history'],
            'viewer': ['view_dashboard', 'view_analytics', 'view_violations', 'view_approval_history']
        };
        
        const permissions = rolePermissions[this.role] || [];
        return permissions.includes('*') || permissions.includes(permission);
    }
    
    /**
     * Check if admin has specific role
     * 
     * @param {string|string[]} roleName - Role(s) to check
     * @returns {boolean}
     */
    hasRole(roleName) {
        if (Array.isArray(roleName)) {
            return roleName.includes(this.role);
        }
        return this.role === roleName;
    }
    
    /**
     * Get authorization header
     * 
     * @returns {Object} - Headers object with authorization
     */
    getAuthHeader() {
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }
    
    /**
     * Start periodic token validation
     */
    startTokenCheckInterval() {
        setInterval(async () => {
            if (this.isLoggedIn()) {
                const valid = await this.validateToken();
                if (!valid) {
                    this.logout();
                }
            }
        }, this.CHECK_INTERVAL);
    }
    
    /**
     * Register listener for auth changes
     * 
     * @param {Function} callback - Callback function(event)
     */
    onChange(callback) {
        this.listeners.push(callback);
    }
    
    /**
     * Notify all listeners of auth changes
     * 
     * @param {string} event - Event name (loggedIn, loggedOut)
     */
    notifyListeners(event) {
        this.listeners.forEach(callback => {
            try {
                callback(event);
            } catch (e) {
                console.error('Error in auth listener:', e);
            }
        });
    }
}

// Global instance
const adminAuth = new AdminAuth();
