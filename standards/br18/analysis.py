"""BR18 Standard Analysis Module.

This module evaluates a room's time-series data against the basic BR18
requirements using the refactored compute_standards API shape.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

from core.analysis import (
    ComplianceAnalysis,
    TestResult,
    AnalysisStatus,
    AnalysisType,
)
from core.spacial_entity import SpatialEntity


CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> Dict[str, Any]:
    """Load the BR18 configuration file."""

    with open(CONFIG_PATH, "r") as fh:
        return yaml.safe_load(fh)


def _series_from_timeseries(
    values: Any,
    timestamps: Optional[List[str]] = None,
) -> pd.Series:
    """Convert raw time-series values plus timestamps to a clean Series."""

    if values is None:
        return pd.Series(dtype=float)

    series = pd.Series(values)
    series = pd.to_numeric(series, errors="coerce")

    if timestamps and len(series) == len(timestamps):
        idx = pd.to_datetime(timestamps, errors="coerce")
        valid_mask = (~idx.isna()) & (~series.isna().to_numpy())
        if valid_mask.any():
            filtered = series[valid_mask]
            filtered.index = pd.DatetimeIndex(idx[valid_mask])
            return filtered
        return pd.Series(dtype=float)

    return series.dropna()


def _estimate_step_hours(index: pd.Index) -> Optional[float]:
    """Best-effort estimate of the sampling step in hours."""

    if not isinstance(index, pd.DatetimeIndex) or len(index) < 2:
        return None

    diffs = index.to_series().diff().dropna().dt.total_seconds()
    diffs = diffs[diffs > 0]
    if diffs.empty:
        return None
    return float(diffs.median()) / 3600.0


def _evaluate_rule(series: pd.Series, rule_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Evaluate a single BR18 rule and compute compliance statistics."""

    if series is None or series.empty:
        return None

    operator = (rule_config.get("operator") or "").lower()
    mask: Optional[pd.Series] = None

    if operator == "between":
        mask = pd.Series(True, index=series.index)
        lower = rule_config.get("lower_bound")
        upper = rule_config.get("upper_bound")
        if lower is not None:
            mask &= series >= lower
        if upper is not None:
            mask &= series <= upper
    elif operator in {"<=", "less_or_equal"}:
        target = rule_config.get("target_value", rule_config.get("upper_bound"))
        if target is None:
            return None
        mask = series <= target
    elif operator in {">=", "greater_or_equal"}:
        target = rule_config.get("target_value", rule_config.get("lower_bound"))
        if target is None:
            return None
        mask = series >= target

    if mask is None or mask.empty:
        return None

    total_points = len(mask)
    compliant_points = int(mask.sum())
    compliance_rate = (compliant_points / total_points) * 100.0 if total_points else 0.0

    step_hours = _estimate_step_hours(series.index) or 1.0
    total_hours = total_points * step_hours
    non_compliant_points = total_points - compliant_points
    non_compliant_hours = non_compliant_points * step_hours

    tolerance_hours = float(rule_config.get("tolerance_hours") or 0.0)
    tolerance_pct = rule_config.get("tolerance_percentage")
    allowed_by_pct = 0.0
    if tolerance_pct is not None:
        allowed_by_pct = (float(tolerance_pct) / 100.0) * total_hours

    allowed_non_compliant_hours = max(tolerance_hours, allowed_by_pct)
    passed = non_compliant_hours <= allowed_non_compliant_hours + 1e-6
    violations_hours = max(0.0, non_compliant_hours - allowed_non_compliant_hours)

    return {
        "rule_id": rule_config.get("id", rule_config.get("name", "br18_rule")),
        "name": rule_config.get("name", "BR18 Rule"),
        "metric": rule_config.get("metric"),
        "operator": operator,
        "compliance_rate": compliance_rate,
        "total_hours": total_hours,
        "non_compliant_hours": non_compliant_hours,
        "allowed_non_compliant_hours": allowed_non_compliant_hours,
        "violations_hours": violations_hours,
        "tolerance_hours": tolerance_hours,
        "tolerance_percentage": tolerance_pct,
        "passed": passed,
        "thresholds": {
            "lower_bound": rule_config.get("lower_bound"),
            "upper_bound": rule_config.get("upper_bound"),
            "target_value": rule_config.get("target_value"),
        },
        "samples_evaluated": total_points,
    }


