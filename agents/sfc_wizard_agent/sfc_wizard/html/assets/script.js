class SFCWizardChat {
    constructor() {
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.messageForm = document.getElementById('messageForm');
        this.socket = null;
        this.isReady = false;
        this.sessionId = null;
        this.sessionExpiryMinutes = 60;
        this.markdownConverter = new showdown.Converter({
            tables: true,
            tasklists: true,
            strikethrough: true,
            emoji: true
        });
        
        // Streaming state
        this.streamingMessageDiv = null;
        this.streamingContentDiv = null;
        this.streamingAccumulatedText = '';
        this.isStreaming = false;
        
        this.initializeSession();
        this.setupFormHandlers();
        this.setupBeforeUnloadHandler();
        this.showInitializingMessage();
        this.waitForAgentReady();
    }

    initializeSession() {
        // Try to get existing session from localStorage
        const sessionData = this.getStoredSession();
        
        if (sessionData && !this.isSessionExpired(sessionData)) {
            this.sessionId = sessionData.sessionId;
            console.log('Restored existing session:', this.sessionId);
        } else {
            // Generate new session ID
            this.sessionId = this.generateSessionId();
            this.storeSession(this.sessionId);
            console.log('Created new session:', this.sessionId);
        }
    }

    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 16) + '_' + Date.now();
    }

    storeSession(sessionId) {
        const sessionData = {
            sessionId: sessionId,
            timestamp: Date.now()
        };
        localStorage.setItem('sfc_wizard_session', JSON.stringify(sessionData));
    }

    getStoredSession() {
        try {
            const sessionJson = localStorage.getItem('sfc_wizard_session');
            if (!sessionJson) return null;
            return JSON.parse(sessionJson);
        } catch (error) {
            console.error('Error parsing stored session:', error);
            localStorage.removeItem('sfc_wizard_session');
            return null;
        }
    }

    isSessionExpired(sessionData) {
        const now = Date.now();
        const expiryTime = sessionData.timestamp + (this.sessionExpiryMinutes * 60 * 1000);
        return now > expiryTime;
    }

    setupBeforeUnloadHandler() {
        window.addEventListener('beforeunload', (e) => {
            // Only show dialog if there's an active conversation
            if (this.hasActiveConversation()) {
                e.preventDefault();
                e.returnValue = 'Are you sure you want to leave? Your conversation will be preserved for 5 minutes.';
                return e.returnValue;
            }
        });
    }

    hasActiveConversation() {
        // Check if there are any messages in the conversation
        return this.messagesContainer && this.messagesContainer.children.length > 1; // More than just welcome message
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
        
        // Send session ID to server after connection
        this.socket.on('connect', () => {
            console.log('Connected to server, sending session ID:', this.sessionId);
            this.socket.emit('register_session', { sessionId: this.sessionId });
        });
        
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

        // Handle streaming events
        this.socket.on('agent_streaming_start', () => {
            this.startStreaming();
        });

        this.socket.on('agent_streaming', (data) => {
            this.updateStreamingMessage(data.content);
        });

        this.socket.on('agent_streaming_end', () => {
            this.endStreaming();
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
        
        // Convert markdown to HTML if message is from assistant
        if (message.role === 'assistant') {
            // Process JSON blocks first
            const processedContent = this.processJsonBlocks(message.content);
            // Convert markdown to HTML
            content.innerHTML = this.markdownConverter.makeHtml(processedContent);
        } else {
            // For user messages, just escape HTML
            content.textContent = message.content;
        }

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
    
    processJsonBlocks(content) {
        // Regular expression to find JSON blocks
        const jsonPattern = /```json\n([\s\S]*?)```/g;
        
        return content.replace(jsonPattern, (match, jsonContent) => {
            try {
                // Try to parse and format the JSON
                const parsed = JSON.parse(jsonContent);
                const formattedJson = JSON.stringify(parsed, null, 2);
                
                // Generate a unique ID for the copy button
                const jsonId = `json_${Math.random().toString(36).substring(2, 10)}`;
                
                // Create formatted JSON block with copy button
                return `<div class="json-container">
<div class="json-header">
<span class="json-label">JSON Configuration</span>
<button class="copy-json-btn" onclick="copyJsonToClipboard('${jsonId}')" title="Copy JSON">
<i class="fas fa-copy"></i>
</button>
</div>
<pre class="json-code" id="${jsonId}"><code>${formattedJson}</code></pre>
</div>`;
            } catch (error) {
                // If it's not valid JSON, return as code block
                return `<pre><code>${jsonContent}</code></pre>`;
            }
        });
    }

    // Streaming methods
    startStreaming() {
        if (this.isStreaming) return; // Already streaming
        
        this.isStreaming = true;
        this.streamingAccumulatedText = '';
        
        // Create a temporary streaming message div
        this.streamingMessageDiv = document.createElement('div');
        this.streamingMessageDiv.className = 'message assistant streaming';

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';

        this.streamingContentDiv = document.createElement('div');
        this.streamingContentDiv.className = 'message-content streaming-content';
        this.streamingContentDiv.innerHTML = '<span class="streaming-cursor">▊</span>';

        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = this.formatTime(new Date().toISOString());

        this.streamingMessageDiv.appendChild(avatar);
        this.streamingMessageDiv.appendChild(this.streamingContentDiv);
        this.streamingContentDiv.appendChild(timestamp);

        this.messagesContainer.appendChild(this.streamingMessageDiv);
        this.scrollToBottom();
    }

    updateStreamingMessage(content) {
        if (!this.isStreaming || !this.streamingContentDiv) return;

        this.streamingAccumulatedText += content;
        
        // Update the content with streaming cursor
        const processedContent = this.processJsonBlocks(this.streamingAccumulatedText);
        const htmlContent = this.markdownConverter.makeHtml(processedContent);
        
        // Find the timestamp element to preserve it
        const timestamp = this.streamingContentDiv.querySelector('.timestamp');
        
        // Update content while preserving timestamp
        this.streamingContentDiv.innerHTML = htmlContent + '<span class="streaming-cursor">▊</span>';
        
        if (timestamp) {
            this.streamingContentDiv.appendChild(timestamp);
        }
        
        this.scrollToBottom();
    }

    endStreaming() {
        if (!this.isStreaming) return;
        
        this.isStreaming = false;
        
        // Remove streaming cursor and styling
        if (this.streamingContentDiv) {
            const cursor = this.streamingContentDiv.querySelector('.streaming-cursor');
            if (cursor) {
                cursor.remove();
            }
            this.streamingContentDiv.classList.remove('streaming-content');
        }
        
        if (this.streamingMessageDiv) {
            this.streamingMessageDiv.classList.remove('streaming');
        }
        
        // Reset streaming state
        this.streamingMessageDiv = null;
        this.streamingContentDiv = null;
        this.streamingAccumulatedText = '';
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
