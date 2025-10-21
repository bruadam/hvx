#!/usr/bin/env python3
"""
Test script to generate a building report with actual data.
"""
import json
from pathlib import Path
from src.core.reporting.ReportService import ReportService
from src.core.models.results.building_analysis import BuildingAnalysis
from src.core.models import BuildingDataset

# Load building analysis from JSON
building_json_path = Path("output/analysis/buildings/building_1.json")

# Create BuildingAnalysis object from dict
building_analysis = BuildingAnalysis.load_from_json(building_json_path)

# BuildingDataset
building_dataset = BuildingDataset.
# Initialize report service
report_service = ReportService(enable_validation=False)

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
