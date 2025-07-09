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
        self.sfc_knowledge = self._load_sfc_knowledge()
        self.current_config = None
        self.validation_errors = []
        self.recommendations = []
        # Track active SFC processes for cleanup
        self.active_processes = []

        # Initialize the Strands agent with SFC-specific tools
        self.agent = self._create_agent()

    def _load_sfc_knowledge(self) -> Dict[str, Any]:
        """Load SFC framework knowledge base"""
        return {
            "supported_protocols": {
                "OPCUA": {
                    "description": "OPC Unified Architecture",
                    "port_default": 4840,
                },
                "MODBUS": {"description": "Modbus TCP/IP", "port_default": 502},
                "S7": {"description": "Siemens S7 Communication", "port_default": 102},
                "MQTT": {
                    "description": "Message Queuing Telemetry Transport",
                    "port_default": 1883,
                },
                "REST": {"description": "RESTful HTTP API", "port_default": 80},
                "SQL": {"description": "SQL Database", "port_default": 1433},
                "SNMP": {
                    "description": "Simple Network Management Protocol",
                    "port_default": 161,
                },
                "PCCC": {
                    "description": "Allen-Bradley Rockwell PCCC",
                    "port_default": 44818,
                },
                "ADS": {"description": "Beckhoff ADS", "port_default": 48898},
                "J1939": {
                    "description": "Vehicle CAN Bus Protocol",
                    "port_default": None,
                },
                "SLMP": {"description": "Mitsubishi/Melsec SLMP", "port_default": 5007},
                "NATS": {"description": "NATS Messaging", "port_default": 4222},
                "OPCDA": {"description": "OPC Data Access", "port_default": None},
                "SIMULATOR": {"description": "Data Simulator", "port_default": None},
            },
            "aws_targets": {
                "AWS-IOT-CORE": {"service": "AWS IoT Core", "real_time": True},
                "AWS-IOT-ANALYTICS": {
                    "service": "AWS IoT Analytics",
                    "real_time": False,
                },
                "AWS-SITEWISE": {"service": "AWS IoT SiteWise", "real_time": True},
                "AWS-S3": {"service": "Amazon S3", "real_time": False},
                "AWS-S3-TABLES": {
                    "service": "Amazon S3 Tables (S3Tables)", 
                    "real_time": False,
                    "description": "AWS S3 Tables (also known as S3Tables, Iceberg or AWS-S3-TABLES) target adapter enables writing data to S3 in a structured format based on Apache Iceberg table format. Supports Parquet, JSON, and CSV formats with customizable partitioning, schema definition, and compression options. The Iceberg-compatible format allows for efficient data querying and analytics."
                },
                "AWS-KINESIS": {"service": "Amazon Kinesis", "real_time": True},
                "AWS-KINESIS-FIREHOSE": {
                    "service": "Amazon Kinesis Data Firehose",
                    "real_time": False,
                },
                "AWS-LAMBDA": {"service": "AWS Lambda", "real_time": True},
                "AWS-SNS": {"service": "Amazon SNS", "real_time": True},
                "AWS-SQS": {"service": "Amazon SQS", "real_time": True},
                "AWS-TIMESTREAM": {"service": "Amazon Timestream", "real_time": True},
                "AWS-MSK": {"service": "Amazon MSK", "real_time": True},
            },
            "edge_targets": {
                "OPCUA": {"description": "OPC-UA Server"},
                "OPCUA-WRITER": {"description": "OPC-UA Writer"},
                "DEBUG": {"description": "Debug Terminal"},
                "FILE": {"description": "File System"},
                "MQTT": {"description": "MQTT Broker"},
                "NATS": {"description": "NATS Server"},
            },
            "common_issues": {
                "connection": [
                    "Network connectivity",
                    "Firewall rules",
                    "Authentication",
                ],
                "configuration": [
                    "Missing required fields",
                    "Invalid JSON",
                    "Type mismatches",
                ],
                "performance": [
                    "High CPU usage",
                    "Memory leaks",
                    "Network bottlenecks",
                ],
                "data_quality": [
                    "Missing data points",
                    "Timestamp issues",
                    "Data transformation errors",
                ],
            },
            "required_config_sections": [
                "AWSVersion",
                "Schedules",
                "Sources",
                "Targets",
            ],
            "aws_version": "2022-04-02",
        }

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
                config = json.loads(config_json)
                self.current_config = config
                self.validation_errors = []
                self.recommendations = []

                # Basic structure validation
                self._validate_basic_structure(config)
                self._validate_schedules(config.get("Schedules", []))
                self._validate_sources(config.get("Sources", {}))
                self._validate_targets(config.get("Targets", {}))
                self._validate_adapters(config)

                if self.validation_errors:
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
            return self._generate_config_template(
                protocol.upper(), target.upper(), environment
            )

        @tool
        def diagnose_sfc_issue(issue_description: str, config_json: str = "") -> str:
            """Diagnose common SFC issues and provide troubleshooting steps.

            Args:
                issue_description: Description of the problem
                config_json: Optional SFC configuration (if available)
            """
            return self._diagnose_issue(issue_description, config_json)

        @tool
        def suggest_sfc_optimization(
            config_json: str, performance_requirements: str = ""
        ) -> str:
            """Suggest optimizations for an SFC configuration based on performance requirements.

            Args:
                config_json: Current SFC configuration
                performance_requirements: Description of performance needs
            """
            return self._suggest_optimizations(config_json, performance_requirements)

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
            return self._generate_environment_specs(
                protocol, devices, data_volume, targets
            )

        @tool
        def explain_sfc_concept(concept: str) -> str:
            """Explain SFC concepts, components, or configuration options.

            Args:
                concept: SFC concept to explain (e.g., schedules, transformations, filters)
            """
            return self._explain_concept(concept)

        @tool
        def generate_test_plan(config_json: str) -> str:
            """Generate a comprehensive test plan for an SFC configuration.

            Args:
                config_json: SFC configuration to test
            """
            return self._generate_test_plan(config_json)

        @tool
        def read_config_from_file(filename: str) -> str:
            """Read an SFC configuration from a JSON file.

            Args:
                filename: Name of the file to read the configuration from
            """
            return self._read_config_from_file(filename)

        @tool
        def save_config_to_file(config_json: str, filename: str) -> str:
            """Save an SFC configuration to a JSON file.

            Args:
                config_json: SFC configuration to save
                filename: Name of the file to save the configuration to
            """
            return self._save_config_to_file(config_json, filename)

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
            return self._what_is_sfc()
        
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
            return self._tail_logs(lines, follow)
            
            
        @tool
        def clean_runs_folder() -> str:
            """Clean the runs folder by removing all SFC runs to free up disk space.
            
            This tool will ask for confirmation (y/n) before deleting any files.
            Active configurations will be preserved.
            """
            return self._clean_runs_folder()
            
        @tool
        def confirm_clean_runs_folder(confirmation: str) -> str:
            """Confirm and execute the cleaning of the runs folder after receiving user confirmation.
            
            Args:
                confirmation: User's response (y/n) to the deletion confirmation prompt
            """
            return self._confirm_clean_runs_folder(confirmation)

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
                    generate_test_plan,
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
                    generate_test_plan,
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

    def _validate_basic_structure(self, config: Dict[str, Any]):
        """Validate basic configuration structure"""
        # Check required sections
        for section in self.sfc_knowledge["required_config_sections"]:
            if section not in config:
                self.validation_errors.append(f"Missing required section: {section}")

        # Check AWS version
        if config.get("AWSVersion") != self.sfc_knowledge["aws_version"]:
            self.validation_errors.append(
                f"AWSVersion should be '{self.sfc_knowledge['aws_version']}'"
            )

    def _validate_schedules(self, schedules: List[Dict[str, Any]]):
        """Validate schedules configuration"""
        if not schedules:
            self.validation_errors.append("At least one schedule must be defined")
            return

        for idx, schedule in enumerate(schedules):
            if "Name" not in schedule:
                self.validation_errors.append(f"Schedule {idx} missing 'Name'")
            if "Sources" not in schedule:
                self.validation_errors.append(
                    f"Schedule '{schedule.get('Name', idx)}' missing 'Sources'"
                )
            if "Targets" not in schedule:
                self.validation_errors.append(
                    f"Schedule '{schedule.get('Name', idx)}' missing 'Targets'"
                )

    def _validate_sources(self, sources: Dict[str, Any]):
        """Validate sources configuration"""
        if not sources:
            self.validation_errors.append("At least one source must be defined")
            return

        for source_name, source_config in sources.items():
            if "ProtocolAdapter" not in source_config:
                self.validation_errors.append(
                    f"Source '{source_name}' missing 'ProtocolAdapter'"
                )
            else:
                # Strict validation: Check if protocol is supported
                protocol = source_config["ProtocolAdapter"]
                if protocol not in self.sfc_knowledge["supported_protocols"]:
                    self.validation_errors.append(
                        f"Source '{source_name}' uses unsupported protocol adapter: '{protocol}'. "
                        f"Supported protocols: {', '.join(sorted(self.sfc_knowledge['supported_protocols'].keys()))}"
                    )
                    
            if "Channels" not in source_config:
                self.validation_errors.append(
                    f"Source '{source_name}' missing 'Channels'"
                )

    def _validate_targets(self, targets: Dict[str, Any]):
        """Validate targets configuration"""
        if not targets:
            self.validation_errors.append("At least one target must be defined")
            return

        for target_name, target_config in targets.items():
            if "TargetType" not in target_config:
                self.validation_errors.append(
                    f"Target '{target_name}' missing 'TargetType'"
                )
            else:
                # Strict validation: Check if target type is supported
                target_type = target_config["TargetType"]
                
                # Check in AWS targets
                aws_targets = self.sfc_knowledge["aws_targets"].keys()
                edge_targets = [target["description"] for target in self.sfc_knowledge["edge_targets"].values()]
                
                # Special case handling for edge targets that have -TARGET suffix
                if target_type.endswith("-TARGET"):
                    base_type = target_type[:-7]  # Remove -TARGET suffix
                    if base_type in self.sfc_knowledge["edge_targets"]:
                        continue
                
                # Check if target is in either AWS targets or edge targets
                if target_type not in aws_targets and target_type not in edge_targets:
                    self.validation_errors.append(
                        f"Target '{target_name}' uses unsupported target type: '{target_type}'. "
                        f"Supported AWS targets: {', '.join(sorted(aws_targets))}. "
                        f"Supported edge targets: {', '.join(sorted(self.sfc_knowledge['edge_targets'].keys()))}"
                    )

    def _validate_adapters(self, config: Dict[str, Any]):
        """Validate adapter configurations"""
        # Check if adapter types or servers are defined
        has_adapter_types = bool(config.get("AdapterTypes"))
        has_adapter_servers = bool(config.get("AdapterServers"))

        if not has_adapter_types and not has_adapter_servers:
            self.validation_errors.append(
                "Either 'AdapterTypes' or 'AdapterServers' must be defined"
            )

        # Similar check for targets
        has_target_types = bool(config.get("TargetTypes"))
        has_target_servers = bool(config.get("TargetServers"))

        if not has_target_types and not has_target_servers:
            self.validation_errors.append(
                "Either 'TargetTypes' or 'TargetServers' must be defined"
            )

    def _generate_config_template(
        self, protocol: str, target: str, environment: str
    ) -> str:
        """Generate a configuration template"""
        if protocol not in self.sfc_knowledge["supported_protocols"]:
            return f"❌ Unsupported protocol: {protocol}. Supported: {', '.join(self.sfc_knowledge['supported_protocols'].keys())}"

        # Create basic template structure
        template = {
            "AWSVersion": self.sfc_knowledge["aws_version"],
            "Name": f"{protocol} to {target} Configuration",
            "Description": f"{environment.title()} configuration for {protocol} protocol to {target} target",
            "LogLevel": "Info" if environment == "production" else "Trace",
            "Schedules": [
                {
                    "Name": f"{protocol}Schedule",
                    "Interval": 1000 if environment == "development" else 5000,
                    "Active": True,
                    "TimestampLevel": "Both",
                    "Sources": {f"{protocol}-SOURCE": ["*"]},
                    "Targets": [f"{target}Target"],
                }
            ],
            "Sources": self._generate_source_template(protocol),
            "Targets": self._generate_target_template(target, environment),
            "TargetTypes": self._generate_target_types(target),
            "AdapterTypes": self._generate_adapter_types(protocol),
            "ProtocolAdapters": self._generate_protocol_adapter_config(protocol),
        }

        return f"✅ Generated {protocol} to {target} template:\n\n```json\n{json.dumps(template, indent=2)}\n```"

    def _generate_source_template(self, protocol: str) -> Dict[str, Any]:
        """Generate source configuration template"""
        base_config = {
            f"{protocol}-SOURCE": {
                "Name": f"{protocol}Source",
                "ProtocolAdapter": protocol,
                "Description": f"{protocol} source configuration",
                "Channels": {},
            }
        }

        # Add protocol-specific configurations
        if protocol == "OPCUA":
            base_config[f"{protocol}-SOURCE"]["AdapterOpcuaServer"] = "OPCUA-SERVER-1"
            base_config[f"{protocol}-SOURCE"]["SourceReadingMode"] = "Polling"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "ServerStatus": {"NodeId": "ns=0;i=2256"},
                "ServerTime": {"NodeId": "ns=0;i=2256", "Selector": "@.currentTime"},
            }
        elif protocol == "MODBUS":
            base_config[f"{protocol}-SOURCE"]["AdapterDevice"] = "MODBUS-DEVICE-1"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "Register1": {"Address": 40001, "Type": "HoldingRegister"},
                "Register2": {"Address": 40002, "Type": "HoldingRegister"},
            }
        elif protocol == "S7":
            base_config[f"{protocol}-SOURCE"]["AdapterController"] = "S7-PLC-1"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "DB1Value1": {"Name": "Value1", "Address": "DB100.DBW0", "Type": "Int"},
                "DB1Value2": {"Name": "Value2", "Address": "DB100.DBD4", "Type": "Real"},
            }
        elif protocol == "ADS":
            base_config[f"{protocol}-SOURCE"]["AdapterDevice"] = "ADS-DEVICE-1"
            base_config[f"{protocol}-SOURCE"]["SourceAmsId"] = "192.168.1.10.1.1"
            base_config[f"{protocol}-SOURCE"]["SourceAmsPort"] = 851
            base_config[f"{protocol}-SOURCE"]["TargetAmsId"] = "192.168.1.20.1.1"
            base_config[f"{protocol}-SOURCE"]["TargetAmsPort"] = 852
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "Temperature": {"Name": "Temperature", "SymbolName": "MAIN.Temperature"},
                "Pressure": {"Name": "Pressure", "SymbolName": "MAIN.PressureValue"},
            }
        elif protocol == "MQTT":
            base_config[f"{protocol}-SOURCE"]["AdapterBroker"] = "MQTT-BROKER-1"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "Temperature": {"Topics": ["sensors/temperature"]},
                "Humidity": {"Topics": ["sensors/humidity"]},
            }
        elif protocol == "REST":
            base_config[f"{protocol}-SOURCE"]["RestServer"] = "REST-SERVER-1"
            base_config[f"{protocol}-SOURCE"]["Request"] = "/api/sensors"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "Temperature": {"Name": "Temperature", "Json": True, "Selector": "@.temperature"},
                "Humidity": {"Name": "Humidity", "Json": True, "Selector": "@.humidity"},
            }
        elif protocol == "SNMP":
            base_config[f"{protocol}-SOURCE"]["AdapterDevice"] = "SNMP-DEVICE-1"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "SystemUptime": {"Name": "Uptime", "ObjectId": "1.3.6.1.2.1.1.3.0"},
                "IncomingTraffic": {"Name": "InOctets", "ObjectId": "1.3.6.1.2.1.2.2.1.10.1"},
            }
        elif protocol == "J1939":
            base_config[f"{protocol}-SOURCE"]["AdapterNetwork"] = "CAN-NETWORK-1"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "EngineSpeed": {"Name": "RPM", "PGN": 61444, "SPNs": [190]},
                "EngineTemp": {"Name": "Temperature", "PGN": 65262, "SPNs": [110]},
            }
        elif protocol == "NATS":
            base_config[f"{protocol}-SOURCE"]["AdapterBroker"] = "NATS-SERVER-1"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "SensorData": {"Subject": "sensors.data"},
                "AlarmEvents": {"Subject": "alarms.events"},
            }
        elif protocol == "OPCDA":
            base_config[f"{protocol}-SOURCE"]["AdapterServer"] = "OPCDA-SERVER-1"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "Temperature": {"ItemId": "Device1.Temperature"},
                "Pressure": {"ItemId": "Device1.Pressure"},
            }
        elif protocol == "PCCC":
            base_config[f"{protocol}-SOURCE"]["AdapterController"] = "PCCC-CONTROLLER-1"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "Counter": {"Name": "ProductCounter", "Address": "N7:0"},
                "Status": {"Name": "MachineStatus", "Address": "B3:0/0"},
            }
        elif protocol == "SIMULATOR":
            base_config[f"{protocol}-SOURCE"]["Channels"] = { 
                "counter": {"Simulation": {"SimulationType": "Counter","DataType": "Int","Min": 0,"Max": 100}},
                "sinus": { "Simulation": {"SimulationType": "Sinus","DataType": "Byte","Min": 0,"Max": 100}},
                "triangle": {"Simulation": {"SimulationType": "Triangle","DataType": "Byte","Min": 0,"Max": 100}}
            }
        elif protocol == "SLMP":
            base_config[f"{protocol}-SOURCE"]["AdapterController"] = "SLMP-CONTROLLER-1"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "DataRegister": {"Name": "Register", "Address": "D100", "Type": "Word"},
                "BitDevice": {"Name": "Status", "Address": "M0", "Type": "Bit"},
            }
        elif protocol == "SQL":
            base_config[f"{protocol}-SOURCE"]["AdapterDatabase"] = "SQL-DB-1"
            base_config[f"{protocol}-SOURCE"]["Query"] = "SELECT temperature, pressure, timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT 1"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "Temperature": {"Name": "Temperature", "ColumnName": "temperature"},
                "Pressure": {"Name": "Pressure", "ColumnName": "pressure"},
            }

        return base_config

    def _generate_target_template(
        self, target: str, environment: str
    ) -> Dict[str, Any]:
        """Generate target configuration template"""
        base_config = {f"{target}Target": {"Active": True, "TargetType": target}}

        # Add target-specific configurations
        if target == "AWS-S3":
            base_config[f"{target}Target"].update(
                {
                    "Region": "us-east-1",
                    "BucketName": "sfc-data-bucket",
                    "Interval": 60,
                    "BufferSize": 10,
                    "Prefix": "industrial-data",
                    "Compression": "Gzip" if environment == "production" else "None",
                }
            )
        elif target == "AWS-IOT-CORE":
            base_config[f"{target}Target"].update(
                {
                    "Region": "us-east-1", 
                    "TopicName": "sfc/industrial-data",
                    "BatchSize": 1024,
                    "BatchCount": 100,
                    "BatchInterval": 5000 if environment == "production" else 1000,
                }
            )
        elif target == "AWS-LAMBDA":
            base_config[f"{target}Target"].update(
                {
                    "Region": "us-east-1",
                    "FunctionName": "sfc-data-processor",
                    "BatchSize": 50,
                    "Interval": 1000,
                }
            )
        elif target == "AWS-KINESIS":
            base_config[f"{target}Target"].update(
                {
                    "Region": "us-east-1",
                    "StreamName": "sfc-data-stream",
                    "BatchSize": 500,
                    "Interval": 1000,
                }
            )
        elif target == "AWS-KINESIS-FIREHOSE":
            base_config[f"{target}Target"].update(
                {
                    "Region": "us-east-1",
                    "DeliveryStreamName": "sfc-delivery-stream",
                    "BatchSize": 500,
                    "Interval": 1000,
                }
            )
        elif target == "AWS-S3-TABLES":
            base_config[f"{target}Target"].update(
               {
                    "Region": "us-east-1",
                    "TableBucket": "sfc-data-tables-bucket",
                    "Interval": 60,
                    "BufferCount": 100,
                    "Namespace": "sfc",
                    "AutoCreate": True,
                    "Tables": [
                        {
                            "TableName": "sfc_table",
                            "Schema": [],
                            "Mappings": [],
                            "Partition": {}
                        }
                    ]
                }
            )
        elif target == "AWS-IOT-ANALYTICS":
            base_config[f"{target}Target"].update(
                {
                    "Region": "us-east-1",
                    "ChannelName": "sfc-data-channel",
                    "BatchSize": 100,
                    "Interval": 1000,
                }
            )
        elif target == "AWS-SITEWISE":
            base_config[f"{target}Target"].update(
                {
                    "Region": "us-east-1",
                    "BatchSize": 10,
                    "Interval": 1000,
                    "PropertyAliases": {
                        "${source}": "${source}.${channel}"
                    },
                }
            )
        elif target == "AWS-SITEWISEEDGE":
            base_config[f"{target}Target"].update(
                {
                    "EndPoint": "localhost",
                    "Port": 50001,
                    "BatchSize": 10,
                    "Interval": 1000,
                    "PropertyAliases": {
                        "${source}": "${source}.${channel}"
                    },
                }
            )
        elif target == "AWS-SNS":
            base_config[f"{target}Target"].update(
                {
                    "Region": "us-east-1",
                    "TopicArn": "arn:aws:sns:us-east-1:123456789012:sfc-notifications",
                    "BatchSize": 10,
                    "Interval": 1000,
                }
            )
        elif target == "AWS-SQS":
            base_config[f"{target}Target"].update(
                {
                    "Region": "us-east-1",
                    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/sfc-data-queue",
                    "BatchSize": 10,
                    "Interval": 1000,
                }
            )
        elif target == "AWS-TIMESTREAM":
            base_config[f"{target}Target"].update(
                {
                    "Region": "us-east-1",
                    "DatabaseName": "sfc-database",
                    "TableName": "sfc-data-table",
                    "BatchSize": 100,
                    "Interval": 1000,
                }
            )
        elif target == "AWS-MSK":
            base_config[f"{target}Target"].update(
                {
                    "Region": "us-east-1",
                    "BootstrapServers": "b-1.sfc-msk-cluster.xxxxx.c1.kafka.us-east-1.amazonaws.com:9094,b-2.sfc-msk-cluster.xxxxx.c1.kafka.us-east-1.amazonaws.com:9094",
                    "Topic": "sfc-data-topic",
                    "BatchSize": 100,
                    "Interval": 1000,
                    "SecurityProtocol": "SASL_SSL",
                }
            )
        elif target == "DEBUG":
            base_config[f"{target}Target"] = {
                "Active": True,
                "TargetType": "DEBUG-TARGET",
            }
        elif target == "FILE":
            base_config[f"{target}Target"] = {
                "Active": True,
                "TargetType": "FILE-TARGET",
                "Directory": "./data",
                "FilenameTemplate": "data-%timestamp%.json",
                "Interval": 60,
                "BufferSize": 10,
            }
        elif target == "MQTT":
            base_config[f"{target}Target"] = {
                "Active": True,
                "TargetType": "MQTT-TARGET",
                "EndPoint": "localhost",
                "Port": 1883,
                "TopicName": "sfc/data",
                "QoS": 1,
                "ConnectionTimeout": 30000,
            }
        elif target == "NATS":
            base_config[f"{target}Target"] = {
                "Active": True,
                "TargetType": "NATS-TARGET",
                "EndPoint": "localhost",
                "Port": 4222,
                "Subject": "sfc.data",
            }
        elif target == "OPCUA":
            base_config[f"{target}Target"] = {
                "Active": True,
                "TargetType": "OPCUA-TARGET",
                "EndPoint": "opc.tcp://localhost:4840",
                "NodeNames": {
                    "Temperature": "ns=2;s=Temperature",
                    "Pressure": "ns=2;s=Pressure",
                }
            }
        elif target == "OPCUA-WRITER":
            base_config[f"{target}Target"] = {
                "Active": True,
                "TargetType": "OPCUA-WRITER",
                "EndPoint": "opc.tcp://localhost:4840",
                "NodeIds": {
                    "Temperature": "ns=2;s=Temperature",
                    "Pressure": "ns=2;s=Pressure",
                }
            }
        elif target == "ROUTER":
            base_config[f"{target}Target"] = {
                "Active": True,
                "TargetType": "ROUTER-TARGET",
                "Routes": [
                    {
                        "Name": "Temperature Route",
                        "TargetName": "DEBUG-TARGET",
                        "Condition": "${channel} == 'Temperature'"
                    },
                    {
                        "Name": "Default Route",
                        "TargetName": "AWS-S3-TARGET"
                    }
                ]
            }

        return base_config

    def _generate_target_types(self, target: str) -> Dict[str, Any]:
        """Generate target types configuration"""
        target_types = {}

        # AWS targets
        if target == "AWS-S3":
            target_types["AWS-S3"] = {
                "JarFiles": ["${MODULES_DIR}/aws-s3-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awss3.AwsS3TargetWriter",
            }
        elif target == "AWS-IOT-CORE":
            target_types["AWS-IOT-CORE"] = {
                "JarFiles": ["${MODULES_DIR}/aws-iot-core-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awsiotcore.AwsIotCoreTargetWriter",
            }
        elif target == "AWS-IOT-ANALYTICS":
            target_types["AWS-IOT-ANALYTICS"] = {
                "JarFiles": ["${MODULES_DIR}/aws-iot-analytics-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awsiotanalytics.AwsIotAnalyticsTargetWriter",
            }
        elif target == "AWS-KINESIS":
            target_types["AWS-KINESIS"] = {
                "JarFiles": ["${MODULES_DIR}/aws-kinesis-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awskinesis.AwsKinesisTargetWriter",
            }
        elif target == "AWS-KINESIS-FIREHOSE":
            target_types["AWS-KINESIS-FIREHOSE"] = {
                "JarFiles": ["${MODULES_DIR}/aws-kinesis-firehose-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awskinesisfirehose.AwsKinesisFirehoseTargetWriter",
            }
        elif target == "AWS-S3-TABLES":
            target_types["AWS-S3-TABLES"] = {
                "JarFiles": ["${MODULES_DIR}/aws-s3-tables-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awss3tables.AwsS3TablesTargetWriter",
            }
        elif target == "AWS-LAMBDA":
            target_types["AWS-LAMBDA"] = {
                "JarFiles": ["${MODULES_DIR}/aws-lambda-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awslambda.AwsLambdaTargetWriter",
            }
        elif target == "AWS-MSK":
            target_types["AWS-MSK"] = {
                "JarFiles": ["${MODULES_DIR}/aws-msk-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awsmsk.AwsMskTargetWriter",
            }
        elif target == "AWS-SITEWISE":
            target_types["AWS-SITEWISE"] = {
                "JarFiles": ["${MODULES_DIR}/aws-sitewise-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awssitewise.AwsSitewiseTargetWriter",
            }
        elif target == "AWS-SITEWISEEDGE":
            target_types["AWS-SITEWISEEDGE"] = {
                "JarFiles": ["${MODULES_DIR}/aws-sitewise-edge-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awssitewiseedge.AwsSitewiseEdgeTargetWriter",
            }
        elif target == "AWS-SNS":
            target_types["AWS-SNS"] = {
                "JarFiles": ["${MODULES_DIR}/aws-sns-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awssns.AwsSnsTargetWriter",
            }
        elif target == "AWS-SQS":
            target_types["AWS-SQS"] = {
                "JarFiles": ["${MODULES_DIR}/aws-sqs-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awssqs.AwsSqsTargetWriter",
            }
        elif target == "AWS-TIMESTREAM":
            target_types["AWS-TIMESTREAM"] = {
                "JarFiles": ["${MODULES_DIR}/aws-timestream-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awstimestream.AwsTimestreamTargetWriter",
            }
            
        # Edge targets
        elif target == "DEBUG":
            target_types["DEBUG-TARGET"] = {
                "JarFiles": ["${MODULES_DIR}/debug-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.debugtarget.DebugTargetWriter",
            }
        elif target == "FILE":
            target_types["FILE-TARGET"] = {
                "JarFiles": ["${MODULES_DIR}/file-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.filetarget.FileTargetWriter",
            }
        elif target == "MQTT":
            target_types["MQTT-TARGET"] = {
                "JarFiles": ["${MODULES_DIR}/mqtt-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.mqtt.MqttTargetWriter",
            }
        elif target == "NATS":
            target_types["NATS-TARGET"] = {
                "JarFiles": ["${MODULES_DIR}/nats-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.nats.NatsTargetWriter",
            }
        elif target == "OPCUA":
            target_types["OPCUA-TARGET"] = {
                "JarFiles": ["${MODULES_DIR}/opcua-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.opcua.OpcuaTargetWriter",
            }
        elif target == "OPCUA-WRITER":
            target_types["OPCUA-WRITER"] = {
                "JarFiles": ["${MODULES_DIR}/opcua-writer/lib"],
                "FactoryClassName": "com.amazonaws.sfc.opcua.OpcuaWriter",
            }
        elif target == "ROUTER":
            target_types["ROUTER-TARGET"] = {
                "JarFiles": ["${MODULES_DIR}/router-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.router.RouterTargetWriter",
            }

        return target_types

    def _generate_adapter_types(self, protocol: str) -> Dict[str, Any]:
        """Generate adapter types configuration"""
        adapter_types = {}

        if protocol == "OPCUA":
            adapter_types["OPCUA"] = {
                "JarFiles": ["${MODULES_DIR}/opcua/lib"],
                "FactoryClassName": "com.amazonaws.sfc.opcua.OpcuaAdapter",
            }
        elif protocol == "MODBUS":
            adapter_types["MODBUS"] = {
                "JarFiles": ["${MODULES_DIR}/modbus/lib"],
                "FactoryClassName": "com.amazonaws.sfc.modbus.ModbusAdapter",
            }
        elif protocol == "S7":
            adapter_types["S7"] = {
                "JarFiles": ["${MODULES_DIR}/s7/lib"],
                "FactoryClassName": "com.amazonaws.sfc.s7.S7Adapter",
            }
        elif protocol == "ADS":
            adapter_types["ADS"] = {
                "JarFiles": ["${MODULES_DIR}/ads/lib"],
                "FactoryClassName": "com.amazonaws.sfc.ads.AdsAdapter",
            }
        elif protocol == "J1939":
            adapter_types["J1939"] = {
                "JarFiles": ["${MODULES_DIR}/j1939/lib"],
                "FactoryClassName": "com.amazonaws.sfc.j1939.J1939Adapter",
            }
        elif protocol == "MQTT":
            adapter_types["MQTT"] = {
                "JarFiles": ["${MODULES_DIR}/mqtt/lib"],
                "FactoryClassName": "com.amazonaws.sfc.mqtt.MqttAdapter",
            }
        elif protocol == "NATS":
            adapter_types["NATS"] = {
                "JarFiles": ["${MODULES_DIR}/nats/lib"],
                "FactoryClassName": "com.amazonaws.sfc.nats.NatsAdapter",
            }
        elif protocol == "OPCDA":
            adapter_types["OPCDA"] = {
                "JarFiles": ["${MODULES_DIR}/opcda/lib"],
                "FactoryClassName": "com.amazonaws.sfc.opcda.OpcdaAdapter",
            }
        elif protocol == "PCCC":
            adapter_types["PCCC"] = {
                "JarFiles": ["${MODULES_DIR}/pccc/lib"],
                "FactoryClassName": "com.amazonaws.sfc.pccc.PcccAdapter",
            }
        elif protocol == "REST":
            adapter_types["REST"] = {
                "JarFiles": ["${MODULES_DIR}/rest/lib"],
                "FactoryClassName": "com.amazonaws.sfc.rest.RestAdapter",
            }
        elif protocol == "SIMULATOR":
            adapter_types["SIMULATOR"] = {
                "JarFiles": ["${MODULES_DIR}/simulator/lib"],
                "FactoryClassName": "com.amazonaws.sfc.simulator.SimulatorAdapter",
            }
        elif protocol == "SLMP":
            adapter_types["SLMP"] = {
                "JarFiles": ["${MODULES_DIR}/slmp/lib"],
                "FactoryClassName": "com.amazonaws.sfc.slmp.SlmpAdapter",
            }
        elif protocol == "SNMP":
            adapter_types["SNMP"] = {
                "JarFiles": ["${MODULES_DIR}/snmp/lib"],
                "FactoryClassName": "com.amazonaws.sfc.snmp.SnmpAdapter",
            }
        elif protocol == "SQL":
            adapter_types["SQL"] = {
                "JarFiles": ["${MODULES_DIR}/sql/lib"],
                "FactoryClassName": "com.amazonaws.sfc.sql.SqlAdapter",
            }

        return adapter_types

    def _generate_protocol_adapter_config(self, protocol: str) -> Dict[str, Any]:
        """Generate protocol adapter configuration"""
        config = {}

        if protocol == "OPCUA":
            config["OPCUA"] = {
                "AdapterType": "OPCUA",
                "OpcuaServers": {
                    "OPCUA-SERVER-1": {
                        "Address": "opc.tcp://localhost",
                        "Port": 4840,
                        "Path": "/",
                        "ConnectTimeout": 10000,
                        "ReadBatchSize": 500,
                    }
                },
            }
        elif protocol == "MODBUS":
            config["MODBUS"] = {
                "AdapterType": "MODBUS",
                "Controllers": {
                    "MODBUS-CONTROLLER-1": {
                        "Address": "192.168.1.100",
                        "Port": 502,
                        "UnitId": 1,
                    }
                },
            }
        elif protocol == "S7":
            config["S7"] = {
                "AdapterType": "S7",
                "Controllers": {
                    "S7-PLC-1": {
                        "Address": "192.168.1.130",
                        "ControllerType": "S7-1200",
                    }
                },
            }
        elif protocol == "ADS":
            config["ADS"] = {
                "AdapterType": "ADS",
                "Controllers": {
                    "ADS-CONTROLLER-1": {
                        "Address": "192.168.1.140",
                        "Port": 48898,
                        "ConnectTimeout": 10000,
                    }
                },
            }
        elif protocol == "J1939":
            config["J1939"] = {
                "AdapterType": "J1939",
                "Networks": {
                    "CAN-NETWORK-1": {
                        "Interface": "can0",
                        "PollInterval": 500,
                    }
                },
            }
        elif protocol == "MQTT":
            config["MQTT"] = {
                "AdapterType": "MQTT",
                "Brokers": {
                    "MQTT-BROKER-1": {
                        "EndPoint": "localhost",
                        "Port": 1883,
                        "ConnectionTimeout": 10,
                    }
                },
                "ReadMode": "KeepLast",
            }
        elif protocol == "NATS":
            config["NATS"] = {
                "AdapterType": "NATS",
                "Brokers": {
                    "NATS-SERVER-1": {
                        "EndPoint": "localhost",
                        "Port": 4222,
                    }
                },
            }
        elif protocol == "OPCDA":
            config["OPCDA"] = {
                "AdapterType": "OPCDA",
                "Servers": {
                    "OPCDA-SERVER-1": {
                        "Host": "localhost",
                        "ProgID": "Matrikon.OPC.Simulation",
                        "ConnectTimeout": 5000,
                    }
                },
            }
        elif protocol == "PCCC":
            config["PCCC"] = {
                "AdapterType": "PCCC",
                "Controllers": {
                    "PCCC-CONTROLLER-1": {
                        "Address": "192.168.1.150",
                        "Port": 44818,
                    }
                },
            }
        elif protocol == "REST":
            config["REST"] = {
                "AdapterType": "REST",
                "Endpoints": {
                    "REST-ENDPOINT-1": {
                        "BaseUrl": "http://localhost:8080/api",
                        "ConnectTimeout": 5000,
                    }
                },
            }
        elif protocol == "SIMULATOR":
            config["SIMULATOR"] = {
                "AdapterType": "SIMULATOR",
            }
        elif protocol == "SLMP":
            config["SLMP"] = {
                "AdapterType": "SLMP",
                "Controllers": {
                    "SLMP-CONTROLLER-1": {
                        "Address": "192.168.1.160",
                        "Port": 5007,
                        "ConnectTimeout": 5000,
                    }
                },
            }
        elif protocol == "SNMP":
            config["SNMP"] = {
                "AdapterType": "SNMP",
                "Devices": {
                    "SNMP-DEVICE-1": {
                        "Address": "192.168.1.170",
                        "Port": 161,
                        "Version": "V2c",
                        "Community": "public",
                    }
                },
            }
        elif protocol == "SQL":
            config["SQL"] = {
                "AdapterType": "SQL",
                "Databases": {
                    "SQL-DB-1": {
                        "ConnectionString": "jdbc:mysql://localhost:3306/testdb",
                        "Driver": "com.mysql.jdbc.Driver",
                        "Username": "${DB_USER}",
                        "Password": "${DB_PASSWORD}",
                    }
                },
            }

        return config

    def _diagnose_issue(self, issue_description: str, config_json: str) -> str:
        """Diagnose SFC issues"""
        issue_lower = issue_description.lower()
        diagnosis = ["🔍 SFC Issue Diagnosis\n"]

        # Connection issues
        if any(
            keyword in issue_lower
            for keyword in ["connect", "connection", "timeout", "unreachable"]
        ):
            diagnosis.extend(
                [
                    "🔌 **Connection Issues Detected**",
                    "• Check network connectivity between SFC and target devices",
                    "• Verify firewall rules allow required ports",
                    "• Confirm device IP addresses and ports in configuration",
                    "• Test connectivity using ping or telnet",
                    "• Check if devices are powered on and operational",
                    "",
                ]
            )

        # Authentication issues
        if any(
            keyword in issue_lower
            for keyword in ["auth", "credential", "permission", "unauthorized"]
        ):
            diagnosis.extend(
                [
                    "🔐 **Authentication Issues Detected**",
                    "• Verify AWS credentials are correctly configured",
                    "• Check IAM roles and policies for required permissions",
                    "• Confirm certificate paths and validity (for IoT/TLS)",
                    "• Validate username/password for protocol adapters",
                    "• Review AWS Secrets Manager configuration if used",
                    "",
                ]
            )

        # Configuration issues
        if any(
            keyword in issue_lower
            for keyword in ["config", "invalid", "missing", "error"]
        ):
            diagnosis.extend(
                [
                    "⚙️ **Configuration Issues Detected**",
                    "• Validate JSON syntax using a JSON validator",
                    "• Check all required sections are present",
                    "• Verify protocol adapter and target type configurations",
                    "• Confirm schedule references match source/target names",
                    "• Review data type compatibility between sources and targets",
                    "",
                ]
            )

        # Performance issues
        if any(
            keyword in issue_lower
            for keyword in ["slow", "performance", "memory", "cpu", "lag"]
        ):
            diagnosis.extend(
                [
                    "⚡ **Performance Issues Detected**",
                    "• Review data collection intervals and batch sizes",
                    "• Check memory usage and increase JVM heap if needed",
                    "• Monitor network bandwidth utilization",
                    "• Consider using data filtering to reduce volume",
                    "• Implement data aggregation for high-frequency sources",
                    "",
                ]
            )

        # Data quality issues
        if any(
            keyword in issue_lower
            for keyword in ["data", "missing", "incorrect", "timestamp"]
        ):
            diagnosis.extend(
                [
                    "📊 **Data Quality Issues Detected**",
                    "• Verify channel configurations match device data points",
                    "• Check data type mappings and transformations",
                    "• Review timestamp configuration and time zones",
                    "• Validate data filtering and change detection settings",
                    "• Monitor source device status and availability",
                    "",
                ]
            )

        # If we have a configuration, provide specific analysis
        if config_json:
            try:
                config = json.loads(config_json)
                diagnosis.extend(
                    [
                        "📋 **Configuration Analysis:**",
                        f"• Schedules defined: {len(config.get('Schedules', []))}",
                        f"• Sources configured: {len(config.get('Sources', {}))}",
                        f"• Targets configured: {len(config.get('Targets', {}))}",
                        f"• Log level: {config.get('LogLevel', 'Not set')}",
                        "",
                    ]
                )
            except:
                diagnosis.append("⚠️ Could not parse provided configuration")

        if len(diagnosis) == 1:  # Only header added
            diagnosis.extend(
                [
                    "❓ **General Troubleshooting Steps:**",
                    "• Check SFC logs for specific error messages",
                    "• Verify all required JAR files are present",
                    "• Confirm Java version compatibility (JVM 1.8+)",
                    "• Test with a minimal configuration first",
                    "• Enable trace logging for detailed diagnostics",
                ]
            )

        return "\n".join(diagnosis)

    def _suggest_optimizations(
        self, config_json: str, performance_requirements: str
    ) -> str:
        """Suggest configuration optimizations"""
        try:
            config = json.loads(config_json)
        except:
            return "❌ Invalid JSON configuration provided"

        suggestions = ["🚀 SFC Optimization Suggestions\n"]

        # Analyze schedules
        schedules = config.get("Schedules", [])
        for schedule in schedules:
            interval = schedule.get("Interval", 1000)
            if interval < 100:
                suggestions.append(
                    f"⚠️ Schedule '{schedule.get('Name')}' has very fast interval ({interval}ms). Consider increasing for better performance."
                )

        # Analyze targets
        targets = config.get("Targets", {})
        for target_name, target_config in targets.items():
            target_type = target_config.get("TargetType", "")

            # S3 optimizations
            if target_type == "AWS-S3":
                buffer_size = target_config.get("BufferSize", 1)
                if buffer_size < 10:
                    suggestions.append(
                        f"💡 Target '{target_name}': Increase BufferSize to 10+ for better S3 performance"
                    )

                if "Compression" not in target_config:
                    suggestions.append(
                        f"💡 Target '{target_name}': Enable compression (Gzip/Zip) to reduce S3 storage costs"
                    )

            # Streaming targets
            elif target_type in ["AWS-KINESIS", "AWS-IOT-CORE"]:
                if "BufferSize" not in target_config:
                    suggestions.append(
                        f"💡 Target '{target_name}': Add buffering for better throughput"
                    )

        # General optimizations based on requirements
        if "high throughput" in performance_requirements.lower():
            suggestions.extend(
                [
                    "",
                    "🏎️ **High Throughput Optimizations:**",
                    "• Use parallel processing with multiple adapter instances",
                    "• Implement data aggregation to reduce message volume",
                    "• Consider using streaming targets (Kinesis) over batch targets",
                    "• Increase JVM heap size and tune garbage collection",
                ]
            )

        if "low latency" in performance_requirements.lower():
            suggestions.extend(
                [
                    "",
                    "⚡ **Low Latency Optimizations:**",
                    "• Use subscription mode for OPC-UA instead of polling",
                    "• Minimize data transformations and filtering",
                    "• Use direct streaming targets (IoT Core, Kinesis)",
                    "• Deploy protocol adapters close to data sources",
                ]
            )

        if "cost optimization" in performance_requirements.lower():
            suggestions.extend(
                [
                    "",
                    "💰 **Cost Optimization:**",
                    "• Enable data compression for S3 targets",
                    "• Use data filtering to reduce unnecessary data transmission",
                    "• Implement change-based data collection",
                    "• Consider data aggregation to reduce API calls",
                ]
            )

        return (
            "\n".join(suggestions)
            if len(suggestions) > 1
            else "✅ Configuration appears well-optimized"
        )

    def _generate_environment_specs(
        self, protocol: str, devices: str, data_volume: str, targets: str
    ) -> str:
        """Generate environment specifications"""
        specs = [
            "🏗️ **SFC Environment Specifications**\n",
            "## Infrastructure Requirements",
            "",
        ]

        # Compute requirements
        if "high volume" in data_volume.lower() or "real-time" in data_volume.lower():
            specs.extend(
                [
                    "### Compute Resources:",
                    "• **CPU**: 4+ cores recommended",
                    "• **RAM**: 8GB+ (increase based on data volume)",
                    "• **Storage**: 100GB+ SSD for local buffering",
                    "• **Java**: OpenJDK 11+ or Oracle JDK 1.8+",
                    "",
                ]
            )
        else:
            specs.extend(
                [
                    "### Compute Resources:",
                    "• **CPU**: 2+ cores sufficient",
                    "• **RAM**: 4GB+ recommended",
                    "• **Storage**: 50GB+ for logs and buffering",
                    "• **Java**: OpenJDK 11+ or Oracle JDK 1.8+",
                    "",
                ]
            )

        # Network requirements
        protocol_info = self.sfc_knowledge["supported_protocols"].get(
            protocol.upper(), {}
        )
        default_port = protocol_info.get("port_default")

        specs.extend(
            [
                "### Network Requirements:",
                f"• **{protocol} Protocol**: Port {default_port} (if applicable)",
                "• **Outbound HTTPS**: Port 443 for AWS services",
                "• **gRPC**: Port 5000-6000 range for SFC components",
                "• **Management**: SSH (22) or RDP (3389) for administration",
                "",
            ]
        )

        # AWS requirements
        if any(
            aws_service in targets.upper()
            for aws_service in self.sfc_knowledge["aws_targets"].keys()
        ):
            specs.extend(
                [
                    "### AWS Requirements:",
                    "• **IAM Role**: With permissions for target services",
                    "• **VPC**: If deploying in private subnet",
                    "• **Security Groups**: Allow required ports",
                    "• **Internet Gateway**: For AWS service access",
                    "",
                ]
            )

        # Security requirements
        specs.extend(
            [
                "### Security Requirements:",
                "• **Certificates**: X.509 certificates for TLS/device auth",
                "• **Firewall**: Configure rules for required ports",
                "• **AWS Credentials**: IAM roles or access keys",
                "• **Network Segmentation**: OT/IT network separation",
                "",
            ]
        )

        # Deployment architecture
        specs.extend(
            [
                "## Deployment Architecture",
                "",
                "### Recommended Setup:",
                "• **Edge Gateway**: SFC Core + Protocol Adapters",
                "• **Cloud Connectivity**: Target Adapters for AWS services",
                "• **Data Flow**: Device → Protocol Adapter → SFC Core → Target Adapter → AWS",
                "",
                "### Network Topology:",
                "• **OT Network**: Industrial devices and protocol adapters",
                "• **DMZ**: SFC Core and edge processing",
                "• **IT Network**: AWS connectivity and management",
                "",
            ]
        )

        # Device-specific requirements
        if "PLC" in devices.upper() or "SCADA" in devices.upper():
            specs.extend(
                [
                    "### Device Integration:",
                    "• **PLC Communication**: Ensure PLC supports required protocols",
                    "• **Network Configuration**: Static IP addresses recommended",
                    "• **Timing Requirements**: Consider real-time constraints",
                    "",
                ]
            )

        return "\n".join(specs)

    def _what_is_sfc(self) -> str:
        """Provide an explanation of what SFC (Shop Floor Connectivity) is"""
        return """
🏭 **Shop Floor Connectivity (SFC)**

Shop Floor Connectivity (SFC) is an industrial data ingestion enabler, that can quickly deliver customizable greenfield & brownfield connectivity solutions.

**Key Features:**
• **Industrial Connectivity**: Connect to various industrial protocols and devices
• **Flexible Integration**: Support for both greenfield (new) and existing (brownfield) installations
• **Data Ingestion**: Collect, transform, and route industrial data
• **AWS Integration**: Seamless connection to AWS services for processing and analysis
• **Customizable**: Adaptable to specific industrial environments and requirements
• **Scalable**: Handle diverse data volumes from industrial equipment

**Benefits:**
• Accelerate digital transformation of industrial environments
• Bridge the gap between OT (Operational Technology) and IT systems
• Enable data-driven decision making for manufacturing processes
• Reduce time-to-value for industrial IoT implementations
• Simplify complex industrial data integration challenges
"""

    def _explain_concept(self, concept: str) -> str:
        """Explain SFC concepts"""
        concept_lower = concept.lower()

        if "schedule" in concept_lower:
            return """
🗓️ **SFC Schedules**

Schedules are the heart of SFC data collection. They define:
- **When** data is collected (Interval in milliseconds)
- **What** data is collected (Sources and Channels)
- **Where** data is sent (Targets)

Key Properties:
• **Interval**: How often to collect data (e.g., 1000ms = every second)
• **Sources**: Which protocol adapters to read from
• **Targets**: Where to send the collected data
• **Active**: Enable/disable the schedule
• **TimestampLevel**: Add timestamps to data (Source, Target, Both, None)

Example:
```json
{
  "Name": "ProductionData",
  "Interval": 5000,
  "Active": true,
  "TimestampLevel": "Both",
  "Sources": {
    "OPC-SOURCE": ["*"]
  },
  "Targets": ["S3Target", "IoTCoreTarget"]
}
```
"""

        elif "transformation" in concept_lower:
            return """
🔄 **SFC Transformations**

Transformations modify data values as they flow through SFC:
- **Mathematical operations**: Add, Subtract, Multiply, Divide
- **Data type conversions**: String to Number, etc.
- **Formatting**: Round, Truncate, Format
- **Conditional logic**: If-Then-Else operations

Common Operators:
• **Math**: Add, Subtract, Multiply, Divide, Modulo
• **Rounding**: Round, Ceil, Floor, TruncAt
• **String**: ToString, Substring, Replace
• **Conditional**: If, Switch, Default

Example:
```json
"Transformations": {
  "ConvertToCelsius": [
    {
      "Operator": "Subtract",
      "Operand": 32
    },
    {
      "Operator": "Multiply",
      "Operand": 0.5556
    },
    {
      "Operator": "Round"
    }
  ]
}
```
"""

        elif "filter" in concept_lower:
            return """
🔍 **SFC Filters**

Filters control which data passes through the system:

**Change Filters**:
- Only send data when values change significantly
- Types: Absolute, Percent, Always
- Reduces network traffic and storage costs

**Value Filters**:
- Filter based on actual data values
- Operators: eq, ne, gt, lt, ge, le
- Can combine with AND/OR logic

**Condition Filters**:
- Check if channels are present/absent
- Useful for error detection and validation

Example Change Filter:
```json
"ChangeFilters": {
  "TenPercentChange": {
    "Type": "Percent",
    "Value": 10,
    "AtLeast": 60000
  }
}
```
"""

        elif "adapter" in concept_lower or "protocol" in concept_lower:
            return """
🔌 **SFC Protocol Adapters**

Protocol Adapters connect SFC to industrial devices:

**Supported Protocols**:
• **OPC-UA**: Modern industrial communication
• **Modbus**: Widely used in manufacturing
• **Siemens S7**: Siemens PLC communication
• **MQTT**: IoT messaging protocol
• **REST**: HTTP-based APIs
• **SQL**: Database connectivity

**Deployment Modes**:
• **In-Process**: Runs within SFC Core JVM
• **IPC (Inter-Process)**: Separate microservice via gRPC

**Configuration**:
- AdapterTypes: Defines JAR files and factory classes
- ProtocolAdapters: Specific adapter configurations
- AdapterServers: Remote adapter service endpoints

Benefits:
✓ Protocol abstraction
✓ Extensible architecture
✓ Secure communication
✓ Distributed deployment
"""

        elif "target" in concept_lower:
            return """
🎯 **SFC Targets**

Targets send processed data to destinations:

**AWS Targets**:
• **IoT Core**: Real-time MQTT messaging
• **S3**: Batch data storage
• **Kinesis**: Streaming data ingestion
• **Lambda**: Serverless processing
• **Timestream**: Time-series database
• **SiteWise**: Industrial asset modeling

**Edge Targets**:
• **File**: Local file storage
• **Debug**: Console output
• **MQTT**: Local MQTT broker
• **OPC-UA**: Local OPC-UA server

**Features**:
• Buffering and compression
• Data transformation templates
• Secure credential management
• Error handling and retry logic
"""

        else:
            return f"""
🤖 **SFC Concept: {concept}**

I can explain these SFC concepts:
• **Schedules**: Data collection timing and routing
• **Transformations**: Data modification operations
• **Filters**: Data filtering and change detection
• **Adapters/Protocols**: Device connectivity
• **Targets**: Data destinations
• **Sources**: Data input configurations
• **Channels**: Individual data points
• **Metadata**: Additional data context

Ask me about any of these concepts for detailed explanations!

**Available Protocols**: {', '.join(self.sfc_knowledge['supported_protocols'].keys())}
**Available AWS Targets**: {', '.join(self.sfc_knowledge['aws_targets'].keys())}
"""

    def _read_config_from_file(self, filename: str) -> str:
        """Read configuration from a JSON file"""
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
            needed_modules = self._analyze_sfc_config_for_modules(config)

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

    def _analyze_sfc_config_for_modules(self, config: Dict[str, Any]) -> List[str]:
        """Analyze SFC config to determine required modules"""
        modules = set()

        # Check protocol adapters
        adapter_types = config.get("AdapterTypes", {})
        for adapter_type in adapter_types:
            # Convert adapter type name to lowercase for module name
            adapter_module = adapter_type.lower()
            modules.add(adapter_module)

        # Check for target types
        target_types = config.get("TargetTypes", {})
        for target_type in target_types:
            # Convert target type to module name format
            if target_type.startswith("AWS-"):
                # For AWS targets, use the format "aws-x-target"
                target_module = target_type.lower().replace("-", "-")
                if "-target" not in target_module:
                    target_module += "-target"
            else:
                # For other targets
                target_module = target_type.lower()
                if "-target" not in target_module:
                    target_module += "-target"

            modules.add(target_module)

        # No longer automatically including core modules
        # modules.add("core")
        # modules.add("metrics")

        return list(modules)

    def _save_config_to_file(self, config_json: str, filename: str) -> str:
        """Save configuration to a JSON file"""
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

    def _generate_test_plan(self, config_json: str) -> str:
        """Generate a test plan for SFC configuration"""
        try:
            config = json.loads(config_json)
        except:
            return "❌ Invalid JSON configuration provided"

        test_plan = [
            "🧪 **SFC Configuration Test Plan**\n",
            "## Pre-Testing Setup",
            "1. **Environment Preparation**",
            "   - Install Java JDK 1.8+ or OpenJDK 11+",
            "   - Download SFC binaries and required JAR files",
            "   - Configure network connectivity to devices",
            "   - Set up AWS credentials and permissions",
            "",
            "2. **Configuration Validation**",
            "   - Validate JSON syntax",
            "   - Check required sections are present",
            "   - Verify adapter and target configurations",
            "",
            "## Functional Testing",
            "",
        ]

        # Analyze configuration to generate specific tests
        schedules = config.get("Schedules", [])
        sources = config.get("Sources", {})
        targets = config.get("Targets", {})

        # Schedule testing
        test_plan.extend(["### Schedule Testing", ""])

        for idx, schedule in enumerate(schedules, 1):
            test_plan.extend(
                [
                    f"**Test {idx}: Schedule '{schedule.get('Name', 'Unknown')}'**",
                    f"- Interval: {schedule.get('Interval', 'Not set')}ms",
                    "- Verify schedule activates correctly",
                    "- Confirm data collection timing",
                    "- Check source-to-target data flow",
                    "",
                ]
            )

        # Source testing
        test_plan.extend(["### Source Testing", ""])

        for idx, (source_name, source_config) in enumerate(sources.items(), 1):
            protocol = source_config.get("ProtocolAdapter", "Unknown")
            test_plan.extend(
                [
                    f"**Test S{idx}: Source '{source_name}' ({protocol})**",
                    "- Test device connectivity",
                    "- Verify channel data retrieval",
                    "- Check data type correctness",
                    "- Validate transformations (if configured)",
                    "",
                ]
            )

        # Target testing
        test_plan.extend(["### Target Testing", ""])

        for idx, (target_name, target_config) in enumerate(targets.items(), 1):
            target_type = target_config.get("TargetType", "Unknown")
            test_plan.extend(
                [
                    f"**Test T{idx}: Target '{target_name}' ({target_type})**",
                    "- Verify target connectivity/credentials",
                    "- Test data delivery and format",
                    "- Check buffering and compression",
                    "- Validate error handling",
                    "",
                ]
            )

        # Integration testing
        test_plan.extend(
            [
                "## Integration Testing",
                "",
                "### End-to-End Tests",
                "1. **Full Data Flow Test**",
                "   - Start SFC with complete configuration",
                "   - Verify data flows from all sources to all targets",
                "   - Check data consistency and timing",
                "",
                "2. **Error Handling Test**",
                "   - Disconnect network/devices temporarily",
                "   - Verify graceful error handling and recovery",
                "   - Check retry mechanisms",
                "",
                "3. **Performance Test**",
                "   - Monitor CPU and memory usage",
                "   - Test with expected data volumes",
                "   - Verify performance under load",
                "",
                "## Test Commands",
                "",
                "### Start SFC for Testing",
                "```bash",
                "# Basic startup with trace logging",
                "sfc-main -config config.json -trace",
                "",
                "# With specific log level",
                "sfc-main -config config.json -info",
                "```",
                "",
                "### Monitor and Debug",
                "```bash",
                "# Check Java processes",
                "jps -v",
                "",
                "# Monitor memory usage",
                "jstat -gc [PID]",
                "",
                "# Check network connections",
                "netstat -an | grep [PORT]",
                "```",
                "",
                "## Success Criteria",
                "✅ All schedules activate without errors",
                "✅ Data flows consistently from sources to targets",
                "✅ No memory leaks or performance degradation",
                "✅ Error conditions handled gracefully",
                "✅ Configuration changes applied dynamically",
                "",
                "## Common Issues to Watch For",
                "⚠️ Connection timeouts to devices",
                "⚠️ AWS credential expiration",
                "⚠️ Memory consumption growth",
                "⚠️ Data format mismatches",
                "⚠️ Network connectivity problems",
            ]
        )

        return "\n".join(test_plan)

    def _start_log_tail_thread(self, log_file_path: str):
        """Start a thread to tail the SFC log file and keep a buffer of recent log entries"""
        # If a thread is already running, stop it before starting a new one
        if self.log_tail_thread and self.log_tail_thread.is_alive():
            self.log_tail_stop_event.set()
            self.log_tail_thread.join(1)  # Wait up to 1 second for thread to stop
        
        # Clear any existing stop event and create a new one
        self.log_tail_stop_event.clear()
        
        # Create and start the thread
        self.log_tail_thread = threading.Thread(
            target=self._log_tail_worker,
            args=(log_file_path, self.log_tail_stop_event, self.log_buffer),
            daemon=True
        )
        self.log_tail_thread.start()
    
    def _log_tail_worker(self, log_file_path: str, stop_event: threading.Event, log_buffer: queue.Queue):
        """Worker thread that continuously reads from the log file and buffers new entries"""
        try:
            with open(log_file_path, 'r') as log_file:
                # Go to the end of the file
                log_file.seek(0, 2)
                
                while not stop_event.is_set():
                    line = log_file.readline()
                    if line:
                        # If the buffer is full, remove the oldest entry
                        if log_buffer.full():
                            try:
                                log_buffer.get_nowait()
                            except queue.Empty:
                                pass
                        
                        # Add the new log line to the buffer
                        try:
                            log_buffer.put_nowait(line.rstrip())
                        except queue.Full:
                            pass  # Buffer is full, skip this line
                    else:
                        # No new data, wait a bit before checking again
                        time.sleep(0.1)
        except Exception as e:
            # If any error occurs, just print it and exit the thread
            print(f"Log tail thread error: {str(e)}")
    
    def _run_last_config(self) -> str:
        """Run the last SFC configuration that was previously executed"""
        if not self.last_config_file or not self.last_config_name:
            return "❌ No previous SFC configuration found. Please run a configuration first."
        
        try:
            # Check if the last config file exists
            if not os.path.exists(self.last_config_file):
                return f"❌ Last configuration file not found: {self.last_config_file}"
            
            # Read the configuration from the file
            with open(self.last_config_file, 'r') as file:
                config_json = file.read()
            
            print(f"🔄 Restarting last configuration: {self.last_config_name}")
            
            # Run the configuration using the existing method
            # We pass the same config name to ensure it runs in the same directory
            return self._run_sfc_config_locally(config_json, self.last_config_name)
            
        except Exception as e:
            return f"❌ Error running last configuration: {str(e)}"

    def _clean_runs_folder(self) -> str:
        """Clean the runs folder by removing all SFC runs to free up disk space
        
        Returns:
            Result message with information about the cleanup operation
        """
        try:
            base_dir = os.getcwd()
            runs_dir = os.path.join(base_dir, "runs")
            
            # Check if runs folder exists
            if not os.path.exists(runs_dir) or not os.path.isdir(runs_dir):
                return "❌ No runs folder found at path: " + runs_dir
            
            # Get list of run folders
            run_dirs = []
            for entry in os.listdir(runs_dir):
                full_path = os.path.join(runs_dir, entry)
                if os.path.isdir(full_path):
                    run_dirs.append(full_path)
            
            if not run_dirs:
                return "✅ Runs folder is already empty"
            
            # Prompt for confirmation
            total_runs = len(run_dirs)
            confirmation_msg = f"⚠️ WARNING: This will delete all {total_runs} run directories in {runs_dir}!\n"
            confirmation_msg += "Do you want to proceed? (y/n): "
            
            # Ask for confirmation - will need to be implemented by user
            return confirmation_msg
            
        except Exception as e:
            return f"❌ Error scanning runs folder: {str(e)}"
    
    def _confirm_clean_runs_folder(self, confirmation: str) -> str:
        """Execute the runs folder cleanup after confirmation
        
        Args:
            confirmation: User confirmation (y/n)
            
        Returns:
            Result message with information about the cleanup operation
        """
        if confirmation.lower() not in ["y", "yes"]:
            return "❌ Operation canceled by user"
        
        try:
            base_dir = os.getcwd()
            runs_dir = os.path.join(base_dir, "runs")
            
            # Check if runs folder exists again (in case it was deleted between calls)
            if not os.path.exists(runs_dir) or not os.path.isdir(runs_dir):
                return "❌ No runs folder found at path: " + runs_dir
            
            # Define helper function to get directory size
            def get_dir_size(path):
                total_size = 0
                for dirpath, _, filenames in os.walk(path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            total_size += os.path.getsize(fp)
                return total_size
            
            # Track deletion statistics
            deleted_count = 0
            skipped_count = 0
            deleted_size = 0
            
            # List directories again (might have changed since first scan)
            run_dirs = []
            for entry in os.listdir(runs_dir):
                full_path = os.path.join(runs_dir, entry)
                if os.path.isdir(full_path):
                    run_dirs.append(full_path)
            
            # Skip active runs
            to_delete = []
            for dir_path in run_dirs:
                dir_name = os.path.basename(dir_path)
                # Skip current and last config directories
                if ((self.current_config_name and dir_name == self.current_config_name) or
                    (self.last_config_name and dir_name == self.last_config_name)):
                    skipped_count += 1
                    continue
                
                to_delete.append(dir_path)
            
            # Process the directories to delete
            for dir_path in to_delete:
                try:
                    # Calculate directory size before deletion for reporting
                    dir_size = get_dir_size(dir_path)
                    
                    # Delete the directory
                    shutil.rmtree(dir_path)
                    
                    deleted_count += 1
                    deleted_size += dir_size
                    
                except Exception as e:
                    print(f"Error deleting {dir_path}: {str(e)}")
                    skipped_count += 1
            
            # Format the deleted size for display
            if deleted_size < 1024:
                size_str = f"{deleted_size} bytes"
            elif deleted_size < 1024 * 1024:
                size_str = f"{deleted_size / 1024:.2f} KB"
            elif deleted_size < 1024 * 1024 * 1024:
                size_str = f"{deleted_size / (1024 * 1024):.2f} MB"
            else:
                size_str = f"{deleted_size / (1024 * 1024 * 1024):.2f} GB"
            
            # Final message
            msg = f"✅ Cleanup completed:\n"
            msg += f"• Deleted: {deleted_count} run{'s' if deleted_count != 1 else ''}\n"
            msg += f"• Freed up: {size_str}\n"
            
            if skipped_count > 0:
                msg += f"• Skipped: {skipped_count} run{'s' if skipped_count != 1 else ''} (active runs or could not delete)\n"
            
            return msg
            
        except Exception as e:
            return f"❌ Error cleaning runs folder: {str(e)}"

    def _tail_logs(self, lines: int = 20, follow: bool = False) -> str:
        """Return the most recent log entries, optionally following in real-time
        
        Args:
            lines: Number of recent log lines to show
            follow: If True, continuously display new log lines in real-time (press Ctrl+C to exit)
        """
        # Check if there's an active SFC configuration running
        if not self.current_config_name:
            return "❌ No SFC configuration is currently running"
        
        # Try to find the log file path
        base_dir = os.getcwd()
        runs_dir = os.path.join(base_dir, "runs")
        test_dir = os.path.join(runs_dir, self.current_config_name)
        log_dir = os.path.join(test_dir, "logs")
        log_file_path = os.path.join(log_dir, "sfc.log")
        
        if not os.path.exists(log_file_path):
            return f"❌ Log file not found: {log_file_path}"
        
        # Handle follow mode for real-time log viewing
        if follow:
            print("\n" + "=" * 80)
            print(f"📜 FOLLOW MODE: Showing real-time logs for {self.current_config_name}")
            print(f"⚠️  TO EXIT: Type 'q' and press Enter")
            print("=" * 80 + "\n")
            
            # Use a simpler approach that doesn't rely on KeyboardInterrupt
            # First, display the last N lines
            try:
                with open(log_file_path, 'r') as file:
                    # Read the last N lines
                    all_lines = file.readlines()
                    last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    
                    # Print the initial lines
                    for line in last_lines:
                        print(line.rstrip())
                
                # Now enter follow mode with a better exit mechanism
                import select
                import sys
                
                # Set up non-blocking input checking
                print("\nMonitoring log file... (Type 'q' + Enter to exit)")
                
                # Open the file for continuous reading
                with open(log_file_path, 'r') as file:
                    # Go to the end of the file
                    file.seek(0, 2)
                    
                    # Keep reading new lines as they're added with an exit option
                    while True:
                        # Check if there's user input without blocking
                        if select.select([sys.stdin], [], [], 0)[0]:
                            user_input = sys.stdin.readline().strip()
                            if user_input.lower() == 'q':
                                print("\n" + "=" * 80)
                                print("Exiting log follow mode. Returning to command mode.")
                                print("=" * 80 + "\n")
                                return "✅ Stopped following logs."
                        
                        # Check for new log content
                        line = file.readline()
                        if line:
                            print(line.rstrip())
                        else:
                            # No new lines, wait a bit before checking again
                            time.sleep(0.1)
            
            except Exception as e:
                return f"❌ Error following log file: {str(e)}"
        
        # Standard non-follow mode: Get log entries from the buffer
        log_entries = []
        buffer_size = self.log_buffer.qsize()
        
        # Try to get requested number of lines from buffer first
        for _ in range(min(lines, buffer_size)):
            try:
                log_entries.append(self.log_buffer.get_nowait())
                self.log_buffer.task_done()
            except queue.Empty:
                break
        
        # If buffer doesn't have enough entries, read from the file directly
        if len(log_entries) < lines:
            try:
                with open(log_file_path, 'r') as file:
                    all_lines = file.readlines()
                    # Get the last N lines that weren't already in the buffer
                    remaining_lines = lines - len(log_entries)
                    file_lines = [line.rstrip() for line in all_lines[-remaining_lines:]]
                    log_entries = file_lines + log_entries  # Prepend file lines
            except Exception as e:
                return f"❌ Error reading log file: {str(e)}"
        
        # Limit to the requested number of lines
        log_entries = log_entries[-lines:]
        
        # Format the output
        if log_entries:
            return f"📜 Latest log entries for {self.current_config_name}:\n\n```\n" + "\n".join(log_entries) + "\n```\n\nUse `tail_logs(50)` to see more lines or `tail_logs(lines=20, follow=True)` to follow logs in real-time."
        else:
            return f"⚠️ No log entries found for {self.current_config_name}"

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
