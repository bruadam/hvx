"""TAIL Rating Circular Chart - Enhanced version inspired by TAIL Rating Scheme.

Reference: https://github.com/asitkm76/TAILRatingScheme
TAIL = Thermal, Acoustic, Indoor Air Quality, Luminous

The TAIL rating uses 4 colors (Green, Yellow, Orange, Red) to show
environmental quality, with Roman numerals I-IV for overall rating.

Enhanced with:
- Hierarchical structure (IAQ subdivided into parameters)
- Gray color for non-computed values
- White dividers between segments
- Clean design without axes
- Better visual hierarchy
"""

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.patches as patches
import numpy as np
from typing import Dict, Optional, Tuple, List
from pathlib import Path


class TAILCircularChart:
    """Generate enhanced circular TAIL rating visualization per building."""
    
    # Color scheme matching TAIL
    COLORS = {
        1: "#66BB6A",  # Green - Best (slightly deeper)
        2: "#FFD54F",  # Yellow - Good (amber)
        3: "#FF9800",  # Orange - Fair (material orange)
        4: "#EF5350",  # Red - Poor (material red)
        None: "#BDBDBD"  # Gray - Not measured (material gray)
    }
    
    ROMAN_NUMERALS = {1: "I", 2: "II", 3: "III", 4: "IV"}
    
    # IAQ sub-parameters mapping
    IAQ_PARAMETERS = {
        "CO2": "CO₂",
        "co2": "CO₂",
        "Humid": "RH",
        "humid": "RH",
        "humidity": "RH",
        "PM2.5": "PM2.5",
        "pm2.5": "PM2.5",
        "pm25": "PM2.5",
        "VOC": "VOC",
        "voc": "VOC",
        "Formaldehyde": "HCHO",
        "formaldehyde": "HCHO",
        "Radon": "Radon",
        "radon": "Radon",
        "Ventilation": "Vent",
        "ventilation": "Vent",
        "Mold": "Mold",
        "mold": "Mold"
    }
    
    def __init__(self, figsize: Tuple[float, float] = (10, 10)):
        """
        Initialize TAIL circular chart.
        
        Args:
            figsize: Figure size as (width, height)
        """
        self.figsize = figsize
        self.divider_color = 'white'
        self.divider_width = 3
        self.label_line_length = 0.4  # Length of label connector lines
        self.label_distance = 4.2  # Distance for outer labels
        
    def create(
        self,
        overall_rating: Optional[int],
        thermal_rating: Optional[int] = None,
        acoustic_rating: Optional[int] = None,
        iaq_rating: Optional[int] = None,
        luminous_rating: Optional[int] = None,
        thermal_details: Optional[Dict[str, Optional[int]]] = None,
        acoustic_details: Optional[Dict[str, Optional[int]]] = None,
        iaq_details: Optional[Dict[str, Optional[int]]] = None,
        luminous_details: Optional[Dict[str, Optional[int]]] = None,
        building_name: str = "Building",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        save_path: Optional[Path] = None
    ) -> Figure:
        """
        Create enhanced TAIL circular rating chart with hierarchical structure.
        
        Args:
            overall_rating: Overall TAIL rating (1-4)
            thermal_rating: Thermal component rating
            acoustic_rating: Acoustic component rating
            iaq_rating: Indoor Air Quality rating
            luminous_rating: Luminous (lighting) rating
            thermal_details: Dict of thermal sub-parameter ratings
            acoustic_details: Dict of acoustic sub-parameter ratings
            iaq_details: Dict of IAQ sub-parameter ratings (CO2, RH, PM2.5, etc.)
            luminous_details: Dict of luminous sub-parameter ratings
            building_name: Name of building
            date_from: Start date of analysis period
            date_to: End date of analysis period
            save_path: Optional path to save figure
            
        Returns:
            Matplotlib figure
        """
        # Create figure with white background
        fig, ax = plt.subplots(
            figsize=self.figsize,
            subplot_kw={'aspect': 'equal'},
            facecolor='white'
        )
        ax.set_facecolor('white')

        # Ring 1: Overall TAIL rating (center circle - slightly bigger)
        self._draw_center_circle(ax, overall_rating)

        # Ring 2: T, A, I, L components (4 quadrants - no component labels)
        components = [
            ("T", thermal_rating, 0, 90, "Thermal"),
            ("L", luminous_rating, 90, 180, "Luminous"),
            ("I", iaq_rating, 180, 270, "IAQ"),
            ("A", acoustic_rating, 270, 360, "Acoustic"),
        ]

        for label, rating, start, end, full_name in components:
            self._draw_component_segment(
                ax=ax,
                r_inner=1.2,
                r_outer=2.2,
                start_angle=start,
                end_angle=end,
                rating=rating,
                label=label,
                full_name=full_name,
                    show_labels=False  # Don't show component labels
            )

        # Draw hierarchical details (sub-parameters)
        label_info = self._draw_hierarchical_details(
            ax,
            thermal_details=thermal_details,
            acoustic_details=acoustic_details,
            iaq_details=iaq_details,
            luminous_details=luminous_details
        )

        # Draw external labels
        self._draw_external_labels(ax, label_info)

        # Add title and subtitle
        title = building_name
        if date_from and date_to:
            title += f" ({date_from} to {date_to})"
        ax.set_title(title, fontsize=16, fontweight='bold', color='#333333', pad=24)

        # Add horizontal legend
        self._add_horizontal_legend(fig)

        # Save if path provided
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')

        return fig  # Ensure a Figure is always returned


    
    
    def _draw_center_circle(self, ax: Axes, rating: Optional[int]):
        """Draw the center circle with overall TAIL rating (slightly bigger)."""
        color = self.COLORS.get(rating, self.COLORS[None])
        roman = self.ROMAN_NUMERALS.get(rating, "?") if rating else "?"
        
        # Draw circle - slightly bigger (1.3 instead of 1.0)
        circle = patches.Circle(
            (0, 0),
            1.3,
            facecolor=color,
            edgecolor=self.divider_color,
            linewidth=self.divider_width,
            zorder=2
        )
        ax.add_patch(circle)
        
        # Add label
        ax.text(
            0, 0, roman,
            ha='center', va='center',
            fontsize=36,
            fontweight='bold',
            color='white' if rating and rating > 2 else '#333333',
            zorder=3
        )
    
    def _draw_component_segment(
        self,
        ax: Axes,
        r_inner: float,
        r_outer: float,
        start_angle: float,
        end_angle: float,
        rating: Optional[int],
        label: str,
        full_name: str,
        show_labels: bool = True
    ):
        """Draw a component segment (T, A, I, or L) with optional labels."""
        color = self.COLORS.get(rating, self.COLORS[None])
        
        # Create wedge
        theta = np.linspace(
            np.radians(start_angle),
            np.radians(end_angle),
            100
        )
        
        # Outer arc
        x_outer = r_outer * np.cos(theta)
        y_outer = r_outer * np.sin(theta)
        
        # Inner arc  
        x_inner = r_inner * np.cos(theta)
        y_inner = r_inner * np.sin(theta)
        
        # Create vertices for polygon
        vertices = np.column_stack([
            np.concatenate([x_outer, x_inner[::-1]]),
            np.concatenate([y_outer, y_inner[::-1]])
        ])
        
        # Draw polygon
        polygon = patches.Polygon(
            vertices,
            facecolor=color,
            edgecolor=self.divider_color,
            linewidth=self.divider_width,
            zorder=1
        )
        ax.add_patch(polygon)
        
        # Only add labels if requested (we don't want them)
        if show_labels:
            # Add label - large letter
            label_angle = np.radians((start_angle + end_angle) / 2)
            label_r = (r_inner + r_outer) / 2
            label_x = label_r * np.cos(label_angle)
            label_y = label_r * np.sin(label_angle)
            
            text_color = 'white' if rating and rating > 2 else '#333333'
            
            ax.text(
                label_x, label_y, label,
                ha='center', va='center',
                fontsize=20,
                fontweight='bold',
                color=text_color,
                zorder=2
            )
    
    def _draw_hierarchical_details(
        self,
        ax: Axes,
        thermal_details: Optional[Dict[str, Optional[int]]],
        acoustic_details: Optional[Dict[str, Optional[int]]],
        iaq_details: Optional[Dict[str, Optional[int]]],
        luminous_details: Optional[Dict[str, Optional[int]]]
    ) -> list:
        """
        Draw outer ring with hierarchical parameter details.
        Returns list of label info for external drawing.
        """
        # Define quadrants for each component
        quadrants = [
            (thermal_details, 0, 90, "T"),
            (luminous_details, 90, 180, "L"),
            (iaq_details, 180, 270, "I"),
            (acoustic_details, 270, 360, "A"),
        ]
        
        r_inner = 2.4
        r_outer = 3.6
        
        label_info = []  # Collect label info for external drawing
        
        for details, start_angle, end_angle, component in quadrants:
            if details and len(details) > 0:
                # Divide quadrant among parameters
                params = list(details.items())
                n_params = len(params)
                angle_range = end_angle - start_angle
                angle_per_param = angle_range / n_params
                
                for i, (param_name, rating) in enumerate(params):
                    param_start = start_angle + i * angle_per_param
                    param_end = start_angle + (i + 1) * angle_per_param
                    
                    # Clean up parameter name
                    short_name = self.IAQ_PARAMETERS.get(param_name, param_name)
                    if len(short_name) > 8:
                        short_name = short_name[:7] + "."
                    
                    # Draw segment without internal label
                    self._draw_detail_segment(
                        ax=ax,
                        r_inner=r_inner,
                        r_outer=r_outer,
                        start_angle=param_start,
                        end_angle=param_end,
                        rating=rating,
                        label=""  # Don't draw label inside
                    )
                    
                    # Store label info for external drawing
                    mid_angle = (param_start + param_end) / 2
                    label_info.append({
                        'name': short_name,
                        'angle': mid_angle,
                        'rating': rating,
                        'r_outer': r_outer
                    })
            else:
                # Draw empty segment if no details
                self._draw_detail_segment(
                    ax=ax,
                    r_inner=r_inner,
                    r_outer=r_outer,
                    start_angle=start_angle,
                    end_angle=end_angle,
                    rating=None,
                    label=""
                )
        
        return label_info
    
    def _draw_detail_segment(
        self,
        ax: Axes,
        r_inner: float,
        r_outer: float,
        start_angle: float,
        end_angle: float,
        rating: Optional[int],
        label: str
    ):
        """Draw a single detail parameter segment (no internal label)."""
        color = self.COLORS.get(rating, self.COLORS[None])
        
        # Create wedge
        theta = np.linspace(
            np.radians(start_angle),
            np.radians(end_angle),
            50
        )
        
        # Outer arc
        x_outer = r_outer * np.cos(theta)
        y_outer = r_outer * np.sin(theta)
        
    # (stray/incorrect line removed)
        x_inner = r_inner * np.cos(theta)
        y_inner = r_inner * np.sin(theta)
        
        # Create vertices for polygon
        vertices = np.column_stack([
            np.concatenate([x_outer, x_inner[::-1]]),
            np.concatenate([y_outer, y_inner[::-1]])
        ])
        
        # Draw polygon
        polygon = patches.Polygon(
            vertices,
            facecolor=color,
            edgecolor=self.divider_color,
            linewidth=self.divider_width,
            zorder=0
        )
        ax.add_patch(polygon)
        
        # No internal labels - will be drawn externally
    
    
    def _draw_external_labels(self, ax: Axes, label_info: list):
        """Draw parameter labels outside the circle with connector lines."""
        for info in label_info:
            angle_rad = np.radians(info['angle'])
            r_outer = info['r_outer']
            name = info['name']
            
            # Start point (edge of outer ring)
            x_start = r_outer * np.cos(angle_rad)
            y_start = r_outer * np.sin(angle_rad)
            
            # End point (label position - further out)
            x_end = self.label_distance * np.cos(angle_rad)
            y_end = self.label_distance * np.sin(angle_rad)
            
            # Draw connector line
            ax.plot(
                [x_start, x_end],
                [y_start, y_end],
                color='#999999',
                linewidth=0.8,
                zorder=1,
                alpha=0.6
            )
            
            # Determine text alignment based on angle
            # Left side (90-270 degrees) = right align, Right side = left align
            if 90 < info['angle'] < 270:
                ha = 'right'
                label_x = x_end - 0.1
            else:
                ha = 'left'
                label_x = x_end + 0.1
            
            # Draw label (horizontal, not rotated)
            ax.text(
                label_x, y_end, name,
                ha=ha, va='center',
                fontsize=9,
                color='#333333',
                zorder=2
            )
    
    def _add_horizontal_legend(self, fig: Figure):
        """Add horizontal legend below chart with 5 columns."""
        legend_elements = [
            patches.Patch(
                facecolor=self.COLORS[1],
                edgecolor='white',
                linewidth=2,
                label='I - Excellent (≥95%)'
            ),
            patches.Patch(
                facecolor=self.COLORS[2],
                edgecolor='white',
                linewidth=2,
                label='II - Good (70-95%)'
            ),
            patches.Patch(
                facecolor=self.COLORS[3],
                edgecolor='white',
                linewidth=2,
                label='III - Fair (50-70%)'
            ),
            patches.Patch(
                facecolor=self.COLORS[4],
                edgecolor='white',
                linewidth=2,
                label='IV - Poor (<50%)'
            ),
            patches.Patch(
                facecolor=self.COLORS[None],
                edgecolor='white',
                linewidth=2,
                label='Not Measured'
            ),
        ]
        
        # Add legend at bottom center, horizontal, 5 columns
        legend = fig.legend(
            handles=legend_elements,
            loc='lower center',
            ncol=5,
            fontsize=9,
            frameon=True,
            fancybox=False,
            shadow=False,
            borderpad=0.8,
            columnspacing=1.5,
            bbox_to_anchor=(0.5, -0.02)
        )
        
        # Style the legend
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_edgecolor('#CCCCCC')
        legend.get_frame().set_linewidth(1)
    
    def _add_enhanced_legend(self, ax: Axes):
        """Add enhanced color legend to plot (deprecated - use horizontal)."""
        legend_elements = [
            patches.Patch(
                facecolor=self.COLORS[1],
                edgecolor='white',
                linewidth=2,
                label='I - Excellent (≥95%)'
            ),
            patches.Patch(
                facecolor=self.COLORS[2],
                edgecolor='white',
                linewidth=2,
                label='II - Good (70-95%)'
            ),
            patches.Patch(
                facecolor=self.COLORS[3],
                edgecolor='white',
                linewidth=2,
                label='III - Fair (50-70%)'
            ),
            patches.Patch(
                facecolor=self.COLORS[4],
                edgecolor='white',
                linewidth=2,
                label='IV - Poor (<50%)'
            ),
            patches.Patch(
                facecolor=self.COLORS[None],
                edgecolor='white',
                linewidth=2,
                label='Not Measured'
            ),
        ]
        
        legend = ax.legend(
            handles=legend_elements,
            loc='upper left',
            bbox_to_anchor=(1.02, 1),
            fontsize=9,
            frameon=True,
            fancybox=False,
            shadow=False,
            borderpad=1,
            labelspacing=0.8
        )
        
        # Style the legend
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_edgecolor('#CCCCCC')
        legend.get_frame().set_linewidth(1)


