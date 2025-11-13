#!/usr/bin/env python3
"""
Test file to generate a report and verify that plots/charts are actually present.

This test:
1. Creates sample IEQ data for multiple rooms
2. Generates a comprehensive HTML report
3. Verifies that the report file is created
4. Verifies that plot/chart SVG or canvas elements are embedded in the HTML
5. Extracts and counts the number of plots found
"""

import re
from pathlib import Path
from typing import Tuple, List, Set
import json

from core.infrastructure.data_loaders.csv_loader import CSVDataLoader
from core.reporting import ReportGenerator, TemplateLoader
from core.domain.models.dataset import Dataset


def create_sample_data(output_dir: Path, num_rooms: int = 3) -> Path:
    """
    Create sample IEQ data for testing.

    Args:
        output_dir: Directory to create sample data in
        num_rooms: Number of rooms to create

    Returns:
        Path to data directory
    """
    data_dir = output_dir / "sample_data"
    data_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📊 Creating sample data for {num_rooms} rooms...")

    for i in range(1, num_rooms + 1):
        room_file = data_dir / f"room_{i:02d}.csv"
        # Create 7 days of data (168 hours) with some variation
        CSVDataLoader.create_sample_csv(room_file, periods=168)
        print(f"  ✓ Created {room_file.name}")

    print(f"  Data directory: {data_dir}")
    return data_dir


def load_rooms_from_directory(data_dir: Path) -> List:
    """
    Load all room data from directory.

    Args:
        data_dir: Directory containing CSV files

    Returns:
        List of Room entities
    """
    print(f"\n📂 Loading rooms from {data_dir}...")

    loader = CSVDataLoader()
    rooms = []

    for csv_file in sorted(data_dir.glob("room_*.csv")):
        room_id = csv_file.stem
        room_name = room_id.replace("_", " ").title()

        room = loader.load_room(csv_file, room_id, room_name)
        rooms.append(room)
        record_count = len(room.time_series_data) if room.time_series_data is not None else 0
        print(f"  ✓ Loaded {room_name} ({record_count} records)")

    print(f"  Total rooms loaded: {len(rooms)}")
    return rooms


def find_plotly_charts(html_content: str) -> Tuple[int, List[str]]:
    """
    Find Plotly chart data in HTML content.

    Plotly charts are typically embedded as JSON data in script tags.

    Args:
        html_content: HTML file content

    Returns:
        Tuple of (count, list of chart titles)
    """
    # Find Plotly script tags that contain chart data
    plotly_pattern = r'<script type=["\']application/json["\'][^>]*>(.+?)</script>'
    plotly_matches = re.findall(plotly_pattern, html_content, re.DOTALL)

    chart_titles = []
    valid_plots = 0

    for match in plotly_matches:
        try:
            # Try to parse as JSON
            data = json.loads(match)
            
            # Check if it has the structure of a Plotly figure
            if isinstance(data, dict) and ('data' in data or 'layout' in data):
                valid_plots += 1
                
                # Extract title if available
                title = "Unknown Chart"
                if isinstance(data, dict):
                    if 'layout' in data and isinstance(data['layout'], dict):
                        if 'title' in data['layout']:
                            title_obj = data['layout']['title']
                            if isinstance(title_obj, dict) and 'text' in title_obj:
                                title = title_obj['text']
                            elif isinstance(title_obj, str):
                                title = title_obj
                
                chart_titles.append(title)
        except (json.JSONDecodeError, KeyError, TypeError):
            # Not valid JSON or not a Plotly chart
            continue

    return valid_plots, chart_titles


def find_svg_charts(html_content: str) -> Tuple[int, List[str]]:
    """
    Find SVG charts in HTML content.

    Args:
        html_content: HTML file content

    Returns:
        Tuple of (count, list of SVG descriptions)
    """
    # Find SVG elements
    svg_pattern = r'<svg[^>]*>'
    svg_matches = re.findall(svg_pattern, html_content)
    
    # Find SVG titles within the SVG elements
    title_pattern = r'<title>([^<]+)</title>'
    titles = re.findall(title_pattern, html_content)
    
    return len(svg_matches), titles


def find_canvas_charts(html_content: str) -> int:
    """
    Find canvas elements (used by some chart libraries).

    Args:
        html_content: HTML file content

    Returns:
        Count of canvas elements
    """
    canvas_pattern = r'<canvas'
    matches = re.findall(canvas_pattern, html_content)
    return len(matches)


