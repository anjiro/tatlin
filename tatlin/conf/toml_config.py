# -*- coding: utf-8 -*-
# Copyright (C) 2025
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import tomllib
import os
from typing import Optional, Tuple


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


class TomlConfig:
    """
    Load and manage TOML configuration for Tatlin.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Load configuration from TOML file.

        Args:
            config_path: Path to TOML config file. If None, searches default locations.
        """
        self.config_data = {}
        self.config_path = config_path

        if config_path is None:
            # Search for config in default locations
            config_path = self._find_config()

        if config_path and os.path.exists(config_path):
            self._load_config(config_path)

        # Initialize render configuration
        self.render = RenderConfig(self.config_data.get("rendering"))

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
            print(f"Warning: Failed to load config from {path}: {e}")
            self.config_data = {}


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
