#!/usr/bin/env python3
"""Test chart generation in HTML reports."""

import json
from pathlib import Path
from src.core.reporting.ReportService import ReportService
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
report_service = ReportService(enable_validation=False)

# Generate report
config_path = Path("config/report_templates/building_detailed.yaml")

print("Generating report with charts...")
print(f"Building: {building_analysis.building_name}")
print(f"Rooms: {building_analysis.room_count}")
print(f"Avg Compliance: {building_analysis.avg_compliance_rate:.1f}%")

result = report_service.html_renderer.render_report(
    config_path=config_path,
    analysis_results=building_analysis,
    dataset=None,
    weather_data=None,
    output_filename="test_charts_report.html"
)

output_file = Path(result['output_path'])

print(f"\n✓ Report saved to: {output_file}")
print(f"  File size: {result['file_size']:,} bytes")

# Read report content to check for charts
with open(output_file, 'r') as f:
    report_content = f.read()

print("\nChart generation status:")

# Check for chart warnings
if "Warning: Could not generate chart" in report_content:
    print("❌ Some charts failed to generate")
    # Extract warnings
    for line in report_content.split('\n'):
        if "Warning: Could not generate chart" in line:
            # Clean HTML from warning
            clean_line = line.replace('<p class="warning">', '').replace('</p>', '').strip()
            if clean_line:
                print(f"  {clean_line}")
else:
    print("✅ All charts generated successfully")

# Count chart images
chart_count = report_content.count('<img src="data:image/png;base64')
print(f"\n📊 Charts embedded: {chart_count}")
