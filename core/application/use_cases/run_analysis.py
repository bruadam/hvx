"""Use case for running IEQ analysis."""

from typing import Any

from core.analytics.aggregators.building_aggregator import BuildingAggregator
from core.analytics.engine.analysis_engine import AnalysisEngine
from core.domain.models.building import Building
from core.domain.models.building_analysis import BuildingAnalysis
from core.domain.models.room import Room
from core.domain.models.room_analysis import RoomAnalysis


class RunAnalysisUseCase:
    """Use case for running IEQ analysis on rooms and buildings."""

    def __init__(self):
        """Initialize use case."""
        self.analysis_engine = AnalysisEngine()
        self.building_aggregator = BuildingAggregator()

    def execute_room_analysis(
        self,
        room: Room,
        tests: list[dict[str, Any]],
        apply_filters: bool = True,
    ) -> RoomAnalysis:
        """
        Run analysis on a single room.

        Args:
            room: Room entity with time series data
            tests: List of test configurations
            apply_filters: Whether to apply time filters

        Returns:
            RoomAnalysis with results

        Raises:
            ValueError: If room has no data or tests are invalid
        """
        if not room.has_data:
            raise ValueError(f"Room {room.name} has no data to analyze")

        return self.analysis_engine.analyze_room(
            room=room,
            tests=tests,
            apply_filters=apply_filters,
        )

    def execute_building_analysis(
        self,
        building: Building,
        room_analyses: list[RoomAnalysis],
    ) -> BuildingAnalysis:
        """
        Aggregate room analyses into building analysis.

        Args:
            building: Building entity
            room_analyses: List of room analysis results

        Returns:
            BuildingAnalysis with aggregated metrics

        Raises:
            ValueError: If no room analyses provided
        """
        if not room_analyses:
            raise ValueError("No room analyses provided for building aggregation")

        return self.building_aggregator.aggregate(
            building=building,
            room_analyses=room_analyses,
        )

    def execute_batch_analysis(
        self,
        rooms: list[Room],
        tests: list[dict[str, Any]],
        apply_filters: bool = True,
    ) -> list[RoomAnalysis]:
        """
        Run analysis on multiple rooms.

        Args:
            rooms: List of room entities
            tests: List of test configurations
            apply_filters: Whether to apply time filters

        Returns:
            List of RoomAnalysis results

        Raises:
            ValueError: If no rooms or tests provided
        """
        if not rooms:
            raise ValueError("No rooms provided for analysis")
        if not tests:
            raise ValueError("No tests provided for analysis")

        room_analyses = []
        for room in rooms:
            try:
                analysis = self.execute_room_analysis(room, tests, apply_filters)
                room_analyses.append(analysis)
            except Exception as e:
                # Log error but continue with other rooms
                print(f"Warning: Failed to analyze {room.name}: {e}")
                continue

        return room_analyses
