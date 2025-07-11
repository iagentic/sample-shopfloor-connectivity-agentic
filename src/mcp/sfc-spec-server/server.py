#!/usr/bin/env python
"""
SFC Documentation MCP Server

This server provides tools and resources to interact with the Shopfloor Connectivity (SFC) 
GitHub repository documentation.
"""

import os
import subprocess
from pathlib import Path
from fastmcp import FastMCP
from typing import Dict, Any, List

# Define the repository path
REPO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfc-repo")

# Create the MCP server
server = FastMCP(
    name="sfc-docs-server",
    instructions="Provides access to SFC documentation and repository management"
)


@server.tool("update_repo")
def update_repo() -> Dict[str, Any]:
    """Updates the SFC repository by pulling the latest changes"""
    try:
        result = subprocess.run(
            ["git", "pull"], 
            cwd=REPO_PATH, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return {
            "message": "Repository updated successfully",
            "details": result.stdout
        }
    except subprocess.CalledProcessError as e:
        return {
            "message": "Failed to update repository",
            "error": e.stderr
        }


@server.resource("resource://core_docs/{doc_name}")
def get_core_doc(doc_name: str) -> Dict[str, Any]:
    """Fetches a specific document from the core docs directory"""
    doc_path = os.path.join(REPO_PATH, "docs", "core", f"{doc_name}.md")
    return _get_markdown_content(doc_path, doc_name)


@server.resource("resource://core_docs")
def list_core_docs() -> Dict[str, Any]:
    """Lists all documents in the core docs directory"""
    return _list_docs_in_directory(os.path.join(REPO_PATH, "docs", "core"))


@server.resource("resource://adapter_docs/{doc_name}")
def get_adapter_doc(doc_name: str) -> Dict[str, Any]:
    """Fetches a specific document from the adapters docs directory"""
    doc_path = os.path.join(REPO_PATH, "docs", "adapters", f"{doc_name}.md")
    return _get_markdown_content(doc_path, doc_name)


@server.resource("resource://adapter_docs")
def list_adapter_docs() -> Dict[str, Any]:
    """Lists all documents in the adapters docs directory"""
    return _list_docs_in_directory(os.path.join(REPO_PATH, "docs", "adapters"))


@server.resource("resource://target_docs/{doc_name}")
def get_target_doc(doc_name: str) -> Dict[str, Any]:
    """Fetches a specific document from the targets docs directory"""
    doc_path = os.path.join(REPO_PATH, "docs", "targets", f"{doc_name}.md")
    return _get_markdown_content(doc_path, doc_name)


@server.resource("resource://target_docs")
def list_target_docs() -> Dict[str, Any]:
    """Lists all documents in the targets docs directory"""
    return _list_docs_in_directory(os.path.join(REPO_PATH, "docs", "targets"))


def _get_markdown_content(file_path: str, doc_name: str) -> Dict[str, Any]:
    """Helper function to get markdown content from a file"""
    try:
        if not os.path.exists(file_path):
            return {
                "error": f"Document '{doc_name}' not found",
                "status": 404
            }
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return {
            "name": doc_name,
            "content": content,
            "type": "markdown"
        }
    except Exception as e:
        return {
            "error": f"Failed to read document: {str(e)}",
            "status": 500
        }


def _list_docs_in_directory(dir_path: str) -> Dict[str, Any]:
    """Helper function to list markdown documents in a directory"""
    try:
        if not os.path.exists(dir_path):
            return {
                "error": f"Directory not found: {dir_path}",
                "status": 404
            }
        
        md_files = []
        for file in os.listdir(dir_path):
            if file.endswith('.md'):
                name = file[:-3]  # Remove .md extension
                md_files.append({
                    "name": name,
                    "path": f"{os.path.basename(dir_path)}/{name}"
                })
        
        return {
            "documents": md_files
        }
    except Exception as e:
        return {
            "error": f"Failed to list documents: {str(e)}",
            "status": 500
        }


if __name__ == "__main__":
    server.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/sfc",
        log_level="debug"
    )
