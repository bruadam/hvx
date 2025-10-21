"""Style configuration loader for matplotlib graphs in clean architecture."""

import yaml
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache


class StyleLoader:
    """Load and apply matplotlib style configurations."""

    def __init__(self):
        # Look for config in clean/config/charts/
        self.config_dir = Path(__file__).parent.parent.parent / "config" / "charts"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._global_style = None
        self._chart_styles = {}

    @lru_cache(maxsize=None)
    def load_global_style(self) -> Dict[str, Any]:
        """Load global style configuration."""
        if self._global_style is None:
            config_path = self.config_dir / "global_style.yaml"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self._global_style = yaml.safe_load(f)
            else:
                # Use defaults if config doesn't exist
                self._global_style = self._get_default_global_style()
        return self._global_style

    @lru_cache(maxsize=None)
    def load_chart_style(self, chart_type: str) -> Dict[str, Any]:
        """Load chart-type-specific style configuration.

        Args:
            chart_type: Type of chart (bar_chart, line_chart, heatmap, compliance_chart)

        Returns:
            Chart-specific style configuration
        """
        if chart_type not in self._chart_styles:
            config_path = self.config_dir / f"{chart_type}_style.yaml"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self._chart_styles[chart_type] = yaml.safe_load(f)
            else:
                self._chart_styles[chart_type] = {}
        return self._chart_styles[chart_type]

    def get_merged_config(
        self,
        chart_type: str,
        user_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get merged configuration: global < chart-specific < user config.

        Args:
            chart_type: Type of chart
            user_config: User-provided configuration overrides

        Returns:
            Merged configuration dictionary
        """
        global_style = self.load_global_style()
        chart_style = self.load_chart_style(chart_type)

        # Deep merge: global -> chart-specific -> user
        merged = self._deep_merge(global_style, chart_style)
        if user_config:
            merged = self._deep_merge(merged, user_config)

        return merged

    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = StyleLoader._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def apply_global_style(self):
        """Apply global matplotlib style settings."""
        style = self.load_global_style()

        # Update matplotlib rcParams
        if 'font' in style:
            for key, value in style['font'].items():
                mpl.rcParams[f'font.{key}'] = value

        if 'axes' in style:
            axes_style = style['axes']
            mpl.rcParams['axes.titlesize'] = axes_style.get('titlesize', 14)
            mpl.rcParams['axes.titleweight'] = axes_style.get('titleweight', 'bold')
            mpl.rcParams['axes.labelsize'] = axes_style.get('labelsize', 12)
            mpl.rcParams['axes.labelweight'] = axes_style.get('labelweight', 'bold')
            mpl.rcParams['axes.edgecolor'] = axes_style.get('edgecolor', '#95a5a6')
            mpl.rcParams['axes.linewidth'] = axes_style.get('linewidth', 1.2)
            mpl.rcParams['axes.grid'] = axes_style.get('grid', True)
            mpl.rcParams['axes.axisbelow'] = axes_style.get('axisbelow', True)

            # Handle spines
            if 'spines' in axes_style:
                spines = axes_style['spines']
                mpl.rcParams['axes.spines.top'] = spines.get('top', False)
                mpl.rcParams['axes.spines.right'] = spines.get('right', False)
                mpl.rcParams['axes.spines.bottom'] = spines.get('bottom', True)
                mpl.rcParams['axes.spines.left'] = spines.get('left', True)

        if 'grid' in style:
            grid_style = style['grid']
            mpl.rcParams['grid.alpha'] = grid_style.get('alpha', 0.3)
            mpl.rcParams['grid.linestyle'] = grid_style.get('linestyle', '--')
            mpl.rcParams['grid.linewidth'] = grid_style.get('linewidth', 0.8)
            mpl.rcParams['grid.color'] = grid_style.get('color', '#bdc3c7')

        if 'legend' in style:
            legend_style = style['legend']
            mpl.rcParams['legend.fontsize'] = legend_style.get('fontsize', 10)
            mpl.rcParams['legend.frameon'] = legend_style.get('frameon', True)
            mpl.rcParams['legend.framealpha'] = legend_style.get('framealpha', 0.9)

        if 'lines' in style:
            lines_style = style['lines']
            mpl.rcParams['lines.linewidth'] = lines_style.get('linewidth', 2)
            mpl.rcParams['lines.markersize'] = lines_style.get('markersize', 6)

        if 'xtick' in style:
            xtick_style = style['xtick']
            mpl.rcParams['xtick.labelsize'] = xtick_style.get('labelsize', 10)
            mpl.rcParams['xtick.direction'] = xtick_style.get('direction', 'out')
            if 'major' in xtick_style:
                mpl.rcParams['xtick.major.size'] = xtick_style['major'].get('size', 5)
                mpl.rcParams['xtick.major.width'] = xtick_style['major'].get('width', 1)

        if 'ytick' in style:
            ytick_style = style['ytick']
            mpl.rcParams['ytick.labelsize'] = ytick_style.get('labelsize', 10)
            mpl.rcParams['ytick.direction'] = ytick_style.get('direction', 'out')
            if 'major' in ytick_style:
                mpl.rcParams['ytick.major.size'] = ytick_style['major'].get('size', 5)
                mpl.rcParams['ytick.major.width'] = ytick_style['major'].get('width', 1)

        if 'savefig' in style:
            savefig_style = style['savefig']
            mpl.rcParams['savefig.dpi'] = savefig_style.get('dpi', 300)
            mpl.rcParams['savefig.format'] = savefig_style.get('format', 'png')
            mpl.rcParams['savefig.bbox'] = savefig_style.get('bbox_inches', 'tight')

    def get_colors(self, key: str = 'categorical') -> list:
        """Get color palette from global style.

        Args:
            key: Color palette key (categorical, sequential, diverging)

        Returns:
            List of colors
        """
        style = self.load_global_style()
        if 'colors' in style and key in style['colors']:
            return style['colors'][key]
        return plt.rcParams['axes.prop_cycle'].by_key()['color']

    def get_figsize(self, chart_type: str, user_config: Optional[Dict] = None) -> tuple:
        """Get figure size for a chart type.

        Args:
            chart_type: Type of chart
            user_config: User configuration overrides

        Returns:
            Tuple of (width, height)
        """
        config = self.get_merged_config(chart_type, user_config)
        if 'figure' in config and 'figsize' in config['figure']:
            return tuple(config['figure']['figsize'])
        return (12, 6)  # Default

    def get_dpi(self, chart_type: str, user_config: Optional[Dict] = None) -> int:
        """Get DPI for a chart type.

        Args:
            chart_type: Type of chart
            user_config: User configuration overrides

        Returns:
            DPI value
        """
        config = self.get_merged_config(chart_type, user_config)
        if 'figure' in config and 'dpi' in config['figure']:
            return config['figure']['dpi']
        return 300  # Default

    @staticmethod
    def _get_default_global_style() -> Dict[str, Any]:
        """Get default global style configuration."""
        return {
            'font': {'family': 'sans-serif', 'size': 10},
            'axes': {
                'titlesize': 14,
                'titleweight': 'bold',
                'labelsize': 12,
                'labelweight': 'bold',
                'edgecolor': '#95a5a6',
                'linewidth': 1.2,
                'grid': True,
                'axisbelow': True,
                'spines': {'top': False, 'right': False, 'bottom': True, 'left': True}
            },
            'grid': {
                'alpha': 0.3,
                'linestyle': '--',
                'linewidth': 0.8,
                'color': '#bdc3c7'
            },
            'legend': {'fontsize': 10, 'frameon': True, 'framealpha': 0.9},
            'lines': {'linewidth': 2, 'markersize': 6},
            'xtick': {
                'labelsize': 10,
                'direction': 'out',
                'major': {'size': 5, 'width': 1}
            },
            'ytick': {
                'labelsize': 10,
                'direction': 'out',
                'major': {'size': 5, 'width': 1}
            },
            'savefig': {'dpi': 300, 'format': 'png', 'bbox_inches': 'tight'},
            'colors': {
                'categorical': ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c'],
                'sequential': ['#ecf0f1', '#bdc3c7', '#95a5a6', '#7f8c8d', '#34495e', '#2c3e50'],
                'diverging': ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#3498db']
            }
        }


# Global instance
_style_loader = StyleLoader()


def get_style_loader() -> StyleLoader:
    """Get the global style loader instance."""
    return _style_loader
