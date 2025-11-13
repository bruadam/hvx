"""
CSV Data Loader

Loads environmental data from CSV files and creates proper model objects.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
import csv
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.models import (
    SpatialEntity,
    SpatialEntityType,
    MeteringPoint,
    TimeSeries,
    MetricType,
    PointType,
    TimeSeriesType,
    VentilationType,
    Room,
    Building,
    Floor,
)


class CSVDataLoader:
    """
    Loads environmental data from CSV files.

    Supports multiple CSV formats:
    1. Wide format: timestamp, room_id, temperature, co2, humidity, ...
    2. Long format: timestamp, room_id, metric, value
    3. Separate files per room
    """

    def __init__(self):
        """Initialize CSV data loader."""
        self.spatial_entities: Dict[str, SpatialEntity] = {}
        self.metering_points: Dict[str, MeteringPoint] = {}
        self.timeseries: Dict[str, TimeSeries] = {}

    def load_wide_format(
        self,
        csv_path: Path | str,
        spatial_entity_id: str,
        spatial_entity_name: str,
        entity_type: SpatialEntityType = SpatialEntityType.ROOM,
        timestamp_column: str = 'timestamp',
        metric_columns: Optional[Dict[str, str]] = None,
        **entity_kwargs
    ) -> Tuple[SpatialEntity, Dict[str, MeteringPoint], Dict[str, TimeSeries]]:
        """
        Load data from wide-format CSV.

        Wide format example:
        timestamp,temperature,co2,humidity
        2024-01-01 00:00:00,21.5,450,45
        2024-01-01 01:00:00,21.3,440,46

        Args:
            csv_path: Path to CSV file
            spatial_entity_id: ID for the spatial entity
            spatial_entity_name: Name for the spatial entity
            entity_type: Type of spatial entity
            timestamp_column: Name of timestamp column
            metric_columns: Dict mapping CSV columns to metric names
                          If None, uses column names as metric names
            **entity_kwargs: Additional properties for spatial entity

        Returns:
            Tuple of (SpatialEntity, dict of MeteringPoints, dict of TimeSeries)
        """
        csv_path = Path(csv_path)

        # Read CSV file
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            raise ValueError(f"No data found in {csv_path}")

        # Get column names (excluding timestamp)
        columns = [col for col in rows[0].keys() if col != timestamp_column]

        # Map columns to metrics
        if metric_columns is None:
            metric_columns = {col: col for col in columns}

        # Create spatial entity
        entity_class = {
            SpatialEntityType.ROOM: Room,
            SpatialEntityType.BUILDING: Building,
            SpatialEntityType.FLOOR: Floor,
        }.get(entity_type, SpatialEntity)

        entity = entity_class(
            id=spatial_entity_id,
            name=spatial_entity_name,
            type=entity_type,
            **entity_kwargs
        )
        self.spatial_entities[entity.id] = entity

        # Create metering points and time series
        metering_points = {}
        timeseries_dict = {}

        for csv_col, metric_name in metric_columns.items():
            if csv_col not in columns:
                continue

            # Map metric name to MetricType
            metric_type = self._get_metric_type(metric_name)

            # Create metering point
            point_id = f"{spatial_entity_id}_{metric_name}"
            point = MeteringPoint(
                id=point_id,
                name=f"{spatial_entity_name} {metric_name}",
                type=PointType.SENSOR,
                spatial_entity_id=entity.id,
                metric=metric_type,
                unit=self._get_unit(metric_name),
                timeseries_ids=[],
            )
            metering_points[point_id] = point
            self.metering_points[point_id] = point

            # Extract time series data
            timestamps = []
            values = []

            for row in rows:
                try:
                    timestamps.append(row[timestamp_column])
                    value = float(row[csv_col])
                    values.append(value)
                except (ValueError, KeyError):
                    continue

            if not values:
                continue

            # Create time series
            ts_id = f"{point_id}_ts"
            ts = TimeSeries(
                id=ts_id,
                point_id=point_id,
                type=TimeSeriesType.MEASURED,
                metric=metric_type,
                unit=self._get_unit(metric_name),
                start=datetime.fromisoformat(timestamps[0]) if timestamps else None,
                end=datetime.fromisoformat(timestamps[-1]) if timestamps else None,
                granularity_seconds=self._estimate_granularity(timestamps),
                source="csv",
                metadata={
                    'csv_file': str(csv_path),
                    'csv_column': csv_col,
                    'data_points': len(values),
                    'timestamps': timestamps,
                    'values': values,
                }
            )
            timeseries_dict[ts_id] = ts
            self.timeseries[ts_id] = ts

            # Link to metering point
            point.timeseries_ids.append(ts_id)

        return entity, metering_points, timeseries_dict

    def load_long_format(
        self,
        csv_path: Path | str,
        timestamp_column: str = 'timestamp',
        entity_id_column: str = 'room_id',
        metric_column: str = 'metric',
        value_column: str = 'value',
        entity_name_column: Optional[str] = None,
        entity_type: SpatialEntityType = SpatialEntityType.ROOM,
    ) -> Tuple[Dict[str, SpatialEntity], Dict[str, MeteringPoint], Dict[str, TimeSeries]]:
        """
        Load data from long-format CSV.

        Long format example:
        timestamp,room_id,metric,value
        2024-01-01 00:00:00,room_1,temperature,21.5
        2024-01-01 00:00:00,room_1,co2,450
        2024-01-01 01:00:00,room_1,temperature,21.3

        Args:
            csv_path: Path to CSV file
            timestamp_column: Name of timestamp column
            entity_id_column: Name of entity ID column
            metric_column: Name of metric column
            value_column: Name of value column
            entity_name_column: Name of entity name column (optional)
            entity_type: Type of spatial entities

        Returns:
            Tuple of (entities dict, metering points dict, timeseries dict)
        """
        csv_path = Path(csv_path)

        # Read CSV
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            raise ValueError(f"No data found in {csv_path}")

        # Group data by entity and metric
        data_by_entity_metric: Dict[str, Dict[str, List[Tuple[str, float]]]] = {}
        entity_names: Dict[str, str] = {}

        for row in rows:
            try:
                entity_id = row[entity_id_column]
                metric_name = row[metric_column]
                timestamp = row[timestamp_column]
                value = float(row[value_column])

                if entity_id not in data_by_entity_metric:
                    data_by_entity_metric[entity_id] = {}

                if metric_name not in data_by_entity_metric[entity_id]:
                    data_by_entity_metric[entity_id][metric_name] = []

                data_by_entity_metric[entity_id][metric_name].append((timestamp, value))

                # Store entity name if provided
                if entity_name_column and entity_name_column in row:
                    entity_names[entity_id] = row[entity_name_column]

            except (ValueError, KeyError) as e:
                print(f"Warning: Skipping row due to error: {e}")
                continue

        # Create entities, metering points, and time series
        entities = {}
        all_metering_points = {}
        all_timeseries = {}

        for entity_id, metrics_data in data_by_entity_metric.items():
            # Create entity
            entity_name = entity_names.get(entity_id, entity_id)
            entity_class = {
                SpatialEntityType.ROOM: Room,
                SpatialEntityType.BUILDING: Building,
                SpatialEntityType.FLOOR: Floor,
            }.get(entity_type, SpatialEntity)

            entity = entity_class(
                id=entity_id,
                name=entity_name,
                type=entity_type,
            )
            entities[entity_id] = entity
            self.spatial_entities[entity_id] = entity

            # Create metering points and time series for each metric
            for metric_name, data_points in metrics_data.items():
                metric_type = self._get_metric_type(metric_name)

                # Create metering point
                point_id = f"{entity_id}_{metric_name}"
                point = MeteringPoint(
                    id=point_id,
                    name=f"{entity_name} {metric_name}",
                    type=PointType.SENSOR,
                    spatial_entity_id=entity_id,
                    metric=metric_type,
                    unit=self._get_unit(metric_name),
                    timeseries_ids=[],
                )
                all_metering_points[point_id] = point
                self.metering_points[point_id] = point

                # Sort data by timestamp
                data_points.sort(key=lambda x: x[0])
                timestamps = [dp[0] for dp in data_points]
                values = [dp[1] for dp in data_points]

                # Create time series
                ts_id = f"{point_id}_ts"
                ts = TimeSeries(
                    id=ts_id,
                    point_id=point_id,
                    type=TimeSeriesType.MEASURED,
                    metric=metric_type,
                    unit=self._get_unit(metric_name),
                    start=datetime.fromisoformat(timestamps[0]) if timestamps else None,
                    end=datetime.fromisoformat(timestamps[-1]) if timestamps else None,
                    granularity_seconds=self._estimate_granularity(timestamps),
                    source="csv",
                    metadata={
                        'csv_file': str(csv_path),
                        'data_points': len(values),
                        'timestamps': timestamps,
                        'values': values,
                    }
                )
                all_timeseries[ts_id] = ts
                self.timeseries[ts_id] = ts

                # Link to metering point
                point.timeseries_ids.append(ts_id)

        return entities, all_metering_points, all_timeseries

    def _get_metric_type(self, metric_name: str) -> MetricType:
        """Map metric name to MetricType enum."""
        metric_lower = metric_name.lower()

        if 'temp' in metric_lower:
            if 'outdoor' in metric_lower or 'climate' in metric_lower:
                return MetricType.CLIMATE_TEMP
            return MetricType.TEMPERATURE
        elif 'co2' in metric_lower:
            return MetricType.CO2
        elif 'humid' in metric_lower or 'rh' in metric_lower:
            return MetricType.HUMIDITY
        elif 'illum' in metric_lower or 'light' in metric_lower or 'lux' in metric_lower:
            return MetricType.ILLUMINANCE
        elif 'noise' in metric_lower or 'sound' in metric_lower:
            return MetricType.NOISE
        elif 'energy' in metric_lower:
            return MetricType.ENERGY
        elif 'power' in metric_lower:
            return MetricType.POWER
        elif 'water' in metric_lower:
            return MetricType.WATER
        else:
            return MetricType.OTHER

    def _get_unit(self, metric_name: str) -> str:
        """Get unit for metric."""
        metric_lower = metric_name.lower()

        if 'temp' in metric_lower:
            return "°C"
        elif 'co2' in metric_lower:
            return "ppm"
        elif 'humid' in metric_lower or 'rh' in metric_lower:
            return "%"
        elif 'illum' in metric_lower or 'lux' in metric_lower:
            return "lux"
        elif 'noise' in metric_lower or 'sound' in metric_lower:
            return "dB(A)"
        elif 'energy' in metric_lower:
            return "kWh"
        elif 'power' in metric_lower:
            return "kW"
        elif 'water' in metric_lower:
            return "L"
        else:
            return ""

    def _estimate_granularity(self, timestamps: List[str]) -> Optional[int]:
        """Estimate granularity in seconds from timestamps."""
        if len(timestamps) < 2:
            return None

        try:
            dt1 = datetime.fromisoformat(timestamps[0])
            dt2 = datetime.fromisoformat(timestamps[1])
            diff = (dt2 - dt1).total_seconds()
            return int(diff)
        except Exception:
            return None

    def get_timeseries_data(self, ts_id: str) -> Tuple[List[str], List[float]]:
        """
        Get timestamps and values for a time series.

        Args:
            ts_id: Time series ID

        Returns:
            Tuple of (timestamps list, values list)
        """
        if ts_id not in self.timeseries:
            return [], []

        ts = self.timeseries[ts_id]
        metadata = ts.metadata

        timestamps = metadata.get('timestamps', [])
        values = metadata.get('values', [])

        return timestamps, values


# Convenience functions

def load_from_csv(
    csv_path: Path | str,
    format: str = "wide",
    **kwargs
) -> Tuple[Dict[str, SpatialEntity], Dict[str, MeteringPoint], Dict[str, TimeSeries]]:
    """
    Load data from CSV file.

    Args:
        csv_path: Path to CSV file
        format: "wide" or "long"
        **kwargs: Additional arguments for loader

    Returns:
        Tuple of (entities dict, metering points dict, timeseries dict)
    """
    loader = CSVDataLoader()

    if format == "wide":
        entity, points, ts = loader.load_wide_format(csv_path, **kwargs)
        return {entity.id: entity}, points, ts
    elif format == "long":
        return loader.load_long_format(csv_path, **kwargs)
    else:
        raise ValueError(f"Unknown format: {format}")


def load_portfolio_from_csv(
    csv_paths: List[Path | str],
    format: str = "wide",
    **kwargs
) -> Tuple[Dict[str, SpatialEntity], Dict[str, MeteringPoint], Dict[str, TimeSeries]]:
    """
    Load multiple CSV files into a portfolio.

    Args:
        csv_paths: List of paths to CSV files
        format: "wide" or "long"
        **kwargs: Additional arguments for loader

    Returns:
        Tuple of (entities dict, metering points dict, timeseries dict)
    """
    loader = CSVDataLoader()

    all_entities = {}
    all_points = {}
    all_ts = {}

    for csv_path in csv_paths:
        if format == "wide":
            # For wide format, need entity ID per file
            entity_id = kwargs.get('spatial_entity_id', Path(csv_path).stem)
            entity_name = kwargs.get('spatial_entity_name', Path(csv_path).stem)

            entity, points, ts = loader.load_wide_format(
                csv_path,
                spatial_entity_id=entity_id,
                spatial_entity_name=entity_name,
                **{k: v for k, v in kwargs.items()
                   if k not in ['spatial_entity_id', 'spatial_entity_name']}
            )
            all_entities[entity.id] = entity
            all_points.update(points)
            all_ts.update(ts)

        elif format == "long":
            entities, points, ts = loader.load_long_format(csv_path, **kwargs)
            all_entities.update(entities)
            all_points.update(points)
            all_ts.update(ts)

    return all_entities, all_points, all_ts


if __name__ == "__main__":
    # Example usage
    print("CSV Data Loader Module")
    print("=" * 60)
    print("\nUsage:")
    print("  from ingestion.csv import load_from_csv")
    print("  entities, points, ts = load_from_csv('data.csv', format='wide')")
    print("\nSupported formats:")
    print("  - wide: timestamp, metric1, metric2, ...")
    print("  - long: timestamp, entity_id, metric, value")
