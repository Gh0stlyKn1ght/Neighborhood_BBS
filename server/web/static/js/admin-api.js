/**
 * Admin API Client Module
 * Handles all API communication for admin management
 * 
 * Features:
 * - Admin CRUD operations
 * - Role management
 * - Audit log queries
 * - Profile management
 * - Password management
 * - Error handling and retry logic
 */

class AdminApiClient {
    constructor(authModule) {
        this.auth = authModule;
        this.API_BASE = '/api/admin-management';
        this.TIMEOUT = 10000; // 10 second timeout
    }
    
    /**
     * Make API request with authentication
     * 
     * @param {string} endpoint - API endpoint path
     * @param {Object} options - Fetch options
     * @returns {Promise<Object>} - Response data
     */
    async request(endpoint, options = {}) {
        const url = `${this.API_BASE}${endpoint}`;
        
        // Ensure auth headers are included
        if (!options.headers) {
            options.headers = {};
        }
        
        if (this.auth.token) {
            options.headers['Authorization'] = `Bearer ${this.auth.token}`;
        }
        
        if (!options.headers['Content-Type']) {
            options.headers['Content-Type'] = 'application/json';
        }
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.TIMEOUT);
            
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            const data = await response.json();
            
            // Handle authentication errors
            if (response.status === 401) {
                this.auth.logout();
                throw new Error('Session expired. Please login again.');
            }
            
            if (!response.ok) {
                throw new Error(data.error || `API Error: ${response.status}`);
            }
            
            return data;
        } catch (e) {
            if (e.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw e;
        }
    }
    
    /**
     * Get current admin profile
     * 
     * @returns {Promise<Object>} - Admin profile object
     */
    async getProfile() {
        const response = await this.request('/profile', {
            method: 'GET'
        });
        return response.admin;
    }
    
    /**
     * Change admin password
     * 
     * @param {string} oldPassword - Current password
     * @param {string} newPassword - New password
     * @returns {Promise<{success: boolean, message: string}>}
     */
    async changePassword(oldPassword, newPassword) {
        const response = await this.request('/change-password', {
            method: 'POST',
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword
            })
        });
        
        return {
            success: response.success,
            message: response.message
        };
    }
    
    // ========== ADMIN MANAGEMENT (super_admin only) ==========
    
    /**
     * Create new admin
     * 
     * @param {Object} adminData - Admin data
     * @returns {Promise<Object>} - Created admin object
     */
    async createAdmin(adminData) {
        const response = await this.request('/admin/create', {
            method: 'POST',
            body: JSON.stringify({
                username: adminData.username,
                password: adminData.password,
                role: adminData.role,
                display_name: adminData.displayName,
                email: adminData.email
            })
        });
        
        return {
            admin_id: response.admin_id,
            username: response.username,
            role: response.role,
            message: response.message
        };
    }
    
    /**
     * List all admins
     * 
     * @param {Object} options - Query options
     * @returns {Promise<Array>} - Array of admin objects
     */
    async listAdmins(options = {}) {
        const limit = options.limit || 100;
        const url = `/admin/list?limit=${limit}`;
        
        const response = await this.request(url, {
            method: 'GET'
        });
        
        return response.admins;
    }
    
    /**
     * Get specific admin details
     * 
     * @param {string} adminId - Admin ID
     * @returns {Promise<Object>} - Admin object
     */
    async getAdmin(adminId) {
        const response = await this.request(`/admin/${adminId}`, {
            method: 'GET'
        });
        
        return response.admin;
    }
    
    /**
     * Update admin role
     * 
     * @param {string} adminId - Admin ID
     * @param {string} newRole - New role (super_admin, moderator, approver, viewer)
     * @returns {Promise<{success: boolean, message: string}>}
     */
    async updateAdminRole(adminId, newRole) {
        const response = await this.request(`/admin/${adminId}/role`, {
            method: 'POST',
            body: JSON.stringify({
                role: newRole
            })
        });
        
        return {
            success: response.success,
            message: response.message
        };
    }
    
    /**
     * Deactivate admin account
     * 
     * @param {string} adminId - Admin ID to deactivate
     * @returns {Promise<{success: boolean, message: string}>}
     */
    async deactivateAdmin(adminId) {
        const response = await this.request(`/admin/${adminId}/deactivate`, {
            method: 'POST'
        });
        
        return {
            success: response.success,
            message: response.message
        };
    }
    
    // ========== AUDIT LOG ==========
    
    /**
     * Get audit log entries
     * 
     * @param {Object} options - Query options
     * @returns {Promise<Array>} - Array of audit log entries
     */
    async getAuditLog(options = {}) {
        const limit = Math.min(options.limit || 100, 500); // Max 500
        const adminId = options.adminId ? `&admin_id=${options.adminId}` : '';
        const url = `/audit-log?limit=${limit}${adminId}`;
        
        const response = await this.request(url, {
            method: 'GET'
        });
        
        return response.audit_log;
    }
    
    // ========== HELPER METHODS ==========
    
    /**
     * Format API error message for display
     * 
     * @param {Error} error - Error object
     * @returns {string} - Formatted error message
     */
    formatError(error) {
        if (error.message) {
            return error.message;
        }
        return 'An unknown error occurred';
    }
    
    /**
     * Check if error is authentication error
     * 
     * @param {Error} error - Error object
     * @returns {boolean}
     */
    isAuthError(error) {
        return error.message && error.message.includes('Session expired');
    }
}

// Create global instance
const adminApi = new AdminApiClient(adminAuth);
