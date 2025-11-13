from typing import Dict, Any, List
from core.models.timeseries import TimeSeries, DataSourceType, MetricType

class RCModel:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def run(self, inputs: Dict[str, TimeSeries]) -> List[TimeSeries]:
        # Dummy implementation: no real physics
        return []
