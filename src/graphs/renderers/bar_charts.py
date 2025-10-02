"""Bar chart renderers."""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any


def render_bar_chart(
    data: Dict[str, Any],
    config: Dict[str, Any],
    output_path: Path
) -> None:
    """Render a bar chart.

    Args:
        data: Chart data including categories and values
        config: Chart configuration
        output_path: Output file path
    """
    fig, ax = plt.subplots(figsize=config.get('figsize', (10, 6)))

    # Extract data
    chart_data = data['data']
    styling = data.get('styling', {})

    categories = chart_data.get('periods', chart_data.get('categories', []))
    values = chart_data.get('compliance_percentage', chart_data.get('values', []))
    colors = styling.get('colors', ['#4CAF50'] * len(categories))

    # Create bars
    x_pos = np.arange(len(categories))
    bars = ax.bar(x_pos, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)

    # Add threshold line if specified
    if 'threshold_line' in styling:
        ax.axhline(
            y=styling['threshold_line'],
            color='red',
            linestyle='--',
            linewidth=2,
            label=f"Target: {styling['threshold_line']}%"
        )

    # Labels and formatting
    ax.set_xlabel(styling.get('xlabel', 'Category'), fontsize=12, fontweight='bold')
    ax.set_ylabel(styling.get('ylabel', 'Value'), fontsize=12, fontweight='bold')
    ax.set_title(data.get('title', 'Bar Chart'), fontsize=14, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, rotation=45, ha='right')

    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, values)):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height + max(values) * 0.01,
            f'{value:.1f}%' if isinstance(value, (int, float)) else str(value),
            ha='center',
            va='bottom',
            fontweight='bold'
        )

    # Legend if configured
    if config.get('show_legend', True) and 'threshold_line' in styling:
        ax.legend()

    # Grid
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=config.get('dpi', 300), bbox_inches='tight')
    plt.close()


def render_grouped_bar_chart(
    data: Dict[str, Any],
    config: Dict[str, Any],
    output_path: Path
) -> None:
    """Render a grouped bar chart for comparing multiple metrics.

    Args:
        data: Chart data with multiple series
        config: Chart configuration
        output_path: Output file path
    """
    fig, ax = plt.subplots(figsize=config.get('figsize', (12, 6)))

    chart_data = data['data']
    styling = data.get('styling', {})

    categories = chart_data['categories']
    series_data = chart_data['series']  # List of {name, values, color}

    x = np.arange(len(categories))
    width = 0.8 / len(series_data)

    # Plot each series
    for i, series in enumerate(series_data):
        offset = (i - len(series_data) / 2) * width + width / 2
        ax.bar(
            x + offset,
            series['values'],
            width,
            label=series['name'],
            color=series.get('color', f'C{i}'),
            alpha=0.8,
            edgecolor='black',
            linewidth=0.8
        )

    # Formatting
    ax.set_xlabel(styling.get('xlabel', 'Category'), fontsize=12, fontweight='bold')
    ax.set_ylabel(styling.get('ylabel', 'Value'), fontsize=12, fontweight='bold')
    ax.set_title(data.get('title', 'Grouped Bar Chart'), fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=config.get('dpi', 300), bbox_inches='tight')
    plt.close()
