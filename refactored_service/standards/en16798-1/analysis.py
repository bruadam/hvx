from typing import Dict, Any
from core.models.analytics import EN16798ComplianceAnalysis, TestResult
from core.models.spatial_entities import SpatialEntity
from core.models.rules import RuleSet, TestRule
from core.models.timeseries import TimeSeries, MetricType

def simple_rule_executor(rule: TestRule, ts: TimeSeries) -> Dict[str, Any]:
    # Dummy implementation: always pass
    return {
        "pass": True,
        "out_of_range_hours": 0.0,
        "out_of_range_percentage": 0.0,
    }

def run(standard_config: Dict[str, Any],
        spatial_entity: SpatialEntity,
        timeseries_dict: Dict[str, TimeSeries],
        ruleset: RuleSet,
        context: Dict[str, Any]) -> EN16798ComplianceAnalysis:
    test_results_ids = []
    for rule in ruleset.rules:
        metric = rule.metric
        ts = timeseries_dict.get(metric)
        if ts is None:
            continue
        res_data = simple_rule_executor(rule, ts)
        tr = TestResult(
            id=f"tr_{ruleset.id}_{rule.id}_{spatial_entity.id}",
            name=f"Test {rule.name}",
            spatial_entity_id=spatial_entity.id,
            rule_set_id=ruleset.id,
            rule_id=rule.id,
            pass=res_data["pass"],
            out_of_range_hours=res_data["out_of_range_hours"],
            out_of_range_percentage=res_data["out_of_range_percentage"],
        )
        # In a real system you'd persist and reference ID; here we just append ID
        test_results_ids.append(tr.id)

    analysis = EN16798ComplianceAnalysis(
        id=context.get("analysis_id", f"an_en16798_{spatial_entity.id}"),
        name=f"EN16798-1 compliance for {spatial_entity.name}",
        spatial_entity_id=spatial_entity.id,
        rule_set_id=ruleset.id,
        test_result_ids=test_results_ids,
        overall_pass=True,
        category="II",
    )
    return analysis
