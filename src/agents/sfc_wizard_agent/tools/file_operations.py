#!/usr/bin/env python3
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

AWS Shopfloor Connectivity (SFC) file operations module.
Handles reading and writing configuration files.
"""

import os
import json
from typing import Dict, Any


class SFCFileOperations:
    """Handles file operations for SFC configurations"""

    @staticmethod
    def read_config_from_file(filename: str) -> str:
        """Read configuration from a JSON file
        
        Args:
            filename: Name of the file to read the configuration from
            
        Returns:
            String result message with the loaded configuration
        """
        try:
            # Add file extension if not provided
            if not filename.lower().endswith(".json"):
                filename += ".json"

            # Check if file exists
            if not os.path.exists(filename):
                return f"❌ File not found: '{filename}'"

            # Read from file
            with open(filename, "r") as file:
                config = json.load(file)

            # Convert back to JSON string with proper indentation
            config_json = json.dumps(config, indent=2)

            return f"✅ Configuration loaded successfully from '{filename}':\n\n```json\n{config_json}\n```"
        except json.JSONDecodeError:
            return f"❌ Invalid JSON format in file: '{filename}'"
        except Exception as e:
            return f"❌ Error reading configuration: {str(e)}"

    @staticmethod
    def save_config_to_file(config_json: str, filename: str) -> str:
        """Save configuration to a JSON file
        
        Args:
            config_json: SFC configuration to save
            filename: Name of the file to save the configuration to
            
        Returns:
            String result message indicating success or failure
        """
        try:
            # Parse the JSON to ensure it's valid
            config = json.loads(config_json)

            # Add file extension if not provided
            if not filename.lower().endswith(".json"):
                filename += ".json"

            # Write to file
            with open(filename, "w") as file:
                json.dump(config, file, indent=2)

            return f"✅ Configuration saved successfully to '{filename}'"
        except json.JSONDecodeError:
            return "❌ Invalid JSON configuration provided"
        except Exception as e:
            return f"❌ Error saving configuration: {str(e)}"
