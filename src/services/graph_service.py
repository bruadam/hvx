"""Graph Service for managing chart library and rendering."""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.graphs.renderers import (
    render_bar_chart,
    render_line_chart,
    render_heatmap,
    render_compliance_chart
)


class GraphService:
    """Service for discovering, previewing, and rendering charts."""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent / "graphs"
        self.registry_path = self.base_dir / "registry.yaml"
        self.fixtures_dir = self.base_dir / "fixtures"
        self._registry = None

    @property
    def registry(self) -> Dict:
        """Load and cache graph registry."""
        if self._registry is None:
            with open(self.registry_path, 'r') as f:
                self._registry = yaml.safe_load(f)
        return self._registry

    def list_available_charts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available charts, optionally filtered by category."""
        charts = self.registry['graphs']

        if category:
            charts = [c for c in charts if c.get('category') == category]

        return charts

    def get_chart_info(self, chart_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific chart."""
        charts = self.registry['graphs']
        for chart in charts:
            if chart['id'] == chart_id:
                return chart
        return None

    def get_categories(self) -> List[str]:
        """Get all unique chart categories."""
        charts = self.registry['graphs']
        categories = set(c.get('category', 'other') for c in charts)
        return sorted(categories)

    def _load_dummy_data(self, chart_id: str) -> Dict[str, Any]:
        """Load dummy data fixture for a chart."""
        chart_info = self.get_chart_info(chart_id)
        if not chart_info:
            raise ValueError(f"Chart '{chart_id}' not found in registry")

        fixture_file = chart_info.get('fixture')
        if not fixture_file:
            raise ValueError(f"No fixture defined for chart '{chart_id}'")

        fixture_path = self.fixtures_dir / fixture_file
        with open(fixture_path, 'r') as f:
            return json.load(f)

    def preview_with_dummy_data(
        self,
        chart_id: str,
        config: Optional[Dict] = None,
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate chart preview using dummy data."""
        # Load dummy data
        data = self._load_dummy_data(chart_id)

        # Render chart
        result = self.render_chart(
            chart_id=chart_id,
            data=data,
            config=config or {},
            output_path=output_path
        )

        return result

    def render_chart(
        self,
        chart_id: str,
        data: Dict[str, Any],
        config: Optional[Dict] = None,
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Render a chart with provided data."""
        chart_info = self.get_chart_info(chart_id)
        if not chart_info:
            raise ValueError(f"Chart '{chart_id}' not found in registry")

        # Set default output path
        if output_path is None:
            output_path = Path(f"output/charts/{chart_id}.png")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Route to appropriate renderer based on chart type
        chart_type = chart_info['type']
        config = config or {}

        if chart_type == 'bar_chart':
            render_bar_chart(data, config, output_path)
        elif chart_type == 'line_chart':
            render_line_chart(data, config, output_path)
        elif chart_type == 'heatmap':
            render_heatmap(data, config, output_path)
        elif chart_type == 'compliance_chart':
            render_compliance_chart(data, config, output_path)
        else:
            raise ValueError(f"Unknown chart type: {chart_type}")

        return {
            'chart_id': chart_id,
            'output_path': str(output_path),
            'status': 'success'
        }
