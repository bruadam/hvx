"""Matplotlib bar chart renderers for clean architecture."""

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from ..chart_config import get_style_loader


def render_bar_chart(
    data: dict[str, Any],
    config: dict[str, Any],
    output_path: Path
) -> None:
    """Render a bar chart.

    Args:
        data: Chart data including categories and values
        config: Chart configuration
        output_path: Output file path
    """
    # Load style configuration
    style_loader = get_style_loader()
    style_loader.apply_global_style()
    style = style_loader.get_merged_config('bar_chart', config)

    # Get figure settings from style
    figsize = style_loader.get_figsize('bar_chart', config)
    dpi = style_loader.get_dpi('bar_chart', config)

    fig, ax = plt.subplots(figsize=figsize)

    # Extract data
    chart_data = data['data']
    styling = data.get('styling', {})

    categories = chart_data.get('periods', chart_data.get('categories', []))
    values = chart_data.get('compliance_percentage', chart_data.get('values', []))

    # Get bar styling from config
    bar_style = style.get('bars', {})
    colors = styling.get('colors', [bar_style.get('colors', {}).get('default', '#3498db')] * len(categories))

    # Create bars
    x_pos = np.arange(len(categories))
    bars = ax.bar(
        x_pos,
        values,
        width=bar_style.get('width', 0.6),
        color=colors,
        alpha=bar_style.get('alpha', 0.8),
        edgecolor=bar_style.get('edgecolor', 'black'),
        linewidth=bar_style.get('linewidth', 1.2)
    )

    # Add threshold line if specified
    threshold_style = style.get('threshold', {})
    if 'threshold_line' in styling and threshold_style.get('enabled', True):
        threshold_value = styling['threshold_line']
        ax.axhline(
            y=threshold_value,
            color=threshold_style.get('color', '#e74c3c'),
            linestyle=threshold_style.get('linestyle', '--'),
            linewidth=threshold_style.get('linewidth', 2),
            alpha=threshold_style.get('alpha', 0.8),
            label=threshold_style.get('label_format', 'Target: {value}%').format(value=threshold_value)
        )

    # Labels and formatting
    title_style = style.get('title', {})
    ax.set_xlabel(styling.get('xlabel', 'Category'))
    ax.set_ylabel(styling.get('ylabel', 'Value'))
    ax.set_title(
        data.get('title', 'Bar Chart'),
        fontsize=title_style.get('fontsize', 14),
        fontweight=title_style.get('fontweight', 'bold'),
        color=title_style.get('color', '#2c3e50'),
        pad=title_style.get('pad', 15)
    )
    ax.set_xticks(x_pos)

    # Apply x-axis rotation from style
    xaxis_style = style.get('xaxis', {})
    ax.set_xticklabels(
        categories,
        rotation=xaxis_style.get('rotation', 45),
        ha=xaxis_style.get('ha', 'right')
    )

    # Add value labels on bars
    value_label_style = bar_style.get('value_labels', {})
    if value_label_style.get('enabled', True):
        offset_factor = value_label_style.get('offset_factor', 0.02)
        label_format = value_label_style.get('format', '{:.1f}%')
        for bar, value in zip(bars, values, strict=False):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height + max(values) * offset_factor,
                label_format.format(value) if isinstance(value, (int, float)) else str(value),
                ha='center',
                va='bottom',
                fontsize=value_label_style.get('fontsize', 9),
                fontweight=value_label_style.get('fontweight', 'bold'),
                color=value_label_style.get('color', '#2c3e50')
            )

    # Legend if configured
    if config.get('show_legend', True) and 'threshold_line' in styling:
        ax.legend()

    # Grid (applied from global style, but can be customized)
    grid_style = style.get('grid', {})
    ax.grid(
        axis=grid_style.get('axis', 'y'),
        alpha=grid_style.get('alpha', 0.3),
        linestyle=grid_style.get('linestyle', '--')
    )
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close()


def render_grouped_bar_chart(
    data: dict[str, Any],
    config: dict[str, Any],
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
