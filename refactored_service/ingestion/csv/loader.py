from pathlib import Path
from typing import Dict, Any, List
import csv
from core.models.timeseries import TimeSeries, DataSourceType, MetricType

class CSVLoader:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def load(self) -> List[TimeSeries]:
        # Very simple sketch: one CSV -> one TimeSeries
        path = Path(self.config["path_pattern"])
        timestamps, values = [], []
        with path.open() as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                timestamps.append(row[0])
                values.append(float(row[1]))
        ts = TimeSeries(
            id=f"ts_{path.stem}",
            point_id="unknown",
            spatial_entity_id="unknown",
            metric=MetricType[self.config["metric"].upper()],
            timestamps=timestamps,
            values=values,
            source_type=DataSourceType.MEASURED,
        )
        return [ts]
