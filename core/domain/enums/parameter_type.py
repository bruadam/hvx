"""IEQ parameter type enumeration."""

from enum import Enum
from typing import TYPE_CHECKING, Optional

from .measurement_type import MeasurementType
from .tail_category import TAILCategory

# Forward declaration to avoid circular imports
if TYPE_CHECKING:
    from .building_type import BuildingType
    from .tail_config import TAILParameterConfig


class ParameterType(str, Enum):
    """Types of environmental parameters that can be measured, computed, or simulated."""

    # Thermal parameters (continuous measurable)
    TEMPERATURE = "temperature"

    # Indoor Air Quality parameters
    CO2 = "co2"  # continuous measurable
    HUMIDITY = "humidity"  # continuous measurable (RH in TAIL)
    PM25 = "pm25"  # continuous measurable
    PM10 = "pm10"  # continuous measurable (not in TAIL but common)
    VOC = "voc"  # continuous measurable (general VOCs)
    FORMALDEHYDE = "formaldehyde"  # continuous measurable (TAIL specific)
    BENZENE = "benzene"  # continuous measurable (TAIL specific)
    RADON = "radon"  # continuous measurable
    VENTILATION_RATE = "ventilation"  # continuous measurable (ventilation rate)

    # Acoustics parameters (continuous measurable)
    NOISE = "noise"

    # Lighting parameters
    ILLUMINANCE = "illuminance"  # continuous measurable
    DAYLIGHT_FACTOR = "daylight_factor"  # simulated

    # Point-in-time/inspection parameters
    MOLD = "mold"  # point-in-time visual inspection

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            self.TEMPERATURE: "Temperature",
            self.CO2: "CO₂",
            self.HUMIDITY: "Relative Humidity",
            self.ILLUMINANCE: "Illuminance",
            self.NOISE: "Noise Level",
            self.PM25: "PM2.5",
            self.PM10: "PM10",
            self.VOC: "Volatile Organic Compounds",
            self.FORMALDEHYDE: "Formaldehyde",
            self.BENZENE: "Benzene",
            self.RADON: "Radon",
            self.VENTILATION_RATE: "Ventilation Rate",
            self.DAYLIGHT_FACTOR: "Daylight Factor",
            self.MOLD: "Mold Assessment",
        }
        return names.get(self, self.value.title())

    @property
    def default_unit(self) -> str:
        """Get default measurement unit."""
        units = {
            self.TEMPERATURE: "°C",
            self.CO2: "ppm",
            self.HUMIDITY: "%",
            self.ILLUMINANCE: "lux",
            self.NOISE: "dB",
            self.PM25: "µg/m³",
            self.PM10: "µg/m³",
            self.VOC: "ppb",
            self.FORMALDEHYDE: "µg/m³",
            self.BENZENE: "µg/m³",
            self.RADON: "Bq/m³",
            self.VENTILATION_RATE: "L/s",
            self.DAYLIGHT_FACTOR: "%",
            self.MOLD: "category",
        }
        return units.get(self, "")

    @property
    def measurement_types(self) -> list[MeasurementType]:
        """Get the possible measurement/data collection methods for this parameter."""
        types_map = {
            # Parameters with single measurement type
            self.TEMPERATURE: [MeasurementType.CONTINUOUS],
            self.CO2: [MeasurementType.CONTINUOUS],
            self.HUMIDITY: [MeasurementType.CONTINUOUS],
            self.PM25: [MeasurementType.CONTINUOUS],
            self.PM10: [MeasurementType.CONTINUOUS],
            self.VOC: [MeasurementType.CONTINUOUS],
            self.FORMALDEHYDE: [MeasurementType.CONTINUOUS],
            self.BENZENE: [MeasurementType.CONTINUOUS],
            self.DAYLIGHT_FACTOR: [MeasurementType.SIMULATED],
            self.MOLD: [MeasurementType.INSPECTION],

            # Parameters with multiple possible measurement types
            # TODO: Verify these measurement types with Pawel
            self.RADON: [MeasurementType.CONTINUOUS, MeasurementType.INSPECTION],
            self.VENTILATION_RATE: [MeasurementType.CONTINUOUS, MeasurementType.INSPECTION],
            self.NOISE: [MeasurementType.CONTINUOUS, MeasurementType.INSPECTION],
            self.ILLUMINANCE: [MeasurementType.CONTINUOUS, MeasurementType.INSPECTION],
        }
        return types_map.get(self, [MeasurementType.CONTINUOUS])

    @property
    def primary_measurement_type(self) -> MeasurementType:
        """Get the primary (preferred) measurement type for this parameter."""
        return self.measurement_types[0]

    @property
    def tail_category(self) -> TAILCategory:
        """Get the TAIL rating category this parameter belongs to."""
        categories = {
            # Thermal (T)
            self.TEMPERATURE: TAILCategory.THERMAL,

            # Acoustics (A)
            self.NOISE: TAILCategory.ACOUSTICS,

            # Indoor Air Quality (I)
            self.CO2: TAILCategory.INDOOR_AIR_QUALITY,
            self.HUMIDITY: TAILCategory.INDOOR_AIR_QUALITY,
            self.PM25: TAILCategory.INDOOR_AIR_QUALITY,
            self.FORMALDEHYDE: TAILCategory.INDOOR_AIR_QUALITY,
            self.BENZENE: TAILCategory.INDOOR_AIR_QUALITY,
            self.RADON: TAILCategory.INDOOR_AIR_QUALITY,
            self.VENTILATION_RATE: TAILCategory.INDOOR_AIR_QUALITY,
            self.MOLD: TAILCategory.INDOOR_AIR_QUALITY,

            # Lighting (L)
            self.ILLUMINANCE: TAILCategory.LIGHTING,
            self.DAYLIGHT_FACTOR: TAILCategory.LIGHTING,

            # Non-TAIL parameters
            self.PM10: TAILCategory.OTHER,
            self.VOC: TAILCategory.OTHER,
        }
        return categories.get(self, TAILCategory.OTHER)

    def supports_measurement_type(self, measurement_type: MeasurementType) -> bool:
        """Check if this parameter supports a specific measurement type."""
        return measurement_type in self.measurement_types

    @property
    def is_tail_parameter(self) -> bool:
        """Check if this parameter is part of the TAIL rating scheme."""
        return self.tail_category != TAILCategory.OTHER

    def get_tail_config(self, building_type: 'BuildingType') -> Optional['TAILParameterConfig']:
        """Get TAIL configuration for this parameter and building type."""
        from .tail_config import TAILConfig
        return TAILConfig.get_parameter_config(self, building_type)

    def is_supported_for_building(self, building_type: 'BuildingType') -> bool:
        """Check if this parameter is supported for a specific building type in TAIL."""
        from .tail_config import TAILConfig
        return TAILConfig.is_parameter_supported(self, building_type)

    @classmethod
    def get_continuous_parameters(cls) -> set['ParameterType']:
        """Get all parameters that support continuous measurement."""
        return {param for param in cls if MeasurementType.CONTINUOUS in param.measurement_types}

    @classmethod
    def get_simulated_parameters(cls) -> set['ParameterType']:
        """Get all parameters that are simulated."""
        return {param for param in cls if MeasurementType.SIMULATED in param.measurement_types}

    @classmethod
    def get_inspection_parameters(cls) -> set['ParameterType']:
        """Get all parameters that support inspection measurement."""
        return {param for param in cls if MeasurementType.INSPECTION in param.measurement_types}

    @classmethod
    def get_parameters_by_measurement_type(cls, measurement_type: MeasurementType) -> set['ParameterType']:
        """Get all parameters that support a specific measurement type."""
        return {param for param in cls if measurement_type in param.measurement_types}

    @classmethod
    def get_tail_parameters(cls) -> set['ParameterType']:
        """Get all parameters used in TAIL rating."""
        return {param for param in cls if param.tail_category != TAILCategory.OTHER}

    @classmethod
    def get_parameters_by_tail_category(cls, category: TAILCategory) -> set['ParameterType']:
        """Get all parameters for a specific TAIL category."""
        return {param for param in cls if param.tail_category == category}
