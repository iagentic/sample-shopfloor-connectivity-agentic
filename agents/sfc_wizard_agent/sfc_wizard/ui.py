"""
UI module for SFC Wizard Agent Chat Interface.
Implements the agent loop as a web-based chat conversation.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import threading

from .agent import SFCWizardAgent, stdio_mcp_client


class ChatUI:
    """Web-based chat UI for SFC Wizard Agent."""

    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port

        # Initialize Flask app
        self.app = Flask(__name__, template_folder="html", static_folder="html/assets")

        # Initialize SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Store conversation history per session
        self.conversations: Dict[str, List[Dict]] = {}

        # SFC Wizard Agent will be initialized later within MCP context
        self.sfc_agent = None
        self.agent_ready = False

        # Setup routes and socket handlers
        self._setup_routes()
        self._setup_socket_handlers()

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def initialize_agent(self):
        """Initialize the SFC Wizard Agent within MCP context."""
        if self.sfc_agent is None:
            self.sfc_agent = SFCWizardAgent()
            self.agent_ready = True
            print("✅ SFC Wizard Agent initialized with MCP tools")

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route("/")
        def index():
            """Main chat interface."""
            # Generate session ID if not exists
            if "session_id" not in session:
                session["session_id"] = str(uuid.uuid4())
            return render_template("chat.html")

        @self.app.route("/health")
        def health():
            """Health check endpoint."""
            return jsonify({"status": "healthy", "service": "SFC Wizard Chat UI"})

        @self.app.route("/ready")
        def ready():
            """Agent readiness check endpoint."""
            if self.agent_ready and self.sfc_agent is not None:
                return jsonify({"status": "ready", "agent": "initialized"})
            else:
                return jsonify({"status": "not_ready", "agent": "initializing"}), 503

    def _setup_socket_handlers(self):
        """Setup SocketIO event handlers."""

        @self.socketio.on("connect")
        def handle_connect():
            """Handle client connection."""
            # Check if agent is ready before allowing connections
            if not self.agent_ready or self.sfc_agent is None:
                emit(
                    "agent_not_ready",
                    {"message": "Agent is still initializing. Please wait..."},
                )
                return False

            session_id = session.get("session_id", str(uuid.uuid4()))
            session["session_id"] = session_id

            # Initialize conversation for new session
            if session_id not in self.conversations:
                self.conversations[session_id] = []
                # Send welcome message
                welcome_message = self._get_welcome_message()
                formatted_welcome = self.sfc_agent._format_output(welcome_message)
                self.conversations[session_id].append(
                    {
                        "role": "assistant",
                        "content": formatted_welcome,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # Send conversation history to client
            emit("conversation_history", {"messages": self.conversations[session_id]})

            self.logger.info(f"Client connected with session: {session_id}")

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handle client disconnection."""
            session_id = session.get("session_id")
            self.logger.info(f"Client disconnected: {session_id}")

        @self.socketio.on("send_message")
        def handle_message(data):
            """Handle incoming chat message."""
            # Double-check agent readiness
            if not self.agent_ready or self.sfc_agent is None:
                emit(
                    "agent_response",
                    {
                        "role": "assistant",
                        "content": "❌ Agent is not ready yet. Please refresh the page and try again.",
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                return

            session_id = session.get("session_id")
            user_message = data.get("message", "").strip()

            if not user_message:
                return

            # Add user message to conversation
            user_msg = {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
            }

            if session_id not in self.conversations:
                self.conversations[session_id] = []

            self.conversations[session_id].append(user_msg)

            # Echo user message back to client
            emit("message_received", user_msg)

            # Check for exit commands
            if user_message.lower() in ["exit", "quit", "bye"]:
                goodbye_content = "🏭 Thank you for using the SFC Wizard!\nMay your industrial data flow smoothly to the cloud! ☁️"
                formatted_goodbye = self.sfc_agent._format_output(goodbye_content)
                goodbye_msg = {
                    "role": "assistant",
                    "content": formatted_goodbye,
                    "timestamp": datetime.now().isoformat(),
                }
                self.conversations[session_id].append(goodbye_msg)
                emit("agent_response", goodbye_msg)
                return

            # Capture session ID and socket ID before spawning thread
            current_sid = request.sid

            # Process message with agent in background thread
            def process_agent_response(sid):
                try:
                    # Emit typing indicator
                    self.socketio.emit("agent_typing", {"typing": True}, room=sid)

                    # Process with SFC Agent (this is where the agent loop happens)
                    response = self.sfc_agent.agent(user_message)

                    # Format the response for UI display
                    formatted_response = self.sfc_agent._format_output(str(response))

                    # Create response message
                    agent_msg = {
                        "role": "assistant",
                        "content": formatted_response,
                        "timestamp": datetime.now().isoformat(),
                    }

                    # Add to conversation history
                    self.conversations[session_id].append(agent_msg)

                    # Send response to client
                    self.socketio.emit("agent_response", agent_msg, room=sid)

                except Exception as e:
                    error_msg = {
                        "role": "assistant",
                        "content": f"❌ Error processing request: {str(e)}\nPlease try rephrasing your question or check your configuration.",
                        "timestamp": datetime.now().isoformat(),
                    }
                    self.conversations[session_id].append(error_msg)
                    self.socketio.emit("agent_response", error_msg, room=sid)
                    self.logger.error(f"Error processing message: {str(e)}")
                finally:
                    # Stop typing indicator
                    self.socketio.emit("agent_typing", {"typing": False}, room=sid)

            # Run agent processing in background thread
            thread = threading.Thread(
                target=process_agent_response, args=(current_sid,)
            )
            thread.daemon = True
            thread.start()

        @self.socketio.on("clear_conversation")
        def handle_clear_conversation():
            """Handle request to clear conversation."""
            session_id = session.get("session_id")
            if session_id in self.conversations:
                self.conversations[session_id] = []
                # Send new welcome message
                welcome_message = self._get_welcome_message()
                formatted_welcome = self.sfc_agent._format_output(welcome_message)
                self.conversations[session_id].append(
                    {
                        "role": "assistant",
                        "content": formatted_welcome,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                emit(
                    "conversation_cleared", {"messages": self.conversations[session_id]}
                )

    def _get_welcome_message(self) -> str:
        """Get the welcome message for new conversations."""
        return """🏭 **AWS SHOP FLOOR CONNECTIVITY (SFC) WIZARD**

Specialized assistant for industrial data connectivity to AWS

🎯 **I can help you with:**
• 🔍 Debug existing SFC configurations
• 🛠️ Create new SFC configurations  
• 💾 Save configurations to JSON files
• 📂 Load configurations from JSON files
• ▶️ Run configurations in local test environments
• 🧪 Test configurations against environments
• 🏗️ Define required deployment environments
• 📚 Explain SFC concepts and components
• 📊 Visualize data from configurations with FILE-TARGET
• 🚀 Type 'example' to run a sample configuration instantly

📋 **Supported Protocols:**
OPCUA | MODBUS | S7 | MQTT | HTTP | and more...

☁️ **Supported AWS Targets:**
AWS-S3 | AWS-IOT-CORE | AWS-TIMESTREAM | DEBUG | and more...

What would you like to do today?"""

    def run(self, debug=False):
        """Run the Flask-SocketIO server."""
        print("=" * 60)
        print("🏭 SFC WIZARD CHAT UI STARTING")
        print("=" * 60)
        print(f"🌐 Chat interface available at: http://{self.host}:{self.port}")
        print("📱 Open the URL in your web browser to start chatting")
        print("🔄 Real-time chat with the SFC Wizard Agent")
        print("=" * 60)

        try:
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=debug,
                allow_unsafe_werkzeug=True,
            )
        except KeyboardInterrupt:
            print("\n🛑 SFC Wizard Chat UI stopped by user")
        except Exception as e:
            print(f"❌ Error starting chat UI: {str(e)}")
        finally:
            # Cleanup SFC processes
            print("🧹 Cleaning up SFC processes...")
            if self.sfc_agent:
                self.sfc_agent._cleanup_processes()


def main():
    """Main function to run the SFC Wizard Chat UI."""
    try:
        with stdio_mcp_client:
            chat_ui = ChatUI(host="127.0.0.1", port=5000)
            # Initialize agent within MCP context
            chat_ui.initialize_agent()
            chat_ui.run(debug=False)
    except Exception as e:
        print(f"Error starting SFC Wizard Chat UI: {str(e)}")
        print(
            "Please make sure all dependencies are installed by running 'scripts/init.sh'"
        )


if __name__ == "__main__":
    main()
