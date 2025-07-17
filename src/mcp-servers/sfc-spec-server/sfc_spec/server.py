#!/usr/bin/env python
"""
SFC Documentation MCP Server

This server provides tools to interact with the Shopfloor Connectivity (SFC)
GitHub repository documentation and functionality.
"""

import os
import subprocess
import re
import json
from fastmcp import FastMCP
from typing import Dict, Any, Optional

# Define the repository path
REPO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfc-repo")

# Create the MCP server
server = FastMCP(
    name="sfc-docs-server",
    instructions="Provides access to SFC documentation and repository management tools",
)


@server.tool("update_repo")
def update_repo() -> Dict[str, Any]:
    """
    Updates the SFC repository by pulling the latest changes from the remote repository.

    This tool runs a git pull command in the SFC repository directory to fetch and
    integrate the latest changes.

    Returns:
        dict: A dictionary containing the result of the update operation
            - message (str): Success or failure message
            - details (str): Output from git pull command (on success)
            - error (str): Error message (on failure)

    Example:
        ```
        {
          "server_name": "sfc-docs-server",
          "tool_name": "update_repo",
          "arguments": {}
        }
        ```
    """
    try:
        result = subprocess.run(
            ["git", "pull"], cwd=REPO_PATH, capture_output=True, text=True, check=True
        )
        return {"message": "Repository updated successfully", "details": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"message": "Failed to update repository", "error": e.stderr}


@server.tool("get_core_doc")
def get_core_doc_tool(doc_name: str) -> Dict[str, Any]:
    """
    Fetches a specific document from the core docs directory.

    This tool retrieves the content of a markdown document from the SFC core
    documentation directory.

    Args:
        doc_name (str): The name of the document to fetch (without .md extension)

    Returns:
        dict: A dictionary containing the document content or error information
            - name (str): The name of the document
            - content (str): The markdown content of the document
            - type (str): The document type (always "markdown")
            - error (str): Error message if document not found or cannot be read
            - status (int): HTTP-like status code indicating result

    Example:
        ```
        {
          "server_name": "sfc-docs-server",
          "tool_name": "get_core_doc",
          "arguments": {
            "doc_name": "architecture"
          }
        }
        ```
    """
    doc_path = os.path.join(REPO_PATH, "docs", "core", f"{doc_name}.md")
    return _get_markdown_content(doc_path, doc_name)


@server.tool("list_core_docs")
def list_core_docs_tool() -> Dict[str, Any]:
    """
    Lists all documents in the core docs directory.

    This tool retrieves a list of all markdown documents available in the SFC
    core documentation directory.

    Returns:
        dict: A dictionary containing the list of documents or error information
            - documents (list): List of document info dictionaries, each containing:
                - name (str): The name of the document (without extension)
                - path (str): Relative path to the document
            - error (str): Error message if directory not found or cannot be read
            - status (int): HTTP-like status code indicating result

    Example:
        ```
        {
          "server_name": "sfc-docs-server",
          "tool_name": "list_core_docs",
          "arguments": {}
        }
        ```
    """
    return _list_docs_in_directory(os.path.join(REPO_PATH, "docs", "core"))


@server.tool("get_adapter_doc")
def get_adapter_doc_tool(doc_name: str) -> Dict[str, Any]:
    """
    Fetches a specific document from the adapters docs directory.

    This tool retrieves the content of a markdown document from the SFC adapters
    documentation directory.

    Args:
        doc_name (str): The name of the document to fetch (without .md extension)

    Returns:
        dict: A dictionary containing the document content or error information
            - name (str): The name of the document
            - content (str): The markdown content of the document
            - type (str): The document type (always "markdown")
            - error (str): Error message if document not found or cannot be read
            - status (int): HTTP-like status code indicating result

    Example:
        ```
        {
          "server_name": "sfc-docs-server",
          "tool_name": "get_adapter_doc",
          "arguments": {
            "doc_name": "mqtt-adapter"
          }
        }
        ```
    """
    doc_path = os.path.join(REPO_PATH, "docs", "adapters", f"{doc_name}.md")
    return _get_markdown_content(doc_path, doc_name)


