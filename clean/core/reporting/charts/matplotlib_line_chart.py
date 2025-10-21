"""Matplotlib line chart renderers for clean architecture."""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..chart_config import get_style_loader


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
    # Load style configuration
    style_loader = get_style_loader()
    style_loader.apply_global_style()
    style = style_loader.get_merged_config('line_chart', config)

    # Get figure settings
    figsize = style_loader.get_figsize('line_chart', config)
    dpi = style_loader.get_dpi('line_chart', config)

    fig, ax = plt.subplots(figsize=figsize)

    chart_data = data['data']
    styling = data.get('styling', {})

    # Parse timestamps if they're strings
    timestamps = chart_data['timestamps']
    if isinstance(timestamps[0], str):
        timestamps = [datetime.fromisoformat(ts) for ts in timestamps]

    values = chart_data.get('temperature', chart_data.get('values', []))

    # Get line styling from config
    line_style = style.get('lines', {})
    colors = style_loader.get_colors('categorical')

    # Plot main line
    ax.plot(
        timestamps,
        values,
        color=styling.get('color', colors[0]),
        linewidth=line_style.get('linewidth', 2.5),
        label=config.get('label', 'Value'),
        marker=line_style.get('marker') if config.get('show_markers', False) else None,
        markersize=line_style.get('markersize', 5),
        alpha=line_style.get('alpha', 0.9)
    )

    # Add target band if configured
    target_band_style = style.get('target_bands', {})
    if config.get('show_targets', True) and target_band_style.get('enabled', True):
        if 'target_min' in chart_data and 'target_max' in chart_data:
            ax.axhspan(
                chart_data['target_min'],
                chart_data['target_max'],
                color=styling.get('target_band_color', target_band_style.get('color', '#d5f4e6')),
                alpha=target_band_style.get('alpha', 0.15),
                label=target_band_style.get('label', 'Target Range')
            )

    # Apply moving average if configured
    ma_style = style.get('moving_average', {})
    if config.get('moving_average') and ma_style.get('enabled', True):
        window = config['moving_average']
        if window > 0 and window < len(values):
            ma = np.convolve(values, np.ones(window) / window, mode='valid')
            ma_timestamps = timestamps[window - 1:]
            ax.plot(
                ma_timestamps,
                ma,
                color=ma_style.get('color', '#e74c3c'),
                linestyle=ma_style.get('linestyle', '--'),
                linewidth=ma_style.get('linewidth', 1.8),
                label=ma_style.get('label_format', '{window}h MA').format(window=window),
                alpha=ma_style.get('alpha', 0.7)
            )

    # Formatting
    title_style = style.get('title', {})
    ax.set_xlabel(styling.get('xlabel', 'Time'))
    ax.set_ylabel(styling.get('ylabel', 'Value'))
    ax.set_title(
        data.get('title', 'Time Series'),
        fontsize=title_style.get('fontsize', 14),
        fontweight=title_style.get('fontweight', 'bold'),
        color=title_style.get('color', '#2c3e50'),
        pad=title_style.get('pad', 15)
    )

    # Format x-axis for datetime
    ts_style = style.get('timeseries', {})
    if isinstance(timestamps[0], datetime):
        date_format = ts_style.get('date_format', '%Y-%m-%d %H:%M')
        ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
        fig.autofmt_xdate(rotation=ts_style.get('date_rotation', 45))

    if config.get('show_legend', True):
        legend_style = style.get('legend', {})
        ax.legend(loc=legend_style.get('loc', 'best'))

    # Grid is applied from global style
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
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
