# SFC Documentation MCP Server

This Model Context Protocol (MCP) server provides tools to interact with the Shopfloor Connectivity (SFC) GitHub repository documentation and functionality. It allows AI assistants to access SFC documentation, extract examples, search for specific information, and validate configurations.

## Features

The server provides the following tools:

### Documentation Tools

- **update_repo**: Updates the SFC repository by pulling the latest changes
- **list_core_docs**, **list_adapter_docs**, **list_target_docs**: Lists documents in respective directories
- **get_core_doc**, **get_adapter_doc**, **get_target_doc**: Retrieves specific documents
- **query_docs**: Searches for documents across different types with filtering options
- **search_doc_content**: Searches for text patterns within documents
- **extract_json_examples**: Extracts JSON examples from documents matching flexible patterns (supports wildcards)

### Configuration Tools

- **get_sfc_config_examples**: Retrieves SFC configuration examples with flexible name pattern matching
- **validate_sfc_config**: Performs basic validation of an SFC configuration

## Installation

1. Ensure you have Python 3.8+ installed
2. Install dependencies:
   ```bash
   pip install fastmcp requests
   ```
3. Clone the SFC repository into the `sfc-repo` directory:
   ```bash
   git clone https://github.com/aws-samples/shopfloor-connectivity sfc-repo
   ```

## Usage

### Running the Server

#### Option 1: Run Directly from GitHub (Recommended)

Run the server directly from the GitHub repository without cloning:

```bash
uvx --from git+https://github.com/aws-samples/sample-sfc-agent.git#subdirectory=src/mcp/sfc-spec-server sfc_spec
```

#### Option 2: Local Development

The server runs using stdio transport for MCP communication:

```bash
python -m sfc_spec.server
```

### MCP Client Configuration

To use this server with an MCP client, add it to your MCP configuration file:

**Claude Desktop Configuration (`claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "sfc-spec-server": {
      "autoApprove": [],
      "disabled": false,
      "timeout": 5000,
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/aws-samples/sample-sfc-agent.git#subdirectory=src/mcp/sfc-spec-server",
        "sfc_spec"
      ],
      "env": {}
    }
  }
}
```

**Cline Configuration:**
```json
{
  "mcpServers": [
    {
      "name": "sfc-spec-server",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/aws-samples/sample-sfc-agent.git#subdirectory=src/mcp/sfc-spec-server",
        "sfc_spec"
      ]
    }
  ]
}
```

**For Local Development:**
```json
{
  "mcpServers": {
    "sfc-spec-server": {
      "command": "python",
      "args": ["-m", "sfc_spec.server"],
      "cwd": "/path/to/sfc-spec-server"
    }
  }
}
```

### Testing the Server

Run the test program to verify server functionality:

```bash
python test_server.py
```

This will test all available tools and report results.

## MCP Tool Usage Examples

Once connected to an MCP client, you can use the tools with the following JSON format:

### Repository Management

#### Update Repository
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "update_repo",
  "arguments": {}
}
```

### Documentation Listing Tools

#### List Core Documentation
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "list_core_docs",
  "arguments": {}
}
```

#### List Adapter Documentation
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "list_adapter_docs",
  "arguments": {}
}
```

#### List Target Documentation
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "list_target_docs",
  "arguments": {}
}
```

### Documentation Retrieval Tools

#### Get Core Documentation
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "get_core_doc",
  "arguments": {
    "doc_name": "architecture"
  }
}
```

#### Get Adapter Documentation
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "get_adapter_doc",
  "arguments": {
    "doc_name": "mqtt-adapter"
  }
}
```

#### Get Target Documentation
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "get_target_doc",
  "arguments": {
    "doc_name": "aws-s3-target"
  }
}
```

### Advanced Documentation Search

#### Query Documents with Filtering
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "query_docs",
  "arguments": {
    "doc_type": "all",
    "search_term": "configuration",
    "include_content": true
  }
}
```