class TAILRatingCalculator:
    """Calculate TAIL ratings from IEQ analysis results."""
    
    @staticmethod
    def calculate_from_building_analysis(
        building_analysis,
        room_analyses: list
    ) -> Dict[str, Optional[int]]:
        """
        Calculate TAIL ratings from building analysis.
        
        Args:
            building_analysis: BuildingAnalysis object
            room_analyses: List of RoomAnalysis objects
            
        Returns:
            Dict with TAIL ratings
        """
        # Calculate overall rating (1-4) based on compliance
        overall_compliance = building_analysis.avg_compliance_rate
        overall_rating = TAILRatingCalculator._compliance_to_rating(overall_compliance)
        
        # For now, use overall compliance for all components
        # In full implementation, would calculate each separately
        ratings = {
            "overall": overall_rating,
            "thermal": overall_rating,  # Based on temperature compliance
            "acoustic": None,  # Would need noise data
            "iaq": overall_rating,  # Based on CO2, humidity, etc.
            "luminous": None,  # Would need illuminance data
        }
        
        # Add detailed ratings
        detailed = {}
        if room_analyses:
            # Aggregate parameter ratings from rooms
            for ra in room_analyses:
                for test_id, result in ra.compliance_results.items():
                    param = result.parameter.value
                    param_rating = TAILRatingCalculator._compliance_to_rating(
                        result.compliance_rate
                    )
                    # Use worst rating across rooms
                    if param not in detailed:
                        detailed[param] = param_rating
                    else:
                        detailed[param] = max(detailed[param], param_rating)
        
        ratings["detailed"] = detailed
        
        return ratings
    
    @staticmethod
    def _compliance_to_rating(compliance_rate: float) -> int:
        """
        Convert compliance percentage to TAIL rating (1-4).
        
        Args:
            compliance_rate: Compliance percentage (0-100)
            
        Returns:
            Rating from 1 (best) to 4 (worst)
        """
        if compliance_rate >= 95:
            return 1  # Green
        elif compliance_rate >= 70:
            return 2  # Yellow
        elif compliance_rate >= 50:
            return 3  # Orange
        else:
            return 4  # Red