@server.tool("list_adapter_docs")
def list_adapter_docs_tool() -> Dict[str, Any]:
    """
    Lists all documents in the adapters docs directory.

    This tool retrieves a list of all markdown documents available in the SFC
    adapters documentation directory.

    Returns:
        dict: A dictionary containing the list of documents or error information
            - documents (list): List of document info dictionaries, each containing:
                - name (str): The name of the document (without extension)
                - path (str): Relative path to the document
            - error (str): Error message if directory not found or cannot be read
            - status (int): HTTP-like status code indicating result

    Example:
        ```
        {
          "server_name": "sfc-docs-server",
          "tool_name": "list_adapter_docs",
          "arguments": {}
        }
        ```
    """
    return _list_docs_in_directory(os.path.join(REPO_PATH, "docs", "adapters"))


@server.tool("get_target_doc")
def get_target_doc_tool(doc_name: str) -> Dict[str, Any]:
    """
    Fetches a specific document from the targets docs directory.

    This tool retrieves the content of a markdown document from the SFC targets
    documentation directory.

    Args:
        doc_name (str): The name of the document to fetch (without .md extension)

    Returns:
        dict: A dictionary containing the document content or error information
            - name (str): The name of the document
            - content (str): The markdown content of the document
            - type (str): The document type (always "markdown")
            - error (str): Error message if document not found or cannot be read
            - status (int): HTTP-like status code indicating result

    Example:
        ```
        {
          "server_name": "sfc-docs-server",
          "tool_name": "get_target_doc",
          "arguments": {
            "doc_name": "aws-s3-target"
          }
        }
        ```
    """
    doc_path = os.path.join(REPO_PATH, "docs", "targets", f"{doc_name}.md")
    return _get_markdown_content(doc_path, doc_name)


@server.tool("list_target_docs")
def list_target_docs_tool() -> Dict[str, Any]:
    """
    Lists all documents in the targets docs directory.

    This tool retrieves a list of all markdown documents available in the SFC
    targets documentation directory.

    Returns:
        dict: A dictionary containing the list of documents or error information
            - documents (list): List of document info dictionaries, each containing:
                - name (str): The name of the document (without extension)
                - path (str): Relative path to the document
            - error (str): Error message if directory not found or cannot be read
            - status (int): HTTP-like status code indicating result

    Example:
        ```
        {
          "server_name": "sfc-docs-server",
          "tool_name": "list_target_docs",
          "arguments": {}
        }
        ```
    """
    return _list_docs_in_directory(os.path.join(REPO_PATH, "docs", "targets"))


def _get_markdown_content(file_path: str, doc_name: str) -> Dict[str, Any]:
    """Helper function to get markdown content from a file"""
    try:
        if not os.path.exists(file_path):
            return {"error": f"Document '{doc_name}' not found", "status": 404}

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        return {"name": doc_name, "content": content, "type": "markdown"}
    except Exception as e:
        return {"error": f"Failed to read document: {str(e)}", "status": 500}


def _list_docs_in_directory(dir_path: str) -> Dict[str, Any]:
    """Helper function to list markdown documents in a directory"""
    try:
        if not os.path.exists(dir_path):
            return {"error": f"Directory not found: {dir_path}", "status": 404}

        md_files = []
        for file in os.listdir(dir_path):
            if file.endswith(".md"):
                name = file[:-3]  # Remove .md extension
                md_files.append(
                    {"name": name, "path": f"{os.path.basename(dir_path)}/{name}"}
                )

        return {"documents": md_files}
    except Exception as e:
        return {"error": f"Failed to list documents: {str(e)}", "status": 500}


