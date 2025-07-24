# Shopfloor Connectivity Agentic

A specialized AI agent built using the [Strands Agents SDK](https://github.com/strands-agents/sdk-python) for the [Shopfloor Connectivity](https://github.com/aws-samples/shopfloor-connectivity) (SFC) Framework.

## Overview

This project provides AI-powered tools for Shopfloor Connectivity (SFC), helping developers and engineers work with industrial data connectivity configurations. The project consists of two main components:

## Components

### 🏭 [SFC Wizard Agent](agents/sfc_wizard_agent/README.md)

An intelligent conversational agent specialized for SFC configuration management, debugging, and testing. The agent provides:

- **Configuration Management**: Validate, create, and optimize SFC configurations
- **Local Testing**: Run configurations in isolated test environments with monitoring
- **Troubleshooting**: Diagnose issues and provide optimization recommendations  
- **Knowledge Base**: Comprehensive support for industrial protocols and AWS targets

**Quick Start:**
```bash
cd agents/sfc_wizard_agent
./scripts/run.sh
```

### 📚 [SFC Spec Server](mcp-servers/sfc-spec-server/README.md) 

A Model Context Protocol (MCP) server that provides SFC specifications, documentation, and sfc_wizard.tools. Features include:

- **Specification Access**: Complete SFC configuration schemas and examples
- **Documentation Tools**: Search and retrieve SFC documentation  
- **Integration Support**: MCP protocol for AI agent integration

**Quick Start:**
```bash
cd mcp-servers/sfc-spec-server  
./scripts/run.sh
```

---

## Installation

### Prerequisites

This project uses [uv](https://astral.sh/uv) for fast Python package management. Install uv first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup Options

#### Option 1: Run Directly from GitHub (Recommended)

You can run the components directly from GitHub without cloning:

**SFC Wizard Agent:**
```bash
uvx --from git+https://github.com/aws-samples/sample-shopfloor-connectivity-agentic.git#subdirectory=agents/sfc_wizard_agent agent
```

**SFC Wizard Agent - UI:**
```bash
uvx --from git+https://github.com/aws-samples/sample-shopfloor-connectivity-agentic.git#subdirectory=agents/sfc_wizard_agent sfc-wizard-ui 
```

**SFC Spec MCP Server:**
```bash
uvx --from git+https://github.com/aws-samples/sample-shopfloor-connectivity-agentic.git#subdirectory=mcp-servers/sfc-spec-server sfc_spec
```

#### Option 2: Local Development

1. Clone this repository
2. Navigate to the desired component directory
3. Run the initialization script:
   ```bash
   ./scripts/init.sh
   ```
4. Run the component:
   ```bash
   ./scripts/run.sh
   ```

### Environment Configuration

Each component can be configured with environment variables. See the individual component READMEs for specific configuration options:

- [SFC Wizard Agent Configuration](agents/sfc_wizard_agent/README.md#configuration)
- [SFC Spec Server Configuration](mcp-servers/sfc-spec-server/README.md#configuration)

## Use Cases

- **Manufacturing Integration**: Connect PLCs and SCADA systems to AWS
- **IoT Data Pipeline**: Stream sensor data to AWS services  
- **Industrial Analytics**: Process manufacturing data in the cloud
- **Predictive Maintenance**: Collect equipment data for ML models
- **Digital Twin**: Real-time data synchronization
- **Configuration Management**: AI-assisted SFC configuration development
- **Troubleshooting**: Intelligent diagnosis of SFC deployment issues

## Development

### Project Structure

```

├── agents/
│   └── sfc_wizard_agent/          # Main AI agent for SFC management
│       ├── README.md              # Agent-specific documentation
│       ├── pyproject.toml         # Agent dependencies
│       └── scripts/               # Agent utility scripts
└── mcp/
    └── sfc-spec-server/           # MCP server for SFC specifications  
        ├── README.md              # Server-specific documentation
        ├── pyproject.toml         # Server dependencies
        └── scripts/               # Server utility scripts
```

### Contributing

See individual component READMEs for development guidelines:
- [SFC Wizard Agent Development](agents/sfc_wizard_agent/README.md#development)
- [SFC Spec Server Development](mcp-servers/sfc-spec-server/README.md#development)

### Troubleshooting

For component-specific troubleshooting, refer to:
- [SFC Wizard Agent Troubleshooting](agents/sfc_wizard_agent/README.md#troubleshooting)
- [SFC Spec Server Troubleshooting](mcp-servers/sfc-spec-server/README.md#troubleshooting)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

## Links

- [Shopfloor Connectivity](https://github.com/aws-samples/shopfloor-connectivity)
- [Strands Agents SDK](https://github.com/strands-agents/sdk-python)
- [AWS Industrial IoT](https://aws.amazon.com/industrial/)
