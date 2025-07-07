# SFC Wizard Agent with Strands SDK

A specialized AI agent built using the [Strands Agents SDK](https://github.com/strands-agents/sdk-python) for AWS Shopfloor Connectivity (SFC) Framework.

## SFC Wizard Agent 🏭
**Specialized for AWS Shopfloor Connectivity (SFC) Framework**

A comprehensive assistant for industrial data connectivity, helping with debugging, creating, and testing SFC configurations for connecting manufacturing equipment to AWS services.

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
./scripts/run.sh
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

The SFC Wizard Agent is built on the Strands framework with specialized tool sets:

### Components

- **Strands Agent**: Core AI agent framework
- **Custom Tools**: Agent-specific functionality using `@tool` decorator
- **Model Support**: Amazon Bedrock with fallbacks
- **Environment Configuration**: `.env` based configuration

### SFC Wizard Tools

- Industrial protocol knowledge base
- Configuration validation and generation
- Performance optimization suggestions
- Testing and deployment guidance
- File operations for configuration management
- Local testing capabilities

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

The SFC Wizard Agent tries to use Amazon Bedrock by default but falls back to Strands default models if unavailable.

For Amazon Bedrock:
1. Configure AWS credentials
2. Ensure access to Claude models in your AWS account
3. Set appropriate AWS region (default: us-west-2)

## Running the Agent

### SFC Wizard Agent

#### Using the run script (Recommended)

The easiest way to run the SFC Wizard Agent is using the dedicated run script:

```bash
./scripts/run.sh
```

This script will:
- Check if `uv` is installed and provide installation instructions if missing
- Automatically run `scripts/init.sh` if dependencies aren't installed
- Launch the SFC Wizard Agent with proper environment setup

#### Direct execution

You can also run the SFC Wizard directly:

```bash
uv run python -m sample_sfc_agent.sfc_wizard_agent
```

Then you can test various functions like:
- `validate_sfc_config` with JSON configuration
- `create_sfc_config_template` - e.g., "Create template for MODBUS to AWS-KINESIS"

### Testing with scripts/test.sh

The `scripts/test.sh` script runs the SFC wizard agent for interactive testing:

```bash
./scripts/test.sh
```

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

1. **Manufacturing Integration**: Connect PLCs and SCADA systems to AWS
2. **IoT Data Pipeline**: Stream sensor data to AWS services
3. **Industrial Analytics**: Process manufacturing data in the cloud
4. **Predictive Maintenance**: Collect equipment data for ML models
5. **Digital Twin**: Real-time data synchronization
6. **Configuration Management**: Validate, create, and optimize SFC configurations
7. **Troubleshooting**: Diagnose and resolve SFC deployment issues

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

## Extending the Agent

### Adding New SFC Protocols

Update the `supported_protocols` dictionary in `SFCWizardAgent._load_sfc_knowledge()`:

```python
"YOUR_PROTOCOL": {
    "description": "Your Protocol Description", 
    "port_default": 1234
}
```

### Creating Custom Tools

Use the `@tool` decorator to add new functionality:

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
