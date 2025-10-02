"""Heatmap renderers."""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any


def render_heatmap(
    data: Dict[str, Any],
    config: Dict[str, Any],
    output_path: Path
) -> None:
    """Render a heatmap.

    Args:
        data: Chart data with 2D matrix
        config: Chart configuration
        output_path: Output file path
    """
    fig, ax = plt.subplots(figsize=config.get('figsize', (14, 8)))

    chart_data = data['data']
    styling = data.get('styling', {})

    # Create heatmap matrix
    matrix = np.array(chart_data.get('occupancy_matrix', chart_data.get('matrix', [])))

    # Normalize if configured
    if config.get('normalize', False):
        matrix = matrix / 100.0 if matrix.max() > 1 else matrix

    # Select colormap
    cmap = config.get('color_scheme', styling.get('colormap', 'viridis'))

    # Create heatmap
    sns.heatmap(
        matrix,
        xticklabels=chart_data.get('hours', chart_data.get('x_labels', [])),
        yticklabels=chart_data.get('days', chart_data.get('y_labels', [])),
        cmap=cmap,
        annot=config.get('show_values', False),
        fmt='.1f' if config.get('show_values', False) else '',
        cbar_kws={'label': styling.get('colorbar_label', 'Value')},
        linewidths=0.5,
        linecolor='gray',
        square=config.get('square', False),
        vmin=config.get('vmin'),
        vmax=config.get('vmax'),
        ax=ax
    )

    # Formatting
    ax.set_xlabel(styling.get('xlabel', 'X Axis'), fontsize=12, fontweight='bold')
    ax.set_ylabel(styling.get('ylabel', 'Y Axis'), fontsize=12, fontweight='bold')
    ax.set_title(data.get('title', 'Heatmap'), fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=config.get('dpi', 300), bbox_inches='tight')
    plt.close()


def render_correlation_matrix(
    data: Dict[str, Any],
    config: Dict[str, Any],
    output_path: Path
) -> None:
    """Render a correlation matrix heatmap.

    Args:
        data: Chart data with correlation matrix
        config: Chart configuration
        output_path: Output file path
    """
    fig, ax = plt.subplots(figsize=config.get('figsize', (10, 8)))

    chart_data = data['data']
    styling = data.get('styling', {})

    matrix = np.array(chart_data['correlation_matrix'])
    labels = chart_data['parameters']

    # Create mask for upper triangle if configured
    mask = None
    if config.get('show_lower_triangle_only', False):
        mask = np.triu(np.ones_like(matrix, dtype=bool))

    # Create heatmap
    sns.heatmap(
        matrix,
        mask=mask,
        xticklabels=labels,
        yticklabels=labels,
        cmap='coolwarm',
        annot=True,
        fmt='.2f',
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={'label': 'Correlation'},
        ax=ax
    )

    ax.set_title(data.get('title', 'Correlation Matrix'), fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=config.get('dpi', 300), bbox_inches='tight')
    plt.close()
