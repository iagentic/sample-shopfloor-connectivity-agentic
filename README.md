# Agent Framework with Strands SDK

A collection of specialized AI agents built using the [Strands Agents SDK](https://github.com/strands-agents/sdk-python), including a general-purpose restricted agent and a specialized AWS Shopfloor Connectivity (SFC) wizard.

## Available Agents

### 1. SFC Wizard Agent 🏭
**Specialized for AWS Shopfloor Connectivity (SFC) Framework**

A comprehensive assistant for industrial data connectivity, helping with debugging, creating, and testing SFC configurations for connecting manufacturing equipment to AWS services.

### 2. Restricted Agent 🤖
**General-purpose constrained assistant**

A safety-focused agent that asks predefined questions on startup and operates within specific constraints and allowed topics.

---

## SFC Wizard Agent

### Overview
The SFC Wizard is your expert assistant for AWS Shopfloor Connectivity, an industrial data ingestion framework that connects manufacturing equipment to AWS services using various industrial protocols.

### Key Capabilities

- **🔍 Debug Configurations**: Validate and troubleshoot existing SFC configurations
- **🛠️ Create Templates**: Generate configuration templates for various protocol/target combinations
- **💾 File Operations**: Save and load configurations to/from JSON files
- **▶️ Local Testing**: Run configurations in isolated test environments
- **🧪 Test Planning**: Create comprehensive test plans for SFC deployments
- **🏗️ Environment Specs**: Define infrastructure requirements for SFC deployments
- **📚 Expert Knowledge**: Explain SFC concepts, components, and best practices

### Supported Protocols & Targets

**Industrial Protocols:**
- OPC-UA, Modbus, Siemens S7, MQTT, REST API, SQL
- SNMP, Allen-Bradley PCCC, Beckhoff ADS, J1939
- Mitsubishi SLMP, NATS, Data Simulator

**AWS Targets:**
- IoT Core, IoT Analytics, IoT SiteWise, S3, Kinesis
- Kinesis Firehose, Lambda, SNS, SQS, Timestream, MSK

**Edge Targets:**
- OPC-UA Server/Writer, Debug Terminal, File System, MQTT, NATS

### How to Run

```bash
uv run python -m sample_sfc_agent.sfc_wizard_agent
```

### Example Interaction

```
============================================================
🏭 AWS SHOPFLOOR CONNECTIVITY (SFC) WIZARD
============================================================
Specialized assistant for industrial data connectivity to AWS

🎯 I can help you with:
• 🔍 Debug existing SFC configurations
• 🛠️  Create new SFC configurations
• 💾 Save configurations to JSON files
• 📂 Load configurations from JSON files
• ▶️  Run configurations in local test environments
• 🧪 Test configurations against environments
• 🏗️  Define required deployment environments
• 📚 Explain SFC concepts and components

SFC Wizard: Create a template for OPC-UA to S3
```

The wizard will generate a complete SFC configuration template with proper structure, protocol-specific settings, and AWS target configurations.

### SFC Wizard Tools

1. **`validate_sfc_config`**: Comprehensive configuration validation
2. **`create_sfc_config_template`**: Generate protocol-to-target templates
3. **`diagnose_sfc_issue`**: Troubleshoot common SFC problems
4. **`suggest_sfc_optimization`**: Performance and cost optimization recommendations
5. **`generate_environment_specs`**: Infrastructure requirement specifications
6. **`explain_sfc_concept`**: Detailed explanations of SFC components
7. **`generate_test_plan`**: Comprehensive testing strategies
8. **`save_config_to_file`**: Save SFC configurations to JSON files
9. **`read_config_from_file`**: Load existing SFC configurations from JSON files
10. **`run_sfc_config_locally`**: Execute configurations in isolated test environments

---

## Restricted Agent

### Overview
A safety-focused AI agent that asks predefined questions on startup and operates within specific constraints to ensure controlled and predictable interactions.

### Features

- **Predefined Startup Questions**: Asks 5 specific questions every time it boots up
- **Restricted Operations**: Only allows certain types of tasks and topics
- **Built-in Safety**: Filters out prohibited content and dangerous requests
- **Custom Tools**: Includes user info retrieval, topic validation, and simple calculator
- **Multiple Model Support**: Supports Amazon Bedrock (default) with fallback options

### Predefined Questions

The agent asks these questions on every startup:

1. What is your name?
2. What task would you like me to help you with today?
3. Do you have any specific constraints or requirements?
4. What is the expected outcome of this task?
5. Are there any resources or information I should be aware of?

### Allowed Topics

The agent is restricted to help with:
- General assistance
- Information lookup
- Text processing
- Simple calculations
- Task planning

### Usage

```bash
./scripts/test.sh
```

Alternatively, you can run directly with:

```bash
uv run python -m sample_sfc_agent.restricted_agent
```

---

## Installation

### Prerequisites

This project uses [uv](https://astral.sh/uv) for fast Python package management. Install uv first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup

1. Clone or download this project
2. Run the initialization script:
   ```bash
   chmod +x scripts/init.sh
   ./scripts/init.sh
   ```

3. (Optional) Configure environment variables:
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

The project uses `pyproject.toml` for dependency management with `uv` package manager.

## Architecture

Both agents are built on the Strands framework with specialized tool sets:

### Common Components

- **Strands Agent**: Core AI agent framework
- **Custom Tools**: Agent-specific functionality using `@tool` decorator
- **Model Support**: Amazon Bedrock with fallbacks
- **Environment Configuration**: `.env` based configuration

### Agent-Specific Tools

**SFC Wizard Tools:**
- Industrial protocol knowledge base
- Configuration validation and generation
- Performance optimization suggestions
- Testing and deployment guidance

**Restricted Agent Tools:**
- User information collection
- Topic validation
- Safe mathematical calculations
- Content filtering

## Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.template .env
```

Configure:
- AWS credentials (for Bedrock model)
- Agent name and version
- Logging level

### Model Configuration

Both agents try to use Amazon Bedrock by default but fall back to Strands default models if unavailable.

For Amazon Bedrock:
1. Configure AWS credentials
2. Ensure access to Claude models in your AWS account
3. Set appropriate AWS region (default: us-west-2)

## Running the Agents

### SFC Wizard Agent

To run the SFC Wizard interactively:

```bash
uv run python -m sample_sfc_agent.sfc_wizard_agent
```

Then you can test various functions like:
- `validate_sfc_config` with JSON configuration
- `create_sfc_config_template` - e.g., "Create template for MODBUS to AWS-KINESIS"

### Restricted Agent

To run the Restricted Agent:

```bash
./scripts/test.sh
```

Or run directly:

```bash
uv run python -m sample_sfc_agent.restricted_agent
```

### Testing with scripts/test.sh

The `scripts/test.sh` script runs the restricted agent for interactive testing.

### Example SFC Configuration Test

```python
# Test a simple OPC-UA to S3 configuration
config = {
    "AWSVersion": "2022-04-02",
    "Schedules": [{"Name": "Test", "Interval": 1000, "Sources": {"OPC": ["*"]}, "Targets": ["S3"]}],
    "Sources": {"OPC": {"ProtocolAdapter": "OPCUA", "Channels": {"test": {"NodeId": "ns=0;i=2256"}}}},
    "Targets": {"S3": {"TargetType": "AWS-S3", "BucketName": "test-bucket"}},
    "AdapterTypes": {"OPCUA": {"JarFiles": ["./opcua/lib"]}},
    "TargetTypes": {"AWS-S3": {"JarFiles": ["./s3/lib"]}}
}
```

## Use Cases

### SFC Wizard Use Cases

1. **Manufacturing Integration**: Connect PLCs and SCADA systems to AWS
2. **IoT Data Pipeline**: Stream sensor data to AWS services
3. **Industrial Analytics**: Process manufacturing data in the cloud
4. **Predictive Maintenance**: Collect equipment data for ML models
5. **Digital Twin**: Real-time data synchronization

### Restricted Agent Use Cases

1. **Educational Tools**: Safe AI interaction for learning
2. **Customer Support**: Controlled assistance within specific domains
3. **Data Processing**: Text and numerical operations with safety constraints
4. **Task Planning**: Structured planning within defined boundaries

## Troubleshooting

### Common Issues

1. **Import Error**: Run `./scripts/init.sh` to install dependencies
2. **AWS Credentials**: Ensure AWS credentials are properly configured for Bedrock
3. **Permission Denied**: Make scripts executable with `chmod +x scripts/*.sh`
4. **SFC Knowledge**: SFC Wizard includes comprehensive knowledge base for industrial protocols

### Dependencies

- Python 3.10+
- strands-agents
- strands-agents-tools
- python-dotenv

## Extending the Agents

### Adding New SFC Protocols

Update the `supported_protocols` dictionary in `SFCWizardAgent._load_sfc_knowledge()`:

```python
"YOUR_PROTOCOL": {
    "description": "Your Protocol Description", 
    "port_default": 1234
}
```

### Adding New Restricted Agent Topics

Modify the `allowed_topics` list in `RestrictedAgent.__init__()`:

```python
self.allowed_topics = [
    "your new topic",
    # ... existing topics
]
```

### Creating Custom Tools

Use the `@tool` decorator for both agents:

```python
@tool
def your_custom_tool(parameter: str) -> str:
    """Tool description.
    
    Args:
        parameter: Parameter description
    """
    # Your logic here
    return "result"
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

## Links

- [AWS Shopfloor Connectivity](https://github.com/aws-samples/shopfloor-connectivity)
- [Strands Agents SDK](https://github.com/strands-agents/sdk-python)
- [AWS Industrial IoT](https://aws.amazon.com/industrial/)
