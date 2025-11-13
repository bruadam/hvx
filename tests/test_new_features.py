#!/usr/bin/env python3
"""
Test script for new reporting features:
1. Room looping (room_details section)
2. Building statistics (building_statistics section)
3. Graph export in HTML
"""

from pathlib import Path
from core.infrastructure.data_loaders.csv_loader import CSVDataLoader
from core.reporting import ReportGenerator, TemplateLoader
from core.domain.models.dataset import Dataset


def main():
    """Test the new reporting features."""
    print("=" * 70)
    print("Testing New Reporting Features")
    print("=" * 70)

    # Setup paths
    base_dir = Path(__file__).parent
    templates_dir = base_dir / "config" / "report_templates"
    output_dir = base_dir / "output" / "test_reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use existing test data
    data_dir = base_dir / "data" / "building_b"

    print(f"\n[1/3] Loading room data from {data_dir}...")

    # Load rooms
    loader = CSVDataLoader()
    rooms = []

    for csv_file in sorted(data_dir.glob("*.csv")):
        room_id = csv_file.stem
        room_name = room_id.replace("_", " ").title()

        room = loader.load_room(csv_file, room_id, room_name)
        rooms.append(room)
        record_count = len(room.time_series_data) if room.time_series_data is not None else 0
        print(f"  ✓ Loaded {room_name} ({record_count} records)")

    print(f"\nTotal rooms loaded: {len(rooms)}")

    if not rooms:
        print("  ✗ No rooms loaded. Exiting.")
        return

    print(f"\n[2/3] Loading report templates...")

    # Test with the new detailed room-by-room template
    template_name = "detailed_room_by_room_report"
    template_path = templates_dir / f"{template_name}.yaml"

    if not template_path.exists():
        print(f"  ✗ Template not found: {template_path}")
        return

    print(f"  ✓ Found template: {template_name}")

    # Load template
    template = TemplateLoader.load_from_file(template_path)
    print(f"    - Type: {template.report_type}")
    print(f"    - Sections: {len(template.sections)}")

    # Print section types
    section_types = [s.type for s in template.sections]
    print(f"    - Section types: {', '.join(section_types)}")

    print(f"\n[3/3] Generating report...")

    # Generate report
    generator = ReportGenerator()
    output_file = output_dir / f"test_{template_name}.html"

    try:
        generator.generate_report(template, rooms, "Building B", output_file)
        print(f"  ✓ Report generated: {output_file}")
        print(f"\n{'=' * 70}")
        print("Success!")
        print("=" * 70)
        print(f"\nOpen the report in your browser:")
        print(f"  file://{output_file}")

        # Check file size
        file_size = output_file.stat().st_size / 1024  # KB
        print(f"\nReport file size: {file_size:.2f} KB")

        # Count sections in generated HTML
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            section_count = content.count('<section')
            chart_count = content.count('class="chart-container"')
            room_card_count = content.count('class="room-detail-card"')

        print(f"Generated content:")
        print(f"  - Sections: {section_count}")
        print(f"  - Charts: {chart_count}")
        print(f"  - Room detail cards: {room_card_count}")

    except Exception as e:
        print(f"  ✗ Error generating report: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
