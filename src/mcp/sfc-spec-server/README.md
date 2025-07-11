# SFC Documentation MCP Server

This is a Model Context Protocol (MCP) server that provides structured information and tools for interacting with the [AWS Shopfloor Connectivity (SFC)](https://github.com/aws-samples/shopfloor-connectivity) GitHub repository.

## Features

The server provides:

1. **Repository Management**:
   - Tool to update the repository using `git pull`

2. **Documentation Access**:
   - Access to markdown documentation from the SFC repository's docs folders:
     - Core documentation (`docs/core`)
     - Adapter documentation (`docs/adapters`)
     - Target documentation (`docs/targets`)

## Tools

### `update_repo`

Updates the local SFC repository by running `git pull` to get the latest changes.

**Usage:**
```python
use_mcp_tool(
    server_name="sfc-docs-server",
    tool_name="update_repo",
    arguments={}
)
```

## Resources

### Core Documentation

- List all core documentation files:
  ```python
  access_mcp_resource(
      server_name="sfc-docs-server",
      uri="core_docs"
  )
  ```

- Get specific core documentation file:
  ```python
  access_mcp_resource(
      server_name="sfc-docs-server",
      uri="core_docs/document_name"  # Replace with actual document name without .md extension
  )
  ```

### Adapter Documentation

- List all adapter documentation files:
  ```python
  access_mcp_resource(
      server_name="sfc-docs-server",
      uri="adapter_docs"
  )
  ```

- Get specific adapter documentation file:
  ```python
  access_mcp_resource(
      server_name="sfc-docs-server",
      uri="adapter_docs/document_name"  # Replace with actual document name without .md extension
  )
  ```

### Target Documentation

- List all target documentation files:
  ```python
  access_mcp_resource(
      server_name="sfc-docs-server",
      uri="target_docs"
  )
  ```

- Get specific target documentation file:
  ```python
  access_mcp_resource(
      server_name="sfc-docs-server",
      uri="target_docs/document_name"  # Replace with actual document name without .md extension
  )
  ```

## Installation and Setup

1. The server requires the SFC repository to be cloned at `src/mcp/sfc-repo`.
2. Ensure that `fastmcp` version 2.10.0 or higher is installed.

## Starting the Server

To start the server, run:

```bash
python src/mcp/server.py
```

The server will start and become available for MCP tool and resource operations.
