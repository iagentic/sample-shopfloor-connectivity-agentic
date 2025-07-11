#!/usr/bin/env python
"""
Test Program for SFC Documentation MCP Server

This script tests all the tools provided by the SFC Documentation MCP Server.
It demonstrates how to connect to the server and use each tool with sample arguments.
"""

import os
import json
import time
import requests
from typing import Dict, Any, Optional


class SFCServerTester:
    """Test client for the SFC Documentation MCP Server"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000/sfc"):
        """
        Initialize the tester with the server URL
        
        Args:
            base_url: Base URL of the MCP server
        """
        self.base_url = base_url
        self.server_name = "sfc-docs-server"
        print(f"🔄 Connecting to SFC Documentation MCP Server at {base_url}")
        
        # Wait for server to be ready
        retries = 5
        while retries > 0:
            try:
                response = requests.get(f"{base_url}/health")
                if response.status_code == 200:
                    print("✅ Server is ready")
                    break
            except requests.RequestException:
                pass
            
            print(f"⏳ Waiting for server to be ready (retries left: {retries})")
            time.sleep(1)
            retries -= 1
            
        if retries == 0:
            print("⚠️  Warning: Could not confirm server is ready. Tests may fail.")
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool with the given arguments
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Dictionary containing the tool's response
        """
        payload = {
            "server_name": self.server_name,
            "tool_name": tool_name,
            "arguments": arguments
        }
        
        try:
            print(f"\n📤 Calling tool '{tool_name}' with arguments: {json.dumps(arguments, indent=2)}")
            response = requests.post(f"{self.base_url}/tool", json=payload)
            response.raise_for_status()
            result = response.json()
            print(f"📥 Tool response: {json.dumps(result, indent=2, default=str)[:500]}...")
            if len(json.dumps(result)) > 500:
                print(f"   (Response truncated, total length: {len(json.dumps(result))} characters)")
            return result
        except requests.RequestException as e:
            print(f"❌ Error calling tool: {e}")
            return {"error": str(e)}
    
    def run_all_tests(self):
        """Run tests for all available tools"""
        print("\n🧪 Running tests for all tools")
        
        # Test update_repo tool
        print("\n==== Testing update_repo ====")
        self.test_update_repo()
        
        # Test document listing tools
        print("\n==== Testing document listing tools ====")
        self.test_list_docs()
        
        # Test document retrieval tools
        print("\n==== Testing document retrieval tools ====")
        self.test_get_docs()
        
        # Test query_docs tool
        print("\n==== Testing query_docs ====")
        self.test_query_docs()
        
        # Test extract_json_examples tool
        print("\n==== Testing extract_json_examples ====")
        self.test_extract_json_examples()
        
        # Test search_doc_content tool
        print("\n==== Testing search_doc_content ====")
        self.test_search_doc_content()
        
        # Test get_sfc_config_examples tool
        print("\n==== Testing get_sfc_config_examples ====")
        self.test_get_sfc_config_examples()
        
        # Test validate_sfc_config tool
        print("\n==== Testing validate_sfc_config ====")
        self.test_validate_sfc_config()
        
        print("\n🏁 All tests completed!")
    
    def test_update_repo(self):
        """Test the update_repo tool"""
        result = self.call_tool("update_repo", {})
        
        if "message" in result:
            print(f"✅ update_repo tool responded with message: {result['message']}")
        else:
            print("❌ update_repo tool did not return expected 'message' field")
    
    def test_list_docs(self):
        """Test all document listing tools"""
        # Test list_core_docs
        core_docs = self.call_tool("list_core_docs", {})
        if "documents" in core_docs:
            print(f"✅ list_core_docs found {len(core_docs['documents'])} documents")
            # Save first doc name for later tests
            if core_docs['documents']:
                self.core_doc_name = core_docs['documents'][0]['name']
                print(f"   Using '{self.core_doc_name}' for later tests")
        
        # Test list_adapter_docs
        adapter_docs = self.call_tool("list_adapter_docs", {})
        if "documents" in adapter_docs:
            print(f"✅ list_adapter_docs found {len(adapter_docs['documents'])} documents")
            # Save first doc name for later tests
            if adapter_docs['documents']:
                self.adapter_doc_name = adapter_docs['documents'][0]['name']
                print(f"   Using '{self.adapter_doc_name}' for later tests")
        
        # Test list_target_docs
        target_docs = self.call_tool("list_target_docs", {})
        if "documents" in target_docs:
            print(f"✅ list_target_docs found {len(target_docs['documents'])} documents")
            # Save first doc name for later tests
            if target_docs['documents']:
                self.target_doc_name = target_docs['documents'][0]['name']
                print(f"   Using '{self.target_doc_name}' for later tests")
    
    def test_get_docs(self):
        """Test all document retrieval tools"""
        # Test get_core_doc
        if hasattr(self, 'core_doc_name'):
            core_doc = self.call_tool("get_core_doc", {"doc_name": self.core_doc_name})
            if "content" in core_doc:
                print(f"✅ get_core_doc retrieved document '{self.core_doc_name}'")
        else:
            print("⏭️  Skipping get_core_doc test (no core documents found)")
        
        # Test get_adapter_doc
        if hasattr(self, 'adapter_doc_name'):
            adapter_doc = self.call_tool("get_adapter_doc", {"doc_name": self.adapter_doc_name})
            if "content" in adapter_doc:
                print(f"✅ get_adapter_doc retrieved document '{self.adapter_doc_name}'")
        else:
            print("⏭️  Skipping get_adapter_doc test (no adapter documents found)")
        
        # Test get_target_doc
        if hasattr(self, 'target_doc_name'):
            target_doc = self.call_tool("get_target_doc", {"doc_name": self.target_doc_name})
            if "content" in target_doc:
                print(f"✅ get_target_doc retrieved document '{self.target_doc_name}'")
        else:
            print("⏭️  Skipping get_target_doc test (no target documents found)")
        
        # Test non-existent document
        non_existent = self.call_tool("get_core_doc", {"doc_name": "non_existent_doc_12345"})
        if "error" in non_existent:
            print("✅ get_core_doc correctly handles non-existent documents")
    
    def test_query_docs(self):
        """Test the query_docs tool with different parameters"""
        # Test with all doc types
        all_docs = self.call_tool("query_docs", {
            "doc_type": "all",
            "include_content": False
        })
        if "results" in all_docs:
            print(f"✅ query_docs found {all_docs['count']} documents across all types")
        
        # Test with a specific doc type
        core_docs = self.call_tool("query_docs", {
            "doc_type": "core",
            "include_content": False
        })
        if "results" in core_docs:
            print(f"✅ query_docs found {core_docs['count']} core documents")
        
        # Test with a search term
        if hasattr(self, 'core_doc_name'):
            search_term = self.core_doc_name[:4]  # Use first few chars as search term
            search_docs = self.call_tool("query_docs", {
                "doc_type": "all",
                "search_term": search_term,
                "include_content": False
            })
            if "results" in search_docs:
                print(f"✅ query_docs found {search_docs['count']} documents containing '{search_term}'")
        
        # Test with invalid doc type
        invalid_type = self.call_tool("query_docs", {
            "doc_type": "invalid_type",
            "include_content": False
        })
        if "error" in invalid_type:
            print("✅ query_docs correctly handles invalid doc_type")
    
    def test_extract_json_examples(self):
        """Test the extract_json_examples tool"""
        # Test with a core document
        if hasattr(self, 'core_doc_name'):
            examples = self.call_tool("extract_json_examples", {
                "doc_type": "core",
                "doc_name": self.core_doc_name
            })
            if "results" in examples:
                print(f"✅ extract_json_examples found examples in documents matching '{self.core_doc_name}'")
                print(f"   Matching documents: {examples.get('matching_documents', [])}")
                print(f"   Total examples: {examples.get('total_examples', 0)}")
        else:
            print("⏭️  Skipping extract_json_examples exact match test (no core documents found)")
        
        # Test with wildcard pattern - using prefix match
        # Use first 3 characters of any known document name + wildcard
        if hasattr(self, 'adapter_doc_name') and len(self.adapter_doc_name) >= 3:
            prefix = self.adapter_doc_name[:3]
            examples = self.call_tool("extract_json_examples", {
                "doc_type": "adapter",
                "doc_name": f"{prefix}*"
            })
            if "results" in examples:
                print(f"✅ extract_json_examples found examples using wildcard pattern '{prefix}*'")
                print(f"   Matching documents: {examples.get('matching_documents', [])}")
                print(f"   Total examples: {examples.get('total_examples', 0)}")
        else:
            print("⏭️  Skipping extract_json_examples wildcard test (no suitable adapter document name)")
        
        # Test with wildcard pattern - using contains match
        examples = self.call_tool("extract_json_examples", {
            "doc_type": "target",
            "doc_name": "*a*"  # Any document with 'a' in the name
        })
        if "results" in examples:
            print(f"✅ extract_json_examples found examples using contains wildcard '*a*'")
            print(f"   Matching documents: {len(examples.get('matching_documents', []))}")
            print(f"   Total examples: {examples.get('total_examples', 0)}")
        
        # Test with invalid doc type
        invalid = self.call_tool("extract_json_examples", {
            "doc_type": "invalid",
            "doc_name": "some_doc"
        })
        if "error" in invalid:
            print("✅ extract_json_examples correctly handles invalid doc_type")
        
        # Test with non-existent document pattern
        non_existent = self.call_tool("extract_json_examples", {
            "doc_type": "core",
            "doc_name": "non_existent_doc_pattern_xyz123"
        })
        if "error" in non_existent and "available_documents" in non_existent:
            print("✅ extract_json_examples correctly handles non-existent document patterns")
            print(f"   Available documents: {len(non_existent.get('available_documents', []))}")
    
    def test_search_doc_content(self):
        """Test the search_doc_content tool"""
        # Search for a common term across all docs
        results = self.call_tool("search_doc_content", {
            "search_text": "configuration",
            "doc_type": "all",
            "case_sensitive": False
        })
        
        if "total_matches" in results:
            print(f"✅ search_doc_content found {results['total_matches']} matches for 'configuration' in {results['documents_count']} documents")
        
        # Search with case sensitivity
        sensitive = self.call_tool("search_doc_content", {
            "search_text": "Configuration",  # Capital C
            "doc_type": "all",
            "case_sensitive": True
        })
        
        if "total_matches" in sensitive:
            print(f"✅ search_doc_content found {sensitive['total_matches']} case-sensitive matches for 'Configuration'")
        
        # Search in a specific doc type
        core_search = self.call_tool("search_doc_content", {
            "search_text": "adapter",
            "doc_type": "core",
            "case_sensitive": False
        })
        
        if "total_matches" in core_search:
            print(f"✅ search_doc_content found {core_search['total_matches']} matches for 'adapter' in core docs")
    
    def test_get_sfc_config_examples(self):
        """Test the get_sfc_config_examples tool"""
        # Get all config examples
        all_examples = self.call_tool("get_sfc_config_examples", {})
        
        if "examples" in all_examples:
            print(f"✅ get_sfc_config_examples found {all_examples['count']} configuration examples")
        
        # Get adapter config examples
        adapter_examples = self.call_tool("get_sfc_config_examples", {
            "component_type": "adapter"
        })
        
        if "examples" in adapter_examples:
            print(f"✅ get_sfc_config_examples found {adapter_examples['count']} adapter configuration examples")
            
            # If examples were found, test name pattern filtering
            if adapter_examples['count'] > 0:
                # Get example with name pattern - use first component's name pattern
                first_component = adapter_examples['examples'][0]['component_name']
                if len(first_component) > 3:
                    name_pattern = f"*{first_component[1:4]}*"  # Use some chars from middle
                    filtered_examples = self.call_tool("get_sfc_config_examples", {
                        "component_type": "adapter",
                        "name_pattern": name_pattern
                    })
                    if "examples" in filtered_examples:
                        print(f"✅ get_sfc_config_examples filtered by name pattern '{name_pattern}' found {filtered_examples['count']} examples")
        
        # Test with wildcard name pattern
        wildcard_examples = self.call_tool("get_sfc_config_examples", {
            "name_pattern": "*"  # Match all names
        })
        
        if "examples" in wildcard_examples:
            print(f"✅ get_sfc_config_examples with wildcard pattern '*' found {wildcard_examples['count']} examples")
        
        # Test with specific pattern that likely matches something
        specific_examples = self.call_tool("get_sfc_config_examples", {
            "name_pattern": "*A*"  # Names containing 'A'
        })
        
        if "examples" in specific_examples:
            print(f"✅ get_sfc_config_examples with pattern '*A*' found {specific_examples['count']} examples")
        
        # Test with invalid component type
        invalid = self.call_tool("get_sfc_config_examples", {
            "component_type": "invalid"
        })
        
        if "error" in invalid:
            print("✅ get_sfc_config_examples correctly handles invalid component_type")
    
    def test_validate_sfc_config(self):
        """Test the validate_sfc_config tool"""
        # Valid adapter config
        valid_adapter = self.call_tool("validate_sfc_config", {
            "config": {
                "name": "TestAdapter",
                "adapterType": "OPCUA",
                "sources": [
                    {
                        "name": "Source1",
                        "topics": [
                            {"name": "Topic1", "sourcePath": "ns=2;i=1"}
                        ]
                    }
                ]
            }
        })
        
        if "valid" in valid_adapter and valid_adapter["valid"]:
            print("✅ validate_sfc_config correctly validates a valid adapter config")
        
        # Invalid adapter config (missing sources)
        invalid_adapter = self.call_tool("validate_sfc_config", {
            "config": {
                "name": "TestAdapter",
                "adapterType": "OPCUA"
                # Missing sources array
            }
        })
        
        if "valid" in invalid_adapter and not invalid_adapter["valid"]:
            print("✅ validate_sfc_config correctly identifies an invalid adapter config")
            print(f"   Errors: {invalid_adapter.get('errors', [])}")
        
        # Valid target config
        valid_target = self.call_tool("validate_sfc_config", {
            "config": {
                "name": "TestTarget",
                "targetType": "S3",
                "targets": [
                    {
                        "name": "Target1",
                        "bucketName": "test-bucket"
                    }
                ]
            }
        })
        
        if "valid" in valid_target and valid_target["valid"]:
            print("✅ validate_sfc_config correctly validates a valid target config")
        
        # Test with non-dict input
        non_dict = self.call_tool("validate_sfc_config", {
            "config": "not a dict"
        })
        
        if "valid" in non_dict and not non_dict["valid"]:
            print("✅ validate_sfc_config correctly handles non-dict input")


if __name__ == "__main__":
    # Start the server in a separate process if needed
    # This assumes the server is already running or will be started manually
    
    # Create and run the tester
    tester = SFCServerTester()
    tester.run_all_tests()
