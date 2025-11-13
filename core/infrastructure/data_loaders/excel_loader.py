"""Excel data loader."""

from pathlib import Path
from typing import Any

import pandas as pd

from core.domain.models.room import Room


class ExcelDataLoader:
    """
    Load room data from Excel files.

    Supports both single-sheet and multi-sheet workbooks.
    Each sheet can represent a different room.
    """

    def __init__(
        self,
        timestamp_column: str = "timestamp",
        date_format: str | None = None,
    ):
        """
        Initialize Excel loader.

        Args:
            timestamp_column: Name of timestamp column
            date_format: DateTime format string (None for auto-detect)
        """
        self.timestamp_column = timestamp_column
        self.date_format = date_format

    def load_room_from_sheet(
        self,
        file_path: Path,
        sheet_name: str,
        room_id: str,
        room_name: str,
        level_id: str | None = None,
        building_id: str | None = None,
        **room_kwargs: Any,
    ) -> Room:
        """
        Load room data from specific Excel sheet.

        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to load
            room_id: Unique room identifier
            room_name: Room name
            level_id: Optional level ID
            building_id: Optional building ID
            **room_kwargs: Additional Room attributes

        Returns:
            Room entity with loaded time series data
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        try:
            # Load Excel sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            # Set timestamp as index
            if self.timestamp_column in df.columns:
                df = df.set_index(self.timestamp_column)

            # Ensure DatetimeIndex
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index, format=self.date_format)

            # Sort by timestamp
            df = df.sort_index()

            # Normalize column names
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
            raise ValueError(f"Error loading Excel sheet {sheet_name} from {file_path}: {e}") from e

    def load_all_sheets(
        self,
        file_path: Path,
        building_id: str | None = None,
        level_id: str | None = None,
        **common_kwargs: Any,
    ) -> list[Room]:
        """
        Load all sheets from Excel file as separate rooms.

        Args:
            file_path: Path to Excel file
            building_id: Optional building ID for all rooms
            level_id: Optional level ID for all rooms
            **common_kwargs: Common attributes for all rooms

        Returns:
            List of Room entities
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        # Get all sheet names
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names

        rooms = []
        for sheet_name in sheet_names:
            # Use sheet name as room ID and name
            room_id = sheet_name.replace(" ", "_").lower()
            room_name = sheet_name

            try:
                room = self.load_room_from_sheet(
                    file_path=file_path,
                    sheet_name=sheet_name,
                    room_id=room_id,
                    room_name=room_name,
                    building_id=building_id,
                    level_id=level_id,
                    **common_kwargs,
                )
                rooms.append(room)
            except Exception as e:
                print(f"Warning: Failed to load sheet {sheet_name}: {e}")

        return rooms

    def get_sheet_names(self, file_path: Path) -> list[str]:
        """
        Get list of sheet names in Excel file.

        Args:
            file_path: Path to Excel file

        Returns:
            List of sheet names
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        excel_file = pd.ExcelFile(file_path)
        return excel_file.sheet_names

    @staticmethod
    def create_sample_excel(
        output_path: Path,
        num_sheets: int = 3,
        start_date: str = "2024-01-01",
        periods: int = 168,
    ) -> None:
        """
        Create a sample Excel file for testing.

        Args:
            output_path: Where to save the Excel file
            num_sheets: Number of sheets (rooms) to create
            start_date: Start date for time series
            periods: Number of data points per sheet
        """
        import numpy as np

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for i in range(num_sheets):
                # Generate timestamps
                timestamps = pd.date_range(start=start_date, periods=periods, freq="H")

                # Generate realistic IEQ data with variation per room
                df = pd.DataFrame(
                    {
                        "timestamp": timestamps,
                        "temperature": 20
                        + i * 0.5
                        + 2 * np.sin(np.linspace(0, 4 * np.pi, periods))
                        + np.random.normal(0, 0.5, periods),
                        "co2": 400
                        + i * 50
                        + 200 * np.sin(np.linspace(0, 4 * np.pi, periods))
                        + np.random.normal(0, 30, periods),
                        "humidity": 45
                        + i * 2
                        + 10 * np.sin(np.linspace(0, 4 * np.pi, periods))
                        + np.random.normal(0, 3, periods),
                    }
                )

                # Ensure positive values
                df = df.clip(lower=0)

                # Write to sheet
                sheet_name = f"Room_{i+1:03d}"
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        print(f"Sample Excel created: {output_path} ({num_sheets} sheets)")
