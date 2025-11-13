"""
Utility for generating synthetic climate data for testing and demonstrations.

This module provides functions to generate realistic synthetic climate data including:
- Solar radiation
- Outdoor temperature
- Outdoor humidity
- Wind speed and direction
"""

from typing import Any

import numpy as np
import pandas as pd


class SyntheticClimateGenerator:
    """Generate realistic synthetic climate data."""

    def __init__(self, latitude: float = 45.0, seed: int | None = None):
        """
        Initialize climate generator.

        Args:
            latitude: Latitude for location (affects solar radiation patterns)
            seed: Random seed for reproducibility
        """
        self.latitude = latitude
        if seed is not None:
            np.random.seed(seed)

    def generate(
        self,
        start_date: str,
        end_date: str,
        freq: str = "h",
        location_params: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """
        Generate comprehensive synthetic climate data.

        Args:
            start_date: Start date (e.g., "2024-01-01")
            end_date: End date (e.g., "2024-12-31")
            freq: Frequency (default "h" for hourly)
            location_params: Optional dict with location-specific parameters:
                - avg_temp: Average annual temperature (default: 12°C)
                - temp_amplitude: Seasonal temperature variation (default: 15°C)
                - avg_humidity: Average relative humidity (default: 65%)
                - avg_wind_speed: Average wind speed (default: 3.5 m/s)

        Returns:
            DataFrame with climate parameters
        """
        # Default location parameters (temperate climate)
        params = {
            "avg_temp": 12.0,
            "temp_amplitude": 15.0,
            "avg_humidity": 65.0,
            "avg_wind_speed": 3.5,
        }
        if location_params:
            params.update(location_params)

        # Generate time index
        dates = pd.date_range(start_date, end_date, freq=freq)

        # Generate each parameter
        outdoor_temp = self._generate_temperature(dates, params)
        solar_radiation = self._generate_solar_radiation(dates)
        outdoor_humidity = self._generate_humidity(dates, outdoor_temp, params)
        wind_speed = self._generate_wind_speed(dates, params)
        wind_direction = self._generate_wind_direction(dates)

        # Create DataFrame
        climate_data = pd.DataFrame(
            {
                "outdoor_temp": outdoor_temp,
                "solar_radiation": solar_radiation,
                "outdoor_humidity": outdoor_humidity,
                "wind_speed": wind_speed,
                "wind_direction": wind_direction,
            },
            index=dates,
        )

        return climate_data

    def _generate_temperature(
        self, dates: pd.DatetimeIndex, params: dict[str, Any]
    ) -> np.ndarray:
        """
        Generate realistic outdoor temperature.

        Combines:
        - Annual seasonal cycle
        - Daily cycle
        - Random weather variations
        """
        n = len(dates)
        avg_temp = params["avg_temp"]
        amplitude = params["temp_amplitude"]

        # Day of year (0-365)
        day_of_year = dates.dayofyear.values

        # Seasonal component (sinusoidal, peaks in summer)
        # Shift by ~80 days so peak is in July (Northern Hemisphere)
        seasonal = amplitude * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)

        # Daily component (smaller amplitude)
        hour_of_day = dates.hour.values
        daily = 4.0 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)

        # Random weather variations (autocorrelated)
        # Use random walk to create persistent weather patterns
        weather_noise = np.cumsum(np.random.normal(0, 0.5, n))
        weather_noise = weather_noise - np.mean(weather_noise)  # Remove drift
        weather_noise = weather_noise / np.std(weather_noise) * 3.0  # Scale

        # Short-term noise
        noise = np.random.normal(0, 0.8, n)

        # Combine all components
        temperature = avg_temp + seasonal + daily + weather_noise + noise

        return temperature

    def _generate_solar_radiation(self, dates: pd.DatetimeIndex) -> np.ndarray:
        """
        Generate realistic solar radiation (W/m²).

        Accounts for:
        - Time of day (zero at night)
        - Season (lower in winter, higher in summer)
        - Cloud cover variations
        """
        n = len(dates)

        # Day of year and hour
        day_of_year = dates.dayofyear.values
        hour_of_day = dates.hour.values

        # Seasonal maximum radiation (higher in summer)
        max_radiation_base = 1000.0  # Peak solar radiation at summer noon
        seasonal_factor = 0.7 + 0.3 * np.sin(
            2 * np.pi * (day_of_year - 80) / 365.25
        )  # 0.7 to 1.0

        # Day length varies with season (simplified)
        # Longer days in summer
        day_length_factor = 12 + 4 * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)
        sunrise = 12 - day_length_factor / 2
        sunset = 12 + day_length_factor / 2

        # Calculate radiation based on hour
        radiation = np.zeros(n)
        for i in range(n):
            if sunrise[i] <= hour_of_day[i] <= sunset[i]:
                # Sinusoidal pattern during day
                hours_from_sunrise = hour_of_day[i] - sunrise[i]
                day_progress = hours_from_sunrise / (sunset[i] - sunrise[i])
                solar_elevation = np.sin(np.pi * day_progress)
                radiation[i] = (
                    max_radiation_base * seasonal_factor[i] * solar_elevation
                )

        # Add cloud cover effects (random reductions)
        cloud_cover = np.random.beta(2, 5, n)  # Skewed toward clear (low values)
        radiation = radiation * (1 - cloud_cover * 0.8)  # Clouds reduce up to 80%

        # Add small noise
        radiation += np.random.normal(0, 10, n)
        radiation = np.maximum(radiation, 0)  # No negative radiation

        return radiation

    def _generate_humidity(
        self, dates: pd.DatetimeIndex, temperature: np.ndarray, params: dict[str, Any]
    ) -> np.ndarray:
        """
        Generate outdoor relative humidity (%).

        Inversely correlated with temperature (higher temp = lower RH generally).
        """
        n = len(dates)
        avg_humidity = params["avg_humidity"]

        # Base seasonal pattern (higher in winter, lower in summer)
        day_of_year = dates.dayofyear.values
        seasonal = -10 * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)

        # Daily pattern (higher at night/morning, lower afternoon)
        hour_of_day = dates.hour.values
        daily = 8 * np.sin(2 * np.pi * (hour_of_day - 6) / 24 + np.pi)

        # Temperature correlation (inverse)
        # Normalize temperature to remove seasonal trend for this calculation
        temp_normalized = temperature - np.mean(temperature)
        temp_effect = -0.3 * temp_normalized

        # Random variations (weather fronts, precipitation)
        weather_noise = np.random.normal(0, 5, n)

        # Persistent weather patterns
        humidity_trend = np.cumsum(np.random.normal(0, 0.3, n))
        humidity_trend = humidity_trend - np.mean(humidity_trend)
        humidity_trend = humidity_trend / np.std(humidity_trend) * 5.0

        # Combine
        humidity = (
            avg_humidity + seasonal + daily + temp_effect + weather_noise + humidity_trend
        )

        # Clamp to realistic range
        humidity = np.clip(humidity, 20, 100)

        return humidity

    def _generate_wind_speed(
        self, dates: pd.DatetimeIndex, params: dict[str, Any]
    ) -> np.ndarray:
        """
        Generate wind speed (m/s).

        Uses Weibull distribution which is typical for wind speeds.
        """
        n = len(dates)
        avg_wind = params["avg_wind_speed"]

        # Base wind from Weibull distribution
        # Shape parameter k=2 (Rayleigh distribution) is typical for wind
        k = 2.0
        lambda_param = avg_wind / 0.886  # Scale to match target average

        base_wind = np.random.weibull(k, n) * lambda_param

        # Add some hourly variation (slightly windier during day)
        hour_of_day = dates.hour.values
        diurnal = 0.5 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)

        # Seasonal variation (windier in winter/spring)
        day_of_year = dates.dayofyear.values
        seasonal = 0.5 * np.cos(2 * np.pi * (day_of_year - 80) / 365.25)

        # Add persistent wind patterns (weather systems)
        wind_trend = np.cumsum(np.random.normal(0, 0.1, n))
        wind_trend = wind_trend - np.mean(wind_trend)
        wind_trend = wind_trend / np.std(wind_trend) * 0.8

        wind_speed = base_wind + diurnal + seasonal + wind_trend

        # Ensure non-negative
        wind_speed = np.maximum(wind_speed, 0)

        return wind_speed

    def _generate_wind_direction(self, dates: pd.DatetimeIndex) -> np.ndarray:
        """
        Generate wind direction (degrees, 0-360).

        With some prevailing direction and variations.
        """
        n = len(dates)

        # Prevailing wind direction (e.g., westerly = 270°)
        prevailing = 270.0

        # Random walk around prevailing direction
        # Using wrapped normal (von Mises) would be more realistic but this is simpler
        variations = np.cumsum(np.random.normal(0, 15, n))
        variations = variations - np.mean(variations)  # Remove drift

        wind_direction = (prevailing + variations) % 360

        return wind_direction


