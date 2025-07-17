#!/usr/bin/env python3
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

SFC Configuration Diagnostics
Provides functions for diagnosing issues and suggesting optimizations for SFC configurations
"""

import json
from typing import Dict, Any, List


def diagnose_issue(issue_description: str, config_json: str, sfc_knowledge: Dict[str, Any]) -> str:
    """Diagnose SFC issues based on issue description and configuration
    
    Args:
        issue_description: Description of the issue
        config_json: JSON string containing the SFC configuration
        sfc_knowledge: Dictionary containing SFC framework knowledge
        
    Returns:
        String containing the diagnosis results
    """
    issue_lower = issue_description.lower()
    diagnosis = ["🔍 SFC Issue Diagnosis\n"]

    # Connection issues
    if any(
        keyword in issue_lower
        for keyword in ["connect", "connection", "timeout", "unreachable"]
    ):
        diagnosis.extend(
            [
                "🔌 **Connection Issues Detected**",
                "• Check network connectivity between SFC and target devices",
                "• Verify firewall rules allow required ports",
                "• Confirm device IP addresses and ports in configuration",
                "• Test connectivity using ping or telnet",
                "• Check if devices are powered on and operational",
                "",
            ]
        )

    # Authentication issues
    if any(
        keyword in issue_lower
        for keyword in ["auth", "credential", "permission", "unauthorized"]
    ):
        diagnosis.extend(
            [
                "🔐 **Authentication Issues Detected**",
                "• Verify AWS credentials are correctly configured",
                "• Check IAM roles and policies for required permissions",
                "• Confirm certificate paths and validity (for IoT/TLS)",
                "• Validate username/password for protocol adapters",
                "• Review AWS Secrets Manager configuration if used",
                "",
            ]
        )

    # Configuration issues
    if any(
        keyword in issue_lower
        for keyword in ["config", "invalid", "missing", "error"]
    ):
        diagnosis.extend(
            [
                "⚙️ **Configuration Issues Detected**",
                "• Validate JSON syntax using a JSON validator",
                "• Check all required sections are present",
                "• Verify protocol adapter and target type configurations",
                "• Confirm schedule references match source/target names",
                "• Review data type compatibility between sources and targets",
                "",
            ]
        )

    # Performance issues
    if any(
        keyword in issue_lower
        for keyword in ["slow", "performance", "memory", "cpu", "lag"]
    ):
        diagnosis.extend(
            [
                "⚡ **Performance Issues Detected**",
                "• Review data collection intervals and batch sizes",
                "• Check memory usage and increase JVM heap if needed",
                "• Monitor network bandwidth utilization",
                "• Consider using data filtering to reduce volume",
                "• Implement data aggregation for high-frequency sources",
                "",
            ]
        )

    # Data quality issues
    if any(
        keyword in issue_lower
        for keyword in ["data", "missing", "incorrect", "timestamp"]
    ):
        diagnosis.extend(
            [
                "📊 **Data Quality Issues Detected**",
                "• Verify channel configurations match device data points",
                "• Check data type mappings and transformations",
                "• Review timestamp configuration and time zones",
                "• Validate data filtering and change detection settings",
                "• Monitor source device status and availability",
                "",
            ]
        )

    # If we have a configuration, provide specific analysis
    if config_json:
        try:
            config = json.loads(config_json)
            diagnosis.extend(
                [
                    "📋 **Configuration Analysis:**",
                    f"• Schedules defined: {len(config.get('Schedules', []))}",
                    f"• Sources configured: {len(config.get('Sources', {}))}",
                    f"• Targets configured: {len(config.get('Targets', {}))}",
                    f"• Log level: {config.get('LogLevel', 'Not set')}",
                    "",
                ]
            )
        except:
            diagnosis.append("⚠️ Could not parse provided configuration")

    if len(diagnosis) == 1:  # Only header added
        diagnosis.extend(
            [
                "❓ **General Troubleshooting Steps:**",
                "• Check SFC logs for specific error messages",
                "• Verify all required JAR files are present",
                "• Confirm Java version compatibility (JVM 1.8+)",
                "• Test with a minimal configuration first",
                "• Enable trace logging for detailed diagnostics",
            ]
        )

    return "\n".join(diagnosis)


def suggest_optimizations(
    config_json: str, performance_requirements: str, sfc_knowledge: Dict[str, Any]
) -> str:
    """Suggest optimizations for an SFC configuration
    
    Args:
        config_json: JSON string containing the SFC configuration
        performance_requirements: Description of performance requirements
        sfc_knowledge: Dictionary containing SFC framework knowledge
        
    Returns:
        String containing optimization suggestions
    """
    try:
        config = json.loads(config_json)
    except:
        return "❌ Invalid JSON configuration provided"

    suggestions = ["🚀 SFC Optimization Suggestions\n"]

    # Analyze schedules
    schedules = config.get("Schedules", [])
    for schedule in schedules:
        interval = schedule.get("Interval", 1000)
        if interval < 100:
            suggestions.append(
                f"⚠️ Schedule '{schedule.get('Name')}' has very fast interval ({interval}ms). Consider increasing for better performance."
            )

    # Analyze targets
    targets = config.get("Targets", {})
    for target_name, target_config in targets.items():
        target_type = target_config.get("TargetType", "")

        # S3 optimizations
        if target_type == "AWS-S3":
            buffer_size = target_config.get("BufferSize", 1)
            if buffer_size < 10:
                suggestions.append(
                    f"💡 Target '{target_name}': Increase BufferSize to 10+ for better S3 performance"
                )

            if "Compression" not in target_config:
                suggestions.append(
                    f"💡 Target '{target_name}': Enable compression (Gzip/Zip) to reduce S3 storage costs"
                )

        # Streaming targets
        elif target_type in ["AWS-KINESIS", "AWS-IOT-CORE"]:
            if "BufferSize" not in target_config:
                suggestions.append(
                    f"💡 Target '{target_name}': Add buffering for better throughput"
                )

    # General optimizations based on requirements
    if "high throughput" in performance_requirements.lower():
        suggestions.extend(
            [
                "",
                "🏎️ **High Throughput Optimizations:**",
                "• Use parallel processing with multiple adapter instances",
                "• Implement data aggregation to reduce message volume",
                "• Consider using streaming targets (Kinesis) over batch targets",
                "• Increase JVM heap size and tune garbage collection",
            ]
        )

    if "low latency" in performance_requirements.lower():
        suggestions.extend(
            [
                "",
                "⚡ **Low Latency Optimizations:**",
                "• Use subscription mode for OPC-UA instead of polling",
                "• Minimize data transformations and filtering",
                "• Use direct streaming targets (IoT Core, Kinesis)",
                "• Deploy protocol adapters close to data sources",
            ]
        )

    if "cost optimization" in performance_requirements.lower():
        suggestions.extend(
            [
                "",
                "💰 **Cost Optimization:**",
                "• Enable data compression for S3 targets",
                "• Use data filtering to reduce unnecessary data transmission",
                "• Implement change-based data collection",
                "• Consider data aggregation to reduce API calls",
            ]
        )

    return (
        "\n".join(suggestions)
        if len(suggestions) > 1
        else "✅ Configuration appears well-optimized"
    )
