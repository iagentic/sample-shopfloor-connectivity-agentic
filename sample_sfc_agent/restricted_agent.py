#!/usr/bin/env python3
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

Restricted Agent using Strands Framework
Asks predefined questions on startup and operates within defined constraints.
"""

import sys
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from strands import Agent, tool
    from strands.models import BedrockModel
except ImportError:
    print(
        "Strands SDK not found. Please run 'scripts/init.sh' to install dependencies."
    )
    sys.exit(1)


class RestrictedAgent:
    """
    A restricted agent that asks predefined questions on startup
    and operates within specific constraints.
    """

    def __init__(self):
        self.predefined_questions = [
            "What is your name?",
            "What task would you like me to help you with today?",
            "Do you have any specific constraints or requirements?",
            "What is the expected outcome of this task?",
            "Are there any resources or information I should be aware of?",
        ]
        self.user_responses = {}
        self.restricted_mode = True
        self.allowed_topics = [
            "general assistance",
            "information lookup",
            "text processing",
            "simple calculations",
            "task planning",
        ]

        # Initialize the Strands agent with restricted tools
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """Create a Strands agent with restricted capabilities"""

        @tool
        def get_user_info(key: str) -> str:
            """Get information provided by the user during startup.

            Args:
                key: The information key to retrieve (name, task, constraints, outcome, resources)
            """
            return self.user_responses.get(key, "Not provided")

        @tool
        def check_topic_allowed(topic: str) -> bool:
            """Check if a topic is within allowed restrictions.

            Args:
                topic: The topic to check
            """
            return any(allowed in topic.lower() for allowed in self.allowed_topics)

        @tool
        def simple_calculator(expression: str) -> str:
            """Perform simple mathematical calculations.

            Args:
                expression: Mathematical expression to evaluate (basic operations only)
            """
            try:
                # Only allow basic mathematical operations for safety
                allowed_chars = set("0123456789+-*/.() ")
                if not all(c in allowed_chars for c in expression):
                    return "Error: Only basic mathematical operations are allowed"

                result = eval(expression)
                return f"Result: {result}"
            except Exception as e:
                return f"Error: {str(e)}"

        # Create agent with restricted tools
        try:
            # Try to use Bedrock model (default)
            model = BedrockModel()
            agent = Agent(
                model=model,
                tools=[get_user_info, check_topic_allowed, simple_calculator],
            )
        except Exception:
            # Fallback to default model if Bedrock is not available
            agent = Agent(tools=[get_user_info, check_topic_allowed, simple_calculator])

        return agent

    def boot(self):
        """Boot sequence that asks predefined questions"""
        print("=" * 50)
        print("🤖 RESTRICTED AGENT STARTUP")
        print("=" * 50)
        print("I'm a restricted AI agent designed to help within specific guidelines.")
        print("Before we begin, I need to ask you a few questions:\n")

        # Ask predefined questions
        question_keys = ["name", "task", "constraints", "outcome", "resources"]

        for i, question in enumerate(self.predefined_questions):
            print(f"Question {i+1}: {question}")
            response = input("Your answer: ").strip()

            if response:
                self.user_responses[question_keys[i]] = response
            else:
                self.user_responses[question_keys[i]] = "Not provided"
            print()

        # Display collected information
        print("=" * 50)
        print("📋 COLLECTED INFORMATION")
        print("=" * 50)
        for key, value in self.user_responses.items():
            print(f"{key.capitalize()}: {value}")

        print("\n" + "=" * 50)
        print("🚀 AGENT READY")
        print("=" * 50)
        print("I'm now ready to assist you within my restricted capabilities.")
        print("My allowed topics include:", ", ".join(self.allowed_topics))
        print("Type 'exit' or 'quit' to end the session.\n")

    def run(self):
        """Main interaction loop"""
        self.boot()

        while True:
            try:
                user_input = input("You: ").strip()

                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("Agent: Goodbye! Have a great day!")
                    break

                if not user_input:
                    continue

                # Check if the request is within allowed boundaries
                if not self._is_request_allowed(user_input):
                    print(
                        "Agent: I'm sorry, but that request is outside my allowed capabilities."
                    )
                    print(f"I can help with: {', '.join(self.allowed_topics)}")
                    continue

                # Process with Strands agent
                try:
                    response = self.agent(user_input)
                    print(f"Agent: {response}")
                except Exception as e:
                    print(f"Agent: I encountered an error: {str(e)}")
                    print("Please try rephrasing your request.")

            except KeyboardInterrupt:
                print("\nAgent: Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"Agent: An unexpected error occurred: {str(e)}")

    def _is_request_allowed(self, request: str) -> bool:
        """Check if a request is within allowed boundaries"""
        request_lower = request.lower()

        # Check for prohibited content
        prohibited_keywords = [
            "hack",
            "exploit",
            "malware",
            "virus",
            "illegal",
            "harmful",
            "dangerous",
            "weapon",
            "drug",
        ]

        if any(keyword in request_lower for keyword in prohibited_keywords):
            return False

        # Check if request aligns with allowed topics
        return (
            any(topic in request_lower for topic in self.allowed_topics)
            or len(request.split()) <= 20
        )  # Allow short, general queries

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "restricted_mode": self.restricted_mode,
            "allowed_topics": self.allowed_topics,
            "user_responses": self.user_responses,
            "questions_asked": len(self.predefined_questions),
        }


def main():
    """Main function to run the restricted agent"""
    print("Starting Restricted Agent...")

    try:
        agent = RestrictedAgent()
        agent.run()
    except Exception as e:
        print(f"Error starting agent: {str(e)}")
        print(
            "Please make sure all dependencies are installed by running 'scripts/init.sh'"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
