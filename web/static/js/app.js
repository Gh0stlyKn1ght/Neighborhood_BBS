// Neighborhood BBS - Main Application JavaScript

const API_BASE = '/api';

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('Neighborhood BBS loaded');
    loadRecentActivity();
});

/**
 * Load recent activity from the API
 */
async function loadRecentActivity() {
    try {
        const feed = document.getElementById('activity-feed');

        // Fetch recent posts
        const postsResponse = await fetch(`${API_BASE}/board/posts?limit=5`);
        const postsData = await postsResponse.json();

        // Fetch chat rooms
        const roomsResponse = await fetch(`${API_BASE}/chat/rooms`);
        const roomsData = await roomsResponse.json();

        const fragment = document.createDocumentFragment();

        // Display recent posts
        if (postsData.posts && postsData.posts.length > 0) {
            const postsHeading = document.createElement('h3');
            postsHeading.textContent = 'Recent Posts';
            fragment.appendChild(postsHeading);

            const postsList = document.createElement('div');
            postsList.className = 'activity-list';

            postsData.posts.forEach(post => {
                const item = document.createElement('div');
                item.className = 'activity-item';

                const title = document.createElement('strong');
                title.textContent = post.title;

                const author = document.createElement('em');
                author.textContent = 'by ' + post.author;

                const date = document.createElement('small');
                date.textContent = formatDate(post.created_at);

                item.appendChild(title);
                item.appendChild(author);
                item.appendChild(date);
                postsList.appendChild(item);
            });

            fragment.appendChild(postsList);
        }

        // Display active rooms
        if (roomsData.rooms && roomsData.rooms.length > 0) {
            const roomsHeading = document.createElement('h3');
            roomsHeading.textContent = 'Active Chat Rooms';
            roomsHeading.style.marginTop = '30px';
            fragment.appendChild(roomsHeading);

            const roomsList = document.createElement('div');
            roomsList.className = 'activity-list';

            roomsData.rooms.forEach(room => {
                const item = document.createElement('div');
                item.className = 'activity-item';

                const name = document.createElement('strong');
                name.textContent = room.name;

                const desc = document.createElement('small');
                desc.textContent = room.description || 'No description';

                item.appendChild(name);
                item.appendChild(desc);
                roomsList.appendChild(item);
            });

            fragment.appendChild(roomsList);
        }

        // Clear and append
        feed.textContent = '';
        if (fragment.childNodes.length > 0) {
            feed.appendChild(fragment);
        } else {
            feed.textContent = 'No recent activity yet.';
        }
    } catch (error) {
        console.error('Error loading activity:', error);
        const feed = document.getElementById('activity-feed');
        feed.textContent = 'Error loading activity. Please refresh.';
        feed.style.color = 'red';
    }
}

/**
 * Format date string for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

/**
 * Send a chat message
 */
async function sendMessage(roomId, author, content) {
    try {
        const response = await fetch(`${API_BASE}/chat/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                room_id: roomId,
                author: author,
                content: content
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log('Message sent:', data);
            return data;
        } else {
            throw new Error(data.error || 'Failed to send message');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Error: ' + error.message);
    }
}

/**
 * Create a new post
 */
async function createPost(title, content, author, category = 'general') {
    try {
        const response = await fetch(`${API_BASE}/board/posts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                content: content,
                author: author,
                category: category
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log('Post created:', data);
            return data;
        } else {
            throw new Error(data.error || 'Failed to create post');
        }
    } catch (error) {
        console.error('Error creating post:', error);
        alert('Error: ' + error.message);
    }
}

/**
 * Get chat history
 */
async function getChatHistory(roomId, limit = 50) {
    try {
        const response = await fetch(`${API_BASE}/chat/history/${roomId}?limit=${limit}`);
        const data = await response.json();
        
        if (response.ok) {
            return data.messages || [];
        } else {
            throw new Error(data.error || 'Failed to get chat history');
        }
    } catch (error) {
        console.error('Error getting chat history:', error);
        return [];
    }
}

/**
 * Get all chat rooms
 */
async function getChatRooms() {
    try {
        const response = await fetch(`${API_BASE}/chat/rooms`);
        const data = await response.json();
        
        if (response.ok) {
            return data.rooms || [];
        } else {
            throw new Error(data.error || 'Failed to get rooms');
        }
    } catch (error) {
        console.error('Error getting rooms:', error);
        return [];
    }
}

/**
 * Create a new chat room
 */
async function createChatRoom(name, description = '') {
    try {
        const response = await fetch(`${API_BASE}/chat/rooms`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                description: description
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log('Room created:', data);
            return data;
        } else {
            throw new Error(data.error || 'Failed to create room');
        }
    } catch (error) {
        console.error('Error creating room:', error);
        alert('Error: ' + error.message);
    }
}

/**
 * Get all posts
 */
async function getAllPosts(limit = 30, offset = 0) {
    try {
        const response = await fetch(`${API_BASE}/board/posts?limit=${limit}&offset=${offset}`);
        const data = await response.json();
        
        if (response.ok) {
            return data.posts || [];
        } else {
            throw new Error(data.error || 'Failed to get posts');
        }
    } catch (error) {
        console.error('Error getting posts:', error);
        return [];
    }
}

/**
 * Get specific post
 */
async function getPost(postId) {
    try {
        const response = await fetch(`${API_BASE}/board/posts/${postId}`);
        const data = await response.json();
        
        if (response.ok) {
            return data.post;
        } else {
            throw new Error(data.error || 'Failed to get post');
        }
    } catch (error) {
        console.error('Error getting post:', error);
        return null;
    }
}

/**
 * Add reply to post
 */
async function replyToPost(postId, author, content) {
    try {
        const response = await fetch(`${API_BASE}/board/posts/${postId}/replies`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                author: author,
                content: content
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log('Reply added:', data);
            return data;
        } else {
            throw new Error(data.error || 'Failed to add reply');
        }
    } catch (error) {
        console.error('Error adding reply:', error);
        alert('Error: ' + error.message);
    }
}

// Export functions for use in HTML
window.API = {
    sendMessage,
    createPost,
    getChatHistory,
    getChatRooms,
    createChatRoom,
    getAllPosts,
    getPost,
    replyToPost
};