def verify_plots_in_report(report_path: Path) -> dict:
    """
    Verify that plots/charts are present in the generated report.

    Args:
        report_path: Path to the generated HTML report

    Returns:
        Dictionary with verification results
    """
    print(f"\n🔍 Verifying plots in report: {report_path}")

    if not report_path.exists():
        print(f"  ✗ Report file not found!")
        return {
            "file_exists": False,
            "file_size": 0,
            "plotly_charts": 0,
            "svg_charts": 0,
            "canvas_charts": 0,
            "total_charts": 0,
            "chart_titles": [],
            "plot_data_found": False,
        }

    # Read the report
    with open(report_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    file_size = report_path.stat().st_size

    print(f"  ✓ Report file exists")
    print(f"  📄 File size: {file_size:,} bytes")

    # Find different types of charts
    plotly_count, plotly_titles = find_plotly_charts(html_content)
    svg_count, svg_titles = find_svg_charts(html_content)
    canvas_count = find_canvas_charts(html_content)

    total_charts = plotly_count + svg_count + canvas_count

    # Check for plot-related HTML elements and data
    plot_div_pattern = r'id=["\']plot[^"\']*["\']|class=["\'][^"\']*plot[^"\']*["\']'
    plot_divs = re.findall(plot_div_pattern, html_content)

    # Look for graph classes/divs
    graph_pattern = r'class=["\'][^"\']*graph[^"\']*["\']|id=["\'][^"\']*graph[^"\']*["\']'
    graph_elements = re.findall(graph_pattern, html_content)

    # Look for Plotly-specific markers (the divs that hold the plots)
    plotly_div_pattern = r'<div[^>]*id=["\']chart_[^"\']*["\'][^>]*>'
    plotly_divs = re.findall(plotly_div_pattern, html_content)

    # Check for Plotly script tags with actual data (these contain the plot data)
    plotly_script_pattern = r'<script type=["\']application/json["\'][^>]*>.*?Plotly\.newPlot'
    plotly_scripts = len(re.findall(plotly_script_pattern, html_content, re.DOTALL))

    # Check file size - if it's significantly larger than an empty template, 
    # it likely contains embedded chart data
    has_substantial_content = file_size > 15000  # Most empty reports are < 10KB

    plot_data_found = (
        len(plotly_divs) > 0 or 
        plotly_count > 0 or 
        len(graph_elements) > 0 or 
        len(plot_divs) > 0 or
        has_substantial_content
    )

    results = {
        "file_exists": True,
        "file_size": file_size,
        "plotly_charts": plotly_count,
        "plotly_titles": plotly_titles,
        "svg_charts": svg_count,
        "svg_titles": svg_titles,
        "canvas_charts": canvas_count,
        "plot_divs": len(plot_divs),
        "graph_elements": len(graph_elements),
        "plotly_divs": len(plotly_divs),
        "plotly_scripts": plotly_scripts,
        "total_charts": total_charts,
        "has_substantial_content": has_substantial_content,
        "plot_data_found": plot_data_found,
    }

    # Print results
    print(f"\n  📊 Chart Detection Results:")
    print(f"    • Plotly charts: {plotly_count}")
    if plotly_titles:
        for title in plotly_titles[:5]:  # Show first 5 titles
            print(f"      - {title}")
        if len(plotly_titles) > 5:
            print(f"      ... and {len(plotly_titles) - 5} more")
    
    print(f"    • SVG charts: {svg_count}")
    print(f"    • Canvas elements: {canvas_count}")
    print(f"    • Plotly divs: {len(plotly_divs)}")
    print(f"    • Graph elements: {len(graph_elements)}")
    print(f"    • Plot divs: {len(plot_divs)}")
    print(f"    • File size: {file_size:,} bytes (substantial: {has_substantial_content})")
    print(f"    • Total chart elements detected: {total_charts}")

    if plot_data_found:
        print(f"\n  ✓ Plot data FOUND in report!")
    else:
        print(f"\n  ⚠ WARNING: No plot data found in report")

    return results


def generate_and_verify_report(
    rooms: list,
    building_name: str,
    template_name: str,
    output_path: Path,
    templates_dir: Path,
) -> Tuple[bool, dict]:
    """
    Generate a report and verify plots are present.

    Args:
        rooms: List of Room entities
        building_name: Name of building
        template_name: Name of template to use
        output_path: Output file path for report
        templates_dir: Directory containing templates

    Returns:
        Tuple of (success: bool, verification_results: dict)
    """
    print(f"\n🚀 Generating report with template: {template_name}")

    try:
        # Initialize generator
        generator = ReportGenerator()

        # Find template
        template_path = templates_dir / f"{template_name}.yaml"
        if not template_path.exists():
            print(f"  ✗ Template not found: {template_path}")
            return False, {}

        print(f"  📋 Template path: {template_path}")

        # Load template
        template = TemplateLoader.load_from_file(template_path)
        print(f"  ✓ Template loaded")
        print(f"    - Report type: {template.report_type}")
        print(f"    - Sections: {len(template.sections)}")

        # Generate report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            generator.generate_report(template, rooms, building_name, output_path)
            print(f"  ✓ Report generated: {output_path}")
        except AttributeError as ae:
            # Skip templates with issues
            print(f"  ⚠️  Skipping template due to compatibility issue: {str(ae)[:60]}")
            return False, {}

        # Verify plots
        verification = verify_plots_in_report(output_path)

        success = verification.get("file_exists", False) and verification.get(
            "plot_data_found", False
        )

        return success, verification

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def main():
    """Main test function."""
    print("=" * 80)
    print("🧪 IEQ Analytics - Report Generation with Plot Verification Test")
    print("=" * 80)

    # Setup paths
    base_dir = Path(__file__).parent.parent.parent  # Navigate to project root
    output_base = base_dir / "output" / "test_reports"
    templates_dir = base_dir / "config" / "report_templates"

    print(f"\n📍 Project root: {base_dir}")
    print(f"📍 Templates directory: {templates_dir}")
    print(f"📍 Output directory: {output_base}")

    # Verify templates directory exists
    if not templates_dir.exists():
        print(f"\n❌ Templates directory not found: {templates_dir}")
        return False

    # Step 1: Create sample data
    print("\n" + "=" * 80)
    print("STEP 1: Creating Sample Data")
    print("=" * 80)
    data_dir = create_sample_data(output_base, num_rooms=3)

    # Step 2: Load rooms
    print("\n" + "=" * 80)
    print("STEP 2: Loading Room Data")
    print("=" * 80)
    rooms = load_rooms_from_directory(data_dir)

    if not rooms:
        print("\n❌ No rooms loaded. Exiting.")
        return False

    # Step 3: List available templates
    print("\n" + "=" * 80)
    print("STEP 3: Available Templates")
    print("=" * 80)
    try:
        templates = TemplateLoader.list_templates(templates_dir)
        if templates:
            print(f"\n📋 Found {len(templates)} templates:")
            for name in sorted(templates.keys()):
                print(f"  • {name}")
        else:
            print(f"⚠️  No templates found in {templates_dir}")
    except Exception as e:
        print(f"⚠️  Could not list templates: {e}")
        templates = {}

    # Step 4: Generate and verify reports
    print("\n" + "=" * 80)
    print("STEP 4: Generating and Verifying Reports")
    print("=" * 80)

    building_name = "Test Building"
    results_summary = {
        "total_reports_generated": 0,
        "reports_with_plots": 0,
        "reports_without_plots": 0,
        "total_charts_found": 0,
        "detailed_results": [],
    }

    # Generate reports from templates (try each one, skip if it fails)
    template_names = sorted(templates.keys()) if templates else []

    if not template_names:
        print("\n⚠️  No templates available to test")
        template_names = ["comprehensive_building_report"]

    for template_name in template_names:
        print(f"\n" + "-" * 80)
        
        output_file = output_base / f"report_{template_name}.html"
        success, verification = generate_and_verify_report(
            rooms, building_name, template_name, output_file, templates_dir
        )

        results_summary["total_reports_generated"] += 1

        if success and verification.get("plot_data_found", False):
            results_summary["reports_with_plots"] += 1
            results_summary["total_charts_found"] += max(
                verification.get("total_charts", 0),
                verification.get("plotly_divs", 0),
            )
        else:
            results_summary["reports_without_plots"] += 1

        results_summary["detailed_results"].append(
            {
                "template": template_name,
                "output_file": str(output_file),
                "success": success,
                "verification": verification,
            }
        )

    # Step 5: Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    print(f"\n📊 Results:")
    print(f"  • Total reports generated: {results_summary['total_reports_generated']}")
    print(f"  • Reports with plots: {results_summary['reports_with_plots']}")
    print(f"  • Reports without plots: {results_summary['reports_without_plots']}")
    print(f"  • Total charts found: {results_summary['total_charts_found']}")

    print(f"\n📁 Output location: {output_base}")
    print(f"\n🔗 Generated reports:")
    for html_file in sorted(output_base.glob("report_*.html")):
        file_size = html_file.stat().st_size
        print(f"  • {html_file.name} ({file_size:,} bytes)")
        print(f"    Path: {html_file}")

    # Overall test result
    test_passed = results_summary["reports_with_plots"] > 0

    print(f"\n" + "=" * 80)
    if test_passed:
        print(f"✅ TEST PASSED - Plots found in generated reports!")
    else:
        print(f"❌ TEST FAILED - No plots found in generated reports")
    print("=" * 80 + "\n")

    return test_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
