#!/usr/bin/env python3
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

AWS Shopfloor Connectivity (SFC) Wizard Agent
Specialized assistant for debugging, creating, and testing SFC configurations.
"""

import sys
import os
import json
import shutil
import tempfile
import subprocess
import requests
import zipfile
import logging
import time
import threading
import queue
from logging.handlers import RotatingFileHandler
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Import the externalized functions
from src.tools.config_generator import generate_config_template
from src.tools.sfc_knowledge import load_sfc_knowledge
from src.tools.config_validator import SFCConfigValidator
from src.tools.diagnostics import diagnose_issue, suggest_optimizations
from src.tools.sfc_explanations import generate_environment_specs, what_is_sfc, explain_concept
from src.tools.file_operations import SFCFileOperations
from src.tools.log_operations import SFCLogOperations
from src.tools.folder_operations import SFCFolderOperations
from src.tools.sfc_module_analyzer import analyze_sfc_config_for_modules

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


class SFCWizardAgent:
    """
    AWS Shopfloor Connectivity (SFC) Wizard Agent
    Specialized for debugging existing configurations, creating new ones,
    testing configurations, and defining environments.
    """

    def __init__(self):
        self.sfc_knowledge = load_sfc_knowledge()
        self.current_config = None
        self.validation_errors = []
        self.recommendations = []
        # Track active SFC processes for cleanup
        self.active_processes = []

        # Initialize the Strands agent with SFC-specific tools
        self.agent = self._create_agent()

    # _load_sfc_knowledge method has been externalized to src/tools/sfc_knowledge.py

    def _create_agent(self) -> Agent:
        """Create a Strands agent with SFC-specific tools"""
        
        # Current running SFC config and log tail thread
        self.current_config_name = None
        self.log_tail_thread = None
        self.log_tail_stop_event = threading.Event()
        self.log_buffer = queue.Queue(maxsize=100)  # Buffer for log messages

        @tool
        def validate_sfc_config(config_json: str) -> str:
            """Validate an SFC configuration file for correctness and completeness.

            Args:
                config_json: JSON string containing the SFC configuration
            """
            try:
                # Parse the configuration
                config = json.loads(config_json)
                self.current_config = config
                
                # Create validator instance and validate the config
                validator = SFCConfigValidator(self.sfc_knowledge)
                is_valid = validator.validate_config(config)
                
                # Store validation results
                self.validation_errors = validator.get_errors()
                self.recommendations = validator.get_recommendations()
                
                # Return validation results
                if not is_valid:
                    return f"❌ Configuration validation failed:\n" + "\n".join(
                        self.validation_errors
                    )
                else:
                    result = "✅ Configuration is valid!"
                    if self.recommendations:
                        result += "\n\n💡 Recommendations:\n" + "\n".join(
                            self.recommendations
                        )
                    return result

            except json.JSONDecodeError as e:
                return f"❌ Invalid JSON format: {str(e)}"
            except Exception as e:
                return f"❌ Validation error: {str(e)}"

        @tool
        def create_sfc_config_template(
            protocol: str, target: str, environment: str = "development"
        ) -> str:
            """Create an SFC configuration template for a specific protocol and target.

            Args:
                protocol: Source protocol (e.g., OPCUA, MODBUS, S7)
                target: Target service (e.g., AWS-S3, AWS-IOT-CORE, DEBUG)
                environment: Environment type (development, production)
            """
            return generate_config_template(
                protocol.upper(), target.upper(), environment, self.sfc_knowledge
            )

        @tool
        def diagnose_sfc_issue(issue_description: str, config_json: str = "") -> str:
            """Diagnose common SFC issues and provide troubleshooting steps.

            Args:
                issue_description: Description of the problem
                config_json: Optional SFC configuration (if available)
            """
            return diagnose_issue(issue_description, config_json, self.sfc_knowledge)

        @tool
        def suggest_sfc_optimization(
            config_json: str, performance_requirements: str = ""
        ) -> str:
            """Suggest optimizations for an SFC configuration based on performance requirements.

            Args:
                config_json: Current SFC configuration
                performance_requirements: Description of performance needs
            """
            return suggest_optimizations(config_json, performance_requirements, self.sfc_knowledge)

        @tool
        def generate_environment_specs(
            protocol: str, devices: str, data_volume: str, targets: str
        ) -> str:
            """Generate environment specifications needed for SFC deployment.

            Args:
                protocol: Primary protocol to be used
                devices: Description of devices to connect
                data_volume: Expected data volume and frequency
                targets: Target AWS services or systems
            """
            return generate_environment_specs(
                protocol, devices, data_volume, targets, self.sfc_knowledge
            )

        @tool
        def explain_sfc_concept(concept: str) -> str:
            """Explain SFC concepts, components, or configuration options.

            Args:
                concept: SFC concept to explain (e.g., schedules, transformations, filters)
            """
            return explain_concept(concept, self.sfc_knowledge)


        @tool
        def read_config_from_file(filename: str) -> str:
            """Read an SFC configuration from a JSON file.

            Args:
                filename: Name of the file to read the configuration from
            """
            return SFCFileOperations.read_config_from_file(filename)

        @tool
        def save_config_to_file(config_json: str, filename: str) -> str:
            """Save an SFC configuration to a JSON file.

            Args:
                config_json: SFC configuration to save
                filename: Name of the file to save the configuration to
            """
            return SFCFileOperations.save_config_to_file(config_json, filename)

        @tool
        def run_sfc_config_locally(config_json: str, config_name: str = "") -> str:
            """Run an SFC configuration locally in a test environment.

            Downloads SFC resources and runs the configuration in a local test environment.

            Args:
                config_json: SFC configuration to run
                config_name: Optional name for the configuration and test folder (defaults to timestamp if not provided)
            """
            return self._run_sfc_config_locally(config_json, config_name)

        @tool
        def what_is_sfc() -> str:
            """Provides an explanation of what Shop Floor Connectivity (SFC) is and its key features."""
            return what_is_sfc()
        
        @tool
        def tail_logs(lines: int = 20, follow: bool = False) -> str:
            """Display the most recent lines from the SFC log file for the current running configuration.
            
            Args:
                lines: Number of recent log lines to show (default: 20)
                follow: If True, continuously display new log lines in real-time.
                        To exit follow mode, press Ctrl+C in the terminal.
            
            Note: When follow=True, the function will enter a real-time viewing mode.
                  The only way to exit this mode is by pressing Ctrl+C in the terminal.
                  After exiting, you'll be returned to the command prompt.
            """
            return SFCLogOperations.tail_logs(self.current_config_name, lines, follow, self.log_buffer)
            
            
        @tool
        def clean_runs_folder() -> str:
            """Clean the runs folder by removing all SFC runs to free up disk space.
            
            This tool will ask for confirmation (y/n) before deleting any files.
            Active configurations will be preserved.
            """
            return SFCFolderOperations.clean_runs_folder(
                current_config_name=self.current_config_name,
                last_config_name=self.last_config_name
            )
            
        @tool
        def confirm_clean_runs_folder(confirmation: str) -> str:
            """Confirm and execute the cleaning of the runs folder after receiving user confirmation.
            
            Args:
                confirmation: User's response (y/n) to the deletion confirmation prompt
            """
            return SFCFolderOperations.confirm_clean_runs_folder(
                confirmation,
                current_config_name=self.current_config_name,
                last_config_name=self.last_config_name
            )

        # Create agent with SFC-specific tools
        try:
            model = BedrockModel()
            agent = Agent(
                model=model,
                tools=[
                    validate_sfc_config,
                    create_sfc_config_template,
                    diagnose_sfc_issue,
                    suggest_sfc_optimization,
                    generate_environment_specs,
                    explain_sfc_concept,
                    read_config_from_file,
                    save_config_to_file,
                    run_sfc_config_locally,
                    what_is_sfc,
                    tail_logs,
                    clean_runs_folder,
                    confirm_clean_runs_folder,
                ],
            )
        except Exception:
            agent = Agent(
                tools=[
                    validate_sfc_config,
                    create_sfc_config_template,
                    diagnose_sfc_issue,
                    suggest_sfc_optimization,
                    generate_environment_specs,
                    explain_sfc_concept,
                    read_config_from_file,
                    save_config_to_file,
                    run_sfc_config_locally,
                    what_is_sfc,
                    tail_logs,
                    clean_runs_folder,
                    confirm_clean_runs_folder,
                ]
            )

        return agent

    # Validation methods have been externalized to src/tools/config_validator.py

    # _generate_config_template method has been externalized to src/tools/config_generator.py

    # _diagnose_issue method has been externalized to src/tools/diagnostics.py
    
    # _suggest_optimizations method has been externalized to src/tools/diagnostics.py

    # _generate_environment_specs method has been externalized to src/tools/sfc_explanations.py

    # _what_is_sfc method has been externalized to src/tools/sfc_explanations.py

    # _explain_concept method has been externalized to src/tools/sfc_explanations.py

    # _read_config_from_file method has been externalized to src/tools/file_operations.py

    # TODO: externalize runner...

    def _run_sfc_config_locally(self, config_json: str, config_name: str = "") -> str:
        """Run SFC configuration locally in a test environment"""
        try:
            # First, terminate any existing SFC processes
            if self.active_processes:
                print("🛑 Stopping existing SFC processes before starting a new one...")
                for process in self.active_processes:
                    if process.poll() is None:  # Process is still running
                        try:
                            process.terminate()
                            process.wait(timeout=2)  # Wait for up to 2 seconds
                        except:
                            # If termination fails, force kill
                            try:
                                process.kill()
                            except:
                                pass
                # Clear the list of active processes
                self.active_processes = []
                print("✅ Existing SFC processes terminated")

            # Parse the JSON to ensure it's valid
            config = json.loads(config_json)

            # Generate a name for the config and test directory if not provided
            if not config_name:
                import datetime

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                config_name = f"sfc_test_{timestamp}"

            # Create base directories
            base_dir = os.getcwd()

            # Create the modules directory at the same level as runs
            modules_dir = os.path.join(base_dir, "modules")
            if not os.path.exists(modules_dir):
                os.makedirs(modules_dir)

            # Create the runs directory
            runs_dir = os.path.join(base_dir, "runs")
            if not os.path.exists(runs_dir):
                os.makedirs(runs_dir)

            # Create a test directory with the config name inside the runs folder
            test_dir = os.path.join(runs_dir, config_name)
            if not os.path.exists(test_dir):
                os.makedirs(test_dir)

            # Save the configuration to a file in the test directory
            config_filename = os.path.join(test_dir, "config.json")
            with open(config_filename, "w") as file:
                json.dump(config, file, indent=2)

            # Fetch the latest SFC release information
            response = requests.get(
                "https://api.github.com/repos/aws-samples/shopfloor-connectivity/releases/latest"
            )
            if response.status_code != 200:
                return f"❌ Failed to fetch SFC release information: HTTP {response.status_code}"

            release_data = response.json()
            sfc_version = release_data["tag_name"]

            # Analyze the configuration to determine which modules are needed
            needed_modules = analyze_sfc_config_for_modules(config)

            # Check if SFC main module exists in shared modules directory or download it
            sfc_main_module = "sfc-main"
            module_target_dir = os.path.join(modules_dir, sfc_main_module)

            if not os.path.exists(module_target_dir):
                sfc_main_url = f"https://github.com/aws-samples/shopfloor-connectivity/releases/download/{sfc_version}/{sfc_main_module}.tar.gz"

                # Download the SFC main binary
                print(f"⬇️ Downloading SFC main {sfc_version}...")
                try:
                    tarball_response = requests.get(sfc_main_url, stream=True)
                    if tarball_response.status_code != 200:
                        return f"❌ Failed to download SFC main binary: HTTP {tarball_response.status_code}"

                    tarball_file_path = os.path.join(
                        modules_dir, f"{sfc_main_module}.tar.gz"
                    )
                    with open(tarball_file_path, "wb") as f:
                        for chunk in tarball_response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    # Extract the SFC main binary to modules directory
                    print(f"📦 Extracting SFC main binary...")
                    import tarfile

                    os.makedirs(module_target_dir, exist_ok=True)

                    # Extract with proper path handling to avoid duplicate directories
                    with tarfile.open(tarball_file_path, "r:gz") as tar:
                        # Check if all files are under a common root directory
                        root_dirs = set()
                        for member in tar.getmembers():
                            parts = member.name.split("/")
                            if parts:
                                root_dirs.add(parts[0])

                        # If everything is under one directory (likely named same as the module)
                        # extract contents directly without the extra directory level
                        if len(root_dirs) == 1:
                            common_prefix = list(root_dirs)[0] + "/"
                            for member in tar.getmembers():
                                if member.name.startswith(common_prefix):
                                    member.name = member.name[len(common_prefix) :]
                                    # Skip directories that would extract to root
                                    if member.name:
                                        tar.extract(member, path=module_target_dir)
                        else:
                            # No common prefix, extract normally
                            tar.extractall(path=module_target_dir)
                except Exception as e:
                    return f"❌ Error downloading/extracting SFC main binary: {str(e)}"
            else:
                print(f"✅ Using cached SFC main binary from {module_target_dir}")

            # We don't need to copy or link anymore, as we'll use the SFC_DEPLOYMENT_DIR

            # Download and extract needed modules
            successful_modules = []
            failed_modules = []

            for module in needed_modules:
                module_target_dir = os.path.join(modules_dir, module)

                # Check if module already exists in shared modules directory
                if not os.path.exists(module_target_dir):
                    module_url = f"https://github.com/aws-samples/shopfloor-connectivity/releases/download/{sfc_version}/{module}.tar.gz"
                    print(f"⬇️ Downloading module: {module}...")

                    try:
                        module_response = requests.get(module_url, stream=True)
                        if module_response.status_code != 200:
                            print(
                                f"⚠️ Module {module} not found or cannot be downloaded"
                            )
                            failed_modules.append(module)
                            continue

                        # Save the module tar.gz file
                        module_file_path = os.path.join(modules_dir, f"{module}.tar.gz")
                        with open(module_file_path, "wb") as f:
                            for chunk in module_response.iter_content(chunk_size=8192):
                                f.write(chunk)

                        # Extract the module to shared modules directory
                        print(f"📦 Extracting module: {module}...")
                        import tarfile

                        os.makedirs(module_target_dir, exist_ok=True)

                        # Extract with proper path handling to avoid duplicate directories
                        with tarfile.open(module_file_path, "r:gz") as tar:
                            # Check if all files are under a common root directory
                            root_dirs = set()
                            for member in tar.getmembers():
                                parts = member.name.split("/")
                                if parts:
                                    root_dirs.add(parts[0])

                            # If everything is under one directory (likely named same as the module)
                            # extract contents directly without the extra directory level
                            if len(root_dirs) == 1:
                                common_prefix = list(root_dirs)[0] + "/"
                                for member in tar.getmembers():
                                    if member.name.startswith(common_prefix):
                                        member.name = member.name[len(common_prefix) :]
                                        # Skip directories that would extract to root
                                        if member.name:
                                            tar.extract(member, path=module_target_dir)
                            else:
                                # No common prefix, extract normally
                                tar.extractall(path=module_target_dir)

                        successful_modules.append(module)
                    except Exception as e:
                        print(f"⚠️ Error processing module {module}: {str(e)}")
                        failed_modules.append(module)
                        continue
                else:
                    print(f"✅ Using cached module: {module}")
                    successful_modules.append(module)

                # No need to copy or link as we'll use SFC_DEPLOYMENT_DIR

            # Find the SFC main executable in the modules directory
            sfc_executable = None
            sfc_main_dir = os.path.join(modules_dir, "sfc-main")

            for root, dirs, files in os.walk(sfc_main_dir):
                for file in files:
                    if file == "sfc-main" or file == "sfc-main.exe":
                        sfc_executable = os.path.join(root, file)
                        # Make executable on Unix-like systems
                        if os.name != "nt":  # not Windows
                            os.chmod(sfc_executable, 0o755)
                        break
                if sfc_executable:
                    break

            if not sfc_executable:
                return f"❌ Could not find SFC main executable in the modules directory"

            # Run the configuration with SFC
            print(f"▶️ Running SFC with configuration...")
            command = [sfc_executable, "-config", config_filename, "-trace"]

            # Set up environment variables for the SFC process
            env = os.environ.copy()
            env["SFC_DEPLOYMENT_DIR"] = os.path.abspath(modules_dir)
            env["MODULES_DIR"] = os.path.abspath(modules_dir)
            
            # Set up log file with rotation
            log_dir = os.path.join(test_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file_path = os.path.join(log_dir, "sfc.log")
            
            # Create a rotating file handler
            log_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                mode='a'
            )
            
            # Create logger
            logger = logging.getLogger(f"sfc_{config_name}")
            logger.setLevel(logging.INFO)
            logger.addHandler(log_handler)
            
            # Create log file and open it for the process output
            log_file = open(log_file_path, 'a')
            
            # Run in background with environment variables and redirect output to log file
            process = subprocess.Popen(
                command, 
                cwd=test_dir, 
                env=env, 
                stdout=log_file,
                stderr=log_file,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )

            # Add to active processes for cleanup when wizard exits
            self.active_processes.append(process)
            
            # Store current config name for log tailing and tracking last config
            self.current_config_name = config_name
            self.last_config_name = config_name
            self.last_config_file = config_filename
            
            # Start log tail thread if it's not already running
            self._start_log_tail_thread(log_file_path)

            # Prepare the response message
            modules_status = ""
            if successful_modules:
                modules_status += (
                    f"\nSuccessfully installed modules: {', '.join(successful_modules)}"
                )
            if failed_modules:
                modules_status += f"\nModules that could not be installed: {', '.join(failed_modules)}"

            return f"""✅ SFC configured and running!

