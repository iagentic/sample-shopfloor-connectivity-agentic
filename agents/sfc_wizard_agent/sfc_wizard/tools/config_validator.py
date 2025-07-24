#!/usr/bin/env python3
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

SFC Configuration Validator
Provides validation functionality for SFC configurations
"""

from typing import Dict, Any, List


class SFCConfigValidator:
    """
    SFC Configuration Validator class

    Provides methods to validate SFC configurations against required schemas and best practices. 
    - Make sure to also check against the settings from the create_sfc_config_template tool
    """

    def __init__(self, sfc_knowledge: Dict[str, Any]):
        """Initialize the validator with SFC knowledge base

        Args:
            sfc_knowledge: Dictionary containing SFC framework knowledge
        """
        self.sfc_knowledge = sfc_knowledge
        self.validation_errors = []
        self.recommendations = []

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate the entire configuration

        Args:
            config: SFC configuration dictionary

        Returns:
            True if valid, False if validation errors were found
        """
        # Clear previous validation state
        self.validation_errors = []
        self.recommendations = []

        # Run all validations
        self.validate_basic_structure(config)
        self.validate_schedules(config.get("Schedules", []))
        self.validate_sources(config.get("Sources", {}))
        self.validate_targets(config.get("Targets", {}))
        self.validate_adapters(config)

        # Return validation result
        return len(self.validation_errors) == 0

    def get_errors(self) -> List[str]:
        """Get validation errors

        Returns:
            List of validation error messages
        """
        return self.validation_errors

    def get_recommendations(self) -> List[str]:
        """Get recommendations for improving the configuration

        Returns:
            List of recommendation messages
        """
        return self.recommendations

    def validate_basic_structure(self, config: Dict[str, Any]) -> None:
        """Validate basic configuration structure

        Args:
            config: SFC configuration dictionary
        """
        # Check required sections
        for section in self.sfc_knowledge["required_config_sections"]:
            if section not in config:
                self.validation_errors.append(f"Missing required section: {section}")

        # Check AWS version
        if config.get("AWSVersion") != self.sfc_knowledge["aws_version"]:
            self.validation_errors.append(
                f"AWSVersion should be '{self.sfc_knowledge['aws_version']}'"
            )

    def validate_schedules(self, schedules: List[Dict[str, Any]]) -> None:
        """Validate schedules configuration

        Args:
            schedules: List of schedule configurations
        """
        if not schedules:
            self.validation_errors.append("At least one schedule must be defined")
            return

        for idx, schedule in enumerate(schedules):
            if "Name" not in schedule:
                self.validation_errors.append(f"Schedule {idx} missing 'Name'")
            if "Sources" not in schedule:
                self.validation_errors.append(
                    f"Schedule '{schedule.get('Name', idx)}' missing 'Sources'"
                )
            if "Targets" not in schedule:
                self.validation_errors.append(
                    f"Schedule '{schedule.get('Name', idx)}' missing 'Targets'"
                )

    def validate_sources(self, sources: Dict[str, Any]) -> None:
        """Validate sources configuration

        Args:
            sources: Dictionary of source configurations
        """
        if not sources:
            self.validation_errors.append("At least one source must be defined")
            return

        for source_name, source_config in sources.items():
            if "ProtocolAdapter" not in source_config:
                self.validation_errors.append(
                    f"Source '{source_name}' missing 'ProtocolAdapter'"
                )
            else:
                # Strict validation: Check if protocol is supported
                protocol = source_config["ProtocolAdapter"]
                if protocol not in self.sfc_knowledge["supported_protocols"]:
                    self.validation_errors.append(
                        f"Source '{source_name}' uses unsupported protocol adapter: '{protocol}'. "
                        f"Supported protocols: {', '.join(sorted(self.sfc_knowledge['supported_protocols'].keys()))}"
                    )

            if "Channels" not in source_config:
                self.validation_errors.append(
                    f"Source '{source_name}' missing 'Channels'"
                )

    def validate_targets(self, targets: Dict[str, Any]) -> None:
        """Validate targets configuration

        Args:
            targets: Dictionary of target configurations
        """
        if not targets:
            self.validation_errors.append("At least one target must be defined")
            return

        for target_name, target_config in targets.items():
            if "TargetType" not in target_config:
                self.validation_errors.append(
                    f"Target '{target_name}' missing 'TargetType'"
                )
            else:
                # Strict validation: Check if target type is supported
                target_type = target_config["TargetType"]

                # Check in AWS targets
                aws_targets = self.sfc_knowledge["aws_targets"].keys()
                edge_targets = [
                    target["description"]
                    for target in self.sfc_knowledge["edge_targets"].values()
                ]

                # Special case handling for edge targets that have -TARGET suffix
                if target_type.endswith("-TARGET"):
                    base_type = target_type[:-7]  # Remove -TARGET suffix
                    if base_type in self.sfc_knowledge["edge_targets"]:
                        continue

                # Check if target is in either AWS targets or edge targets
                if target_type not in aws_targets and target_type not in edge_targets:
                    self.validation_errors.append(
                        f"Target '{target_name}' uses unsupported target type: '{target_type}'. "
                        f"Supported AWS targets: {', '.join(sorted(aws_targets))}. "
                        f"Supported edge targets: {', '.join(sorted(self.sfc_knowledge['edge_targets'].keys()))}"
                    )

    def validate_adapters(self, config: Dict[str, Any]) -> None:
        """Validate adapter configurations

        Args:
            config: SFC configuration dictionary
        """
        # Check if adapter types or servers are defined
        has_adapter_types = bool(config.get("AdapterTypes"))
        has_adapter_servers = bool(config.get("AdapterServers"))

        if not has_adapter_types and not has_adapter_servers:
            self.validation_errors.append(
                "Either 'AdapterTypes' or 'AdapterServers' must be defined"
            )

        # Similar check for targets
        has_target_types = bool(config.get("TargetTypes"))
        has_target_servers = bool(config.get("TargetServers"))

        if not has_target_types and not has_target_servers:
            self.validation_errors.append(
                "Either 'TargetTypes' or 'TargetServers' must be defined"
            )
