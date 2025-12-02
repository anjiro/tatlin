# -*- coding: utf-8 -*-
# Copyright (C) 2025
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import tomllib
import json
import os
from typing import Optional, Tuple, List
import logging


class RenderConfig:
    """
    Configuration for rendering settings (colors, fonts, sizes, etc.)
    """

    def __init__(self, config_dict: Optional[dict] = None):
        """
        Initialize render configuration with optional TOML config dictionary.
        Falls back to defaults if config is not provided or values are missing.
        """
        if config_dict is None:
            config_dict = {}

        # Gcode line colors (RGBA tuples)
        colors = config_dict.get("gcode_colors", {})
        self.color_movement_default = self._parse_color(
            colors.get("movement_default"), (0.6, 0.6, 0.6, 0.6)
        )
        self.color_outer_perimeter = self._parse_color(
            colors.get("outer_perimeter"), (0.0, 0.875, 0.875, 0.6)
        )
        self.color_perimeter = self._parse_color(
            colors.get("perimeter"), (0.0, 1.0, 0.0, 0.6)
        )
        self.color_loop = self._parse_color(
            colors.get("loop"), (1.0, 0.875, 0.0, 0.6)
        )
        self.color_extruder_on = self._parse_color(
            colors.get("extruder_on"), (1.0, 0.0, 0.0, 0.6)
        )

        # Selection highlight - can be a color or just an alpha multiplier
        selection = config_dict.get("selection", {})
        self.selection_color = self._parse_color(
            selection.get("color"), (1.0, 1.0, 0.0, 0.8)
        )
        # If alpha_multiplier is set, we'll use it instead of replacing color
        self.selection_alpha_multiplier = selection.get("alpha_multiplier")

        # Cylinder rendering
        rendering = config_dict.get("rendering", {})
        self.cylinder_radius = rendering.get("cylinder_radius", 0.1)
        self.cylinder_sides = rendering.get("cylinder_sides", 8)

        # Font settings
        font = config_dict.get("font", {})
        self.font_size = font.get("size", 9)
        self.font_family = font.get("family", "monospace")

        # Platform/grid settings
        platform = config_dict.get("platform", {})
        self.platform_width = platform.get("width", 120)  # Default: MakerBot Thing-O-Matic size
        self.platform_depth = platform.get("depth", 100)
        self.platform_grid_size = platform.get("grid_size", 10)

        grid_colors = platform.get("colors", {})
        # Using the greenish default colors
        default_r, default_g, default_b = 0xAF / 255, 0xDF / 255, 0x5F / 255
        self.platform_color_minor = self._parse_color(
            grid_colors.get("minor"), (default_r, default_g, default_b, 0.1)
        )
        self.platform_color_intermediate = self._parse_color(
            grid_colors.get("intermediate"), (default_r, default_g, default_b, 0.2)
        )
        self.platform_color_major = self._parse_color(
            grid_colors.get("major"), (default_r, default_g, default_b, 0.33)
        )
        self.platform_color_fill = self._parse_color(
            grid_colors.get("fill"), (default_r, default_g, default_b, 0.05)
        )

        # Background color
        self.background_color = self._parse_color(
            config_dict.get("background_color"), (0.0, 0.0, 0.0, 0.0)
        )

    def _parse_color(self, value, default: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """
        Parse a color value from config. Accepts:
        - List/tuple of 3 values (RGB, alpha=1.0)
        - List/tuple of 4 values (RGBA)
        - None (returns default)

        All values should be in range 0.0-1.0
        """
        if value is None:
            return default

        if isinstance(value, (list, tuple)):
            if len(value) == 3:
                return (float(value[0]), float(value[1]), float(value[2]), 1.0)
            elif len(value) == 4:
                return (float(value[0]), float(value[1]), float(value[2]), float(value[3]))

        # Invalid format, return default
        return default


class MachineConfig:
    """
    Configuration for machine settings (platform offsets, etc.)
    """

    def __init__(self, config_dict: Optional[dict] = None):
        if config_dict is None:
            config_dict = {}

        # Platform offsets (optional, for positioning models)
        self.platform_offset_x = config_dict.get("platform_offset_x", 0.0)
        self.platform_offset_y = config_dict.get("platform_offset_y", 0.0)
        self.platform_offset_z = config_dict.get("platform_offset_z", 0.0)


class UIConfig:
    """
    Configuration for UI settings (window size, mode, recent files).
    These are runtime/session state saved to a JSON file.
    """

    def __init__(self, state_dict: Optional[dict] = None):
        if state_dict is None:
            state_dict = {}

        # Window dimensions
        self.window_w = state_dict.get("window_w", 640)
        self.window_h = state_dict.get("window_h", 700)

        # 2D mode preference
        self.gcode_2d = state_dict.get("gcode_2d", False)

        # Recent files list (list of tuples: (basename, filepath, filetype))
        # Stored as list of dicts in JSON
        recent = state_dict.get("recent_files", [])
        self.recent_files = [(r.get("name", ""), r.get("path", ""), r.get("type"))
                             for r in recent] if recent else []

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "window_w": self.window_w,
            "window_h": self.window_h,
            "gcode_2d": self.gcode_2d,
            "recent_files": [
                {"name": f[0], "path": f[1], "type": f[2]}
                for f in self.recent_files
            ]
        }


