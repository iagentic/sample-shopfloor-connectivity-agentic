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

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```cmd
pip install uv
```

Or follow the [UV installation guide](https://docs.astral.sh/uv/getting-started/installation/).

## Quick Start

### Option 1: Run Directly from GitHub (Recommended)

Run the agent directly from the GitHub repository without cloning:

```bash
uvx --from git+https://github.com/aws-samples/sample-shopfloor-connectivity-agentic.git#subdirectory=src/agents/sfc_wizard_agent agent
```

### Option 2: Local Development

1. **Navigate to the agent directory:**
   ```bash
   cd agents/sfc_wizard_agent
   ```

2. **Initialize dependencies:**
   
   **Linux/macOS:**
   ```bash
   ./scripts/init.sh
   ```
   
   **Windows:**
   ```cmd
   scripts\init.bat
   ```

3. **Run the agent:**
   
   **Linux/macOS:**
   ```bash
   ./scripts/run.sh
   ```
   
   **Windows:**
   ```cmd
   run.bat
   ```
   
   > Note: Windows batch files (run.bat and run-ui.bat) are located in the main agent directory 
   > for convenient double-click execution.

   Or run with Python directly:
   ```bash
   uv run python -m sfc_wizard.agent
   ```

### Windows-Specific Setup

For Windows users, we provide additional compatibility options:

1. **Install Windows-specific dependencies:**
   ```cmd
   pip install -e .[windows]
   ```
   This installs the windows-curses package to enable terminal visualization.

2. **Web UI Mode:** On Windows, the data visualizer will automatically use the web UI mode for visualization if the terminal mode is not available.

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
MCP_SERVER_PATH=../../../mcp-servers/sfc-spec-server/sfc_spec/server.py

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
agents/sfc_wizard_agent/
├── README.md                   # This file
├── pyproject.toml              # Project configuration and dependencies
├── uv.lock                     # Locked dependency versions
├── run.bat                     # Run the agent (Windows) - for double-click execution
├── run-ui.bat                  # Run the web UI (Windows) - for double-click execution
├── scripts/                    # Utility scripts
│   ├── init.sh                # Initialize dependencies (Linux/macOS)
│   ├── init.bat               # Initialize dependencies (Windows)
│   ├── run.sh                 # Run the agent (Linux/macOS)
│   ├── run-ui.sh              # Run the web UI (Linux/macOS)
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

**Linux/macOS:**
```bash
./scripts/test.sh
```

### Code Formatting

**Linux/macOS:**
```bash
./scripts/lint.sh
```

### Adding Dependencies

Edit `pyproject.toml` and run:

**Linux/macOS:**
```bash
./scripts/init.sh
```

**Windows:**
```cmd
scripts\init.bat
```

## Troubleshooting

### Common Issues

1. **UV not found**: Install UV using the installation command above
2. **Dependencies missing**: Run `./scripts/init.sh` (Linux/macOS) or `scripts\init.bat` (Windows) to install dependencies
3. **AWS credentials**: Ensure AWS credentials are configured for deployment features
4. **MCP server errors**: Check that the SFC Spec Server is properly configured
5. **Windows-specific issues**: 
   - If terminal visualization doesn't work, ensure the `windows-curses` package is installed or use the web UI mode
   - Path issues on Windows: Use backslashes (`\`) for file paths in Windows commands

### Getting Help

The agent includes built-in help and explanations. You can ask:

- "What is SFC?" - Learn about Shop Floor Connectivity
- "Explain OPC-UA configuration" - Get protocol-specific guidance
- "How do I debug connection issues?" - Troubleshooting assistance

## Cross-Platform Compatibility

This project is designed to work across Linux, macOS, and Windows. Key compatibility features include:

- **Platform-specific scripts**: Equivalent `.sh` and `.bat` scripts for all operations
- **Terminal visualization**: Uses `curses` on Linux/macOS and `windows-curses` on Windows
- **Automatic mode selection**: Falls back to web UI mode on platforms where terminal visualization isn't supported
- **Path handling**: Cross-platform path handling with OS-aware path separators

## Contributing

This project follows the Amazon Open Source Code of Conduct. Please see the main repository's CONTRIBUTING.md for guidelines.

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.

## Related Components

- **[SFC Spec Server](../../mcp-servers/sfc-spec-server/README.md)** - MCP server providing SFC specifications and tools
- **[Main Repository](../../../README.md)** - Overall project documentation and samples

---

*Part of the AWS Shop Floor Connectivity sample project for connecting industrial devices to AWS services.*
