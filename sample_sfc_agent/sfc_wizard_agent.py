#!/usr/bin/env python3
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

AWS Shopfloor Connectivity (SFC) Wizard Agent
Specialized assistant for debugging, creating, and testing SFC configurations.
"""

import sys
import json
from typing import List, Dict, Any
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
            base_config[f"{protocol}-SOURCE"][
                "AdapterController"
            ] = "MODBUS-CONTROLLER-1"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "Register1": {"Address": "40001", "DataType": "UInt16"},
                "Register2": {"Address": "40002", "DataType": "UInt16"},
            }
        elif protocol == "S7":
            base_config[f"{protocol}-SOURCE"]["AdapterController"] = "S7-PLC-1"
            base_config[f"{protocol}-SOURCE"]["Channels"] = {
                "DB1Value1": {"Address": "%DB1:0:DINT"},
                "DB1Value2": {"Address": "%DB1:4:REAL"},
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
                {"Region": "us-east-1", "TopicName": "sfc/industrial-data"}
            )
        elif target == "DEBUG":
            base_config[f"{target}Target"] = {
                "Active": True,
                "TargetType": "DEBUG-TARGET",
            }

        return base_config

    def _generate_target_types(self, target: str) -> Dict[str, Any]:
        """Generate target types configuration"""
        target_types = {}

        if target == "AWS-S3":
            target_types["AWS-S3"] = {
                "JarFiles": ["./aws-s3-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awss3.AwsS3TargetWriter",
            }
        elif target == "AWS-IOT-CORE":
            target_types["AWS-IOT-CORE"] = {
                "JarFiles": ["./aws-iot-core-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.awsiotcore.AwsIotCoreTargetWriter",
            }
        elif target == "DEBUG":
            target_types["DEBUG-TARGET"] = {
                "JarFiles": ["./debug-target/lib"],
                "FactoryClassName": "com.amazonaws.sfc.debugtarget.DebugTargetWriter",
            }

        return target_types

    def _generate_adapter_types(self, protocol: str) -> Dict[str, Any]:
        """Generate adapter types configuration"""
        adapter_types = {}

        if protocol == "OPCUA":
            adapter_types["OPCUA"] = {
                "JarFiles": ["./opcua/lib"],
                "FactoryClassName": "com.amazonaws.sfc.opcua.OpcuaAdapter",
            }
        elif protocol == "MODBUS":
            adapter_types["MODBUS"] = {
                "JarFiles": ["./modbus/lib"],
                "FactoryClassName": "com.amazonaws.sfc.modbus.ModbusAdapter",
            }
        elif protocol == "S7":
            adapter_types["S7"] = {
                "JarFiles": ["./s7/lib"],
                "FactoryClassName": "com.amazonaws.sfc.s7.S7Adapter",
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

    def run(self):
        """Main interaction loop"""
        self.boot()

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


def main():
    """Main function to run the SFC Wizard"""
    print("Starting SFC Wizard Agent...")

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
