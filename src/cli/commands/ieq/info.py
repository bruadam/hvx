"""IEQ info command - terminology explanations."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


@click.command(name='info')
def info():
    """Show IEQ terminology and quick explanations."""
    title = "IEQ Terminology — Quick Reference"

    md = Markdown(
        """
# Terminology

- **IEQ (Indoor Environmental Quality)**: Overall measure of the indoor environment including air quality, thermal comfort, acoustic comfort and lighting.

- **Compliance Rate**: Percentage of measurements meeting the defined thresholds (defined in tests.yaml) for a given metric (e.g., temperature, CO2).

- **Quality Score**: In this project, "quality" primarily measures data completeness and reliability. This refers to how complete and reliable the measured data is (missing values lower the score).

- **Building / Portfolio**: A building is a single physical site; a portfolio is a collection of buildings analyzed together.

- **Room / Level**: Rooms are the smallest analyzed units (sensor groups); levels group rooms vertically in a building.

- **Hierarchical Analysis**: Analysis that aggregates metrics from rooms → levels → buildings → portfolio.

- **Smart Recommendations**: Automated suggestions generated from analysis to improve IEQ (e.g., ventilation adjustments).

- **Dataset**: Serialized (pickle) representation of the loaded building data used as input for analysis.

- **Analysis Directory**: Output folder containing JSON summaries and artifacts produced by the hierarchical analysis.


For more details see the docs: [docs/QUICKSTART.md]
"""
    )

    panel = Panel.fit(md, title=title, border_style="cyan")
    console.print(panel)
