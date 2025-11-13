"""Use case for generating TAIL rating circular charts."""

from datetime import datetime
from pathlib import Path

from core.domain.models.building_analysis import BuildingAnalysis
from core.domain.models.room_analysis import RoomAnalysis
from core.reporting.charts.tail_circular_chart import (
    create_tail_chart_for_building,
)


class GenerateTAILChartUseCase:
    """Use case for generating TAIL rating circular charts for buildings."""

    def execute(
        self,
        building_analysis: BuildingAnalysis,
        room_analyses: list[RoomAnalysis],
        building_name: str,
        output_dir: Path | None = None
    ) -> Path:
        """
        Generate TAIL circular chart for a building.

        Args:
            building_analysis: BuildingAnalysis with aggregated metrics
            room_analyses: List of RoomAnalysis objects
            building_name: Name of the building
            output_dir: Directory to save chart (default: output/tail_charts)

        Returns:
            Path to saved chart
        """
        # Set default output directory
        if output_dir is None:
            output_dir = Path("output/tail_charts")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = building_name.replace(" ", "_").replace("/", "_")
        output_path = output_dir / f"{safe_name}_TAIL_{timestamp}.png"

        # Generate chart
        fig = create_tail_chart_for_building(
            building_analysis=building_analysis,
            room_analyses=room_analyses,
            building_name=building_name,
            output_path=output_path
        )

        # Close figure to free memory
        import matplotlib.pyplot as plt
        plt.close(fig)

        return output_path

    def execute_batch(
        self,
        buildings_data: list[tuple],
        output_dir: Path | None = None
    ) -> list[Path]:
        """
        Generate TAIL charts for multiple buildings.

        Args:
            buildings_data: List of (building_analysis, room_analyses, name) tuples
            output_dir: Directory to save charts

        Returns:
            List of paths to saved charts
        """
        paths = []

        for building_analysis, room_analyses, building_name in buildings_data:
            try:
                path = self.execute(
                    building_analysis=building_analysis,
                    room_analyses=room_analyses,
                    building_name=building_name,
                    output_dir=output_dir
                )
                paths.append(path)
            except Exception as e:
                print(f"Failed to generate TAIL chart for {building_name}: {e}")
                continue

        return paths
