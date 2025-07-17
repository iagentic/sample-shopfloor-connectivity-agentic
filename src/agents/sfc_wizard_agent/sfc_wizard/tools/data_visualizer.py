#!/usr/bin/env python3
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

Data Visualizer for AWS Shopfloor Connectivity (SFC)
Provides ncurses-based visualization for time-series data from SFC.
"""

import os
import json
import glob
import curses
import time
import datetime
import jmespath
from typing import List, Dict, Any, Optional, Tuple


class DataVisualizer:
    """
    Ncurses-based data visualizer for time series data from SFC
    """

    def __init__(self):
        self.data_points = []
        self.timestamps = []
        self.min_value = 0
        self.max_value = 0
        self.title = ""

    def _load_data_files(self, data_dir: str) -> List[Dict]:
        """Load data from all JSON files in the directory recursively"""
        all_data = []

        # Get a list of all JSON files in the directory and its subdirectories and sort them by name
        json_files = sorted(
            glob.glob(os.path.join(data_dir, "**", "*.json"), recursive=True)
        )

        for file_path in json_files:
            try:
                with open(file_path, "r") as f:
                    file_data = json.load(f)
                    if isinstance(file_data, list):
                        all_data.extend(file_data)
                    else:
                        all_data.append(file_data)
            except Exception as e:
                print(f"Error loading {file_path}: {str(e)}")

        return all_data

    def _calculate_spline_points(self, x0, y0, x1, y1, x2, y2, x3, y3, num_points=5):
        """Calculate points along a cubic spline for smooth curves"""
        points = []

        # Generate intermediate points using a cubic Catmull-Rom spline
        # This is a simplified version suitable for terminal graphics
        for t in range(num_points + 1):
            t = t / num_points

            # Catmull-Rom basis functions
            h00 = 2 * t**3 - 3 * t**2 + 1
            h10 = t**3 - 2 * t**2 + t
            h01 = -2 * t**3 + 3 * t**2
            h11 = t**3 - t**2

            # Only use the middle segment
            px = h00 * x1 + h10 * (x2 - x0) + h01 * x2 + h11 * (x3 - x1)
            py = h00 * y1 + h10 * (y2 - y0) + h01 * y2 + h11 * (y3 - y1)

            points.append((int(px), int(py)))

        return points

    def _extract_values(
        self, data: List[Dict], jmespath_expr: str
    ) -> Tuple[List[float], List[str]]:
        """Extract values and timestamps using the provided JMESPath expression"""
        values = []
        timestamps = []

        for item in data:
            try:
                # Extract the value using JMESPath
                value = jmespath.search(jmespath_expr, item)
                if value is not None and isinstance(value, (int, float)):
                    values.append(float(value))

                    # Extract timestamp from the item
                    timestamp = item.get("timestamp", "")
                    timestamps.append(timestamp)
            except Exception as e:
                print(f"Error extracting data: {str(e)}")

        return values, timestamps

    def _prepare_data(self, data_dir: str, jmespath_expr: str) -> bool:
        """Load and prepare data for visualization"""
        # Load all data files
        all_data = self._load_data_files(data_dir)
        if not all_data:
            return False

        # Extract values and timestamps
        values, timestamps = self._extract_values(all_data, jmespath_expr)
        if not values or len(values) != len(timestamps):
            return False

        # Store the data
        self.data_points = values
        self.timestamps = timestamps

        # Calculate min and max values for scaling
        self.min_value = min(values)
        self.max_value = max(values)

        # Set title - include the jmespath expression
        self.title = f"Data Visualization: {jmespath_expr}"

        # Store the latest value for display
        self.latest_value = values[-1] if values else None

        return True

    def _draw_axes(self, win, height: int, width: int):
        """Draw the X and Y axes"""
        # Draw X axis
        win.addch(height - 3, 2, curses.ACS_LTEE)
        win.hline(height - 3, 3, curses.ACS_HLINE, width - 6)
        win.addch(height - 3, width - 3, curses.ACS_RTEE)

        # Draw Y axis
        win.addch(2, 2, curses.ACS_TTEE)
        win.vline(3, 2, curses.ACS_VLINE, height - 6)
        win.addch(height - 3, 2, curses.ACS_LTEE)

        # Add labels
        win.addstr(height - 2, width // 2 - 4, "Time →")
        win.addstr(height // 2, 0, "Value", curses.A_VERTICAL)

        # Add min and max values on Y axis
        if self.max_value != self.min_value:
            win.addstr(2, 4, f"{self.max_value:.1f}")
            win.addstr(height - 4, 4, f"{self.min_value:.1f}")

        # Add timestamp information to X axis if we have timestamps
        if self.timestamps and len(self.timestamps) > 1:
            # Display timestamp at start, middle and end points
            display_points = [0, len(self.timestamps) // 2, len(self.timestamps) - 1]
            x_scale = (width - 6) / max(1, len(self.data_points) - 1)

            for i in display_points:
                if i < len(self.timestamps):
                    # Format timestamp if it exists
                    timestamp = self.timestamps[i]
                    if timestamp:
                        # Try to parse the timestamp and format it nicely
                        try:
                            # If timestamp is in ISO format, parse and format it
                            dt = datetime.datetime.fromisoformat(
                                timestamp.replace("Z", "+00:00")
                            )
                            formatted_time = dt.strftime("%H:%M:%S")
                        except (ValueError, TypeError):
                            # If parsing fails, use the original timestamp (truncated if needed)
                            formatted_time = str(timestamp)
                            if len(formatted_time) > 10:
                                formatted_time = formatted_time[:10] + "..."

                        # Calculate position and display timestamp
                        x_pos = int(3 + i * x_scale)
                        # Center the text at the x position
                        x_pos = max(
                            3,
                            min(
                                width - len(formatted_time) - 3,
                                x_pos - len(formatted_time) // 2,
                            ),
                        )
                        try:
                            win.addstr(height - 2, x_pos, formatted_time)
                        except:
                            # If we can't write at this position (e.g., near the edge), skip it
                            pass

    def _draw_graph(self, win, height: int, width: int):
        """Draw the graph with the data points"""
        if not self.data_points:
            return

        # Calculate scaling factors to use full width
        x_scale = (width - 6) / max(1, len(self.data_points) - 1)

        value_range = max(
            0.1, self.max_value - self.min_value
        )  # Avoid division by zero
        y_scale = (height - 6) / value_range

        # Calculate all point coordinates first
        coords = []
        for i, value in enumerate(self.data_points):
            # Calculate screen coordinates
            x = int(3 + i * x_scale)
            y = int(height - 4 - ((value - self.min_value) * y_scale))

            # Keep coordinates within bounds
            x = max(3, min(width - 4, x))
            y = max(3, min(height - 4, y))

            coords.append((x, y))

        # Set up color regions - divide the points into three age groups
        total_points = len(coords)
        if total_points > 0:
            old_threshold = total_points // 3
            new_threshold = total_points - old_threshold

            # Function to get color based on index position
            def get_color_pair(idx):
                if idx < old_threshold:
                    return 1  # Yellow (oldest)
                elif idx < new_threshold:
                    return 2  # Green (middle age)
                else:
                    return 3  # Blue (newest)

            # Draw spline curves connecting points with color gradient
            if len(coords) >= 4:
                # Need at least 4 points for a cubic spline
                for i in range(1, len(coords) - 2):
                    x0, y0 = coords[i - 1]
                    x1, y1 = coords[i]
                    x2, y2 = coords[i + 1]
                    x3, y3 = coords[i + 2]

                    # Get color for this segment
                    color_pair = get_color_pair(i)
                    if curses.has_colors():
                        win.attron(curses.color_pair(color_pair))

                    # Calculate spline points
                    spline_points = self._calculate_spline_points(
                        x0, y0, x1, y1, x2, y2, x3, y3
                    )

                    # Draw the spline segment
                    last_px, last_py = None, None
                    for px, py in spline_points:
                        # Keep coordinates in bounds
                        px = max(3, min(width - 4, px))
                        py = max(3, min(height - 4, py))

                        if last_px is not None and last_py is not None:
                            # Draw very thin line (dots)
                            self._draw_line(win, last_py, last_px, py, px, "·")

                        last_px, last_py = px, py

                    if curses.has_colors():
                        win.attroff(curses.color_pair(color_pair))
            elif len(coords) > 1:
                # If we don't have enough points for a spline, connect with straight lines
                for i in range(1, len(coords)):
                    x1, y1 = coords[i - 1]
                    x2, y2 = coords[i]

                    # Get color for this segment
                    color_pair = get_color_pair(i - 1)
                    if curses.has_colors():
                        win.attron(curses.color_pair(color_pair))

                    self._draw_line(win, y1, x1, y2, x2, "·")

                    if curses.has_colors():
                        win.attroff(curses.color_pair(color_pair))

            # Plot points as X markers over the lines with appropriate colors
            for i, (x, y) in enumerate(coords):
                # Get color for this point
                color_pair = get_color_pair(i)

                if curses.has_colors():
                    win.attron(curses.color_pair(color_pair))

                # Draw the point as an 'x'
                try:
                    win.addch(y, x, "x")
                except:
                    pass

                if curses.has_colors():
                    win.attroff(curses.color_pair(color_pair))

    def _draw_line(self, win, y0: int, x0: int, y1: int, x1: int, char: str = "·"):
        """Draw a line between two points using Bresenham's line algorithm"""
        steep = abs(y1 - y0) > abs(x1 - x0)

        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1

        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0

        dx = x1 - x0
        dy = abs(y1 - y0)
        err = dx // 2

        if y0 < y1:
            y_step = 1
        else:
            y_step = -1

        y = y0
        for x in range(x0, x1 + 1):
            if steep:
                try:
                    win.addch(x, y, char)
                except:
                    pass
            else:
                try:
                    win.addch(y, x, char)
                except:
                    pass

            err -= dy
            if err < 0:
                y += y_step
                err += dx

    def visualize(self, data_dir: str, jmespath_expr: str) -> str:
        """
        Visualize time series data using ncurses

        Args:
            data_dir: Directory containing the JSON data files
            jmespath_expr: JMESPath expression to extract the value to plot

        Returns:
            Result message
        """
        # Prepare the data
        if not self._prepare_data(data_dir, jmespath_expr):
            return f"❌ Failed to prepare data from {data_dir} using expression '{jmespath_expr}'"

        if not self.data_points:
            return f"❌ No data points found in {data_dir} using expression '{jmespath_expr}'"

        # Initialize ncurses
        try:
            # Wrapper to ensure proper cleanup
            result = curses.wrapper(self._visualize_with_curses)
            return result
        except Exception as e:
            return f"❌ Error during visualization: {str(e)}"

    def _visualize_with_curses(self, stdscr):
        """Handle the ncurses visualization"""
        # Clear screen
        stdscr.clear()
        curses.curs_set(0)  # Hide cursor

        # Set up colors if available
        if curses.has_colors():
            curses.start_color()
            # Color scheme: older (yellow) -> middle (green) -> newer (blue)
            curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Oldest data
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Middle data
            curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)  # Newest data
            curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Text and axes

        # Get screen dimensions
        height, width = stdscr.getmaxyx()

        # Draw border first
        stdscr.box()

        # Draw title with jmespath expression inside the border
        if curses.has_colors():
            stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(1, (width - len(self.title)) // 2, self.title)
        if curses.has_colors():
            stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)

        # Add latest value as subtitle if available
        if hasattr(self, "latest_value") and self.latest_value is not None:
            subtitle = f"Latest Value: {self.latest_value:.2f}"
            if curses.has_colors():
                stdscr.attron(curses.color_pair(3))  # Use blue (newest) color
            stdscr.addstr(2, (width - len(subtitle)) // 2, subtitle)
            if curses.has_colors():
                stdscr.attroff(curses.color_pair(3))

        # Draw axes
        self._draw_axes(stdscr, height, width)

        # Draw the graph with color
        self._draw_graph(stdscr, height, width)

        # Add instructions
        instruction = "Press any key to exit"
        stdscr.addstr(height - 1, (width - len(instruction)) // 2, instruction)

        # Add stats
        stats = f"Points: {len(self.data_points)} | Min: {self.min_value:.2f} | Max: {self.max_value:.2f}"
        stdscr.addstr(3, (width - len(stats)) // 2, stats)

        # Refresh and wait for keypress
        stdscr.refresh()
        stdscr.getch()

        return f"✅ Successfully visualized {len(self.data_points)} data points from expression: '{self.title}'"


def visualize_time_series(data_dir: str, jmespath_expr: str) -> str:
    """
    Visualize time series data from SFC data files

    Args:
        data_dir: Directory containing the JSON data files
        jmespath_expr: JMESPath expression to extract the value to plot (e.g., "sources.SinusSource.values.sinus.value")

    Returns:
        Result message
    """
    # First, check if the directory exists
    if not os.path.isdir(data_dir):
        return f"❌ Directory not found: {data_dir}"

    # Check if the directory contains any JSON files (recursively)
    json_files = glob.glob(os.path.join(data_dir, "**", "*.json"), recursive=True)
    if not json_files:
        return f"❌ No JSON files found in {data_dir} (including subdirectories)"

    # Initialize the visualizer and run it
    visualizer = DataVisualizer()
    result = visualizer.visualize(data_dir, jmespath_expr)

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python data_visualizer.py <data_dir> <jmespath_expr>")
        sys.exit(1)

    data_dir = sys.argv[1]
    jmespath_expr = sys.argv[2]

    result = visualize_time_series(data_dir, jmespath_expr)
    print(result)