def create_tail_chart_for_building(
    building_analysis,
    room_analyses: list,
    building_name: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    output_path: Optional[Path] = None
) -> Figure:
    """
    Convenience function to create enhanced TAIL chart from analysis results.
    
    Args:
        building_analysis: BuildingAnalysis object
        room_analyses: List of RoomAnalysis objects
        building_name: Name of building
        date_from: Start date of analysis period
        date_to: End date of analysis period
        output_path: Optional path to save figure
        
    Returns:
        Matplotlib figure
    """
    # Calculate ratings
    ratings = TAILRatingCalculator.calculate_from_building_analysis(
        building_analysis, room_analyses
    )
    
    # Organize detailed ratings by component
    detailed = ratings.get("detailed", {})
    
    # Categorize parameters
    thermal_details = {}
    acoustic_details = {}
    iaq_details = {}
    luminous_details = {}
    
    if isinstance(detailed, dict):
        for param, rating in detailed.items():
            param_lower = param.lower()
            if "temp" in param_lower or "thermal" in param_lower:
                thermal_details[param] = rating
            elif "noise" in param_lower or "acoustic" in param_lower or "sound" in param_lower:
                acoustic_details[param] = rating
            elif "lux" in param_lower or "light" in param_lower or "illumin" in param_lower or "daylight" in param_lower:
                luminous_details[param] = rating
            else:
                # Default to IAQ
                iaq_details[param] = rating
    
    # Create chart
    chart = TAILCircularChart(figsize=(12, 10))
    fig = chart.create(
        overall_rating=ratings.get("overall"),
        thermal_rating=ratings.get("thermal"),
        acoustic_rating=ratings.get("acoustic"),
        iaq_rating=ratings.get("iaq"),
        luminous_rating=ratings.get("luminous"),
        thermal_details=thermal_details if thermal_details else None,
        acoustic_details=acoustic_details if acoustic_details else None,
        iaq_details=iaq_details if iaq_details else None,
        luminous_details=luminous_details if luminous_details else None,
        building_name=building_name,
        date_from=date_from,
        date_to=date_to,
        save_path=output_path
    )
    
    return fig

    # Fallback (should never be reached, but for type checker)
    return plt.figure()
