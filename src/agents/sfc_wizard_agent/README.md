# SFC Wizard Agent

An intelligent agent specialized for AWS Shop Floor Connectivity (SFC) configuration management, debugging, and testing. Built with the Strands framework and Model Context Protocol (MCP) for enhanced AI-powered industrial connectivity solutions.

## Overview

The SFC Wizard Agent is a conversational AI assistant that helps you:

- 🔍 **Debug existing SFC configurations** - Identify and resolve configuration issues
- 🛠️ **Create new SFC configurations** - Generate optimized configurations for various protocols
- 💾 **Manage configuration files** - Load, save, and validate JSON configurations
- ▶️ **Test configurations locally** - Run SFC configurations in local test environments
- 📊 **Visualize data flows** - Monitor and visualize data from FILE-TARGET configurations
- 📚 **Learn SFC concepts** - Get explanations of SFC components and best practices

## Prerequisites

- **Python 3.10+** - Required for the agent runtime
- **UV Package Manager** - For dependency management and execution
- **AWS Account** - For deploying configurations to AWS services

### Install UV

If you haven't installed UV yet, install it using:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or follow the [UV installation guide](https://docs.astral.sh/uv/getting-started/installation/).

## Quick Start

### Option 1: Run Directly from GitHub (Recommended)

Run the agent directly from the GitHub repository without cloning:

```bash
uvx --from git+https://github.com/aws-samples/sample-sfc-agent.git#subdirectory=src/agents/sfc_wizard_agent agent
```

### Option 2: Local Development

1. **Navigate to the agent directory:**
   ```bash
   cd src/agents/sfc_wizard_agent
   ```

2. **Initialize dependencies:**
   ```bash
   ./scripts/init.sh
   ```

3. **Run the agent:**
   ```bash
   uv run python -m sfc_wizard.agent
   ```

   Or use the convenience script:
   ```bash
   ./scripts/run.sh
   ```

## Supported Protocols & Targets

### Industrial Protocols
- **OPC-UA** - OPC Unified Architecture
- **Modbus** - Modbus TCP/RTU protocol
- **S7** - Siemens S7 communication
- **And more** - Additional protocols supported by SFC

### AWS Targets
- **AWS IoT Core** - For IoT device management and messaging
- **Amazon S3** - For data storage and archival
- **Amazon Timestream** - For time-series data
- **DEBUG** - For local testing and development

## Key Features

### Interactive Configuration Management
- Validate existing SFC configurations
- Generate configuration templates for specific protocols and targets
- Load configurations from JSON files
- Save validated configurations to files

### Local Testing Environment
- Run SFC configurations locally for testing
- Monitor real-time logs with tail functionality
- Visualize data flows from FILE-TARGET configurations
- Clean up test runs and manage disk space

### Intelligent Assistance
- Diagnose common SFC issues with troubleshooting guidance
- Suggest optimizations based on performance requirements
- Explain SFC concepts and components
- Provide environment specifications for deployment

## Configuration

### Environment Variables

Create a `.env` file in the agent directory with:

```env
# MCP Server Configuration (optional)
MCP_SERVER_COMMAND=uv
MCP_SERVER_ARGS=run,python
MCP_SERVER_PATH=../../../src/mcp-servers/sfc-spec-server/sfc_spec/server.py

# AWS Configuration (for deployment)
AWS_REGION=us-east-1
AWS_PROFILE=default
```

### MCP Integration

The agent integrates with the SFC Spec Server via Model Context Protocol (MCP) for enhanced SFC specification support. The MCP server provides additional tools and resources for SFC development.

## Usage Examples

### Creating a New Configuration

```
SFC Wizard: Create an OPC-UA configuration for AWS IoT Core in production environment
```

### Validating an Existing Configuration

```
SFC Wizard: Validate the configuration in my-sfc-config.json file
```

### Running a Local Test

```
SFC Wizard: Run this configuration locally for testing
```

### Monitoring Logs

```
SFC Wizard: Show me the last 50 lines of logs from the running configuration
```

### Visualizing Data

```
SFC Wizard: Visualize the last 10 minutes of data using the expression "sources.SinusSource.values.sinus.value"
```

## Project Structure

```
src/agents/sfc_wizard_agent/
├── README.md                   # This file
├── pyproject.toml              # Project configuration and dependencies
├── uv.lock                     # Locked dependency versions
├── scripts/                    # Utility scripts
│   ├── init.sh                # Initialize dependencies
│   ├── run.sh                 # Run the agent
│   ├── test.sh                # Run tests
│   └── lint.sh                # Code linting
├── sfc_wizard/                 # Main agent package
│   ├── __init__.py
│   └── agent.py               # Main agent implementation
└── tools/                      # SFC-specific tools
    ├── config_generator.py     # Configuration template generation
    ├── config_validator.py     # Configuration validation
    ├── diagnostics.py          # Issue diagnosis and optimization
    ├── file_operations.py      # File I/O operations
    ├── folder_operations.py    # Directory management
    ├── log_operations.py       # Log monitoring and analysis
    ├── sfc_explanations.py     # SFC concept explanations
    ├── sfc_knowledge.py        # SFC knowledge base
    ├── sfc_runner.py           # Local SFC execution
    └── sfc_visualization.py    # Data visualization
```

## Development

### Running Tests

```bash
./scripts/test.sh
```

### Code Formatting

```bash
./scripts/lint.sh
```

### Adding Dependencies

Edit `pyproject.toml` and run:

```bash
./scripts/init.sh
```

## Troubleshooting

### Common Issues

1. **UV not found**: Install UV using the installation command above
2. **Dependencies missing**: Run `./scripts/init.sh` to install dependencies
3. **AWS credentials**: Ensure AWS credentials are configured for deployment features
4. **MCP server errors**: Check that the SFC Spec Server is properly configured

### Getting Help

The agent includes built-in help and explanations. You can ask:

- "What is SFC?" - Learn about Shop Floor Connectivity
- "Explain OPC-UA configuration" - Get protocol-specific guidance
- "How do I debug connection issues?" - Troubleshooting assistance

## Contributing

This project follows the Amazon Open Source Code of Conduct. Please see the main repository's CONTRIBUTING.md for guidelines.

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.

## Related Components

- **[SFC Spec Server](../../mcp-servers/sfc-spec-server/README.md)** - MCP server providing SFC specifications and tools
- **[Main Repository](../../../README.md)** - Overall project documentation and samples

---

*Part of the AWS Shop Floor Connectivity sample project for connecting industrial devices to AWS services.*
