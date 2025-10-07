#!/usr/bin/env python3
"""
Test script to generate a building report with actual data.
"""
import json
from pathlib import Path
from src.core.reporting.UnifiedReportService import UnifiedReportService
from src.core.models.results.building_analysis import BuildingAnalysis

# Load building analysis from JSON
building_json_path = Path("output/analysis/buildings/building_1.json")

with open(building_json_path, 'r') as f:
    building_data = json.load(f)

# Create BuildingAnalysis object from dict
building_analysis = BuildingAnalysis(
    building_id=building_data['building_id'],
    building_name=building_data['building_name'],
    level_ids=building_data['level_ids'],
    room_ids=building_data['room_ids'],
    level_count=building_data['level_count'],
    room_count=building_data['room_count'],
    avg_compliance_rate=building_data['avg_compliance_rate'],
    avg_quality_score=building_data['avg_quality_score'],
    test_aggregations=building_data['test_aggregations'],
    level_comparisons=building_data.get('level_comparisons', {}),
    best_performing_levels=building_data.get('best_performing_levels', []),
    worst_performing_levels=building_data.get('worst_performing_levels', []),
    best_performing_rooms=building_data.get('best_performing_rooms', []),
    worst_performing_rooms=building_data.get('worst_performing_rooms', []),
    critical_issues=building_data.get('critical_issues', []),
    recommendations=building_data.get('recommendations', []),
    analysis_timestamp=building_data.get('analysis_timestamp', ''),
    status=building_data.get('status', 'completed'),
    metadata=building_data.get('metadata', {})
)

# Initialize report service
report_service = UnifiedReportService(enable_validation=False)

# Generate report
template_name = "building_detailed"
config_path = Path("config/report_templates/building_detailed.yaml")

print("Generating building report...")
print(f"Building: {building_analysis.building_name}")
print(f"Rooms: {building_analysis.room_count}")
print(f"Avg Compliance: {building_analysis.avg_compliance_rate:.1f}%")

result = report_service.html_renderer.render_report(
    config_path=config_path,
    analysis_results=building_analysis,
    dataset=None,
    weather_data=None,
    output_filename="test_building_1_with_data.html"
)

print(f"\n✓ Report generated: {result['output_path']}")
print(f"  File size: {result['file_size']} bytes")
print("\nOpen the file in a browser to view!")
