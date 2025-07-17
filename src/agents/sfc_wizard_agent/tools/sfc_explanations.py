#!/usr/bin/env python3
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

AWS Shopfloor Connectivity (SFC) explanations module.
Provides explanations for SFC concepts and environment specifications.
"""

from typing import Dict, Any


def generate_environment_specs(
    protocol: str, devices: str, data_volume: str, targets: str, sfc_knowledge: Dict[str, Any]
) -> str:
    """Generate environment specifications needed for SFC deployment.

    Args:
        protocol: Primary protocol to be used
        devices: Description of devices to connect
        data_volume: Expected data volume and frequency
        targets: Target AWS services or systems
        sfc_knowledge: Dictionary containing SFC knowledge base

    Returns:
        String containing formatted environment specifications
    """
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
    protocol_info = sfc_knowledge["supported_protocols"].get(
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
        for aws_service in sfc_knowledge["aws_targets"].keys()
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


def what_is_sfc() -> str:
    """Provide an explanation of what SFC (Shop Floor Connectivity) is

    Returns:
        String explanation of SFC
    """
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


def explain_concept(concept: str, sfc_knowledge: Dict[str, Any]) -> str:
    """Explain SFC concepts

    Args:
        concept: SFC concept to explain
        sfc_knowledge: Dictionary containing SFC knowledge base

    Returns:
        String explanation of the requested concept
    """
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

**Available Protocols**: {', '.join(sfc_knowledge['supported_protocols'].keys())}
**Available AWS Targets**: {', '.join(sfc_knowledge['aws_targets'].keys())}
"""
