#!/usr/bin/env python3
"""
Test script for report generation system.

Demonstrates:
1. Loading report templates from YAML
2. Generating sample IEQ data
3. Running analytics
4. Generating comprehensive HTML reports
"""

from pathlib import Path
from core.infrastructure.data_loaders.csv_loader import CSVDataLoader
from core.reporting import ReportGenerator, TemplateLoader
from core.domain.models.dataset import Dataset


def create_sample_data(output_dir: Path, num_rooms: int = 5) -> Path:
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

    print(f"Creating sample data for {num_rooms} rooms...")

    for i in range(1, num_rooms + 1):
        room_file = data_dir / f"room_{i:02d}.csv"
        # Create 7 days of data (168 hours)
        CSVDataLoader.create_sample_csv(room_file, periods=168)
        print(f"  ✓ Created {room_file.name}")

    print(f"Sample data created in: {data_dir}")
    return data_dir


def load_rooms_from_directory(data_dir: Path, building_name: str = "Test Building"):
    """
    Load all room data from directory.

    Args:
        data_dir: Directory containing CSV files
        building_name: Name of building

    Returns:
        List of Room entities
    """
    print(f"\nLoading rooms from {data_dir}...")

    loader = CSVDataLoader()
    rooms = []

    for csv_file in sorted(data_dir.glob("room_*.csv")):
        room_id = csv_file.stem
        room_name = room_id.replace("_", " ").title()

        room = loader.load_room(csv_file, room_id, room_name)
        rooms.append(room)
        record_count = len(room.time_series_data) if room.time_series_data is not None else 0
        print(f"  ✓ Loaded {room_name} ({record_count} records)")

    print(f"Loaded {len(rooms)} rooms")
    return rooms


def generate_reports(
    rooms: list, building_name: str, templates_dir: Path, output_dir: Path
):
    """
    Generate reports from all available templates.

    Args:
        rooms: List of Room entities
        building_name: Name of building
        templates_dir: Directory containing template YAML files
        output_dir: Output directory for reports
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating reports...")
    print(f"Templates directory: {templates_dir}")
    print(f"Output directory: {output_dir}")

    # Initialize report generator
    generator = ReportGenerator()

    # List available templates
    templates = TemplateLoader.list_templates(templates_dir)

    if not templates:
        print(f"  ⚠ No templates found in {templates_dir}")
        return

    print(f"\nFound {len(templates)} templates:")
    for name, path in templates.items():
        print(f"  - {name} ({path.name})")

    # Generate report from each template
    print("\nGenerating reports...")

    for template_name, template_path in templates.items():
        try:
            print(f"\n  Processing: {template_name}")

            # Load template
            template = TemplateLoader.load_from_file(template_path)
            print(f"    Template type: {template.report_type}")
            print(f"    Sections: {len(template.sections)}")

            # Generate output filename
            output_file = output_dir / f"{template_name}.html"

            # Generate report
            generator.generate_report(template, rooms, building_name, output_file)

            print(f"    ✓ Report generated: {output_file}")

        except Exception as e:
            print(f"    ✗ Error: {e}")

    print(f"\n✓ Report generation complete!")
    print(f"\nGenerated reports are in: {output_dir}")
    print("\nTo view reports, open the HTML files in a browser:")
    for html_file in output_dir.glob("*.html"):
        print(f"  - {html_file}")


def main():
    """Main test function."""
    print("=" * 70)
    print("IEQ Analytics - Report Generation Test")
    print("=" * 70)

    # Setup paths
    base_dir = Path(__file__).parent
    output_base = base_dir / "output" / "reports"
    templates_dir = base_dir / "config" / "report_templates"

    # Step 1: Create sample data
    print("\n[Step 1/3] Creating sample data...")
    data_dir = create_sample_data(output_base, num_rooms=8)

    # Step 2: Load rooms
    print("\n[Step 2/3] Loading room data...")
    rooms = load_rooms_from_directory(data_dir, building_name="Building A")

    if not rooms:
        print("  ✗ No rooms loaded. Exiting.")
        return

    # Step 3: Generate reports from all templates
    print("\n[Step 3/3] Generating reports...")
    reports_output = output_base / "generated_reports"
    generate_reports(rooms, "Building A", templates_dir, reports_output)

    # Summary
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)
    print(f"\nGenerated files:")
    print(f"  Sample data: {data_dir}")
    print(f"  Reports: {reports_output}")
    print("\nNext steps:")
    print("  1. Open the HTML reports in your browser")
    print("  2. Customize YAML templates in: config/report_templates/")
    print("  3. Create your own templates for specific use cases")


if __name__ == "__main__":
    main()
