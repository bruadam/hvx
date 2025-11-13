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
    required = [k for k, v in standard_config.get("required_inputs", {}).items() if v]
    missing = [m for m in required if m not in timeseries_dict]
    if missing:
        return ComplianceAnalysis(
            id=context.get("analysis_id", f"an_br18_{spatial_entity.id}"),
            name=f"BR18 compliance (insufficient data) for {spatial_entity.name}",
            spatial_entity_id=spatial_entity.id,
            rule_set_id=ruleset.id,
            overall_pass=False,
            summary_results={"status": "insufficient_data", "missing": missing},
        )
    return ComplianceAnalysis(
        id=context.get("analysis_id", f"an_br18_{spatial_entity.id}"),
        name=f"BR18 compliance for {spatial_entity.name}",
        spatial_entity_id=spatial_entity.id,
        rule_set_id=ruleset.id,
        overall_pass=True,
    )
