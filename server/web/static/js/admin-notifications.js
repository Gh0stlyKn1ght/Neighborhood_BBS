/**
 * Admin Notifications Module
 * Manages real-time notifications with automatic polling
 * 
 * Phase 4 Week 14
 */

class NotificationManager {
    constructor(adminAuthInstance) {
        this.auth = adminAuthInstance;
        this.notifications = [];
        this.unreadCount = 0;
        this.pollingInterval = 5000; // 5 seconds
        this.pollingTimer = null;
        this.pollAttempts = 0;
        this.isPolling = false;
        this.requestTimeout = 10000; // 10 second timeout
        
        // Listeners for UI updates
        this.onNotificationsUpdate = null;
        this.onUnreadCountUpdate = null;
        this.onNotificationReceived = null;
    }
    
    /**
     * Initialize notification manager
     * Sets up polling and API endpoints
     */
    async init() {
        console.log('Initializing NotificationManager');
        
        // Load initial notifications
        await this.fetchNotifications();
        
        // Start polling for new notifications
        this.startPolling();
    }
    
    /**
     * Start automatic polling for notifications
     * Uses exponential backoff if no changes detected
     */
    startPolling() {
        if (this.isPolling) return;
        
        this.isPolling = true;
        this.pollAttempts = 0;
        
        const poll = async () => {
            try {
                const oldCount = this.unreadCount;
                await this.fetchNotifications();
                
                // If got new notifications, reset attempts and poll frequently
                if (this.unreadCount > oldCount) {
                    this.pollAttempts = 0;
                } else {
                    this.pollAttempts++;
                }
                
                // Exponential backoff: 5s, 10s, 20s, 30s (max)
                const backoffInterval = Math.min(5000 * Math.pow(1.5, this.pollAttempts), 30000);
                
                this.pollingTimer = setTimeout(poll, backoffInterval);
            } catch (error) {
                console.error('Polling error:', error);
                this.pollingTimer = setTimeout(poll, this.pollingInterval);
            }
        };
        
        this.pollingTimer = setTimeout(poll, this.pollingInterval);
    }
    
    /**
     * Stop automatic polling
     */
    stopPolling() {
        if (this.pollingTimer) {
            clearTimeout(this.pollingTimer);
            this.pollingTimer = null;
        }
        this.isPolling = false;
    }
    
    /**
     * Fetch notifications from server
     * 
     * @param {number} limit - Max notifications to fetch (default 50)
     * @param {number} offset - Pagination offset (default 0)
     * @param {boolean} unreadOnly - Only fetch unread (default false)
     */
    async fetchNotifications(limit = 50, offset = 0, unreadOnly = false) {
        try {
            const token = this.auth.getToken();
            if (!token) {
                console.warn('No auth token available');
                return [];
            }
            
            const params = new URLSearchParams({
                limit,
                offset,
                unread: unreadOnly ? 'true' : 'false'
            });
            
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), this.requestTimeout);
            
            const response = await fetch(
                `/api/admin-management/notifications?${params}`,
                {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    signal: controller.signal
                }
            );
            
