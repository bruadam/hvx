"""
Sensor- and telemetry-related enums.
"""

from enum import Enum


class MetricType(str, Enum):
    TEMPERATURE = "temperature"
    CO2 = "co2"
    HUMIDITY = "humidity"
    ILLUMINANCE = "illuminance"
    LUX = "lux"
    NOISE = "noise"
    SOUND_PRESSURE = "sound_pressure"
    ENERGY = "energy"
    ELECTRICITY = "electricity"
    GAS = "gas"
    HEAT = "heat"
    COOLING = "cooling"
    POWER = "power"
    APPARENT_POWER = "apparent_power"
    REACTIVE_POWER = "reactive_power"
    WATER = "water"
    WATER_HOT = "water_hot"
    WATER_COLD = "water_cold"
    STEAM = "steam"
    CHILLED_WATER = "chilled_water"
    DOMESTIC_HOT_WATER = "domestic_hot_water"
    AIRFLOW = "airflow"
    AIRFLOW_SUPPLY = "airflow_supply"
    AIRFLOW_RETURN = "airflow_return"
    AIR_TEMPERATURE_SUPPLY = "air_temperature_supply"
    AIR_TEMPERATURE_RETURN = "air_temperature_return"
    WATER_FLOW = "water_flow"
    WATER_TEMPERATURE_SUPPLY = "water_temperature_supply"
    WATER_TEMPERATURE_RETURN = "water_temperature_return"
    DIFFERENTIAL_PRESSURE = "differential_pressure"
    DIFFERENTIAL_TEMPERATURE = "differential_temperature"
    HEAT_FLUX = "heat_flux"
    VALVE_POSITION = "valve_position"
    DAMPER_POSITION = "damper_position"
    OCCUPANCY = "occupancy"
    DESIGN_OCCUPANCY = "design_occupancy"
    OCCUPANCY_PERCENT = "occupancy_percent"
    TEMPERATURE_SETPOINT = "temperature_setpoint"
    CO2_SETPOINT = "co2_setpoint"
    HUMIDITY_SETPOINT = "humidity_setpoint"
    PRESSURE = "pressure"
    BAROMETRIC_PRESSURE = "barometric_pressure"
    WIND_SPEED = "wind_speed"
    WIND_DIRECTION = "wind_direction"
    SOLAR_IRRADIANCE = "solar_irradiance"
    VOC = "voc"
    PM25 = "pm2_5"
    PM10 = "pm10"
    OUTDOOR_TEMPERATURE = "outdoor_temperature"
    OUTDOOR_HUMIDITY = "outdoor_humidity"
    MOTION = "motion"
    LIGHT_LEVEL = "light_level"
    OTHER = "other"


class TimeSeriesType(str, Enum):
    MEASURED = "measured"
    SIMULATED = "simulated"
    DERIVED = "derived"
    CLIMATE = "climate"


class SensorSourceType(str, Enum):
    API = "api"
    CSV = "csv"
    STREAM = "stream"
    MANUAL = "manual"
    FILE = "file"
    OTHER = "other"


class PointType(str, Enum):
    SENSOR = "sensor"
    METER = "meter"
    SIMULATED_POINT = "simulated_point"
    DERIVED_POINT = "derived_point"
    WEATHER_STATION = "weather_station"


__all__ = [
    "MetricType",
    "TimeSeriesType",
    "SensorSourceType",
    "PointType",
]
