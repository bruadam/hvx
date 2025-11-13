"""CLI commands for TAIL rating visualizations."""

from pathlib import Path

import click
from rich.console import Console

from core.application.use_cases.generate_tail_chart import GenerateTAILChartUseCase
from core.application.use_cases.load_analysis import LoadAnalysisUseCase

console = Console()


@click.group()
def tail():
    """Generate TAIL rating circular charts."""
    pass


@tail.command(name='generate')
@click.option('--session', '-s', help='Load from saved session', required=True)
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output directory')
@click.pass_context
def generate_tail_chart(ctx, session, output):
    """
    Generate TAIL rating circular chart from analysis session.

    The TAIL rating scheme (Thermal, Acoustic, Indoor Air Quality, Luminous)
    provides a visual rating of building environmental quality using a
    circular chart with color-coded ratings.

    Examples:
        hvx tail generate --session my_analysis
        hvx tail generate --session my_analysis --output charts/
    """
    console.print("\n[cyan]Generating TAIL Rating Chart...[/cyan]\n")

    try:
        # Load analysis session
        console.print(f"Loading session: {session}")
        load_use_case = LoadAnalysisUseCase()
        session_data = load_use_case.execute_load_session(session)

        if not session_data.get('building_analysis'):
            console.print("[red]✗ No building analysis found in session[/red]")
            ctx.exit(1)

        # Get building info
        building_analysis = session_data['building_analysis']
        building_name = building_analysis.building_name

        # For now, we'll use the raw data from JSON since full reconstruction
        # isn't implemented yet. This is a demonstration of the feature.
        console.print("[yellow]Note: Using simplified data for chart generation[/yellow]")

        # Generate TAIL chart
        GenerateTAILChartUseCase()

        # Create a demo chart with the building data
        # In production, would use actual room_analyses
        from core.reporting.charts.tail_circular_chart import (
            TAILCircularChart,
            TAILRatingCalculator,
        )

        # Calculate rating from compliance
        compliance = building_analysis.avg_compliance_rate
        overall_rating = TAILRatingCalculator._compliance_to_rating(compliance)

        # Set output path
        if output:
            output_dir = Path(output)
        else:
            output_dir = Path("output/tail_charts")

        output_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"{building_name.replace(' ', '_')}_TAIL_{timestamp}.png"

        # Create chart
        chart = TAILCircularChart(figsize=(10, 10))
        fig = chart.create(
            overall_rating=overall_rating,
            thermal_rating=overall_rating,
            acoustic_rating=None,
            iaq_rating=overall_rating,
            luminous_rating=None,
            detailed_ratings={
                "temp": overall_rating,
                "co2": overall_rating,
                "humid": overall_rating,
            },
            building_name=building_name,
            save_path=output_path
        )

        import matplotlib.pyplot as plt
        plt.close(fig)

        console.print(f"\n[green]✓ TAIL chart generated:[/green] {output_path}")
        console.print(f"  Building: {building_name}")
        console.print(f"  Overall Rating: {TAILCircularChart.ROMAN_NUMERALS[overall_rating]} ({overall_rating}/4)")
        console.print(f"  Compliance: {compliance:.1f}%")

    except FileNotFoundError as e:
        console.print(f"[red]✗ Session not found:[/red] {e}")
        ctx.exit(1)
    except Exception as e:
        console.print(f"\n[red]✗ Chart generation failed:[/red] {str(e)}")
        if ctx.obj.get('verbose'):
            console.print_exception()
        ctx.exit(1)


@tail.command(name='about')
@click.pass_context
def about_tail(ctx):
    """
    Learn about the TAIL Rating Scheme.
    """
    console.print("\n[bold cyan]About TAIL Rating Scheme[/bold cyan]\n")

    console.print("[bold]TAIL[/bold] stands for:")
    console.print("  • [green]T[/green]hermal - Temperature comfort")
    console.print("  • [green]A[/green]coustic - Noise levels")
    console.print("  • [green]I[/green]ndoor Air Quality - CO2, humidity, pollutants")
    console.print("  • [green]L[/green]uminous - Lighting and daylight")

    console.print("\n[bold]Rating Scale:[/bold]")
    console.print("  [green]I - Green[/green]    Best quality (≥95% compliant)")
    console.print("  [yellow]II - Yellow[/yellow]   Good quality (70-95% compliant)")
    console.print("  [#ffb347]III - Orange[/#ffb347]  Fair quality (50-70% compliant)")
    console.print("  [red]IV - Red[/red]      Poor quality (<50% compliant)")

    console.print("\n[bold]Reference:[/bold]")
    console.print("  TAIL Rating Scheme was developed by the ALDREN project")
    console.print("  https://github.com/asitkm76/TAILRatingScheme")
    console.print("  https://www.sciencedirect.com/science/article/pii/S0378778821003133")

    console.print("\n[bold]Usage:[/bold]")
    console.print("  hvx tail generate --session my_analysis")
    console.print()