def run(
    spatial_entity: SpatialEntity,
    timeseries_dict: Dict[str, List[float]],
    timestamps: Optional[List[str]] = None,
    season: str = "all_year",
    **kwargs: Any,
) -> ComplianceAnalysis:
    """Run the BR18 compliance assessment for a spatial entity."""

    config = load_config()
    standard_id = config.get("id", "br18")
    now = datetime.now(timezone.utc)

    series_cache = {
        metric: _series_from_timeseries(values, timestamps)
        for metric, values in timeseries_dict.items()
    }

    required_inputs = config.get("required_inputs", {})
    missing_metrics = [
        metric
        for metric, required in required_inputs.items()
        if required and (metric not in series_cache or series_cache[metric].empty)
    ]

    analysis_id = f"compliance_{spatial_entity.id}_{standard_id}"

    if missing_metrics:
        return ComplianceAnalysis(
            id=analysis_id,
            name=f"BR18 compliance (insufficient data) for {spatial_entity.name}",
            type=AnalysisType.COMPLIANCE,
            spatial_entity_id=spatial_entity.id,
            rule_set_id=standard_id,
            overall_pass=False,
            status=AnalysisStatus.FAILED,
            started_at=now,
            ended_at=now,
            summary_results={
                "status": "insufficient_data",
                "missing": missing_metrics,
                "standard": config.get("name", "BR18"),
                "version": config.get("version"),
            },
        )

    test_results: List[TestResult] = []
    rules_summary: Dict[str, Any] = {}

    for rule_cfg in config.get("rules", []):
        metric = rule_cfg.get("metric")
        series = series_cache.get(metric)
        evaluation = _evaluate_rule(series, rule_cfg) if series is not None else None
        if not evaluation:
            continue

        rule_id = evaluation["rule_id"]
        rules_summary[rule_id] = {
            "name": evaluation["name"],
            "metric": evaluation["metric"],
            "compliance_rate": evaluation["compliance_rate"],
            "non_compliant_hours": evaluation["non_compliant_hours"],
            "allowed_non_compliant_hours": evaluation["allowed_non_compliant_hours"],
            "violations_hours": evaluation["violations_hours"],
            "passed": evaluation["passed"],
            "thresholds": evaluation["thresholds"],
        }

        test_results.append(
            TestResult(
                id=f"test_{spatial_entity.id}_{rule_id}",
                name=f"BR18 - {evaluation['name']}",
                type=AnalysisType.TEST_RESULT,
                spatial_entity_id=spatial_entity.id,
                rule_id=rule_id,
                successful=evaluation["passed"],
                out_of_range_percentage=max(0.0, 100.0 - evaluation["compliance_rate"]),
                status=AnalysisStatus.COMPLETED,
                details={
                    "metric": evaluation["metric"],
                    "thresholds": evaluation["thresholds"],
                    "compliance_rate": evaluation["compliance_rate"],
                    "non_compliant_hours": evaluation["non_compliant_hours"],
                    "allowed_non_compliant_hours": evaluation["allowed_non_compliant_hours"],
                    "violations_hours": evaluation["violations_hours"],
                },
            )
        )

    ended_at = datetime.now(timezone.utc)
    overall_pass = all(tr.successful for tr in test_results) if test_results else False

    return ComplianceAnalysis(
        id=analysis_id,
        name=f"BR18 compliance for {spatial_entity.name}",
        type=AnalysisType.COMPLIANCE,
        spatial_entity_id=spatial_entity.id,
        rule_set_id=standard_id,
        test_result_ids=[tr.id for tr in test_results],
        overall_pass=overall_pass,
        status=AnalysisStatus.COMPLETED,
        started_at=now,
        ended_at=ended_at,
        summary_results={
            "standard": config.get("name", "BR18"),
            "version": config.get("version"),
            "season": season,
            "overall_pass": overall_pass,
            "rules": rules_summary,
        },
    )

