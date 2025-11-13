import importlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List
from core.models.standards import StandardDefinition
from core.models.rules import RuleSet, TestRule, ApplicabilityCondition

STANDARDS_ROOT = Path(__file__).resolve().parents[2] / "standards"

def load_standards() -> List[Dict[str, Any]]:
    standards = []
    for folder in STANDARDS_ROOT.iterdir():
        if not folder.is_dir():
            continue
        cfg_path = folder / "config.yaml"
        if not cfg_path.exists():
            continue
        config = yaml.safe_load(cfg_path.read_text())

        rules = []
        for r in config.get("rules", []):
            rules.append(TestRule(
                id=r["id"],
                name=r.get("name", r["id"]),
                metric=r["metric"],
                operator=r["operator"],
                lower_bound=r.get("lower_bound"),
                upper_bound=r.get("upper_bound"),
                target_value=r.get("target_value"),
                tolerance_hours=r.get("tolerance_hours"),
                tolerance_percentage=r.get("tolerance_percentage"),
                time_window=r.get("time_window"),
                applies_during=r.get("applies_during"),
            ))

        app = config.get("applicability", {})
        cond = ApplicabilityCondition(
            id=f"cond_{config['id']}",
            countries=app.get("countries"),
            regions=app.get("regions"),
            continents=app.get("continents"),
            building_types=app.get("building_types"),
            room_types=app.get("room_types"),
            min_area_m2=app.get("min_area"),
            max_area_m2=app.get("max_area"),
            ventilation_types=app.get("ventilation_types"),
            seasons=app.get("seasons"),
        )

        rs = RuleSet(
            id=f"rs_{config['id']}",
            name=config["name"],
            standard=config["standard_type"],
            category=None,
            rules=rules,
            applicability_conditions=[cond],
        )

        std = StandardDefinition(
            id=config["id"],
            name=config["name"],
            version=config.get("version", "0"),
            standard_type=config["standard_type"],
            category_based=config.get("category_based", False),
            categories=config.get("categories", []),
            raw_config=config,
            rulesets=[rs],
        )

        module_path, func_name = config["analysis_module"].split(":")
        module = importlib.import_module(module_path)
        fn = getattr(module, func_name)

        standards.append({
            "definition": std,
            "config": config,
            "run": fn,
            "folder": str(folder),
        })
    return standards