def generate_climate_data(
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    freq: str = "h",
    latitude: float = 45.0,
    location_type: str = "temperate",
    seed: int | None = None,
) -> pd.DataFrame:
    """
    Convenience function to generate synthetic climate data.

    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        freq: Data frequency ("h" for hourly, "15min" for 15-min, etc.)
        latitude: Latitude of location
        location_type: Preset location type ("temperate", "hot", "cold", "humid")
        seed: Random seed for reproducibility

    Returns:
        DataFrame with climate parameters

    Example:
        >>> climate_data = generate_climate_data(
        ...     start_date="2024-01-01",
        ...     end_date="2024-12-31",
        ...     location_type="temperate",
        ...     seed=42
        ... )
        >>> print(climate_data.head())
    """
    # Preset location parameters
    location_presets = {
        "temperate": {
            "avg_temp": 12.0,
            "temp_amplitude": 15.0,
            "avg_humidity": 65.0,
            "avg_wind_speed": 3.5,
        },
        "hot": {
            "avg_temp": 25.0,
            "temp_amplitude": 10.0,
            "avg_humidity": 50.0,
            "avg_wind_speed": 2.5,
        },
        "cold": {
            "avg_temp": 2.0,
            "temp_amplitude": 20.0,
            "avg_humidity": 70.0,
            "avg_wind_speed": 4.5,
        },
        "humid": {
            "avg_temp": 18.0,
            "temp_amplitude": 12.0,
            "avg_humidity": 80.0,
            "avg_wind_speed": 3.0,
        },
    }

    params = location_presets.get(location_type, location_presets["temperate"])

    generator = SyntheticClimateGenerator(latitude=latitude, seed=seed)
    return generator.generate(start_date, end_date, freq, params)


if __name__ == "__main__":
    # Example usage
    print("Generating synthetic climate data...")
    climate = generate_climate_data(
        start_date="2024-01-01",
        end_date="2024-12-31",
        freq="h",
        location_type="temperate",
        seed=42,
    )

    print("\nGenerated climate data:")
    print(climate.head(24))  # Show first 24 hours

    print("\nStatistics:")
    print(climate.describe())

    print("\nData shape:", climate.shape)
    print("Columns:", list(climate.columns))
