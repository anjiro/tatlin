# -*- coding: utf-8 -*-
# Copyright (C) 2011 Denis Kobozev
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import wx

from tatlin.lib.gl.scene import Scene
from tatlin.lib.ui.panel import Panel
from tatlin.lib.util import format_float

from .view import ViewButtons


class GcodePanel(Panel):
    def __init__(self, parent, scene: Scene, file_path=None):
        super(GcodePanel, self).__init__(parent, scene)
        self.file_path = file_path

        # ----------------------------------------------------------------------
        # DIMENSIONS
        # ----------------------------------------------------------------------

        static_box_dimensions = wx.StaticBox(self, label="Dimensions")
        sizer_dimensions = wx.StaticBoxSizer(static_box_dimensions, wx.VERTICAL)

        label_width = wx.StaticText(self, label="X:")
        self.label_width_value = wx.StaticText(self)

        label_depth = wx.StaticText(self, label="Y:")
        self.label_depth_value = wx.StaticText(self)

        label_height = wx.StaticText(self, label="Z:")
        self.label_height_value = wx.StaticText(self)

        grid_dimensions = wx.GridSizer(3, 2, 5, 5)
        grid_dimensions.Add(label_width, 0, wx.ALIGN_CENTER)
        grid_dimensions.Add(self.label_width_value, 0, wx.ALIGN_CENTER)
        grid_dimensions.Add(label_depth, 0, wx.ALIGN_CENTER)
        grid_dimensions.Add(self.label_depth_value, 0, wx.ALIGN_CENTER)
        grid_dimensions.Add(label_height, 0, wx.ALIGN_CENTER)
        grid_dimensions.Add(self.label_height_value, 0, wx.ALIGN_CENTER)

        sizer_dimensions.Add(grid_dimensions, 0, wx.EXPAND | wx.ALL, border=5)

        # ----------------------------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------------------------

        static_box_display = wx.StaticBox(self, label="Display")
        sizer_display = wx.StaticBoxSizer(static_box_display, wx.VERTICAL)

        label_layers = wx.StaticText(self, label="Layers")
        self.slider_layers = wx.Slider(self, style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.check_arrows = wx.CheckBox(self, label="Show arrows")
        self.check_3d = wx.CheckBox(self, label="3D view")
        view_buttons = ViewButtons(self, scene)
        self.check_ortho = wx.CheckBox(self, label="Orthographic projection")
        self.btn_reset_view = wx.Button(self, label="Reset view")

        box_display = wx.BoxSizer(wx.VERTICAL)
        box_display.Add(label_layers, 0, wx.ALIGN_LEFT)
        box_display.Add(self.slider_layers, 0, wx.EXPAND | wx.TOP, border=5)
        box_display.Add(self.check_arrows, 0, wx.EXPAND | wx.TOP, border=5)
        box_display.Add(self.check_3d, 0, wx.EXPAND | wx.TOP, border=5)
        box_display.Add(view_buttons, 0, wx.ALIGN_CENTER | wx.TOP, border=5)
        box_display.Add(self.check_ortho, 0, wx.EXPAND | wx.TOP, border=5)
        box_display.Add(self.btn_reset_view, 0, wx.EXPAND | wx.TOP, border=5)

        sizer_display.Add(box_display, 0, wx.EXPAND | wx.ALL, border=5)

        # ----------------------------------------------------------------------
        # GCODE TEXT VIEW
        # ----------------------------------------------------------------------

        static_box_gcode = wx.StaticBox(self, label="Gcode")
        sizer_gcode = wx.StaticBoxSizer(static_box_gcode, wx.VERTICAL)

        # Create text control for Gcode display
        # TE_MULTILINE: multiline text control
        # TE_READONLY: read-only (selectable but not editable)
        # TE_RICH2: enables text styling for syntax highlighting
        # TE_DONTWRAP: don't wrap long lines
        self.text_gcode = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.TE_DONTWRAP,
        )

        # Set fixed-width (monospace) font
        font = wx.Font(
            9,
            wx.FONTFAMILY_TELETYPE,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL,
        )
        self.text_gcode.SetFont(font)

        # Load and display Gcode file content
        if self.file_path:
            self._load_gcode_text()

        sizer_gcode.Add(self.text_gcode, 1, wx.EXPAND | wx.ALL, border=5)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(sizer_dimensions, 0, wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT, border=5)
        box.Add(sizer_display, 0, wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT, border=5)
        box.Add(sizer_gcode, 1, wx.EXPAND | wx.ALL, border=5)  # proportion=1 to take remaining space

        self.SetSizer(box)

    def connect_handlers(self):
        if self._handlers_connected:
            return

        self.slider_layers.Bind(wx.EVT_SCROLL, self.on_slider_moved)
        self.check_arrows.Bind(wx.EVT_CHECKBOX, self.on_arrows_toggled)
        self.btn_reset_view.Bind(wx.EVT_BUTTON, self.on_reset_clicked)
        self.check_3d.Bind(wx.EVT_CHECKBOX, self.on_set_mode)
        self.check_ortho.Bind(wx.EVT_CHECKBOX, self.on_set_ortho)

        self._handlers_connected = True

    def on_slider_moved(self, event):
        self.scene.change_num_layers(event.GetEventObject().GetValue())
        self.scene.invalidate()

    def on_arrows_toggled(self, event):
        """
        Show/hide arrows on the Gcode model.
        """
        self.scene.show_arrows(event.GetEventObject().GetValue())
        self.scene.invalidate()

    def on_reset_clicked(self, event):
        """
        Restore the view of the model shown on startup.
        """
        self.scene.reset_view()
        self.scene.invalidate()

    def on_set_mode(self, event):
        val = event.GetEventObject().GetValue()
        self.check_ortho.Enable(val)

        self.scene.mode_2d = not val
        if self.scene.initialized:
            self.scene.invalidate()

    def on_set_ortho(self, event):
        self.scene.mode_ortho = event.GetEventObject().GetValue()
        self.scene.invalidate()

    def set_initial_values(self, layers_range_max, layers_value, width, height, depth):
        if layers_range_max > 1:
            self.slider_layers.SetRange(1, layers_range_max)
            self.slider_layers.SetValue(layers_value)
            self.slider_layers.Show()
        else:
            self.slider_layers.Hide()

        self.check_arrows.SetValue(True)  # check the box
        self.check_3d.SetValue(True)

        self.label_width_value.SetLabel(format_float(width))
        self.label_height_value.SetLabel(format_float(height))
        self.label_depth_value.SetLabel(format_float(depth))

    def set_3d_view(self, value):
        self.check_3d.SetValue(value)

    def _load_gcode_text(self):
        """Load Gcode file content and apply syntax highlighting."""
        if not self.file_path:
            return

        try:
            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Set the text content
            self.text_gcode.SetValue(content)

            # Apply syntax highlighting
            self._apply_syntax_highlighting(content)

        except Exception as e:
            self.text_gcode.SetValue(f"Error loading file: {e}")

    def _apply_syntax_highlighting(self, content):
        """Apply syntax highlighting to Gcode text."""
        lines = content.split("\n")
        pos = 0

        # Define colors for syntax highlighting
        comment_color = wx.Colour(100, 100, 100)  # Gray for comments
        gcode_color = wx.Colour(0, 0, 200)  # Blue for G-codes
        mcode_color = wx.Colour(200, 0, 200)  # Magenta for M-codes
        param_color = wx.Colour(0, 128, 0)  # Green for parameters

        # Freeze the control to prevent flickering during updates
        self.text_gcode.Freeze()

        for line in lines:
            line_start = pos
            stripped = line.strip()

            # Find comment position
            comment_pos = line.find(";")
            if comment_pos == -1:
                comment_pos = len(line)

            # Process non-comment part
            if comment_pos > 0:
                non_comment = line[:comment_pos]
                i = 0
                while i < len(non_comment):
                    # Skip whitespace
                    if non_comment[i].isspace():
                        i += 1
                        continue

                    # Check for G-code
                    if non_comment[i].upper() == "G" and i + 1 < len(non_comment):
                        # Find end of G-code number
                        j = i + 1
                        while j < len(non_comment) and (
                            non_comment[j].isdigit() or non_comment[j] == "."
                        ):
                            j += 1
                        self.text_gcode.SetStyle(
                            line_start + i, line_start + j, wx.TextAttr(gcode_color)
                        )
                        i = j
                        continue

                    # Check for M-code
                    if non_comment[i].upper() == "M" and i + 1 < len(non_comment):
                        # Find end of M-code number
                        j = i + 1
                        while j < len(non_comment) and non_comment[j].isdigit():
                            j += 1
                        self.text_gcode.SetStyle(
                            line_start + i, line_start + j, wx.TextAttr(mcode_color)
                        )
                        i = j
                        continue

                    # Check for parameters (X, Y, Z, E, F, etc.)
                    if (
                        non_comment[i].upper()
                        in "XYZEFIJPQRS"
                        and i + 1 < len(non_comment)
                    ):
                        # Find end of parameter value
                        j = i + 1
                        while j < len(non_comment) and (
                            non_comment[j].isdigit()
                            or non_comment[j] in ".-+"
                        ):
                            j += 1
                        self.text_gcode.SetStyle(
                            line_start + i, line_start + j, wx.TextAttr(param_color)
                        )
                        i = j
                        continue

                    i += 1

            # Highlight comment
            if comment_pos < len(line):
                self.text_gcode.SetStyle(
                    line_start + comment_pos,
                    line_start + len(line),
                    wx.TextAttr(comment_color),
                )

            # Move to next line (including newline character)
            pos += len(line) + 1

        # Thaw the control to redraw
        self.text_gcode.Thaw()

        # Scroll to top
        self.text_gcode.SetInsertionPoint(0)
