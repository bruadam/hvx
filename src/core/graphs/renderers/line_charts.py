"""Line chart renderers."""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


def render_line_chart(
    data: Dict[str, Any],
    config: Dict[str, Any],
    output_path: Path
) -> None:
    """Render a line chart (time series).

    Args:
        data: Chart data including timestamps and values
        config: Chart configuration
        output_path: Output file path
    """
    fig, ax = plt.subplots(figsize=config.get('figsize', (12, 6)))

    chart_data = data['data']
    styling = data.get('styling', {})

    # Parse timestamps if they're strings
    timestamps = chart_data['timestamps']
    if isinstance(timestamps[0], str):
        timestamps = [datetime.fromisoformat(ts) for ts in timestamps]

    values = chart_data.get('temperature', chart_data.get('values', []))

    # Plot main line
    ax.plot(
        timestamps,
        values,
        color=styling.get('color', '#2196F3'),
        linewidth=config.get('linewidth', 2),
        label=config.get('label', 'Value'),
        marker='o' if config.get('show_markers', False) else None,
        markersize=4
    )

    # Add target band if configured
    if config.get('show_targets', True):
        if 'target_min' in chart_data and 'target_max' in chart_data:
            ax.axhspan(
                chart_data['target_min'],
                chart_data['target_max'],
                color=styling.get('target_band_color', '#E3F2FD'),
                alpha=0.3,
                label='Target Range'
            )

    # Apply moving average if configured
    if config.get('moving_average'):
        window = config['moving_average']
        if window > 0 and window < len(values):
            ma = np.convolve(values, np.ones(window) / window, mode='valid')
            ma_timestamps = timestamps[window - 1:]
            ax.plot(
                ma_timestamps,
                ma,
                color='red',
                linestyle='--',
                linewidth=1.5,
                label=f'{window}h MA',
                alpha=0.7
            )

    # Formatting
    ax.set_xlabel(styling.get('xlabel', 'Time'), fontsize=12, fontweight='bold')
    ax.set_ylabel(styling.get('ylabel', 'Value'), fontsize=12, fontweight='bold')
    ax.set_title(data.get('title', 'Time Series'), fontsize=14, fontweight='bold')

    # Format x-axis for datetime
    if isinstance(timestamps[0], datetime):
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        fig.autofmt_xdate()

    if config.get('show_legend', True):
        ax.legend(loc='best')

    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=config.get('dpi', 300), bbox_inches='tight')
    plt.close()


def render_multi_line_chart(
    data: Dict[str, Any],
    config: Dict[str, Any],
    output_path: Path
) -> None:
    """Render multiple lines on same chart.

    Args:
        data: Chart data with multiple series
        config: Chart configuration
        output_path: Output file path
    """
    fig, ax = plt.subplots(figsize=config.get('figsize', (12, 6)))

    chart_data = data['data']
    styling = data.get('styling', {})

    # Parse timestamps
    timestamps = chart_data['timestamps']
    if isinstance(timestamps[0], str):
        timestamps = [datetime.fromisoformat(ts) for ts in timestamps]

    # Plot each series
    series_data = chart_data['series']  # List of {name, values, color}
    for i, series in enumerate(series_data):
        ax.plot(
            timestamps,
            series['values'],
            color=series.get('color', f'C{i}'),
            linewidth=2,
            label=series['name'],
            alpha=0.8
        )

    # Formatting
    ax.set_xlabel(styling.get('xlabel', 'Time'), fontsize=12, fontweight='bold')
    ax.set_ylabel(styling.get('ylabel', 'Value'), fontsize=12, fontweight='bold')
    ax.set_title(data.get('title', 'Multi-Line Chart'), fontsize=14, fontweight='bold')

    if isinstance(timestamps[0], datetime):
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        fig.autofmt_xdate()

    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=config.get('dpi', 300), bbox_inches='tight')
    plt.close()
