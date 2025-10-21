"""Table components for CLI UI."""

from typing import List
from rich.table import Table
from rich import box

from core.domain.models.room_analysis import RoomAnalysis
from core.domain.models.building_analysis import BuildingAnalysis


def create_room_analysis_table(room_analyses: List[RoomAnalysis], show_details: bool = False) -> Table:
    """Create table displaying room analysis results."""
    table = Table(
        title="Room Analysis Results",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Room", style="cyan", no_wrap=True)
    table.add_column("Compliance", justify="right")
    table.add_column("Grade", justify="center")
    table.add_column("Quality", justify="right")
    if show_details:
        table.add_column("Violations", justify="right")

    for analysis in room_analyses:
        compliance_rate = analysis.overall_compliance_rate
        grade = _get_compliance_grade(compliance_rate)

        # Color code compliance rate
        compliance_color = _get_compliance_color(compliance_rate)
        compliance_str = f"[{compliance_color}]{compliance_rate:.1f}%[/{compliance_color}]"

        # Color code grade
        grade_color = _get_grade_color(grade)
        grade_str = f"[{grade_color}]{grade}[/{grade_color}]"

        quality_str = f"{analysis.data_quality_score:.1f}%"

        if show_details:
            table.add_row(
                analysis.room_name,
                compliance_str,
                grade_str,
                quality_str,
                str(analysis.total_violations)
            )
        else:
            table.add_row(
                analysis.room_name,
                compliance_str,
                grade_str,
                quality_str
            )

    return table


def create_building_summary_table(building_analysis: BuildingAnalysis) -> Table:
    """Create table displaying building summary."""
    table = Table(
        title=f"{building_analysis.building_name} - Summary",
        box=box.ROUNDED,
        show_header=False,
        padding=(0, 2)
    )

    table.add_column("Metric", style="cyan bold")
    table.add_column("Value")

    # Compliance
    compliance_rate = building_analysis.avg_compliance_rate
    grade = building_analysis.compliance_grade
    compliance_color = _get_compliance_color(compliance_rate)
    grade_color = _get_grade_color(grade)

    table.add_row(
        "Overall Compliance",
        f"[{compliance_color}]{compliance_rate:.1f}%[/{compliance_color}] " +
        f"[{grade_color}](Grade {grade})[/{grade_color}]"
    )

    # Quality
    table.add_row(
        "Data Quality",
        f"{building_analysis.avg_quality_score:.1f}%"
    )

    # Rooms
    table.add_row(
        "Rooms Analyzed",
        str(building_analysis.room_count)
    )

    # Violations
    violation_color = "green" if building_analysis.total_violations == 0 else "yellow" if building_analysis.total_violations < 10 else "red"
    table.add_row(
        "Total Violations",
        f"[{violation_color}]{building_analysis.total_violations}[/{violation_color}]"
    )

    return table


def create_test_results_table(room_analysis: RoomAnalysis) -> Table:
    """Create table displaying test results for a room."""
    table = Table(
        title=f"{room_analysis.room_name} - Test Results",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Test ID", style="cyan")
    table.add_column("Compliance", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Violations", justify="right")

    for test_id, result in room_analysis.compliance_results.items():
        compliance_rate = result.compliance_rate
        compliance_color = _get_compliance_color(compliance_rate)
        compliance_str = f"[{compliance_color}]{compliance_rate:.1f}%[/{compliance_color}]"

        status = "✓ Pass" if result.is_compliant else "✗ Fail"
        status_color = "green" if result.is_compliant else "red"
        status_str = f"[{status_color}]{status}[/{status_color}]"

        violation_color = "green" if result.violation_count == 0 else "yellow"
        violation_str = f"[{violation_color}]{result.violation_count}[/{violation_color}]"

        table.add_row(
            test_id,
            compliance_str,
            status_str,
            violation_str
        )

    return table


def create_standards_table(standards: List[dict]) -> Table:
    """Create table displaying available standards."""
    table = Table(
        title="Available Standards",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("#", justify="right", style="cyan")
    table.add_column("Standard", style="bold")
    table.add_column("Description")
    table.add_column("Tests", justify="center")

    for idx, standard in enumerate(standards, 1):
        table.add_row(
            str(idx),
            standard.get('name', 'Unknown'),
            standard.get('description', ''),
            str(standard.get('test_count', 0))
        )

    return table


def _get_compliance_grade(rate: float) -> str:
    """Get grade letter from compliance rate."""
    if rate >= 95:
        return "A"
    elif rate >= 85:
        return "B"
    elif rate >= 70:
        return "C"
    elif rate >= 50:
        return "D"
    else:
        return "F"


def _get_compliance_color(rate: float) -> str:
    """Get color for compliance rate."""
    if rate >= 95:
        return "green"
    elif rate >= 85:
        return "yellow"
    elif rate >= 70:
        return "orange"
    else:
        return "red"


def _get_grade_color(grade: str) -> str:
    """Get color for grade."""
    grade_colors = {
        'A': 'green',
        'B': 'yellow',
        'C': 'orange',
        'D': 'red',
        'F': 'bold red'
    }
    return grade_colors.get(grade, 'white')
