"""
Complete IEQ Analytics Pipeline Test

This script demonstrates the entire analytics pipeline from data loading to aggregation.
It creates sample data, loads it, runs analysis, and generates results.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))

# Import domain models
from core.domain.models.room import Room
from core.domain.models.level import Level
from core.domain.models.building import Building
from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.standard_type import StandardType
from core.domain.enums.building_type import BuildingType

# Import analytics
from core.analytics.engine.analysis_engine import AnalysisEngine
from core.analytics.aggregators.building_aggregator import BuildingAggregator
from core.analytics.aggregators.portfolio_aggregator import PortfolioAggregator

# Import data loaders
from core.infrastructure.data_loaders.csv_loader import CSVDataLoader
from core.infrastructure.data_loaders.dataset_builder import DatasetBuilder


def print_header(text: str) -> None:
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_section(text: str) -> None:
    """Print formatted section."""
    print("\n" + "-" * 80)
    print(f"  {text}")
    print("-" * 80)


def create_sample_data() -> Path:
    """Create sample CSV data for testing."""
    print_header("STEP 1: Creating Sample Data")

    data_dir = Path("data/test_building")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create sample data for 3 rooms
    csv_loader = CSVDataLoader()

    room_files = []
    for i in range(1, 4):
        file_path = data_dir / f"room_{i:03d}.csv"
        csv_loader.create_sample_csv(
            output_path=file_path,
            start_date="2024-01-01",
            periods=168,  # 1 week of hourly data
            freq="H",
        )
        room_files.append(file_path)

    print(f"✓ Created {len(room_files)} sample CSV files in {data_dir}")
    return data_dir


def load_data(data_dir: Path) -> tuple:
    """Load data using data loaders."""
    print_header("STEP 2: Loading Data")

    csv_loader = CSVDataLoader()

    # Load rooms from CSV files
    csv_files = list(data_dir.glob("*.csv"))
    print(f"Found {len(csv_files)} CSV files")

    rooms = []
    for i, csv_file in enumerate(csv_files, 1):
        room_id = f"R{i:03d}"
        room_name = f"Room {i:03d}"

        room = csv_loader.load_room(
            file_path=csv_file,
            room_id=room_id,
            room_name=room_name,
            building_id="B001",
            level_id="L001",
        )

        rooms.append(room)
        print(f"✓ Loaded {room_name}:")
        print(f"    Data points: {room.get_measurement_count()}")
        print(f"    Parameters: {[p.value for p in room.available_parameters]}")
        print(f"    Completeness: {room.get_data_completeness():.1f}%")

    # Create level and building
    level = Level(
        id="L001",
        name="Ground Floor",
        building_id="B001",
        floor_number=0,
    )

    for room in rooms:
        level.add_room(room.id)

    building = Building(
        id="B001",
        name="Test Building",
        building_type=BuildingType.OFFICE,
    )
    building.add_level(level.id)

    print(f"\n✓ Created building structure:")
    print(f"    Building: {building.name}")
    print(f"    Levels: {building.level_count}")
    print(f"    Rooms: {level.room_count}")

    return rooms, level, building


def define_compliance_tests() -> list:
    """Define compliance tests to run."""
    print_header("STEP 3: Defining Compliance Tests")

    tests = [
        {
            "test_id": "en16798_temp_cat_i",
            "parameter": ParameterType.TEMPERATURE,
            "standard": StandardType.EN16798_1,
            "threshold": {"lower": 20.0, "upper": 24.0, "unit": "°C"},
            "compliance_level": 95.0,
            "filter": {"type": "opening_hours", "hours": (8, 18)},
        },
        {
            "test_id": "en16798_temp_cat_ii",
            "parameter": ParameterType.TEMPERATURE,
            "standard": StandardType.EN16798_1,
            "threshold": {"lower": 19.0, "upper": 26.0, "unit": "°C"},
            "compliance_level": 95.0,
            "filter": {"type": "opening_hours", "hours": (8, 18)},
        },
        {
            "test_id": "en16798_co2_cat_i",
            "parameter": ParameterType.CO2,
            "standard": StandardType.EN16798_1,
            "threshold": {"upper": 800.0, "unit": "ppm"},
            "compliance_level": 95.0,
        },
        {
            "test_id": "en16798_co2_cat_ii",
            "parameter": ParameterType.CO2,
            "standard": StandardType.EN16798_1,
            "threshold": {"upper": 950.0, "unit": "ppm"},
            "compliance_level": 95.0,
        },
    ]

    print(f"Defined {len(tests)} compliance tests:")
    for test in tests:
        print(f"  • {test['test_id']}: {test['parameter'].display_name} "
              f"({test['standard'].value})")

    return tests


def analyze_rooms(rooms: list, tests: list) -> list:
    """Run analysis on all rooms."""
    print_header("STEP 4: Analyzing Rooms")

    engine = AnalysisEngine()
    room_analyses = []

    for room in rooms:
        print(f"\nAnalyzing {room.name}...")

        analysis = engine.analyze_room(
            room=room,
            tests=tests,
            apply_filters=True,
        )

        room_analyses.append(analysis)

        print(f"  ✓ Overall compliance: {analysis.overall_compliance_rate:.1f}%")
        print(f"  ✓ Data quality score: {analysis.data_quality_score:.1f}%")
        print(f"  ✓ Tests performed: {analysis.test_count}")
        print(f"  ✓ Passed: {len(analysis.passed_tests)}, Failed: {len(analysis.failed_tests)}")
        print(f"  ✓ Total violations: {analysis.total_violations}")

        if analysis.critical_issues:
            print(f"  ⚠ Critical issues: {len(analysis.critical_issues)}")

    return room_analyses


def display_detailed_results(room_analyses: list) -> None:
    """Display detailed analysis results."""
    print_header("STEP 5: Detailed Results by Room")

    for analysis in room_analyses:
        print_section(f"Room: {analysis.room_name}")

        print(f"\nOverall Metrics:")
        print(f"  Compliance Rate: {analysis.overall_compliance_rate:.2f}%")
        print(f"  Data Quality: {analysis.data_quality_score:.2f}%")
        print(f"  Data Completeness: {analysis.data_completeness:.2f}%")

        print(f"\nTest Results ({analysis.test_count} tests):")
        for test_id, result in analysis.compliance_results.items():
            status = "✓ PASS" if result.is_compliant else "✗ FAIL"
            print(f"  {status} {test_id}")
            print(f"      Compliance: {result.compliance_rate:.1f}%")
            print(f"      Points: {result.compliant_points}/{result.total_points}")
            print(f"      Violations: {result.violation_count}")

            if result.violation_count > 0:
                severity = result.get_severity_breakdown()
                print(f"      Severity: Critical={severity['critical']}, "
                      f"Major={severity['major']}, "
                      f"Moderate={severity['moderate']}, "
                      f"Minor={severity['minor']}")

        if analysis.recommendations:
            print(f"\nRecommendations:")
            for rec in analysis.recommendations[:3]:
                print(f"  • {rec}")

        if analysis.critical_issues:
            print(f"\nCritical Issues:")
            for issue in analysis.critical_issues:
                print(f"  ⚠ {issue}")


def aggregate_to_building(building: Building, room_analyses: list) -> None:
    """Aggregate room analyses to building level."""
    print_header("STEP 6: Building-Level Aggregation")

    building_analysis = BuildingAggregator.aggregate(
        building=building,
        room_analyses=room_analyses,
    )

    print(f"Building: {building_analysis.building_name}")
    print(f"\nBuilding Metrics:")
    print(f"  Overall Compliance: {building_analysis.avg_compliance_rate:.2f}%")
    print(f"  Compliance Grade: {building_analysis.compliance_grade}")
    print(f"  Average Quality Score: {building_analysis.avg_quality_score:.2f}%")
    print(f"  Total Rooms Analyzed: {building_analysis.room_count}")
    print(f"  Total Violations: {building_analysis.total_violations}")

    print(f"\nTest Aggregations:")
    for test_id, agg in building_analysis.test_aggregations.items():
        print(f"  {test_id}:")
        print(f"    Average Compliance: {agg['avg_compliance_rate']:.1f}%")
        print(f"    Range: {agg['min_compliance_rate']:.1f}% - {agg['max_compliance_rate']:.1f}%")
        print(f"    Rooms Passed: {agg['rooms_passed']}/{agg['rooms_tested']}")

    print(f"\nBest Performing Rooms:")
    for room in building_analysis.best_performing_rooms[:3]:
        print(f"  • {room['room_name']}: {room['compliance_rate']:.1f}%")

    print(f"\nWorst Performing Rooms:")
    for room in building_analysis.worst_performing_rooms[:3]:
        print(f"  • {room['room_name']}: {room['compliance_rate']:.1f}%")

    if building_analysis.recommendations:
        print(f"\nBuilding-Wide Recommendations:")
        for rec in building_analysis.recommendations[:3]:
            print(f"  • {rec}")

    return building_analysis


def aggregate_to_portfolio(building_analyses: list) -> None:
    """Aggregate building analyses to portfolio level."""
    print_header("STEP 7: Portfolio-Level Aggregation")

    portfolio_analysis = PortfolioAggregator.aggregate(
        portfolio_id="PF001",
        portfolio_name="Test Portfolio",
        building_analyses=building_analyses,
    )

    print(f"Portfolio: {portfolio_analysis.portfolio_name}")
    print(f"\nPortfolio Metrics:")
    print(f"  Overall Compliance: {portfolio_analysis.avg_compliance_rate:.2f}%")
    print(f"  Compliance Grade: {portfolio_analysis.compliance_grade}")
    print(f"  Average Quality Score: {portfolio_analysis.avg_quality_score:.2f}%")
    print(f"  Total Buildings: {portfolio_analysis.building_count}")
    print(f"  Total Rooms: {portfolio_analysis.total_room_count}")
    print(f"  Total Violations: {portfolio_analysis.total_violations}")

    print(f"\nBuilding Comparison:")
    for building_id, summary in portfolio_analysis.building_summaries.items():
        print(f"  {summary['building_name']}:")
        print(f"    Compliance: {summary['avg_compliance_rate']:.1f}% [{summary['compliance_grade']}]")
        print(f"    Rooms: {summary['room_count']}")
        print(f"    Violations: {summary['total_violations']}")

    if portfolio_analysis.portfolio_recommendations:
        print(f"\nPortfolio-Level Recommendations:")
        for rec in portfolio_analysis.portfolio_recommendations:
            print(f"  • {rec}")


def export_results(room_analyses: list, building_analysis, output_dir: Path) -> None:
    """Export results to JSON files."""
    print_header("STEP 8: Exporting Results")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Export room analyses
    for analysis in room_analyses:
        output_file = output_dir / f"room_{analysis.room_id}_analysis.json"
        summary = analysis.to_summary_dict()

        import json
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"✓ Exported {analysis.room_name} analysis to {output_file}")

    # Export building analysis
    building_file = output_dir / "building_analysis.json"
    building_summary = building_analysis.to_summary_dict()

    with open(building_file, "w") as f:
        json.dump(building_summary, f, indent=2, default=str)

    print(f"✓ Exported building analysis to {building_file}")
    print(f"\nAll results exported to: {output_dir}")


def main():
    """Run complete pipeline test."""
    print_header("IEQ Analytics Complete Pipeline Test")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Step 1: Create sample data
        data_dir = create_sample_data()

        # Step 2: Load data
        rooms, level, building = load_data(data_dir)

        # Step 3: Define tests
        tests = define_compliance_tests()

        # Step 4: Analyze rooms
        room_analyses = analyze_rooms(rooms, tests)

        # Step 5: Display detailed results
        display_detailed_results(room_analyses)

        # Step 6: Aggregate to building
        building_analysis = aggregate_to_building(building, room_analyses)

        # Step 7: Aggregate to portfolio
        aggregate_to_portfolio([building_analysis])

        # Step 8: Export results
        export_results(room_analyses, building_analysis, Path("output/test_results"))

        print_header("✓ PIPELINE TEST COMPLETED SUCCESSFULLY")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print_header("✗ PIPELINE TEST FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
