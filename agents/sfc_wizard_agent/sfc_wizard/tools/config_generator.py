#!/usr/bin/env python3
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

AWS Shopfloor Connectivity (SFC) Configuration Generator
Provides functions for generating SFC configuration templates
"""

import json
from typing import Dict, Any


def generate_config_template(
    protocol: str, target: str, environment: str, sfc_knowledge: Dict[str, Any]
) -> str:
    """Generate a configuration template

    Args:
        protocol: Source protocol (e.g., OPCUA, MODBUS, S7)
        target: Target service (e.g., AWS-S3, AWS-IOT-CORE, DEBUG)
        environment: Environment type (development, production)
        sfc_knowledge: Dictionary containing SFC framework knowledge

    Returns:
        String containing the generated configuration template
    """
    if protocol not in sfc_knowledge["supported_protocols"]:
        return f"❌ Unsupported protocol: {protocol}. Supported: {', '.join(sfc_knowledge['supported_protocols'].keys())}"

    # Create basic template structure
    template = {
        "AWSVersion": sfc_knowledge["aws_version"],
        "Name": f"{protocol} to {target} Configuration",
        "Description": f"{environment.title()} configuration for {protocol} protocol to {target} target",
        "LogLevel": "Info" if environment == "production" else "Trace",
        "Schedules": [
            {
                "Name": f"{protocol}Schedule",
                "Interval": 1000 if environment == "development" else 5000,
                "Active": True,
                "TimestampLevel": "Both",
                "Sources": {f"{protocol}-SOURCE": ["*"]},
                "Targets": [f"{target}Target"],
            }
        ],
        "Sources": generate_source_template(protocol, sfc_knowledge),
        "Targets": generate_target_template(target, environment, sfc_knowledge),
        "TargetTypes": generate_target_types(target, sfc_knowledge),
        "AdapterTypes": generate_adapter_types(protocol, sfc_knowledge),
        "ProtocolAdapters": generate_protocol_adapter_config(protocol, sfc_knowledge),
    }

    return f"✅ Generated {protocol} to {target} template:\n\n```json\n{json.dumps(template, indent=2)}\n```"


def generate_source_template(
    protocol: str, sfc_knowledge: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate source configuration template

    Args:
        protocol: Source protocol (e.g., OPCUA, MODBUS, S7)
        sfc_knowledge: Dictionary containing SFC framework knowledge

    Returns:
        Dictionary containing source configuration
    """
    base_config = {
        f"{protocol}-SOURCE": {
            "Name": f"{protocol}Source",
            "ProtocolAdapter": protocol,
            "Description": f"{protocol} source configuration",
            "Channels": {},
        }
    }

    return base_config


def generate_target_template(
    target: str, environment: str, sfc_knowledge: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate target configuration template

    Args:
        target: Target service (e.g., AWS-S3, AWS-IOT-CORE, DEBUG)
        environment: Environment type (development, production)
        sfc_knowledge: Dictionary containing SFC framework knowledge

    Returns:
        Dictionary containing target configuration
    """
    base_config = {f"{target}Target": {"Active": True, "TargetType": target}}

    return base_config


def generate_target_types(target: str, sfc_knowledge: Dict[str, Any]) -> Dict[str, Any]:
    """Generate target types configuration

    Args:
        target: Target service (e.g., AWS-S3, AWS-IOT-CORE, DEBUG)
        sfc_knowledge: Dictionary containing SFC framework knowledge

    Returns:
        Dictionary containing target type configuration
    """
    target_types = {}

    return target_types


def generate_adapter_types(
    protocol: str, sfc_knowledge: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate adapter types configuration

    Args:
        protocol: Source protocol (e.g., OPCUA, MODBUS, S7)
        sfc_knowledge: Dictionary containing SFC framework knowledge

    Returns:
        Dictionary containing adapter type configuration
    """
    adapter_types = {}

    return adapter_types


def generate_protocol_adapter_config(
    protocol: str, sfc_knowledge: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate protocol adapter configuration

    Args:
        protocol: Source protocol (e.g., OPCUA, MODBUS, S7)
        sfc_knowledge: Dictionary containing SFC framework knowledge

    Returns:
        Dictionary containing protocol adapter configuration
    """
    config = {}

    return config
