"""CSV data loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.domain.enums.parameter_type import ParameterType
from core.domain.models.room import Room


class CSVDataLoader:
    """
    Load room data from CSV files.

    Expected CSV format:
    - First column: timestamp (datetime)
    - Other columns: parameter names (temperature, co2, humidity, etc.)
    """

    def __init__(
        self,
        timestamp_column: str = "timestamp",
        date_format: str | None = None,
        delimiter: str = ",",
    ):
        """
        Initialize CSV loader.

        Args:
            timestamp_column: Name of timestamp column (default: "timestamp")
            date_format: DateTime format string (None for auto-detect)
            delimiter: CSV delimiter (default: ",")
        """
        self.timestamp_column = timestamp_column
        self.date_format = date_format
        self.delimiter = delimiter

    def load_room(
        self,
        file_path: Path,
        room_id: str,
        room_name: str,
        level_id: str | None = None,
        building_id: str | None = None,
        **room_kwargs: Any,
    ) -> Room:
        """
        Load room data from CSV file.

        Args:
            file_path: Path to CSV file
            room_id: Unique room identifier
            room_name: Room name
            level_id: Optional level ID
            building_id: Optional building ID
            **room_kwargs: Additional Room attributes

        Returns:
            Room entity with loaded time series data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            # Load CSV
            df = pd.read_csv(
                file_path,
                delimiter=self.delimiter,
                parse_dates=[self.timestamp_column] if self.timestamp_column else False,
            )

            # Set timestamp as index
            if self.timestamp_column in df.columns:
                df = df.set_index(self.timestamp_column)
            elif df.index.name is None:
                # Try to use first column as timestamp
                df.index = pd.to_datetime(df.index)

            # Ensure DatetimeIndex
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index, format=self.date_format)

            # Sort by timestamp
            df = df.sort_index()

            # Normalize column names (lowercase)
            df.columns = [col.lower().strip() for col in df.columns]

            # Create room entity
            room = Room(
                id=room_id,
                name=room_name,
                level_id=level_id,
                building_id=building_id,
                data_file_path=file_path,
                time_series_data=df,
                data_start=df.index.min() if not df.empty else None,
                data_end=df.index.max() if not df.empty else None,
                **room_kwargs,
            )

            return room

        except Exception as e:
            raise ValueError(f"Error loading CSV file {file_path}: {e}") from e

    def load_multiple_rooms(
        self,
        file_paths: list[Path],
        room_id_extractor: callable | None = None,
        room_name_extractor: callable | None = None,
        **common_kwargs: Any,
    ) -> list[Room]:
        """
        Load multiple rooms from CSV files.

        Args:
            file_paths: List of CSV file paths
            room_id_extractor: Function to extract room ID from Path (default: use stem)
            room_name_extractor: Function to extract name from Path (default: use stem)
            **common_kwargs: Common attributes for all rooms

        Returns:
            List of Room entities
        """
        rooms = []

        for file_path in file_paths:
            # Extract room ID and name
            if room_id_extractor:
                room_id = room_id_extractor(file_path)
            else:
                room_id = file_path.stem  # Filename without extension

            if room_name_extractor:
                room_name = room_name_extractor(file_path)
            else:
                room_name = file_path.stem.replace("_", " ").title()

            try:
                room = self.load_room(
                    file_path=file_path,
                    room_id=room_id,
                    room_name=room_name,
                    **common_kwargs,
                )
                rooms.append(room)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")

        return rooms

    def validate_csv_format(self, file_path: Path) -> dict[str, Any]:
        """
        Validate CSV file format.

        Args:
            file_path: Path to CSV file

        Returns:
            Dictionary with validation results
        """
        try:
            df = pd.read_csv(file_path, nrows=5)

            validation = {
                "valid": True,
                "row_count": len(df),
                "columns": list(df.columns),
                "has_timestamp": self.timestamp_column in df.columns,
                "detected_parameters": [],
                "warnings": [],
            }

            # Check for known parameters
            for col in df.columns:
                col_lower = col.lower().strip()
                try:
                    param = ParameterType(col_lower)
                    validation["detected_parameters"].append(param.value)
                except ValueError:
                    if col_lower != self.timestamp_column:
                        validation["warnings"].append(f"Unknown parameter: {col}")

            if not validation["has_timestamp"]:
                validation["warnings"].append(
                    f"No '{self.timestamp_column}' column found"
                )

            return validation

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "warnings": [],
            }

    @staticmethod
    def create_sample_csv(
        output_path: Path,
        start_date: str = "2024-01-01",
        periods: int = 168,  # 1 week of hourly data
        freq: str = "H",
    ) -> None:
        """
        Create a sample CSV file for testing.

        Args:
            output_path: Where to save the CSV
            start_date: Start date for time series
            periods: Number of data points
            freq: Frequency ('H'=hourly, 'D'=daily)
        """
        import numpy as np

        # Generate timestamps (using 'h' instead of deprecated 'H')
        timestamps = pd.date_range(start=start_date, periods=periods, freq=freq.lower())

        # Generate realistic IEQ data
        df = pd.DataFrame(
            {
                "timestamp": timestamps,
                "temperature": 20 + 2 * np.sin(np.linspace(0, 4 * np.pi, periods))
                + np.random.normal(0, 0.5, periods),
                "co2": 400 + 200 * np.sin(np.linspace(0, 4 * np.pi, periods))
                + np.random.normal(0, 30, periods),
                "humidity": 45 + 10 * np.sin(np.linspace(0, 4 * np.pi, periods))
                + np.random.normal(0, 3, periods),
            }
        )

        # Ensure positive values (only for numeric columns, not timestamp)
        numeric_cols = ["temperature", "co2", "humidity"]
        df[numeric_cols] = df[numeric_cols].clip(lower=0)

        # Save to CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Sample CSV created: {output_path}")
