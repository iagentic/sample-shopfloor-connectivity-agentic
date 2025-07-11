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
   ```
   pip install fastmcp requests
   ```
3. Clone the SFC repository into the `sfc-repo` directory:
   ```
   git clone https://github.com/aws-samples/shopfloor-connectivity sfc-repo
   ```

## Usage

### Running the Server

Start the MCP server:

```bash
python server.py
```

The server will run on `http://127.0.0.1:8000/sfc` by default.

### Testing the Server

Run the test program to verify server functionality:

```bash
python test_server.py
```

This will test all available tools and report results.

## Tool Examples

### Retrieving SFC Documentation

```json
{
  "server_name": "sfc-docs-server",
  "tool_name": "get_core_doc",
  "arguments": {
    "doc_name": "architecture"
  }
}
```

### Searching Documentation

```json
{
  "server_name": "sfc-docs-server",
  "tool_name": "search_doc_content",
  "arguments": {
    "search_text": "configuration",
    "doc_type": "all",
    "case_sensitive": false
  }
}
```

### Validating a Configuration

```json
{
  "server_name": "sfc-docs-server",
  "tool_name": "validate_sfc_config",
  "arguments": {
    "config": {
      "name": "MyAdapter",
      "adapterType": "OPCUA",
      "sources": [
        {
          "name": "OpcuaSource1",
          "endpoint": "opc.tcp://localhost:4840/opcua/server",
          "topics": [
            {"name": "Topic1", "sourcePath": "ns=2;i=1", "dataType": "Int32"}
          ]
        }
      ]
    }
  }
}
```

### Extracting JSON Examples

```json
{
  "server_name": "sfc-docs-server",
  "tool_name": "extract_json_examples",
  "arguments": {
    "doc_type": "core",
    "doc_name": "config*"
  }
}
```

The `doc_name` parameter supports flexible pattern matching:
- Exact match: `"configuration"` matches only "configuration.md"
- Prefix match: `"config*"` matches files starting with "config"
- Suffix match: `"*config"` matches files ending with "config"
- Contains match: `"*config*"` matches any file containing "config"

### Retrieving Configuration Examples

```json
{
  "server_name": "sfc-docs-server",
  "tool_name": "get_sfc_config_examples",
  "arguments": {
    "component_type": "adapter",
    "name_pattern": "*OPCUA*"
  }
}
```

The `name_pattern` parameter supports the same wildcard matching as the `extract_json_examples` tool, allowing you to filter configuration examples by component name.

## Integration with AI Assistants

This server is designed to be used with AI assistants that support the Model Context Protocol (MCP). When connected, the assistant can use these tools to:

1. Access and search SFC documentation
2. Extract configuration examples and JSON snippets
3. Validate user-provided configurations
4. Provide relevant guidance about SFC components

By leveraging this MCP server, assistants can provide more accurate and context-aware help with SFC-related tasks without requiring the full documentation to be included in their context window.