class TomlConfig:
    """
    Load and manage TOML configuration for Tatlin.
    """

    def __init__(self, config_path: Optional[str] = None, state_path: Optional[str] = None):
        """
        Load configuration from TOML file and state from JSON file.

        Args:
            config_path: Path to TOML config file. If None, searches default locations.
            state_path: Path to JSON state file. If None, uses default location.
        """
        self.config_data = {}
        self.config_path = config_path
        self.state_data = {}

        # Determine state file path using XDG Base Directory Specification
        if state_path is None:
            # Use XDG_STATE_HOME if set, otherwise default to ~/.local/state
            xdg_state_home = os.environ.get("XDG_STATE_HOME")
            if xdg_state_home:
                state_dir = os.path.join(xdg_state_home, "tatlin")
            else:
                state_dir = os.path.expanduser(os.path.join("~", ".local", "state", "tatlin"))

            # Create directory if it doesn't exist
            os.makedirs(state_dir, exist_ok=True)

            state_path = os.path.join(state_dir, "state.json")
        self.state_path = state_path

        if config_path is None:
            # Search for config in default locations
            config_path = self._find_config()
            self.config_path = config_path

        if config_path and os.path.exists(config_path):
            self._load_config(config_path)

        # Load state from JSON
        self._load_state()

        # Initialize configuration objects
        self.render = RenderConfig(self.config_data.get("rendering"))
        self.machine = MachineConfig(self.config_data.get("machine"))
        self.ui = UIConfig(self.state_data)

    def _find_config(self) -> Optional[str]:
        """
        Search for config file in default locations.
        Returns path to first found config, or None.
        """
        search_paths = [
            os.path.expanduser("~/.tatlin.toml"),
            os.path.expanduser("~/.config/tatlin/config.toml"),
            "tatlin.toml",
            "config.toml",
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

        return None

    def _load_config(self, path: str):
        """Load TOML configuration from file."""
        try:
            with open(path, "rb") as f:
                self.config_data = tomllib.load(f)
        except Exception as e:
            # If config fails to load, use defaults
            logging.warning(f"Failed to load config from {path}: {e}")
            self.config_data = {}

    def _load_state(self):
        """Load UI state from JSON file."""
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r") as f:
                    self.state_data = json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load state from {self.state_path}: {e}")
                self.state_data = {}
        else:
            self.state_data = {}

    def _save_state(self):
        """Save UI state to JSON file."""
        try:
            with open(self.state_path, "w") as f:
                json.dump(self.ui.to_dict(), f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to save state to {self.state_path}: {e}")

    # Compatibility methods for old Config API
    def read(self, key: str, conv=None):
        """
        Read a configuration value with backward compatibility.
        Supports old INI-style keys like 'machine.platform_w', 'ui.window_w', etc.
        """
        # Map old INI keys to new structure
        if key == "machine.platform_w":
            return self.render.platform_width
        elif key == "machine.platform_d":
            return self.render.platform_depth
        elif key == "machine.platform_offset_x":
            return self.machine.platform_offset_x
        elif key == "machine.platform_offset_y":
            return self.machine.platform_offset_y
        elif key == "machine.platform_offset_z":
            return self.machine.platform_offset_z
        elif key == "ui.window_w":
            return self.ui.window_w
        elif key == "ui.window_h":
            return self.ui.window_h
        elif key == "ui.gcode_2d":
            return self.ui.gcode_2d
        elif key == "ui.recent_files":
            # Return None to match old behavior (recent files handled separately)
            return None
        else:
            logging.warning(f"Unknown config key: {key}")
            return None

    def write(self, key: str, val):
        """
        Write a configuration value with backward compatibility.
        """
        if key == "ui.window_w":
            self.ui.window_w = int(val)
        elif key == "ui.window_h":
            self.ui.window_h = int(val)
        elif key == "ui.gcode_2d":
            self.ui.gcode_2d = bool(int(val)) if isinstance(val, (int, str)) else bool(val)
        elif key == "ui.recent_files":
            # Recent files handled by update_recent_files method
            pass
        else:
            logging.warning(f"Cannot write to config key: {key}")

    def commit(self):
        """Save state to JSON file."""
        self._save_state()


# Global config instance - will be initialized by the application
_global_config: Optional[TomlConfig] = None


def get_config() -> TomlConfig:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = TomlConfig()
    return _global_config


def set_config(config: TomlConfig):
    """Set the global configuration instance."""
    global _global_config
    _global_config = config
