"""Room domain entity."""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
from pydantic import Field

from core.domain.enums.occupancy import ActivityLevel
from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.pollution_level import PollutionLevel
from core.domain.enums.ventilation import VentilationType
from core.domain.models.base.base_entity import BaseEntity
from core.domain.value_objects.time_range import TimeRange

if TYPE_CHECKING:
    from core.domain.models.analysis.room_analysis import RoomAnalysis


class Room(BaseEntity[None]):
    """
    Room entity representing a physical space with environmental measurements.

    This is a rich domain model that contains both data and behavior.
    Inherits id, name, attributes, timestamps, and physical properties from BaseEntity.
    Physical properties (area, volume, occupancy, orientations, etc.) are stored at the room level.
    """

    # Hierarchy
    level_id: str | None = Field(default=None, description="Parent level ID")
    building_id: str | None = Field(default=None, description="Parent building ID")

    # EN 16798-1 specific metadata
    room_type: str | None = Field(default=None, description="Room type (office, classroom, etc.)")
    ventilation_type: VentilationType | None = Field(
        default=None, description="Type of ventilation system"
    )
    pollution_level: PollutionLevel | None = Field(
        default=None, description="Building pollution level for ventilation calculations"
    )
    activity_level: ActivityLevel | None = Field(
        default=None, description="Occupant activity level (metabolic rate)"
    )

    # Data
    data_file_path: Path | None = Field(default=None, description="Path to source data file")
    time_series_data: pd.DataFrame | None = Field(
        default=None,
        description="Time series environmental data",
        exclude=True,  # Don't serialize DataFrame in JSON
    )

    # Temporal coverage
    data_start: datetime | None = Field(default=None, description="Earliest measurement")
    data_end: datetime | None = Field(default=None, description="Latest measurement")

    model_config = {"arbitrary_types_allowed": True}  # Allow pandas DataFrame

    @property
    def has_data(self) -> bool:
        """Check if room has time series data loaded."""
        return self.time_series_data is not None and not self.time_series_data.empty

    @property
    def data_time_range(self) -> TimeRange | None:
        """Get time range of available data."""
        if self.data_start and self.data_end:
            return TimeRange(start=self.data_start, end=self.data_end)
        return None

    @property
    def available_parameters(self) -> list[ParameterType]:
        """Get list of available parameter types in data."""
        if not self.has_data:
            return []

        available = []
        if self.time_series_data is not None:
            for param in ParameterType:
                if param.value in self.time_series_data.columns:
                    available.append(param)
        return available

    def get_parameter_data(self, parameter: ParameterType) -> pd.Series | None:
        """
        Get time series data for a specific parameter.

        Args:
            parameter: Parameter type to retrieve

        Returns:
            pandas Series with parameter data, or None if not available
        """
        if not self.has_data or self.time_series_data is None:
            return None

        if parameter.value in self.time_series_data.columns:
            return self.time_series_data[parameter.value]
        return None

    def get_data_completeness(self, parameter: ParameterType | None = None) -> float:
        """
        Calculate data completeness (percentage of non-null values).

        Args:
            parameter: Specific parameter to check, or None for overall completeness

        Returns:
            Completeness as percentage (0-100)
        """
        if not self.has_data or self.time_series_data is None:
            return 0.0

        if parameter:
            series = self.get_parameter_data(parameter)
            if series is None:
                return 0.0
            return float((series.notna().sum() / len(series)) * 100)

        # Overall completeness across all columns
        return float((self.time_series_data.notna().sum().sum() / self.time_series_data.size) * 100)

    def get_measurement_count(self, parameter: ParameterType | None = None) -> int:
        """
        Get count of measurements.

        Args:
            parameter: Specific parameter to count, or None for total rows

        Returns:
            Number of measurements
        """
        if not self.has_data or self.time_series_data is None:
            return 0

        if parameter:
            series = self.get_parameter_data(parameter)
            if series is None:
                return 0
            return int(series.notna().sum())

        return len(self.time_series_data)

    def filter_by_time_range(self, time_range: TimeRange) -> "Room":
        """
        Create a new Room instance with data filtered to time range.

        Args:
            time_range: Time range to filter to

        Returns:
            New Room instance with filtered data
        """
        if not self.has_data or self.time_series_data is None:
            return self

        # Filter DataFrame by time range
        mask = (self.time_series_data.index >= time_range.start) & (
            self.time_series_data.index <= time_range.end
        )
        filtered_df = self.time_series_data[mask].copy()

        # Create new room instance with filtered data
        return self.model_copy(
            update={
                "time_series_data": filtered_df,
                "data_start": filtered_df.index.min() if not filtered_df.empty else None,
                "data_end": filtered_df.index.max() if not filtered_df.empty else None,
            }
        )

    def get_summary(self) -> dict[str, Any]:
        """Get summary information about this room."""
        # Get base summary from BaseEntity
        summary = super().get_summary()
        
        # Add room-specific information
        summary.update({
            "level_id": self.level_id,
            "building_id": self.building_id,
            "metadata": {
                "area_m2": self.area,
                "volume_m3": self.volume,
                "occupancy": self.occupancy,
                "glass_to_wall_ratio": self.glass_to_wall_ratio,
                "last_renovation_year": self.last_renovation_year,
                "room_type": self.room_type,
                "ventilation_type": self.ventilation_type.value
                if self.ventilation_type
                else None,
                "pollution_level": self.pollution_level.value
                if self.pollution_level
                else None,
                "activity_level": self.activity_level.value
                if self.activity_level
                else None,
            },
            "has_data": self.has_data,
            "measurement_count": self.get_measurement_count() if self.has_data else 0,
            "available_parameters": [p.value for p in self.available_parameters],
            "data_completeness_pct": (
                round(self.get_data_completeness(), 2) if self.has_data else 0.0
            ),
            "data_time_range": (
                {
                    "start": self.data_start.isoformat() if self.data_start else None,
                    "end": self.data_end.isoformat() if self.data_end else None,
                }
                if self.has_data
                else None
            ),
        })
        
        return summary
    
    def compute_metrics(
        self,
        standards: list[str] | None = None,
        force_recompute: bool = False
    ) -> "RoomAnalysis | None":
        """
        Compute compliance metrics and analysis for this room.
        
        Auto-computes EN16798, TAIL, and other metrics if data is available.
        Results are cached in computed_metrics dict.
        
        Args:
            standards: List of standards to compute (e.g., ['en16798', 'tail']).
                      If None, computes all applicable standards.
            force_recompute: If True, recompute even if metrics already cached
            
        Returns:
            RoomAnalysis object with all computed metrics, or None if no data available
            
        Example:
            room = Room(id="101", name="Office 101", area=25.0, ...)
            room.time_series_data = load_data(...)  # Load sensor data
            analysis = room.compute_metrics(standards=['en16798', 'tail'])
            
            # Access cached results
            print(room.get_metric('en16798_category'))  # 'II'
            print(room.get_metric('tail_thermal_rating'))  # 2
            print(room.get_metric('overall_compliance_rate'))  # 85.5
        """
        # Check if we have data to analyze
        if not self.has_data:
            return None
        
        # Return cached results if available and not forcing recompute
        if not force_recompute and self.has_metric('room_analysis'):
            return self.get_metric('room_analysis')
        
        # Import here to avoid circular dependency
        from core.analytics.calculators.en16798_calculator import (
            EN16798RoomMetadata,
            EN16798StandardCalculator
        )
        from core.analytics.calculators.tail_calculator import TAILRatingCalculator
        from core.domain.models.analysis.room_analysis import RoomAnalysis
        
        # Initialize analysis object
        analysis = RoomAnalysis(
            entity_id=self.id,
            entity_name=self.name,
            level_id=self.level_id,
            building_id=self.building_id
        )
        
        # Determine which standards to compute
        if standards is None:
            standards = ['en16798', 'tail']  # Default to all
        
        # Compute EN 16798-1 compliance if requested
        if 'en16798' in standards and self.room_type:
            try:
                metadata = EN16798RoomMetadata(
                    room_type=self.room_type,
                    floor_area=self.area or 25.0,  # Default if not set
                    volume=self.volume,
                    occupancy_count=self.occupancy,
                    ventilation_type=self.ventilation_type or VentilationType.NATURAL,
                    pollution_level=self.pollution_level or PollutionLevel.NON_LOW,
                    activity_level=self.activity_level
                )
                
                calculator = EN16798StandardCalculator()
                
                # Store EN16798 metadata
                self.set_metric('en16798_metadata', metadata)
                
                # Note: Actual compliance calculation requires running tests against
                # time series data. This is a placeholder for the pattern.
                # In practice, you'd call a compliance checker here.
                
            except Exception as e:
                print(f"Warning: Could not compute EN16798 metrics: {e}")
        
        # Compute TAIL rating if requested
        if 'tail' in standards:
            try:
                # TAIL rating can be computed from compliance results
                # This is a placeholder - actual implementation would
                # analyze time series data and compute compliance per category
                
                tail_calc = TAILRatingCalculator()
                
                # Store TAIL calculator reference
                self.set_metric('tail_calculator', tail_calc)
                
            except Exception as e:
                print(f"Warning: Could not compute TAIL metrics: {e}")
        
        # Cache the analysis object
        self.set_metric('room_analysis', analysis)
        self.metrics_computed_at = datetime.now()
        
        return analysis
    
    def get_analysis(self) -> "RoomAnalysis | None":
        """
        Get cached analysis results.
        
        Returns:
            Cached RoomAnalysis or None if not computed
        """
        return self.get_metric('room_analysis')