#### Search Document Content
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "search_doc_content",
  "arguments": {
    "search_text": "OPC UA",
    "doc_type": "adapter",
    "case_sensitive": false
  }
}
```

### JSON Example Extraction

#### Extract JSON Examples with Pattern Matching
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "extract_json_examples",
  "arguments": {
    "doc_type": "core",
    "doc_name": "config*"
  }
}
```

**Pattern Matching Options:**
- Exact match: `"configuration"` matches only "configuration.md"
- Prefix match: `"config*"` matches files starting with "config"
- Suffix match: `"*config"` matches files ending with "config"
- Contains match: `"*config*"` matches any file containing "config"

#### Get SFC Configuration Examples
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "get_sfc_config_examples",
  "arguments": {
    "component_type": "adapter",
    "name_pattern": "*OPCUA*"
  }
}
```

### Configuration Validation

#### Validate SFC Configuration
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "validate_sfc_config",
  "arguments": {
    "config": {
      "name": "MyOPCUAAdapter",
      "adapterType": "OPCUA",
      "description": "OPC UA adapter for industrial equipment",
      "sources": [
        {
          "name": "OpcuaSource1",
          "endpoint": "opc.tcp://localhost:4840/opcua/server",
          "securityPolicy": "None",
          "topics": [
            {
              "name": "Temperature",
              "sourcePath": "ns=2;i=1001",
              "dataType": "Float"
            },
            {
              "name": "Pressure",
              "sourcePath": "ns=2;i=1002",
              "dataType": "Float"
            }
          ]
        }
      ]
    }
  }
}
```

#### Validate Target Configuration
```json
{
  "server_name": "sfc-spec-server",
  "tool_name": "validate_sfc_config",
  "arguments": {
    "config": {
      "name": "MyS3Target",
      "targetType": "AWS_S3",
      "description": "AWS S3 target for data storage",
      "targets": [
        {
          "name": "S3Bucket1",
          "bucket": "my-sfc-data-bucket",
          "region": "us-east-1",
          "prefix": "industrial-data/",
          "compression": "gzip"
        }
      ]
    }
  }
}
```

## Example Tool Usage Workflows

### Complete Documentation Search Workflow
```json
[
  {
    "server_name": "sfc-spec-server",
    "tool_name": "update_repo",
    "arguments": {}
  },
  {
    "server_name": "sfc-spec-server",
    "tool_name": "query_docs",
    "arguments": {
      "doc_type": "adapter",
      "search_term": "opcua",
      "include_content": false
    }
  },
  {
    "server_name": "sfc-spec-server",
    "tool_name": "get_adapter_doc",
    "arguments": {
      "doc_name": "opcua-adapter"
    }
  },
  {
    "server_name": "sfc-spec-server",
    "tool_name": "extract_json_examples",
    "arguments": {
      "doc_type": "adapter",
      "doc_name": "opcua*"
    }
  }
]
```

### Configuration Development Workflow
```json
[
  {
    "server_name": "sfc-spec-server",
    "tool_name": "get_sfc_config_examples",
    "arguments": {
      "component_type": "adapter",
      "name_pattern": "*MQTT*"
    }
  },
  {
    "server_name": "sfc-spec-server",
    "tool_name": "validate_sfc_config",
    "arguments": {
      "config": {
        "name": "MyMQTTAdapter",
        "adapterType": "MQTT",
        "sources": [
          {
            "name": "MqttSource1",
            "broker": "mqtt://localhost:1883",
            "topics": [
              {"name": "sensor1", "sourcePath": "sensors/temperature"}
            ]
          }
        ]
      }
    }
  }
]
```

## Integration with AI Assistants

This server is designed to be used with AI assistants that support the Model Context Protocol (MCP). When connected, the assistant can use these tools to:

1. Access and search SFC documentation
2. Extract configuration examples and JSON snippets
3. Validate user-provided configurations
4. Provide relevant guidance about SFC components

By leveraging this MCP server, assistants can provide more accurate and context-aware help with SFC-related tasks without requiring the full documentation to be included in their context window.
