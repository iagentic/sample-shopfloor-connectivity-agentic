#!/usr/bin/env python3
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

AWS Shopfloor Connectivity (SFC) Data Visualization Module
Provides visualization capabilities for SFC data stored in file targets.
"""

import os
import json
import datetime
from typing import Optional, Tuple, List, Dict, Any

from sfc_wizard.tools.data_visualizer import visualize_time_series


def visualize_file_target_data(
    config_name: Optional[str], minutes: int = 10, jmespath_expr: str = "value", ui_mode: bool = False,
    seconds: int = None
) -> str:
    """
    Visualize data from an active SFC configuration with FILE-TARGET

    Args:
        config_name: Name of the currently running configuration (None if no active config)
        minutes: Number of minutes of data to visualize (default: 10)
        jmespath_expr: JMESPath expression to extract values (default: "value")
        ui_mode: If True, returns a markdown representation instead of using ncurses
        seconds: Optional seconds parameter for finer time control in UI mode (overrides minutes when provided)

    Returns:
        Result message or markdown graph
    """
    if config_name is None:
        return "❌ No active SFC configuration is running"

    # Build the path to the configuration directory
    base_dir = os.getcwd()
    run_dir = os.path.join(base_dir, "runs", config_name)

    if not os.path.exists(run_dir):
        return f"❌ Configuration directory {run_dir} not found"

    # Find and load the configuration file
    config_file = os.path.join(run_dir, "config.json")
    if not os.path.exists(config_file):
        return f"❌ Configuration file {config_file} not found"

    try:
        with open(config_file, "r") as f:
            config = json.load(f)
    except Exception as e:
        return f"❌ Failed to read configuration file: {str(e)}"

    # Check if this config has a FILE-TARGET
    file_target = None
    file_target_config = None

    if "Targets" in config:
        for target_name, target_config in config["Targets"].items():
            if (
                "TargetType" in target_config
                and target_config["TargetType"] == "FILE-TARGET"
                and target_config.get("Active", False)
            ):
                file_target = target_name
                file_target_config = target_config
                break

    if file_target is None:
        return "❌ No active FILE-TARGET found in the configuration"

    # Get the directory where data files are stored
    data_dir = file_target_config.get("Directory", "./data")

    # If the path is relative, make it absolute relative to the run directory
    if not os.path.isabs(data_dir):
        data_dir = os.path.normpath(os.path.join(run_dir, data_dir))

    if not os.path.exists(data_dir):
        return f"❌ Data directory {data_dir} not found"

    # Filter for files from the last n minutes
    cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=minutes)

    # Determine the timeframe in seconds
    timeframe_seconds = None
    if seconds is not None:
        timeframe_seconds = seconds
        timeframe_description = f"last {seconds} seconds"
    elif minutes is not None:
        timeframe_seconds = minutes * 60
        timeframe_description = f"last {minutes} minutes"
    
    # Call the data visualizer with UI mode parameter
    result = visualize_time_series(data_dir, jmespath_expr, timeframe_seconds, ui_mode)

    # For UI mode, enhance the result with smaller timeframe options if appropriate
    if ui_mode and "❌" not in result:  # Only add options if visualization succeeded
        small_timeframe_options = [5, 10, 15, 20, 30, 50]  # seconds
        current_timeframe = seconds if seconds is not None else minutes * 60
        
        # Add timeframe options at the end of the result
        timeframe_links = "\n\n### Timeframe Options\n"
        for time_opt in small_timeframe_options:
            if time_opt == current_timeframe:
                timeframe_links += f"**{time_opt}s** | "
            else:
                timeframe_links += f"{time_opt}s | "
        
        # Add minute options
        minute_options = [1, 2, 5, 10]
        for min_opt in minute_options:
            min_seconds = min_opt * 60
            if min_seconds == current_timeframe:
                timeframe_links += f"**{min_opt}m** | "
            else:
                timeframe_links += f"{min_opt}m | "
                
        # Remove trailing separator and add note
        timeframe_links = timeframe_links.rstrip(" | ")
        timeframe_links += "\n\n*To change timeframe, request visualization with specific seconds or minutes.*"
        
        result += timeframe_links

    return result
