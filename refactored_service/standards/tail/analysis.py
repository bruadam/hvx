from typing import Dict, Any
from core.models.analytics import ComplianceAnalysis
from core.models.spatial_entities import SpatialEntity
from core.models.rules import RuleSet
from core.models.timeseries import TimeSeries

def run(standard_config: Dict[str, Any],
        spatial_entity: SpatialEntity,
        timeseries_dict: Dict[str, TimeSeries],
        ruleset: RuleSet,
        context: Dict[str, Any]) -> ComplianceAnalysis:
    return ComplianceAnalysis(
        id=context.get("analysis_id", f"an_tail_{spatial_entity.id}"),
        name=f"TAIL compliance for {spatial_entity.name}",
        spatial_entity_id=spatial_entity.id,
        rule_set_id=ruleset.id,
        overall_pass=True,
        summary_results={"tail_category": "A"},
    )
