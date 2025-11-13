from typing import Dict, Any
from core.engine.loader import load_standards
from core.models.spatial_entities import SpatialEntity
from core.models.timeseries import TimeSeries

def run(spatial_entity: SpatialEntity,
        timeseries: Dict[str, TimeSeries],
        context: Dict[str, Any]):
    standards = load_standards()
    en = next((s for s in standards if s["definition"].standard_type == "EN16798-1"), None)
    if not en:
        return None
    std_def = en["definition"]
    ruleset = std_def.rulesets[0]
    return en["run"](en["config"], spatial_entity, timeseries, ruleset, context)
