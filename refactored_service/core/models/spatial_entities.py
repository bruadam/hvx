from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import pandas as pd


class SpatialEntityType(str, Enum):
    PORTFOLIO = "portfolio"
    BUILDING = "building"
    FLOOR = "floor"
    ROOM = "room"
    ZONE = "zone"


class BrickCompatible(BaseModel):
    brick_class: Optional[str] = None
    brick_uri: Optional[str] = None
    brick_properties: Dict[str, str] = Field(default_factory=dict)


class SpatialEntity(BrickCompatible):
    """
    Spatial entity representing a location in the building hierarchy.

    Includes automated compute() methods for standards and calculators.
    """
    id: str
    name: str
    type: SpatialEntityType

    parent_id: Optional[str] = None
    child_ids: List[str] = Field(default_factory=list)

    # Physical properties
    area_m2: Optional[float] = None
    volume_m3: Optional[float] = None
    window_area_m2: Optional[float] = None
    occupancy_count: Optional[int] = None

    # Location
    country: Optional[str] = None
    region: Optional[str] = None
    climate_zone: Optional[str] = None

    # Building properties
    building_type: Optional[str] = None
    room_type: Optional[str] = None
    ventilation_type: Optional[str] = None
    pollution_level: Optional[str] = None
    construction_type: Optional[str] = "medium"

    # Timeseries data (stored as dict of parameter -> values)
    timeseries_data: Dict[str, List[float]] = Field(default_factory=dict)
    timeseries_timestamps: List[str] = Field(default_factory=list)

    # Analysis results cache
    _analysis_cache: Dict[str, Any] = Field(default_factory=dict, exclude=True)

    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def get_timeseries(self, parameter: str) -> Optional[pd.Series]:
        """Get timeseries data for a parameter as pandas Series."""
        if parameter not in self.timeseries_data:
            return None

        if not self.timeseries_timestamps:
            return pd.Series(self.timeseries_data[parameter])

        return pd.Series(
            self.timeseries_data[parameter],
            index=pd.to_datetime(self.timeseries_timestamps)
        )

    def set_timeseries(self, parameter: str, values: List[float], timestamps: Optional[List[str]] = None):
        """Set timeseries data for a parameter."""
        self.timeseries_data[parameter] = values
        if timestamps:
            self.timeseries_timestamps = timestamps

    def has_parameter(self, parameter: str) -> bool:
        """Check if entity has data for a parameter."""
        return parameter in self.timeseries_data and len(self.timeseries_data[parameter]) > 0

    def compute_en16798(
        self,
        categories: Optional[List[str]] = None,
        season: str = "heating",
        outdoor_co2: float = 400.0
    ) -> Dict[str, Any]:
        """
        Compute EN 16798-1 compliance analysis.

        Automatically uses available parameters (temperature, co2, humidity).

        Args:
            categories: List of categories to check (default: all)
            season: "heating" or "cooling"
            outdoor_co2: Outdoor CO2 concentration

        Returns:
            Dict with compliance results
        """
        from ...calculators.en16798_calculator import (
            EN16798Calculator,
            EN16798Category,
            VentilationType,
            PollutionLevel,
        )

        calc = EN16798Calculator()

        # Parse categories
        if categories is None:
            cats = list(EN16798Category)
        else:
            cats = [EN16798Category(c) for c in categories]

        # Parse ventilation type
        vent_type = VentilationType.MECHANICAL
        if self.ventilation_type:
            try:
                vent_type = VentilationType(self.ventilation_type)
            except ValueError:
                pass

        # Get timeseries
        temp = self.get_timeseries('temperature')
        co2 = self.get_timeseries('co2')
        humidity = self.get_timeseries('humidity')
        outdoor_temp = self.get_timeseries('outdoor_temperature')

        # Run analysis
        if temp is not None or co2 is not None or humidity is not None:
            result = calc.assess_timeseries_compliance(
                temperature=temp,
                co2=co2,
                humidity=humidity,
                outdoor_temperature=outdoor_temp,
                season=season,
                ventilation_type=vent_type,
                outdoor_co2=outdoor_co2,
                categories_to_check=cats,
            )

            # Cache result
            self._analysis_cache['en16798'] = result
            return result

        return {"error": "No environmental data available"}

    def compute_tail(
        self,
        thresholds: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """
        Compute TAIL rating.

        Automatically uses available parameters and categorizes them.

        Args:
            thresholds: Optional custom thresholds

        Returns:
            Dict with TAIL rating results
        """
        from ...calculators.tail_calculator import TAILCalculator

        calc = TAILCalculator()

        # Get all available timeseries
        timeseries_data = {}
        for param in ['temperature', 'co2', 'humidity', 'illuminance', 'noise']:
            ts = self.get_timeseries(param)
            if ts is not None:
                timeseries_data[param] = ts

        if not timeseries_data:
            return {"error": "No environmental data available"}

        # Use default thresholds if not provided
        if thresholds is None:
            thresholds = {
                "temperature": {"lower": 20.0, "upper": 24.0},
                "co2": {"lower": 0, "upper": 1200},
                "humidity": {"lower": 25, "upper": 60},
                "illuminance": {"lower": 300, "upper": 1000},
                "noise": {"lower": 0, "upper": 45},
            }

        # Run analysis
        result = calc.assess_timeseries(timeseries_data, thresholds)

        # Convert to dict
        result_dict = {
            "overall_rating": result.overall_rating.value,
            "overall_rating_label": result.overall_rating_label,
            "overall_compliance_rate": result.overall_compliance_rate,
            "categories": {
                cat.value: {
                    "rating": cat_result.rating.value,
                    "rating_label": cat_result.rating_label,
                    "compliance_rate": cat_result.compliance_rate,
                    "parameter_count": cat_result.parameter_count,
                }
                for cat, cat_result in result.categories.items()
            },
            "total_parameters": result.total_parameters,
        }

        # Cache result
        self._analysis_cache['tail'] = result_dict
        return result_dict

    def compute_ventilation(self) -> Dict[str, Any]:
        """
        Estimate ventilation rate from CO2 decay.

        Requires CO2 timeseries data.

        Returns:
            Dict with ventilation results
        """
        from ...calculators.ventilation_calculator import VentilationCalculator

        co2 = self.get_timeseries('co2')
        if co2 is None:
            return {"error": "CO2 data required for ventilation estimation"}

        calc = VentilationCalculator(outdoor_co2=400.0)
        result = calc.estimate_from_co2_decay(
            co2_series=co2,
            volume_m3=self.volume_m3,
        )

        if result is None:
            return {"error": "Could not estimate ventilation from CO2 data"}

        result_dict = {
            "ach": result.ach,
            "ventilation_l_s": result.ventilation_l_s,
            "category": result.category,
            "r_squared": result.r_squared,
            "quality_score": result.quality_score,
            "confidence_interval": result.confidence_interval,
            "description": result.description,
        }

        # Cache result
        self._analysis_cache['ventilation'] = result_dict
        return result_dict

    def compute_occupancy(self) -> Dict[str, Any]:
        """
        Detect occupancy patterns from CO2.

        Requires CO2 timeseries data.

        Returns:
            Dict with occupancy results
        """
        from ...calculators.occupancy_calculator import OccupancyCalculator

        co2 = self.get_timeseries('co2')
        if co2 is None:
            return {"error": "CO2 data required for occupancy detection"}

        calc = OccupancyCalculator()
        pattern = calc.detect_occupancy(co2)

        result_dict = {
            "occupancy_rate": pattern.occupancy_rate,
            "estimated_occupants": pattern.estimated_occupant_count,
            "avg_co2_occupied": pattern.avg_co2_occupied,
            "avg_co2_unoccupied": pattern.avg_co2_unoccupied,
            "typical_hours": pattern.typical_occupancy_hours,
            "description": pattern.description,
        }

        # Cache result
        self._analysis_cache['occupancy'] = result_dict
        return result_dict

    def compute_rc_model(
        self,
        setpoint_heating: float = 20.0,
        setpoint_cooling: float = 26.0,
        model_type: str = "2R2C"
    ) -> Dict[str, Any]:
        """
        Run RC thermal model simulation.

        Requires outdoor temperature. Optional: solar irradiance.

        Args:
            setpoint_heating: Heating setpoint (°C)
            setpoint_cooling: Cooling setpoint (°C)
            model_type: "1R1C", "2R2C", or "3R3C"

        Returns:
            Dict with simulation results
        """
        from ...calculators.rc_thermal_model import (
            RCThermalModel,
            RCModelParameters,
            RCModelType,
        )

        outdoor_temp = self.get_timeseries('outdoor_temperature')
        if outdoor_temp is None:
            return {"error": "Outdoor temperature required for RC model"}

        # Get solar irradiance or use default
        solar = self.get_timeseries('solar_irradiance')
        if solar is None:
            solar = pd.Series(0.0, index=outdoor_temp.index)

        # Estimate parameters
        params = RCModelParameters.estimate_from_building_properties(
            volume_m3=self.volume_m3 or (self.area_m2 * 3.0 if self.area_m2 else 75.0),
            area_m2=self.area_m2 or 25.0,
            window_area_m2=self.window_area_m2 or ((self.area_m2 or 25.0) * 0.2),
            construction_type=self.construction_type or "medium",
        )

        # Create model
        model_type_enum = RCModelType(model_type)
        model = RCThermalModel(params, model_type_enum)

        # Simulate
        result = model.simulate(
            outdoor_temperature=outdoor_temp,
            solar_irradiance=solar,
            setpoint_heating=setpoint_heating,
            setpoint_cooling=setpoint_cooling,
        )

        result_dict = {
            "metrics": result.metrics,
            "u_value": model.estimate_u_value(),
            "time_constant_hours": model.estimate_thermal_time_constant(),
        }

        # Cache result
        self._analysis_cache['rc_model'] = result_dict
        return result_dict

    def compute_all(
        self,
        analyses: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Compute all available analyses.

        Args:
            analyses: List of analyses to run. Options: "en16798", "tail", "ventilation", "occupancy", "rc_model"
                     If None, runs all available based on data.
            **kwargs: Additional arguments for specific analyses

        Returns:
            Dict with all analysis results
        """
        if analyses is None:
            analyses = []
            if self.has_parameter('temperature') or self.has_parameter('co2'):
                analyses.extend(['en16798', 'tail'])
            if self.has_parameter('co2'):
                analyses.extend(['ventilation', 'occupancy'])
            if self.has_parameter('outdoor_temperature'):
                analyses.append('rc_model')

        results = {}

        if 'en16798' in analyses:
            results['en16798'] = self.compute_en16798(**kwargs.get('en16798', {}))

        if 'tail' in analyses:
            results['tail'] = self.compute_tail(**kwargs.get('tail', {}))

        if 'ventilation' in analyses:
            results['ventilation'] = self.compute_ventilation()

        if 'occupancy' in analyses:
            results['occupancy'] = self.compute_occupancy()

        if 'rc_model' in analyses:
            results['rc_model'] = self.compute_rc_model(**kwargs.get('rc_model', {}))

        return results

    def get_cached_result(self, analysis_type: str) -> Optional[Any]:
        """Get cached analysis result."""
        return self._analysis_cache.get(analysis_type)

    def clear_cache(self):
        """Clear all cached analysis results."""
        self._analysis_cache.clear()