@server.tool("query_docs")
def query_docs_tool(
    doc_type: str, search_term: Optional[str] = None, include_content: bool = True
) -> Dict[str, Any]:
    """
    Dynamically queries documentation based on parameters.

    This tool allows you to search for documents across different documentation types
    with optional filtering by search term and content inclusion.

    Args:
        doc_type (str): Type of document to query. Must be one of:
            - "core": Search only in core documentation
            - "adapter": Search only in adapter documentation
            - "target": Search only in target documentation
            - "all": Search across all documentation types
        search_term (str, optional): Term to search for within document names.
            If provided, only documents containing this term (case-insensitive) will be included.
        include_content (bool, optional): Whether to include the full content of matched documents.
            Defaults to True.

    Returns:
        dict: A dictionary containing the query results
            - query (dict): The original query parameters
            - results (list): List of document info dictionaries, each containing:
                - name (str): The name of the document (without extension)
                - type (str): The document type (core, adapters, or targets)
                - path (str): Relative path to the document
                - content (str): The document content (if include_content is True)
                - error (str): Error message if document content cannot be read
            - count (int): Number of documents found
            - error (str): Error message if the query parameters are invalid
            - status (int): HTTP-like status code indicating result

    Example:
        ```
        {
          "server_name": "sfc-docs-server",
          "tool_name": "query_docs",
          "arguments": {
            "doc_type": "all",
            "search_term": "configuration",
            "include_content": true
          }
        }
        ```
    """
    results = []

    # Determine which directories to search
    directories = []
    if doc_type.lower() == "all":
        directories = ["core", "adapters", "targets"]
    elif doc_type.lower() in ["core", "adapter", "target"]:
        # Map singular to plural form if needed
        dir_map = {"core": "core", "adapter": "adapters", "target": "targets"}
        directories = [dir_map.get(doc_type.lower(), doc_type.lower())]
    else:
        return {
            "error": f"Invalid doc_type: {doc_type}. Must be 'core', 'adapter', 'target', or 'all'.",
            "status": 400,
        }

    # Search in each directory
    for directory in directories:
        dir_path = os.path.join(REPO_PATH, "docs", directory)
        if not os.path.exists(dir_path):
            continue

        for file in os.listdir(dir_path):
            if file.endswith(".md"):
                name = file[:-3]  # Remove .md extension

                # Apply search filter if provided
                if search_term and search_term.lower() not in name.lower():
                    continue

                doc_info = {
                    "name": name,
                    "type": directory,
                    "path": f"{directory}/{name}",
                }

                # Include content if requested
                if include_content:
                    file_path = os.path.join(dir_path, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            doc_info["content"] = f.read()
                    except Exception as e:
                        doc_info["error"] = f"Failed to read content: {str(e)}"

                results.append(doc_info)

    return {
        "query": {
            "doc_type": doc_type,
            "search_term": search_term,
            "include_content": include_content,
        },
        "results": results,
        "count": len(results),
    }


@server.tool("extract_json_examples")
def extract_json_examples_tool(doc_type: str, doc_name: str) -> Dict[str, Any]:
    """
    Extracts JSON examples from documents matching the specified pattern.

    This tool parses documents and extracts any JSON code blocks they contain.
    It attempts to parse each code block as JSON and returns all valid JSON examples.
    The doc_name parameter supports flexible matching patterns.

    Args:
        doc_type (str): The type of document. Must be one of:
            - "core": Document from core documentation
            - "adapter": Document from adapter documentation
            - "target": Document from target documentation
        doc_name (str): The name pattern to match documents (without .md extension).
            Supports the following matching patterns:
            - Exact match: "configuration" matches only "configuration.md"
            - Prefix match: "config*" matches files starting with "config"
            - Wildcards: "conf*ion" matches files like "configuration", "confirmation", etc.
            - Wildcards anywhere: "*aws*" matches any file containing "aws"

    Returns:
        dict: A dictionary containing the extracted JSON examples
            - matching_documents (list): List of document names that matched the pattern
            - total_examples (int): Total number of JSON examples found
            - results (list): List of document result dictionaries, each containing:
                - document_name (str): The name of the document
                - document_type (str): The type of the document
                - examples_count (int): Number of JSON examples found
                - examples (list): List of example dictionaries, each containing:
                    - example_id (int): Sequential ID of the example
                    - content (dict): The parsed JSON content
            - error (str): Error message if document not found or cannot be accessed
            - status (int): HTTP-like status code indicating result

    Example:
        ```
        {
          "server_name": "sfc-docs-server",
          "tool_name": "extract_json_examples",
          "arguments": {
            "doc_type": "core",
            "doc_name": "config*"
          }
        }
        ```
    """
    # Get the document content based on type
    dir_map = {"core": "core", "adapter": "adapters", "target": "targets"}

    if doc_type not in dir_map:
        return {
            "error": f"Invalid doc_type: {doc_type}. Must be 'core', 'adapter', or 'target'.",
            "status": 400,
        }

    # Get directory path
    dir_name = dir_map[doc_type]
    dir_path = os.path.join(REPO_PATH, "docs", dir_name)

    if not os.path.exists(dir_path):
        return {
            "error": f"Directory not found for document type '{doc_type}'",
            "status": 404,
        }

    # Get list of markdown files in the directory
    md_files = [f[:-3] for f in os.listdir(dir_path) if f.endswith(".md")]

    # Convert doc_name pattern to regex pattern
    # Replace * with .* for regex wildcard and escape other special characters
    import fnmatch

    # Find matching documents
    matching_docs = []
    for doc in md_files:
        if fnmatch.fnmatch(doc.lower(), doc_name.lower()):
            matching_docs.append(doc)

    if not matching_docs:
        return {
            "error": f"No documents found matching '{doc_name}' in {dir_name} documentation",
            "status": 404,
            "available_documents": md_files,
        }

    # Process each matching document
    all_results = []
    total_examples = 0

    for doc in matching_docs:
        # Get document content
        doc_path = os.path.join(dir_path, f"{doc}.md")
        doc_content = _get_markdown_content(doc_path, doc)

        # Skip if error
        if "error" in doc_content:
            continue

        # Extract JSON examples from markdown content
        content = doc_content.get("content", "")
        json_examples = []

        # Pattern to match code blocks in markdown
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        code_blocks = re.findall(code_block_pattern, content)

        for i, block in enumerate(code_blocks):
            try:
                # Attempt to parse the block as JSON
                parsed_json = json.loads(block.strip())
                json_examples.append({"example_id": i + 1, "content": parsed_json})
            except json.JSONDecodeError:
                # If it's not valid JSON, skip this block
                continue

        # Add to results if we found examples
        if json_examples:
            all_results.append(
                {
                    "document_name": doc,
                    "document_type": doc_type,
                    "examples_count": len(json_examples),
                    "examples": json_examples,
                }
            )
            total_examples += len(json_examples)

    return {
        "matching_documents": matching_docs,
        "total_examples": total_examples,
        "results": all_results,
        "count": len(all_results),
    }


@server.tool("search_doc_content")
def search_doc_content_tool(
    search_text: str, doc_type: str = "all", case_sensitive: bool = False
) -> Dict[str, Any]:
    """
    Searches for specific text within document content.

    This tool searches for a text pattern across document content and returns
    documents containing the search text along with context around the matches.

    Args:
        search_text (str): The text to search for within documents
        doc_type (str, optional): Type of documents to search in. Must be one of:
            - "core": Search only in core documentation
            - "adapter": Search only in adapter documentation
            - "target": Search only in target documentation
            - "all": Search across all documentation types (default)
        case_sensitive (bool, optional): Whether to perform a case-sensitive search.
            Defaults to False.

    Returns:
        dict: A dictionary containing the search results
            - query (dict): The original search parameters
            - results (list): List of document match dictionaries, each containing:
                - name (str): The name of the document (without extension)
                - type (str): The document type (core, adapters, or targets)
                - path (str): Relative path to the document
                - matches (list): List of match dictionaries, each containing:
                    - line_number (int): Line number where the match was found
                    - context (str): Text context surrounding the match
            - total_matches (int): Total number of matches across all documents
            - documents_count (int): Number of documents with matches

    Example:
        ```
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
    """
    # Determine which directories to search
    directories = []
    if doc_type.lower() == "all":
        directories = ["", "core", "adapters", "targets"]
    elif doc_type.lower() in ["core", "adapter", "target"]:
        # Map singular to plural form if needed
        dir_map = {"core": "core", "adapter": "adapters", "target": "targets"}
        directories = [dir_map.get(doc_type.lower(), doc_type.lower())]
    else:
        return {
            "error": f"Invalid doc_type: {doc_type}. Must be 'core', 'adapter', 'target', or 'all'.",
            "status": 400,
        }

    # Prepare for searching
    results = []
    total_matches = 0
    flags = 0 if case_sensitive else re.IGNORECASE

    # Search in each directory
    for directory in directories:
        dir_path = os.path.join(REPO_PATH, "docs", directory)
        if not os.path.exists(dir_path):
            continue

        for file in os.listdir(dir_path):
            if file.endswith(".md"):
                name = file[:-3]  # Remove .md extension
                file_path = os.path.join(dir_path, file)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Split content into lines for context
                    lines = content.split("\n")

                    # Find all matches
                    matches = []
                    for i, line in enumerate(lines):
                        if re.search(search_text, line, flags):
                            # Get context (3 lines before and after)
                            start = max(0, i - 3)
                            end = min(len(lines), i + 4)
                            context = "\n".join(lines[start:end])

                            matches.append({"line_number": i + 1, "context": context})

                    if matches:
                        results.append(
                            {
                                "name": name,
                                "type": directory,
                                "path": f"{directory}/{name}",
                                "matches": matches,
                                "match_count": len(matches),
                            }
                        )
                        total_matches += len(matches)

                except Exception as e:
                    # Skip files that can't be read
                    continue

    return {
        "query": {
            "search_text": search_text,
            "doc_type": doc_type,
            "case_sensitive": case_sensitive,
        },
        "results": results,
        "total_matches": total_matches,
        "documents_count": len(results),
    }


@server.tool("get_sfc_config_examples")
def get_sfc_config_examples_tool(
    component_type: Optional[str] = None, name_pattern: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves SFC configuration examples from the documentation.

    This tool extracts configuration examples for SFC components from the documentation.
    It can filter by component type and component name pattern if specified.

    Args:
        component_type (str, optional): The type of component to filter examples for.
            If provided, must be one of:
            - "adapter": Return only adapter configuration examples
            - "target": Return only target configuration examples
            - "core": Return only core configuration examples
            - None: Return all configuration examples (default)
        name_pattern (str, optional): Pattern to filter component names.
            Supports the following matching patterns:
            - Exact match: "MyAdapter" matches only components named "MyAdapter"
            - Prefix match: "My*" matches components starting with "My"
            - Wildcards: "*Adapter" matches components ending with "Adapter"
            - Wildcards anywhere: "*AWS*" matches any component with "AWS" in the name

    Returns:
        dict: A dictionary containing the configuration examples
            - examples (list): List of example dictionaries, each containing:
                - component_type (str): The type of component (adapter, target, core)
                - component_name (str): The name of the specific component
                - document_name (str): The name of the document containing the example
                - config (dict): The parsed configuration example
            - count (int): Number of examples found
            - error (str): Error message if component_type is invalid
            - status (int): HTTP-like status code indicating result

    Example:
        ```
        {
          "server_name": "sfc-docs-server",
          "tool_name": "get_sfc_config_examples",
          "arguments": {
            "component_type": "adapter",
            "name_pattern": "*OPCUA*"
          }
        }
        ```
    """
    # Validate component_type if provided
    if component_type and component_type not in ["adapter", "target", "core"]:
        return {
            "error": f"Invalid component_type: {component_type}. Must be 'adapter', 'target', 'core', or None.",
            "status": 400,
        }

    # Determine which doc types to search
    doc_types = []
    if component_type:
        doc_types = [component_type]
    else:
        doc_types = ["core", "adapter", "target"]

    # Map singular to plural form for directory names
    dir_map = {"core": "core", "adapter": "adapters", "target": "targets"}

    all_examples = []

    import fnmatch

    # Process each doc type
    for doc_type in doc_types:
        dir_name = dir_map.get(doc_type, doc_type)
        dir_path = os.path.join(REPO_PATH, "docs", dir_name)

        if not os.path.exists(dir_path):
            continue

        # Get all documents in this directory
        docs = _list_docs_in_directory(dir_path)
        if "error" in docs:
            continue

        # Extract JSON examples from each document
        for doc in docs.get("documents", []):
            doc_name = doc.get("name")

            # Get document path and content
            doc_path = os.path.join(REPO_PATH, "docs", dir_name, f"{doc_name}.md")
            doc_content = _get_markdown_content(doc_path, doc_name)

            if "error" in doc_content:
                continue

            # Extract JSON examples from markdown content
            content = doc_content.get("content", "")

            # Pattern to match code blocks in markdown
            code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
            code_blocks = re.findall(code_block_pattern, content)

            for i, block in enumerate(code_blocks):
                try:
                    # Attempt to parse the block as JSON
                    json_content = json.loads(block.strip())

                    # Identify if this looks like a configuration example
                    if isinstance(json_content, dict) and any(
                        key in json_content
                        for key in [
                            "name",
                            "adapterType",
                            "targetType",
                            "sources",
                            "sources",
                            "targets",
                        ]
                    ):
                        component_name = json_content.get("name", "unknown")

                        # Apply name pattern filter if provided
                        if name_pattern and not fnmatch.fnmatch(
                            component_name.lower(), name_pattern.lower()
                        ):
                            continue

                        all_examples.append(
                            {
                                "component_type": doc_type,
                                "component_name": component_name,
                                "document_name": doc_name,
                                "config": json_content,
                            }
                        )
                except json.JSONDecodeError:
                    # If it's not valid JSON, skip this block
                    continue

    return {"examples": all_examples, "count": len(all_examples)}


@server.tool("validate_sfc_config")
def validate_sfc_config_tool(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs basic validation of an SFC configuration.

    This tool checks if a provided configuration object has the required structure
    and fields for an SFC component configuration.

    Args:
        config (dict): The configuration object to validate. Should be a dictionary
            representing an SFC component configuration.

    Returns:
        dict: A dictionary containing the validation results
            - valid (bool): Whether the configuration is valid
            - errors (list): List of validation error messages (if any)
            - warnings (list): List of validation warning messages (if any)
            - component_type (str): Detected component type (adapter, target, or unknown)
            - component_name (str): The name of the component from the config

    Example:
        ```
        {
          "server_name": "sfc-docs-server",
          "tool_name": "validate_sfc_config",
          "arguments": {
            "config": {
              "name": "MyAdapter",
              "adapterType": "OPCUA",
              "description": "An example OPC UA adapter",
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
    """
    errors = []
    warnings = []

    # Check if config is a dictionary
    if not isinstance(config, dict):
        errors.append("Configuration must be a JSON object")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "component_type": "unknown",
            "component_name": "unknown",
        }

    # Get component name
    component_name = config.get("name", "unknown")
    if not component_name or component_name == "unknown":
        warnings.append("Configuration is missing a name field")

    # Determine component type and validate required fields
    component_type = "unknown"

    # Check if it's an adapter config
    if "adapterType" in config:
        component_type = "adapter"

        # Validate adapter-specific fields
        if not config.get("sources"):
            errors.append("Adapter configuration must include 'sources' array")
        else:
            if not isinstance(config["sources"], list):
                errors.append("'sources' must be an array")
            else:
                for i, source in enumerate(config["sources"]):
                    if not isinstance(source, dict):
                        errors.append(f"Source at index {i} must be an object")
                        continue

                    if "name" not in source:
                        errors.append(
                            f"Source at index {i} is missing required 'name' field"
                        )

                    # Check for topics
                    if "topics" in source:
                        if not isinstance(source["topics"], list):
                            errors.append(
                                f"'topics' in source '{source.get('name', i)}' must be an array"
                            )
                        else:
                            for j, topic in enumerate(source["topics"]):
                                if not isinstance(topic, dict):
                                    errors.append(
                                        f"Topic at index {j} in source '{source.get('name', i)}' must be an object"
                                    )
                                    continue

                                if "name" not in topic:
                                    errors.append(
                                        f"Topic at index {j} in source '{source.get('name', i)}' is missing required 'name' field"
                                    )

    # Check if it's a target config
    elif "targetType" in config:
        component_type = "target"

        # Validate target-specific fields
        if not config.get("targets"):
            errors.append("Target configuration must include 'targets' array")
        else:
            if not isinstance(config["targets"], list):
                errors.append("'targets' must be an array")
            else:
                for i, target in enumerate(config["targets"]):
                    if not isinstance(target, dict):
                        errors.append(f"Target at index {i} must be an object")
                        continue

                    if "name" not in target:
                        errors.append(
                            f"Target at index {i} is missing required 'name' field"
                        )

    # Check if it's a combined config
    elif "sources" in config and "targets" in config:
        component_type = "core"

        # Perform similar validations as above for sources and targets
        if not isinstance(config["sources"], list):
            errors.append("'sources' must be an array")
        if not isinstance(config["targets"], list):
            errors.append("'targets' must be an array")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "component_type": component_type,
        "component_name": component_name,
    }


def main():
    """Entry point for the MCP server."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