Configuration: {config_name}
Directory: {test_dir}
SFC Version: {sfc_version}
Configuration File: {config_filename}{modules_status}

SFC is running with your configuration in a new process.
You can check the logs in the test directory for status information.
"""

        except json.JSONDecodeError:
            return "❌ Invalid JSON configuration provided"
        except requests.RequestException as e:
            return f"❌ Network error while fetching SFC: {str(e)}"
        except Exception as e:
            return f"❌ Error running SFC configuration: {str(e)}"
    
    # _analyze_sfc_config_for_modules method has been externalized to src/tools/sfc_module_analyzer.py
    
    # _save_config_to_file method has been externalized to src/tools/file_operations.py

    # _log_tail_worker method has been externalized to src/tools/log_operations.py

    # _clean_runs_folder method has been externalized to src/tools/folder_operations.py
    
    # _confirm_clean_runs_folder method has been externalized to src/tools/folder_operations.py

    # _tail_logs method has been externalized to src/tools/log_operations.py

    def boot(self):
        """Boot sequence for SFC Wizard"""
        print("=" * 60)
        print("🏭 AWS SHOPFLOOR CONNECTIVITY (SFC) WIZARD")
        print("=" * 60)
        print("Specialized assistant for industrial data connectivity to AWS")
        print()
        print("🎯 I can help you with:")
        print("• 🔍 Debug existing SFC configurations")
        print("• 🛠️  Create new SFC configurations")
        print("• 💾 Save configurations to JSON files")
        print("• 📂 Load configurations from JSON files")
        print("• ▶️  Run configurations in local test environments")
        print("• 🧪 Test configurations against environments")
        print("• 🏗️  Define required deployment environments")
        print("• 📚 Explain SFC concepts and components")
        print()
        print("📋 Supported Protocols:")
        protocol_list = list(self.sfc_knowledge["supported_protocols"].keys())
        for i in range(0, len(protocol_list), 4):
            print("   " + " | ".join(protocol_list[i : i + 4]))
        print()
        print("☁️ Supported AWS Targets:")
        aws_targets = list(self.sfc_knowledge["aws_targets"].keys())
        for i in range(0, len(aws_targets), 3):
            print("   " + " | ".join(aws_targets[i : i + 3]))
        print()
        print("Type 'exit' or 'quit' to end the session.")
        print("=" * 60)
        print()

    def _cleanup_processes(self):
        """Clean up all running SFC processes when wizard exits"""
        if not self.active_processes:
            return

        print("\n🛑 Stopping all running SFC processes...")
        for process in self.active_processes:
            if process.poll() is None:  # Process is still running
                try:
                    process.terminate()
                    process.wait(timeout=2)  # Wait for up to 2 seconds
                except:
                    # If termination fails, force kill
                    try:
                        process.kill()
                    except:
                        pass
        print(f"✅ Terminated {len(self.active_processes)} SFC processes")
        self.active_processes = []

    def run(self):
        """Main interaction loop"""
        self.boot()

        try:
            while True:
                try:
                    user_input = input("SFC Wizard: ").strip()

                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print("\n🏭 Thank you for using the SFC Wizard!")
                        print("May your industrial data flow smoothly to the cloud! ☁️")
                        break

                    if not user_input:
                        continue

                    # Process with Strands agent
                    try:
                        response = self.agent(user_input)
                        print(f"\n{response}\n")
                    except Exception as e:
                        print(f"\n❌ Error processing request: {str(e)}")
                        print(
                            "Please try rephrasing your question or check your configuration.\n"
                        )

                except KeyboardInterrupt:
                    print("\n\n🏭 SFC Wizard session interrupted. Goodbye!")
                    break
                except Exception as e:
                    print(f"\n❌ Unexpected error: {str(e)}")
        finally:
            # Clean up all active SFC processes when wizard exits
            self._cleanup_processes()


def main():
    """Main function to run the SFC Wizard"""
    try:
        wizard = SFCWizardAgent()
        wizard.run()
    except Exception as e:
        print(f"Error starting SFC Wizard: {str(e)}")
        print(
            "Please make sure all dependencies are installed by running 'scripts/init.sh'"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