            clearTimeout(timeout);
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.auth.logout();
                    return [];
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'ok') {
                this.notifications = data.data || [];
                
                if (this.onNotificationsUpdate) {
                    this.onNotificationsUpdate(this.notifications);
                }
                
                return this.notifications;
            }
            
            return [];
        } catch (error) {
            console.error('Error fetching notifications:', error);
            return [];
        }
    }
    
    /**
     * Get unread notification count
     */
    async getUnreadCount() {
        try {
            const token = this.auth.getToken();
            if (!token) return 0;
            
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), this.requestTimeout);
            
            const response = await fetch(
                '/api/admin-management/notifications/unread',
                {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    signal: controller.signal
                }
            );
            
            clearTimeout(timeout);
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.auth.logout();
                    return 0;
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'ok' && data.data) {
                const oldCount = this.unreadCount;
                this.unreadCount = data.data.unread || 0;
                
                // Trigger callback if count changed
                if (oldCount !== this.unreadCount && this.onUnreadCountUpdate) {
                    this.onUnreadCountUpdate(this.unreadCount);
                }
                
                return this.unreadCount;
            }
            
            return 0;
        } catch (error) {
            console.error('Error getting unread count:', error);
            return 0;
        }
    }
    
    /**
     * Mark a notification as read
     * 
     * @param {string} notificationId - Notification ID
     */
    async markAsRead(notificationId) {
        try {
            const token = this.auth.getToken();
            if (!token) return false;
            
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), this.requestTimeout);
            
            const response = await fetch(
                `/api/admin-management/notifications/${notificationId}/read`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    signal: controller.signal
                }
            );
            
            clearTimeout(timeout);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            // Update local state
            const notif = this.notifications.find(n => n.notification_id === notificationId);
            if (notif) {
                notif.read = 1;
                this.unreadCount = Math.max(0, this.unreadCount - 1);
                
                if (this.onNotificationsUpdate) {
                    this.onNotificationsUpdate(this.notifications);
                }
                if (this.onUnreadCountUpdate) {
                    this.onUnreadCountUpdate(this.unreadCount);
                }
            }
            
            return true;
        } catch (error) {
            console.error('Error marking notification as read:', error);
            return false;
        }
    }
    
    /**
     * Mark all notifications as read
     */
    async markAllAsRead() {
        try {
            const token = this.auth.getToken();
            if (!token) return 0;
            
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), this.requestTimeout);
            
            const response = await fetch(
                '/api/admin-management/notifications/read-all',
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    signal: controller.signal
                }
            );
            
            clearTimeout(timeout);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // Update local state
            this.notifications.forEach(n => n.read = 1);
            this.unreadCount = 0;
            
            if (this.onNotificationsUpdate) {
                this.onNotificationsUpdate(this.notifications);
            }
            if (this.onUnreadCountUpdate) {
                this.onUnreadCountUpdate(this.unreadCount);
            }
            
            return data.count || 0;
        } catch (error) {
            console.error('Error marking all as read:', error);
            return 0;
        }
    }
    
    /**
     * Delete a notification
     * 
     * @param {string} notificationId - Notification ID
     */
    async deleteNotification(notificationId) {
        try {
            const token = this.auth.getToken();
            if (!token) return false;
            
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), this.requestTimeout);
            
            const response = await fetch(
                `/api/admin-management/notifications/${notificationId}`,
                {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    signal: controller.signal
                }
            );
            
            clearTimeout(timeout);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            // Update local state
            const index = this.notifications.findIndex(n => n.notification_id === notificationId);
            if (index > -1) {
                const wasUnread = !this.notifications[index].read;
                this.notifications.splice(index, 1);
                
                if (wasUnread) {
                    this.unreadCount = Math.max(0, this.unreadCount - 1);
                }
                
                if (this.onNotificationsUpdate) {
                    this.onNotificationsUpdate(this.notifications);
                }
                if (this.onUnreadCountUpdate) {
                    this.onUnreadCountUpdate(this.unreadCount);
                }
            }
            
            return true;
        } catch (error) {
            console.error('Error deleting notification:', error);
            return false;
        }
    }
    
    /**
     * Delete multiple notifications (batch operation)
     * 
     * @param {string[]} notificationIds - Array of notification IDs
     */
    async batchDelete(notificationIds) {
        try {
            const token = this.auth.getToken();
            if (!token) return 0;
            
            if (!Array.isArray(notificationIds) || notificationIds.length === 0) {
                return 0;
            }
            
            // Limit to 100 per request
            const ids = notificationIds.slice(0, 100);
            
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), this.requestTimeout);
            
            const response = await fetch(
                '/api/admin-management/notifications/batch-delete',
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ notification_ids: ids }),
                    signal: controller.signal
                }
            );
            
            clearTimeout(timeout);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            // Update local state
            ids.forEach(id => {
                const index = this.notifications.findIndex(n => n.notification_id === id);
                if (index > -1) {
                    if (!this.notifications[index].read) {
                        this.unreadCount--;
                    }
                    this.notifications.splice(index, 1);
                }
            });
            
            this.unreadCount = Math.max(0, this.unreadCount);
            
            if (this.onNotificationsUpdate) {
                this.onNotificationsUpdate(this.notifications);
            }
            if (this.onUnreadCountUpdate) {
                this.onUnreadCountUpdate(this.unreadCount);
            }
            
            const data = await response.json();
            return data.count || 0;
        } catch (error) {
            console.error('Error in batch delete:', error);
            return 0;
        }
    }
    
    /**
     * Get notification statistics
     */
    async getStats() {
        try {
            const token = this.auth.getToken();
            if (!token) return null;
            
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), this.requestTimeout);
            
            const response = await fetch(
                '/api/admin-management/notifications/stats',
                {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    signal: controller.signal
                }
            );
            
            clearTimeout(timeout);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            return data.status === 'ok' ? data.data : null;
        } catch (error) {
            console.error('Error getting stats:', error);
            return null;
        }
    }
    
    /**
     * Get a single notification by ID
     * 
     * @param {string} notificationId - Notification ID
     */
    async getNotification(notificationId) {
        try {
            const token = this.auth.getToken();
            if (!token) return null;
            
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), this.requestTimeout);
            
            const response = await fetch(
                `/api/admin-management/notifications/${notificationId}`,
                {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    signal: controller.signal
                }
            );
            
            clearTimeout(timeout);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            return data.status === 'ok' ? data.data : null;
        } catch (error) {
            console.error('Error getting notification:', error);
            return null;
        }
    }
    
    /**
     * Show a toast notification in the UI
     * 
     * @param {object} notification - Notification object
     */
    showToast(notification) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `notification-toast notification-${notification.severity}`;
        toast.innerHTML = `
            <div class="toast-content">
                <strong>${notification.title}</strong>
                <p>${notification.message}</p>
            </div>
            <button class="toast-close">&times;</button>
        `;
        
        // Add to page
        const container = document.getElementById('toast-container') || 
                         document.body.appendChild(Object.assign(document.createElement('div'), {
                             id: 'toast-container',
                             className: 'toast-container'
                         }));
        
        container.appendChild(toast);
        
        // Close button handler
        toast.querySelector('.toast-close').onclick = () => {
            toast.remove();
        };
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
        
        return toast;
    }
    
    /**
     * Get current notifications list
     */
    getNotifications() {
        return this.notifications;
    }
    
    /**
     * Get unread count
     */
    getUnreadCountSync() {
        return this.unreadCount;
    }
    
    /**
     * Clear all notifications from memory
     */
    clear() {
        this.notifications = [];
        this.unreadCount = 0;
    }
}

// Create global instance
let notificationManager = null;

function initNotificationManager(authInstance) {
    notificationManager = new NotificationManager(authInstance);
    window.notificationManager = notificationManager;
    return notificationManager;
}
