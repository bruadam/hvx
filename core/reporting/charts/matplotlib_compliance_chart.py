"""Matplotlib compliance and performance chart renderers for clean architecture."""

from pathlib import Path
from typing import Any

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


def render_compliance_chart(
    data: dict[str, Any],
    config: dict[str, Any],
    output_path: Path
) -> None:
    """Render a compliance overview chart.

    Args:
        data: Chart data with compliance metrics
        config: Chart configuration
        output_path: Output file path
    """
    fig, ax = plt.subplots(figsize=config.get('figsize', (10, 6)))

    chart_data = data['data']
    styling = data.get('styling', {})

    categories = chart_data['categories']
    compliance_rates = chart_data['compliance_rates']

    # Define color scheme based on compliance level
    colors = []
    for rate in compliance_rates:
        if rate >= 95:
            colors.append('#4CAF50')  # Green - Excellent
        elif rate >= 85:
            colors.append('#FFC107')  # Yellow - Good
        elif rate >= 70:
            colors.append('#FF9800')  # Orange - Fair
        else:
            colors.append('#F44336')  # Red - Poor

    # Create bars
    bars = ax.bar(categories, compliance_rates, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)

    # Add threshold lines
    ax.axhline(y=95, color='green', linestyle='--', linewidth=1, alpha=0.5, label='Excellent (95%)')
    ax.axhline(y=85, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='Good (85%)')
    ax.axhline(y=70, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Minimum (70%)')

    # Add value labels
    for bar, value in zip(bars, compliance_rates, strict=False):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height + 2,
            f'{value:.1f}%',
            ha='center',
            va='bottom',
            fontweight='bold',
            fontsize=10
        )

    # Formatting
    ax.set_xlabel(styling.get('xlabel', 'Category'), fontsize=12, fontweight='bold')
    ax.set_ylabel(styling.get('ylabel', 'Compliance (%)'), fontsize=12, fontweight='bold')
    ax.set_title(data.get('title', 'Compliance Overview'), fontsize=14, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.legend(loc='lower right', fontsize=9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path, dpi=config.get('dpi', 300), bbox_inches='tight')
    plt.close()


def render_performance_matrix(
    data: dict[str, Any],
    config: dict[str, Any],
    output_path: Path
) -> None:
    """Render a performance matrix (scatter plot with quadrants).

    Args:
        data: Chart data with x/y performance metrics
        config: Chart configuration
        output_path: Output file path
    """
    fig, ax = plt.subplots(figsize=config.get('figsize', (10, 10)))

    chart_data = data['data']
    styling = data.get('styling', {})

    x_values = chart_data['x_values']  # e.g., compliance rate
    y_values = chart_data['y_values']  # e.g., data quality
    labels = chart_data.get('labels', [f'Item {i}' for i in range(len(x_values))])

    # Define quadrant boundaries
    x_threshold = config.get('x_threshold', 85)
    y_threshold = config.get('y_threshold', 90)

    # Color code by quadrant
    colors = []
    for x, y in zip(x_values, y_values, strict=False):
        if x >= x_threshold and y >= y_threshold:
            colors.append('#4CAF50')  # Green - High/High
        elif x >= x_threshold:
            colors.append('#FFC107')  # Yellow - High/Low
        elif y >= y_threshold:
            colors.append('#2196F3')  # Blue - Low/High
        else:
            colors.append('#F44336')  # Red - Low/Low

    # Scatter plot
    ax.scatter(x_values, y_values, c=colors, s=200, alpha=0.6, edgecolors='black', linewidth=1.5)

    # Add labels for each point
    for i, label in enumerate(labels):
        ax.annotate(
            label,
            (x_values[i], y_values[i]),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=8,
            fontweight='bold'
        )

    # Draw quadrant lines
    ax.axvline(x=x_threshold, color='gray', linestyle='--', linewidth=2, alpha=0.5)
    ax.axhline(y=y_threshold, color='gray', linestyle='--', linewidth=2, alpha=0.5)

    # Add quadrant labels
    ax.text(x_threshold + 2, ax.get_ylim()[1] - 2, 'High Performance',
            fontsize=10, ha='left', va='top', style='italic', alpha=0.7)
    ax.text(x_threshold - 2, ax.get_ylim()[0] + 2, 'Needs Improvement',
            fontsize=10, ha='right', va='bottom', style='italic', alpha=0.7)

    # Formatting
    ax.set_xlabel(styling.get('xlabel', 'X Metric'), fontsize=12, fontweight='bold')
    ax.set_ylabel(styling.get('ylabel', 'Y Metric'), fontsize=12, fontweight='bold')
    ax.set_title(data.get('title', 'Performance Matrix'), fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Legend
    legend_elements = [
        mpatches.Patch(color='#4CAF50', label='High/High'),
        mpatches.Patch(color='#FFC107', label='High/Low'),
        mpatches.Patch(color='#2196F3', label='Low/High'),
        mpatches.Patch(color='#F44336', label='Low/Low')
    ]
    ax.legend(handles=legend_elements, loc='lower right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=config.get('dpi', 300), bbox_inches='tight')
    plt.close()
