from typing import Dict, Any, List
from core.models.timeseries import TimeSeries, DataSourceType, MetricType

class EEMeterModel:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def run(self, inputs: Dict[str, TimeSeries]) -> List[TimeSeries]:
        # Dummy baseline: copy energy input
        energy_ts = inputs.get("energy")
        if energy_ts is None:
            return []
        baseline = TimeSeries(
            id=f"{energy_ts.id}_baseline",
            point_id=energy_ts.point_id,
            spatial_entity_id=energy_ts.spatial_entity_id,
            metric=MetricType.ENERGY,
            timestamps=energy_ts.timestamps,
            values=energy_ts.values,
            source_type=DataSourceType.SIMULATED,
            source_metadata={"model": "eemeter"},
        )
        return [baseline]
