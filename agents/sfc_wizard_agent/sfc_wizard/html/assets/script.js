class SFCWizardChat {
    constructor() {
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.messageForm = document.getElementById('messageForm');
        this.socket = null;
        this.isReady = false;
        
        this.setupFormHandlers();
        this.showInitializingMessage();
        this.waitForAgentReady();
    }

    showInitializingMessage() {
        const initMessage = {
            role: 'assistant',
            content: '🔄 Initializing SFC Wizard Agent...\nPlease wait while the MCP server and agent startup.',
            timestamp: new Date().toISOString()
        };
        this.displayMessage(initMessage);
    }

    async waitForAgentReady() {
        const maxRetries = 30;
        let retries = 0;
        
        const checkReady = async () => {
            try {
                const response = await fetch('/ready');
                const data = await response.json();
                
                if (response.ok && data.status === 'ready') {
                    this.clearMessages();
                    this.initializeSocket();
                    return true;
                }
                
                if (retries >= maxRetries) {
                    this.showErrorMessage('❌ Agent initialization timeout. Please refresh the page to try again.');
                    return false;
                }
                
                retries++;
                setTimeout(checkReady, 1000);
                
            } catch (error) {
                console.error('Error checking agent readiness:', error);
                if (retries >= maxRetries) {
                    this.showErrorMessage('❌ Failed to connect to agent. Please refresh the page to try again.');
                    return false;
                }
                retries++;
                setTimeout(checkReady, 1000);
            }
        };
        
        checkReady();
    }

    showErrorMessage(message) {
        const errorMessage = {
            role: 'assistant',
            content: message,
            timestamp: new Date().toISOString()
        };
        this.clearMessages();
        this.displayMessage(errorMessage);
    }

    initializeSocket() {
        this.socket = io();
        this.isReady = true;
        this.setupSocketListeners();
        this.messageInput.placeholder = "Ask about SFC configurations, protocols, or type 'example' to try it out...";
        this.messageInput.focus();
        this.messageInput.disabled = false;
        this.sendBtn.disabled = false;
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('conversation_history', (data) => {
            this.clearMessages();
            data.messages.forEach(msg => this.displayMessage(msg));
        });

        this.socket.on('message_received', (message) => {
            this.displayMessage(message);
        });

        this.socket.on('agent_response', (message) => {
            this.displayMessage(message);
            this.hideTypingIndicator();
        });

        this.socket.on('agent_typing', (data) => {
            if (data.typing) {
                this.showTypingIndicator();
            } else {
                this.hideTypingIndicator();
            }
        });

        this.socket.on('conversation_cleared', (data) => {
            this.clearMessages();
            data.messages.forEach(msg => this.displayMessage(msg));
        });

        this.socket.on('agent_not_ready', (data) => {
            this.showErrorMessage(data.message);
        });

        this.socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
            this.showErrorMessage('❌ Connection failed. Please refresh the page to try again.');
        });
    }

    setupFormHandlers() {
        this.messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    sendMessage() {
        if (!this.isReady || !this.socket) {
            this.showErrorMessage('❌ Agent is not ready. Please wait for initialization to complete.');
            return;
        }

        const message = this.messageInput.value.trim();
        if (!message) return;

        this.socket.emit('send_message', { message });
        this.messageInput.value = '';
        this.messageInput.focus();
    }

    displayMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.innerHTML = message.role === 'user' ? 
            '<i class="fas fa-user"></i>' : 
            '<i class="fas fa-robot"></i>';

        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = message.content;

        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = this.formatTime(message.timestamp);

        if (message.role === 'user') {
            messageDiv.appendChild(content);
            messageDiv.appendChild(avatar);
            content.appendChild(timestamp);
        } else {
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(content);
            content.appendChild(timestamp);
        }

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        this.typingIndicator.classList.add('show');
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.classList.remove('show');
    }

    clearMessages() {
        this.messagesContainer.innerHTML = '';
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

function clearConversation() {
    if (!window.chat.isReady || !window.chat.socket) {
        alert('Agent is not ready yet. Please wait for initialization to complete.');
        return;
    }
    
    if (confirm('Are you sure you want to clear the conversation?')) {
        window.chat.socket.emit('clear_conversation');
    }
}

function copyJsonToClipboard(jsonId) {
    const jsonElement = document.getElementById(jsonId);
    if (!jsonElement) {
        console.error('JSON element not found:', jsonId);
        return;
    }
    
    const jsonText = jsonElement.textContent;
    
    // Use the Clipboard API if available
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(jsonText).then(() => {
            showCopyFeedback(jsonId);
        }).catch(err => {
            console.error('Failed to copy JSON:', err);
            fallbackCopyTextToClipboard(jsonText, jsonId);
        });
    } else {
        // Fallback for older browsers
        fallbackCopyTextToClipboard(jsonText, jsonId);
    }
}

function fallbackCopyTextToClipboard(text, jsonId) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showCopyFeedback(jsonId);
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
        alert('Failed to copy JSON to clipboard. Please select and copy manually.');
    }
    
    document.body.removeChild(textArea);
}

function showCopyFeedback(jsonId) {
    // Find the copy button for this JSON block
    const copyBtn = document.querySelector(`button[onclick*="${jsonId}"]`);
    if (copyBtn) {
        const originalHTML = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i>';
        copyBtn.style.color = '#28a745';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalHTML;
            copyBtn.style.color = '';
        }, 2000);
    }
}

// Initialize chat when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chat = new SFCWizardChat();
});
