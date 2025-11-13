from typing import Dict, Any, List
from core.models.timeseries import TimeSeries, DataSourceType, MetricType

class EloverblikConnector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def fetch(self, start: str, end: str) -> List[TimeSeries]:
        # Dummy implementation; replace with real API calls
        return []
