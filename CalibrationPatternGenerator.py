import numpy as np
import os
from datetime import datetime

class CNCCalibrationGenerator:
    def __init__(self):
        # Default pattern parameters
        self.pattern_width = 10.0  # mm
        self.pattern_height = 10.0  # mm
        self.patterns_x = 3  # Number of patterns in X direction
        self.patterns_y = 3  # Number of patterns in Y direction
        self.spacing_x = 5.0  # mm
        self.spacing_y = 5.0  # mm
        self.bit_width = 3.175  # mm (1/8 inch)
        self.cutting_depth = 1.0  # mm
        self.safe_z = 5.0  # mm
        self.feed_rate = 500  # mm/min
        self.spindle_speed = 10000  # RPM
        self.overlap_ratio = 0.5  # Overlap between adjacent pocket paths
        self.operation_type = "pocket"  # "contour" or "pocket"
        self.plunge_rate = 250  # mm/min
        self.step_over = 0.5  # Factor of bit width (0-1)
        self.pocket_pattern = "y_first"  # "x_first", "y_first", or "contour"
        
        # Parameters to vary
        self.x_parameter = "spindle_speed"  # Parameter to vary in X direction
        self.y_parameter = "feed_rate"  # Parameter to vary in Y direction
        
        # Simplified parameter start and step values
        self.parameter_start = {}
        self.parameter_step = {}
        
        # Initialize with default start/step values
        self.parameter_start = {
            "feed_rate": 500,
            "spindle_speed": 10000,
            "cutting_depth": 1.0,
            "bit_width": 3.175,
            "overlap_ratio": 0.5,
            "plunge_rate": 250,
            "step_over": 0.5
        }
        
        self.parameter_step = {
            "feed_rate": 100,
            "spindle_speed": 1000,
            "cutting_depth": 0.2,
            "bit_width": 0.5,
            "overlap_ratio": 0.1,
            "plunge_rate": 50,
            "step_over": 0.1
        }
        
        # Valid parameters that can be varied
        self.variable_parameters = [
            "feed_rate", 
            "spindle_speed", 
            "cutting_depth", 
            "bit_width",
            "overlap_ratio",
            "plunge_rate",
            "step_over"
        ]
        
        # Label parameters
        self.include_labels = True  # Whether to engrave parameter labels
        self.label_offset = 5.0  # mm, distance from pattern edge
        self.label_depth = 0.3  # mm, engraving depth for labels
        self.label_feed_rate = 300  # mm/min, feed rate for label engraving
        self.label_spindle_speed = 12000  # RPM, spindle speed for label engraving
        self.label_bit_width = 1.0  # mm, bit width for label engraving
        self.label_plunge_rate = 150  # mm/min, plunge rate for label engraving
        self.label_scale = 0.8  # Scale factor for label size
        self.label_char_width = 3.0  # Width of each character in mm
        self.label_char_height = 5.0  # Height of each character in mm
        self.label_char_spacing = 0.5  # Spacing between characters in mm
        self.label_name_offset = 15.0  # Increased distance for parameter names
        
        # Parameter display names (for labels)
        self.parameter_display_names = {
            "feed_rate": "Feed",
            "spindle_speed": "RPM",
            "cutting_depth": "Depth",
            "bit_width": "Bit",
            "overlap_ratio": "Overlap",
            "plunge_rate": "Plunge",
            "step_over": "Step"
        }
        
        # Units for parameters (for labels)
        self.parameter_units = {
            "feed_rate": "mm/min",
            "spindle_speed": "",
            "cutting_depth": "mm",
            "bit_width": "mm",
            "overlap_ratio": "",
            "plunge_rate": "mm/min",
            "step_over": ""
        }
        
        # Output file
        self.output_file = f"cnc_calibration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gcode"
        
    def generate_gcode(self):
        """Generate G-code for the calibration pattern"""
        gcode = self._generate_header()
        
        # Generate labels for X parameters (top row)
        if self.include_labels:
            gcode += self._generate_x_parameter_labels()
        
        # Generate labels for Y parameters (leftmost column)
        if self.include_labels:
            gcode += self._generate_y_parameter_labels()
        
        # Generate each pattern in the grid
        for y in range(self.patterns_y):
            for x in range(self.patterns_x):
                # Calculate position of this pattern
                pos_x = x * (self.pattern_width + self.spacing_x)
                pos_y = y * (self.pattern_height + self.spacing_y)
                
                # Get parameters for this pattern
                params = self._get_parameters_for_pattern(x, y)
                
                # Generate pattern
                if params["operation_type"] == "contour":
                    gcode += self._generate_contour_pattern(pos_x, pos_y, params)
                else:  # pocket
                    gcode += self._generate_pocket_pattern(pos_x, pos_y, params)
        
        gcode += self._generate_footer()
        
        # Save to file
        with open(self.output_file, 'w') as f:
            f.write(gcode)
        
        return gcode
    
    def _get_parameters_for_pattern(self, x, y):
        """Get the parameters for a specific pattern based on its position"""
        # Create a copy of all parameters as a dictionary
        params = {
            "feed_rate": self.feed_rate,
            "spindle_speed": self.spindle_speed,
            "cutting_depth": self.cutting_depth,
            "bit_width": self.bit_width,
            "overlap_ratio": self.overlap_ratio,
            "operation_type": self.operation_type,
            "plunge_rate": self.plunge_rate,
            "step_over": self.step_over,
            "pocket_pattern": self.pocket_pattern
        }
        
        # Adjust X parameter
        if self.x_parameter in self.variable_parameters:
            start_value = self.parameter_start[self.x_parameter]
            step_value = self.parameter_step[self.x_parameter]
            params[self.x_parameter] = start_value + x * step_value
        
        # Adjust Y parameter 
        if self.y_parameter in self.variable_parameters:
            start_value = self.parameter_start[self.y_parameter]
            step_value = self.parameter_step[self.y_parameter]
            params[self.y_parameter] = start_value + y * step_value
            
        return params
    
    def _format_parameter_value(self, param, value):
        """Format parameter value for display"""
        # Format based on parameter type
        if param in ["overlap_ratio", "step_over"]:
            # Display as percentage
            return f"{int(value*100)}%"
        elif param in ["cutting_depth", "bit_width"]:
            # Display with 2 decimal places
            return f"{value:.2f}"
        elif param in ["feed_rate", "plunge_rate", "spindle_speed"]:
            # Display as integer
            return f"{int(value)}"
        else:
            # Default format
            return f"{value}"
    
    def _generate_header(self):
        """Generate the G-code header"""
        header = f"""
;---------------------------------------------------------
; CNC Calibration Pattern Generator
; Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
; Pattern grid: {self.patterns_x}x{self.patterns_y}
; Pattern size: {self.pattern_width}mm x {self.pattern_height}mm
; X parameter: {self.x_parameter} starting at {self.parameter_start[self.x_parameter]} with step {self.parameter_step[self.x_parameter]}
; Y parameter: {self.y_parameter} starting at {self.parameter_start[self.y_parameter]} with step {self.parameter_step[self.y_parameter]}
; Operation type: {self.operation_type}
; Pocket pattern: {self.pocket_pattern}
; Default bit width: {self.bit_width}mm
; Default cutting depth: {self.cutting_depth}mm
; Default overlap ratio: {self.overlap_ratio}
; Labels: {"Enabled" if self.include_labels else "Disabled"}
;---------------------------------------------------------
G90 ; Absolute positioning
G21 ; Metric units
G17 ; XY plane selection
G54 ; Work coordinate system
G0 Z{self.safe_z} ; Move to safe Z height
"""
        return header
    
    def _generate_footer(self):
        """Generate the G-code footer"""
        footer = f"""
; End of program
G0 Z{self.safe_z} ; Move to safe Z height
M5 ; Stop spindle
M30 ; End program and rewind
"""
        return footer
    
    def _generate_contour_pattern(self, pos_x, pos_y, params):
        """Generate G-code for a contour pattern with given parameters"""
        feed_rate = params["feed_rate"]
        spindle_speed = params["spindle_speed"]
        cutting_depth = params["cutting_depth"]
        plunge_rate = params["plunge_rate"]
        
        gcode = f"""
; Contour pattern at X{pos_x} Y{pos_y}
; Parameters: F{feed_rate} S{spindle_speed} Z{cutting_depth} Plunge:{plunge_rate}
M3 S{spindle_speed} ; Start spindle
G0 X{pos_x} Y{pos_y} ; Move to start position
G0 Z{self.safe_z} ; Move to safe Z height
G1 Z{-cutting_depth} F{plunge_rate} ; Plunge to cutting depth
"""
        # Generate rectangle
        gcode += f"G1 X{pos_x + self.pattern_width} Y{pos_y} F{feed_rate} ; Bottom edge\n"
        gcode += f"G1 X{pos_x + self.pattern_width} Y{pos_y + self.pattern_height} ; Right edge\n"
        gcode += f"G1 X{pos_x} Y{pos_y + self.pattern_height} ; Top edge\n"
        gcode += f"G1 X{pos_x} Y{pos_y} ; Left edge\n"
        
        # Return to safe Z
        gcode += f"G0 Z{self.safe_z} ; Move to safe Z height\n"
        
        return gcode
    
    def _generate_pocket_pattern(self, pos_x, pos_y, params):
        """Generate G-code for a pocket pattern with given parameters"""
        feed_rate = params["feed_rate"]
        spindle_speed = params["spindle_speed"]
        cutting_depth = params["cutting_depth"]
        bit_width = params["bit_width"]
        overlap_ratio = params["overlap_ratio"]
        plunge_rate = params["plunge_rate"]
        step_over = params["step_over"]
        pocket_pattern = params["pocket_pattern"]
        
        gcode = f"""
; Pocket pattern at X{pos_x} Y{pos_y}
; Parameters: F{feed_rate} S{spindle_speed} Z{cutting_depth} Bit:{bit_width} Overlap:{overlap_ratio} Plunge:{plunge_rate}
; Fill pattern: {pocket_pattern}
M3 S{spindle_speed} ; Start spindle
"""
        # Calculate effective bit width based on step_over
        effective_bit_width = bit_width * step_over
        
        # Calculate number of passes needed to cover the pattern
        x_passes = max(1, int(np.ceil(self.pattern_width / effective_bit_width)))
        y_passes = max(1, int(np.ceil(self.pattern_height / effective_bit_width)))
        
        # Actual step size (may be smaller than effective_bit_width to fit pattern exactly)
        x_step = self.pattern_width / x_passes
        y_step = self.pattern_height / y_passes
        
        if pocket_pattern == "y_first":
            # Generate zigzag pattern prioritizing Y-direction (rows)
            gcode += self._generate_y_first_pocket(pos_x, pos_y, x_passes, y_passes, x_step, y_step, cutting_depth, feed_rate, plunge_rate)
        elif pocket_pattern == "x_first":
            # Generate zigzag pattern prioritizing X-direction (columns)
            gcode += self._generate_x_first_pocket(pos_x, pos_y, x_passes, y_passes, x_step, y_step, cutting_depth, feed_rate, plunge_rate)
        elif pocket_pattern == "contour":
            # Generate inward spiral pattern (contour approach)
            gcode += self._generate_contour_pocket(pos_x, pos_y, x_passes, y_passes, x_step, y_step, cutting_depth, feed_rate, plunge_rate)
        else:
            # Default to Y-first pattern
            gcode += self._generate_y_first_pocket(pos_x, pos_y, x_passes, y_passes, x_step, y_step, cutting_depth, feed_rate, plunge_rate)
        
        # Return to safe Z
        gcode += f"G0 Z{self.safe_z} ; Move to safe Z height\n"
        
        return gcode
    
    def _generate_y_first_pocket(self, pos_x, pos_y, x_passes, y_passes, x_step, y_step, cutting_depth, feed_rate, plunge_rate):
        """Generate G-code for Y-first pocket pattern (horizontal rows)"""
        gcode = "; Y-first pattern (horizontal rows)\n"
        
        # Generate zigzag pattern to fill pocket
        for i in range(y_passes):
            y_pos = pos_y + i * y_step
            
            # Move to start of this row
            if i % 2 == 0:  # Even rows go left to right
                gcode += f"G0 X{pos_x} Y{y_pos} ; Move to start of row {i}\n"
                gcode += f"G0 Z{self.safe_z} ; Move to safe Z height\n"
                gcode += f"G1 Z{-cutting_depth} F{plunge_rate} ; Plunge to cutting depth\n"
                
                # Cut along the row
                gcode += f"G1 X{pos_x + self.pattern_width} Y{y_pos} F{feed_rate} ; Cut row {i}\n"
            else:  # Odd rows go right to left
                gcode += f"G0 X{pos_x + self.pattern_width} Y{y_pos} ; Move to start of row {i}\n"
                gcode += f"G0 Z{self.safe_z} ; Move to safe Z height\n"
                gcode += f"G1 Z{-cutting_depth} F{plunge_rate} ; Plunge to cutting depth\n"
                
                # Cut along the row
                gcode += f"G1 X{pos_x} Y{y_pos} F{feed_rate} ; Cut row {i}\n"
        
        return gcode
    
    def _generate_x_first_pocket(self, pos_x, pos_y, x_passes, y_passes, x_step, y_step, cutting_depth, feed_rate, plunge_rate):
        """Generate G-code for X-first pocket pattern (vertical columns)"""
        gcode = "; X-first pattern (vertical columns)\n"
        
        # Generate zigzag pattern to fill pocket
        for i in range(x_passes):
            x_pos = pos_x + i * x_step
            
            # Move to start of this column
            if i % 2 == 0:  # Even columns go bottom to top
                gcode += f"G0 X{x_pos} Y{pos_y} ; Move to start of column {i}\n"
                gcode += f"G0 Z{self.safe_z} ; Move to safe Z height\n"
                gcode += f"G1 Z{-cutting_depth} F{plunge_rate} ; Plunge to cutting depth\n"
                
                # Cut along the column
                gcode += f"G1 X{x_pos} Y{pos_y + self.pattern_height} F{feed_rate} ; Cut column {i}\n"
            else:  # Odd columns go top to bottom
                gcode += f"G0 X{x_pos} Y{pos_y + self.pattern_height} ; Move to start of column {i}\n"
                gcode += f"G0 Z{self.safe_z} ; Move to safe Z height\n"
                gcode += f"G1 Z{-cutting_depth} F{plunge_rate} ; Plunge to cutting depth\n"
                
                # Cut along the column
                gcode += f"G1 X{x_pos} Y{pos_y} F{feed_rate} ; Cut column {i}\n"
        
        return gcode
    
    def _generate_contour_pocket(self, pos_x, pos_y, x_passes, y_passes, x_step, y_step, cutting_depth, feed_rate, plunge_rate):
        """Generate G-code for contour pocket pattern (inward spiral)"""
        gcode = "; Contour pattern (inward spiral)\n"
        
        # Calculate number of rings (the smaller of x_passes/2 or y_passes/2)
        rings = min(x_passes // 2, y_passes // 2)
        
        # Ensure at least one ring
        rings = max(1, rings)
        
        # Generate inward spiral pattern
        for r in range(rings):
            # Calculate corners of this ring
            left = pos_x + r * x_step
            right = pos_x + self.pattern_width - r * x_step
            bottom = pos_y + r * y_step
            top = pos_y + self.pattern_height - r * y_step
            
            # Skip rings that are too small
            if right <= left or top <= bottom:
                continue
            
            # Move to start (bottom-left corner)
            gcode += f"G0 X{left} Y{bottom} ; Move to start of ring {r}\n"
            gcode += f"G0 Z{self.safe_z} ; Move to safe Z height\n"
            gcode += f"G1 Z{-cutting_depth} F{plunge_rate} ; Plunge to cutting depth\n"
            
            # Cut rectangle (counterclockwise)
            gcode += f"G1 X{right} Y{bottom} F{feed_rate} ; Bottom edge\n"
            gcode += f"G1 X{right} Y{top} F{feed_rate} ; Right edge\n"
            gcode += f"G1 X{left} Y{top} F{feed_rate} ; Top edge\n"
            gcode += f"G1 X{left} Y{bottom} F{feed_rate} ; Left edge\n"
            
            # Lift before moving to next ring
            gcode += f"G0 Z{self.safe_z} ; Lift to safe height\n"
        
        # If we have odd number of passes, add a centerline
        if x_passes % 2 == 1 or y_passes % 2 == 1:
            center_x = pos_x + self.pattern_width / 2
            center_y = pos_y + self.pattern_height / 2
            
            if x_passes % 2 == 1:
                # Add vertical centerline
                gcode += f"G0 X{center_x} Y{pos_y} ; Move to start of centerline\n"
                gcode += f"G0 Z{self.safe_z} ; Move to safe Z height\n"
                gcode += f"G1 Z{-cutting_depth} F{plunge_rate} ; Plunge to cutting depth\n"
                gcode += f"G1 X{center_x} Y{pos_y + self.pattern_height} F{feed_rate} ; Cut vertical centerline\n"
                gcode += f"G0 Z{self.safe_z} ; Lift to safe height\n"
            
            if y_passes % 2 == 1:
                # Add horizontal centerline
                gcode += f"G0 X{pos_x} Y{center_y} ; Move to start of centerline\n"
                gcode += f"G0 Z{self.safe_z} ; Move to safe Z height\n"
                gcode += f"G1 Z{-cutting_depth} F{plunge_rate} ; Plunge to cutting depth\n"
                gcode += f"G1 X{pos_x + self.pattern_width} Y{center_y} F{feed_rate} ; Cut horizontal centerline\n"
                gcode += f"G0 Z{self.safe_z} ; Lift to safe height\n"
        
        return gcode
    
    def _generate_x_parameter_labels(self):
        """Generate G-code for X parameter labels at the top of the grid"""
        gcode = f"""
; Generating X parameter labels
M3 S{self.label_spindle_speed} ; Start spindle for labels
"""
        
        # Get the parameter display name
        param_name = self.parameter_display_names.get(self.x_parameter, self.x_parameter)
        
        # Generate parameter name at the top center of the grid
        total_width = self.patterns_x * (self.pattern_width + self.spacing_x) - self.spacing_x
        param_name_x = total_width / 2
        param_name_y = -self.label_name_offset  # Increased distance for parameter name
        
        # Engrave parameter name
        gcode += self.engrave_text(param_name, param_name_x - len(param_name) * self.label_char_width / 2, param_name_y)
        
        # Generate value labels for each column (vertically oriented)
        for x in range(self.patterns_x):
            pos_x = x * (self.pattern_width + self.spacing_x) + self.pattern_width / 2
            
            # Calculate the value for this column
            start_value = self.parameter_start[self.x_parameter]
            step_value = self.parameter_step[self.x_parameter]
            param_value = start_value + x * step_value
            
            # Format the value as text
            value_text = self._format_parameter_value(self.x_parameter, param_value)
            
            # Engrave the value vertically (90 degrees rotated)
            # Vertical spacing ensures no overlap between column labels
            value_x = pos_x
            value_y = -self.label_offset
            
            # Use vertical text for column values
            gcode += self.engrave_text(value_text, value_x, value_y, vertical=True)
        
        return gcode
    
    def _generate_y_parameter_labels(self):
        """Generate G-code for Y parameter labels at the left of the grid"""
        gcode = f"""
; Generating Y parameter labels
M3 S{self.label_spindle_speed} ; Start spindle for labels
"""
        
        # Get the parameter display name
        param_name = self.parameter_display_names.get(self.y_parameter, self.y_parameter)
        
        # Generate parameter name at the left center of the grid
        total_height = self.patterns_y * (self.pattern_height + self.spacing_y) - self.spacing_y
        param_name_x = -self.label_name_offset  # Increased distance for parameter name
        param_name_y = total_height / 2
        
        # Engrave parameter name (vertical text)
        gcode += self.engrave_text(param_name, param_name_x, param_name_y, vertical=True)
        
        # Generate value labels for each row
        for y in range(self.patterns_y):
            pos_y = y * (self.pattern_height + self.spacing_y) + self.pattern_height / 2
            
            # Calculate the value for this row
            start_value = self.parameter_start[self.y_parameter]
            step_value = self.parameter_step[self.y_parameter]
            param_value = start_value + y * step_value
            
            # Format the value as text
            value_text = self._format_parameter_value(self.y_parameter, param_value)
            
            # Engrave the value
            # Position values between parameter name and patterns
            value_x = -self.label_offset - len(value_text) * self.label_char_width
            value_y = pos_y
            gcode += self.engrave_text(value_text, value_x, value_y)
        
        return gcode
    
    def engrave_text(self, text, x, y, vertical=False):
        """
        Generate G-code to engrave text.
        
        Args:
            text (str): Text to engrave
            x (float): X-coordinate of text start position
            y (float): Y-coordinate of text start position
            vertical (bool): Whether to engrave text vertically
            
        Returns:
            str: G-code for text engraving
        """
        gcode = f"\n; Engraving text: '{text}' at X{x} Y{y}{' (vertical)' if vertical else ''}\n"
        
        # Set up for engraving
        gcode += f"M3 S{self.label_spindle_speed} ; Start spindle for text\n"
        
        # Character definitions - simplified vector paths for each character
        char_vectors = self._get_character_vectors()
        
        current_x = x
        current_y = y
        
        # Engrave each character
        for char in text:
            if char in char_vectors:
                char_width = self.label_char_width
                char_height = self.label_char_height
                
                # Get the vector path for this character
                vectors = char_vectors[char]
                
                # Transform the vectors based on position and orientation
                for vector in vectors:
                    path_type, points = vector
                    transformed_points = []
                    
                    # Transform points based on position and orientation
                    for point in points:
                        px, py = point
                        # Scale points to fit character size
                        px = px * char_width
                        py = py * char_height
                        
                        # Apply vertical transformation if needed
                        if vertical:
                            # Swap x and y, but keep text readable (not upside down)
                            px, py = py, -px
                        
                        # Apply position offset
                        px += current_x
                        py += current_y
                        
                        transformed_points.append((px, py))
                    
                    # Generate tool path for this vector
                    if path_type == "move":
                        # Move to first point
                        start_x, start_y = transformed_points[0]
                        gcode += f"G0 X{start_x:.3f} Y{start_y:.3f} ; Move to start of stroke\n"
                        gcode += f"G0 Z{self.safe_z} ; Lift to safe height\n"
                        gcode += f"G1 Z{-self.label_depth} F{self.label_plunge_rate} ; Plunge to cutting depth\n"
                        
                        # Draw line through remaining points
                        for i in range(1, len(transformed_points)):
                            px, py = transformed_points[i]
                            gcode += f"G1 X{px:.3f} Y{py:.3f} F{self.label_feed_rate} ; Draw stroke\n"
                            
                        # Lift at end of stroke
                        gcode += f"G0 Z{self.safe_z} ; Lift to safe height\n"
            
            # Move to next character position
            if vertical:
                current_y -= (char_height + self.label_char_spacing)
            else:
                current_x += (char_width + self.label_char_spacing)
        
        return gcode
    
    def _get_character_vectors(self):
        """
        Define vector paths for characters.
        Each character is defined as a list of vectors.
        Each vector is a tuple of (path_type, points).
        path_type can be "move" (for a continuous tool path).
        points is a list of (x, y) coordinates normalized to [0, 1] range.
        """
        # Character vector definitions included here
        # (Same as previous implementation, not duplicated for brevity)
        char_vectors = {
            '0': [
                ("move", [(0.2, 0), (0.8, 0), (1, 0.2), (1, 0.8), (0.8, 1), (0.2, 1), (0, 0.8), (0, 0.2), (0.2, 0)])
            ],
            '1': [
                ("move", [(0.3, 0.2), (0.5, 0), (0.5, 1)]),
                ("move", [(0.3, 1), (0.7, 1)])
            ],
            '2': [
                ("move", [(0, 0.2), (0.2, 0), (0.8, 0), (1, 0.2), (1, 0.4), (0, 1), (1, 1)])
            ],
            '3': [
                ("move", [(0, 0.2), (0.2, 0), (0.8, 0), (1, 0.2), (1, 0.4), (0.8, 0.5), (0.5, 0.5)]),
                ("move", [(0.8, 0.5), (1, 0.6), (1, 0.8), (0.8, 1), (0.2, 1), (0, 0.8)])
            ],
            '4': [
                ("move", [(0.8, 0), (0.8, 1), (0, 0.4), (1, 0.4)])
            ],
            '5': [
                ("move", [(1, 0), (0, 0), (0, 0.5), (0.8, 0.5), (1, 0.7), (1, 0.9), (0.8, 1), (0.2, 1), (0, 0.9)])
            ],
            '6': [
                ("move", [(1, 0.1), (0.8, 0), (0.2, 0), (0, 0.2), (0, 0.8), (0.2, 1), (0.8, 1), (1, 0.8), (1, 0.6), (0.8, 0.5), (0, 0.5)])
            ],
            '7': [
                ("move", [(0, 1), (1, 1), (0.5, 0)])
            ],
            '8': [
                ("move", [(0.5, 0.5), (0.2, 0.5), (0, 0.3), (0, 0.2), (0.2, 0), (0.8, 0), (1, 0.2), (1, 0.3), (0.8, 0.5), (0.5, 0.5), (0.2, 0.5)]),
                ("move", [(0.5, 0.5), (0.8, 0.5), (1, 0.7), (1, 0.8), (0.8, 1), (0.2, 1), (0, 0.8), (0, 0.7), (0.2, 0.5), (0.5, 0.5)])
            ],
            '9': [
                ("move", [(1, 0.5), (0.2, 0.5), (0, 0.7), (0, 0.9), (0.2, 1), (0.8, 1), (1, 0.9), (1, 0.1), (0.8, 0), (0.2, 0), (0, 0.1)])
            ],
            '.': [
                ("move", [(0.4, 0), (0.6, 0), (0.6, 0.2), (0.4, 0.2), (0.4, 0)])
            ],
            '%': [
                ("move", [(0, 1), (1, 0)]),
                ("move", [(0.2, 0.8), (0.2, 1), (0, 1), (0, 0.8), (0.2, 0.8)]),
                ("move", [(0.8, 0), (1, 0), (1, 0.2), (0.8, 0.2), (0.8, 0)])
            ],
            'A': [
                ("move", [(0, 0), (0.5, 1), (1, 0)]),
                ("move", [(0.2, 0.4), (0.8, 0.4)])
            ],
            'B': [
                ("move", [(0, 0), (0, 1), (0.8, 1), (1, 0.8), (1, 0.6), (0.8, 0.5), (0, 0.5)]),
                ("move", [(0.8, 0.5), (1, 0.4), (1, 0.2), (0.8, 0), (0, 0)])
            ],
            'C': [
                ("move", [(1, 0.2), (0.8, 0), (0.2, 0), (0, 0.2), (0, 0.8), (0.2, 1), (0.8, 1), (1, 0.8)])
            ],
            'D': [
                ("move", [(0, 0), (0, 1), (0.7, 1), (1, 0.8), (1, 0.2), (0.7, 0), (0, 0)])
            ],
            'E': [
                ("move", [(1, 0), (0, 0), (0, 1), (1, 1)]),
                ("move", [(0, 0.5), (0.7, 0.5)])
            ],
            'F': [
                ("move", [(0, 0), (0, 1), (1, 1)]),
                ("move", [(0, 0.5), (0.7, 0.5)])
            ],
            'G': [
                ("move", [(1, 0.2), (0.8, 0), (0.2, 0), (0, 0.2), (0, 0.8), (0.2, 1), (0.8, 1), (1, 0.8), (1, 0.5), (0.5, 0.5)])
            ],
            'H': [
                ("move", [(0, 0), (0, 1)]),
                ("move", [(1, 0), (1, 1)]),
                ("move", [(0, 0.5), (1, 0.5)])
            ],
            'I': [
                ("move", [(0.5, 0), (0.5, 1)]),
                ("move", [(0.3, 0), (0.7, 0)]),
                ("move", [(0.3, 1), (0.7, 1)])
            ],
            'J': [
                ("move", [(0, 0.2), (0.2, 0), (0.8, 0), (1, 0.2), (1, 1)])
            ],
            'K': [
                ("move", [(0, 0), (0, 1)]),
                ("move", [(0, 0.5), (1, 1)]),
                ("move", [(0, 0.5), (1, 0)])
            ],
            'L': [
                ("move", [(0, 1), (0, 0), (1, 0)])
            ],
            'M': [
                ("move", [(0, 0), (0, 1), (0.5, 0.5), (1, 1), (1, 0)])
            ],
            'N': [
                ("move", [(0, 0), (0, 1), (1, 0), (1, 1)])
            ],
            'O': [
                ("move", [(0.2, 0), (0.8, 0), (1, 0.2), (1, 0.8), (0.8, 1), (0.2, 1), (0, 0.8), (0, 0.2), (0.2, 0)])
            ],
            'P': [
                ("move", [(0, 0), (0, 1), (0.8, 1), (1, 0.8), (1, 0.6), (0.8, 0.5), (0, 0.5)])
            ],
            'Q': [
                ("move", [(0.2, 0), (0.8, 0), (1, 0.2), (1, 0.8), (0.8, 1), (0.2, 1), (0, 0.8), (0, 0.2), (0.2, 0)]),
                ("move", [(0.6, 0.4), (1, 0)])
            ],
            'R': [
                ("move", [(0, 0), (0, 1), (0.8, 1), (1, 0.8), (1, 0.6), (0.8, 0.5), (0, 0.5)]),
                ("move", [(0.5, 0.5), (1, 0)])
            ],
            'S': [
                ("move", [(1, 0.2), (0.8, 0), (0.2, 0), (0, 0.2), (0, 0.4), (0.2, 0.5), (0.8, 0.5), (1, 0.6), (1, 0.8), (0.8, 1), (0.2, 1), (0, 0.8)])
            ],
            'T': [
                ("move", [(0.5, 0), (0.5, 1)]),
                ("move", [(0, 1), (1, 1)])
            ],
            'U': [
                ("move", [(0, 1), (0, 0.2), (0.2, 0), (0.8, 0), (1, 0.2), (1, 1)])
            ],
            'V': [
                ("move", [(0, 1), (0.5, 0), (1, 1)])
            ],
            'W': [
                ("move", [(0, 1), (0.2, 0), (0.5, 0.5), (0.8, 0), (1, 1)])
            ],
            'X': [
                ("move", [(0, 0), (1, 1)]),
                ("move", [(0, 1), (1, 0)])
            ],
            'Y': [
                ("move", [(0, 1), (0.5, 0.5), (1, 1)]),
                ("move", [(0.5, 0.5), (0.5, 0)])
            ],
            'Z': [
                ("move", [(0, 1), (1, 1), (0, 0), (1, 0)])
            ],
            'm': [
                ("move", [(0, 0), (0, 0.5), (0.2, 0.6), (0.4, 0.5), (0.4, 0), (0.4, 0.5), (0.6, 0.6), (0.8, 0.5), (0.8, 0)])
            ],
            '/': [
                ("move", [(0, 0), (1, 1)])
            ],
            ' ': [
                # Space - no vectors
            ],
            '-': [
                ("move", [(0.2, 0.5), (0.8, 0.5)])
            ],
            '+': [
                ("move", [(0.5, 0.2), (0.5, 0.8)]),
                ("move", [(0.2, 0.5), (0.8, 0.5)])
            ],
            ':': [
                ("move", [(0.5, 0.25), (0.5, 0.35)]),
                ("move", [(0.5, 0.65), (0.5, 0.75)])
            ],
            ',': [
                ("move", [(0.5, 0.1), (0.3, -0.1)])
            ],
            '(': [
                ("move", [(0.6, 0), (0.4, 0.2), (0.4, 0.8), (0.6, 1)])
            ],
            ')': [
                ("move", [(0.4, 0), (0.6, 0.2), (0.6, 0.8), (0.4, 1)])
            ],
        }
        
        return char_vectors
    
    def configure(self, **kwargs):
        """Configure the generator with user-specified parameters"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                # Special handling for parameter_start and parameter_step dictionaries
                if key in ["parameter_start", "parameter_step"] and isinstance(value, dict):
                    for param, val in value.items():
                        getattr(self, key)[param] = val
                else:
                    setattr(self, key, value)
            else:
                print(f"Warning: Unknown parameter '{key}'")
        return self


# Example usage
if __name__ == "__main__":
    generator = CNCCalibrationGenerator()
    
    # Configure the generator with simplified parameter syntax
    generator.configure(
        pattern_width=1.5,
        pattern_height=2.5,
        patterns_x=12,
        patterns_y=12,
        spacing_x=0.5,
        spacing_y=0.5,
        bit_width=0.3,  # 1/8 inch
        operation_type="pocket",
        pocket_pattern="contour",  # Using contour fill pattern
        cutting_depth=0.3, 
        
        # Varying parameters
        x_parameter="spindle_speed",
        y_parameter="feed_rate",
        
        # Simplified parameter configuration
        parameter_start={
            "spindle_speed": 6000,
            "feed_rate": 400
        },
        parameter_step={
            "spindle_speed": 500,
            "feed_rate": 50
        },
        
        # Common parameters
        spindle_speed=12000,
        
        # Label configuration
        include_labels=True,
        label_depth=0.1,
        label_feed_rate=250,
        label_spindle_speed=15000,
        label_bit_width=0.1,
        label_plunge_rate=100,
        label_char_width=1,
        label_char_height=1.5,
        label_char_spacing=0.2,
        label_name_offset=18.0
    )
    
    # Generate the G-code
    gcode = generator.generate_gcode()
    print(f"G-code generated and saved to {generator.output_file}")
    
    # Print a sample of the G-code
    print("\nSample of generated G-code:")
    print("\n".join(gcode.split("\n")[:30]))