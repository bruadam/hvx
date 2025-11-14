#!/usr/bin/env python3
"""
Generate a TAIL circular chart from the refactored summary JSON.

This script revives the original `generate_tail_chart` helper from the previous
codebase so that the visualisation can still be produced from the new
`ComplianceAnalysis.summary_results` payload.  To use it:

    1. Run the TAIL standard for a building/room and persist the resulting
       summary JSON (see `summary_results` on the analysis object).
    2. Save the summary to a file (or construct the dict in memory).
    3. Run:

           python examples/generate_tail_chart.py summary.json "HQ Building"

    The script emits a PNG in `output/tail_charts/<name>_TAIL_<timestamp>.png`.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np


# ---------------------------------------------------------------------------
# Visual component (ported from legacy `tail_circular_chart.py`)
# ---------------------------------------------------------------------------
class TAILCircularChart:
    """Generate enhanced circular TAIL rating visualisation per entity."""

    COLORS = {
        1: "#66BB6A",  # Green
        2: "#FFD54F",  # Yellow
        3: "#FF9800",  # Orange
        4: "#EF5350",  # Red
        None: "#BDBDBD",  # Grey when data is missing
    }
    ROMAN_NUMERALS = {1: "I", 2: "II", 3: "III", 4: "IV"}

    IAQ_PARAMETERS = {
        "co2": "CO₂",
        "rh": "RH",
        "humidity": "RH",
        "pm2.5": "PM2.5",
        "pm25": "PM2.5",
        "pm10": "PM10",
        "voc": "VOC",
        "tvoc": "VOC",
        "formaldehyde": "HCHO",
        "benzene": "Benzene",
        "radon": "Radon",
        "ventilation": "Vent",
        "mold": "Mold",
    }

    def __init__(self, figsize: tuple[float, float] = (12, 10)) -> None:
        self.figsize = figsize
        self.divider_color = "white"
        self.divider_width = 3

    def create(
        self,
        overall_rating: Optional[int],
        thermal_rating: Optional[int],
        acoustic_rating: Optional[int],
        iaq_rating: Optional[int],
        luminous_rating: Optional[int],
        thermal_details: Optional[Dict[str, int]] = None,
        acoustic_details: Optional[Dict[str, int]] = None,
        iaq_details: Optional[Dict[str, int]] = None,
        luminous_details: Optional[Dict[str, int]] = None,
        building_name: str = "Building",
        date_range: Optional[str] = None,
        save_path: Optional[Path] = None,
    ):
        fig, ax = plt.subplots(
            figsize=self.figsize,
            subplot_kw={"aspect": "equal"},
            facecolor="white",
        )
        ax.set_facecolor("white")

        self._draw_center_circle(ax, overall_rating)

        components = [
            ("Thermal", thermal_rating, 0, 90, thermal_details),
            ("Luminous", luminous_rating, 90, 180, luminous_details),
            ("IAQ", iaq_rating, 180, 270, iaq_details),
            ("Acoustic", acoustic_rating, 270, 360, acoustic_details),
        ]

        for label, rating, start, end, details in components:
            self._draw_component_segment(ax, label, rating, start, end)
            if details:
                self._draw_detail_segments(ax, details, start, end)

        self._draw_annotations(ax, building_name, overall_rating, date_range)
        ax.axis("off")

        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(save_path, bbox_inches="tight", dpi=200)

        return fig

    def _color(self, rating: Optional[int]) -> str:
        return self.COLORS.get(rating, self.COLORS[None])

    def _draw_center_circle(self, ax, rating: Optional[int]) -> None:
        circle = patches.Circle(
            (0, 0),
            radius=1.4,
            facecolor=self._color(rating),
            edgecolor="white",
            linewidth=2,
        )
        ax.add_patch(circle)
        if rating:
            ax.text(
                0,
                0.1,
                self.ROMAN_NUMERALS.get(rating, "?"),
                ha="center",
                va="center",
                fontsize=36,
                color="white",
                fontweight="bold",
            )
        ax.text(
            0,
            -0.6,
            "TAIL",
            ha="center",
            va="center",
            fontsize=18,
            color="white",
            fontweight="semibold",
        )

    def _draw_component_segment(self, ax, label, rating, start_angle, end_angle):
        wedge = patches.Wedge(
            (0, 0),
            r=3.0,
            theta1=start_angle,
            theta2=end_angle,
            facecolor=self._color(rating),
            edgecolor="white",
            linewidth=3,
        )
        ax.add_patch(wedge)
        theta = np.deg2rad((start_angle + end_angle) / 2)
        ax.text(
            0.0 + 1.6 * np.cos(theta),
            0.0 + 1.6 * np.sin(theta),
            label,
            ha="center",
            va="center",
            fontsize=14,
            color="white",
            rotation=(start_angle + end_angle) / 2 - 90,
        )

    def _draw_detail_segments(self, ax, details: Dict[str, int], start_angle: float, end_angle: float):
        items = list(details.items())
        if not items:
            return

        angle_span = (end_angle - start_angle) / len(items)
        radius_inner, radius_outer = 3.0, 4.0
        for idx, (param, rating) in enumerate(items):
            seg_start = start_angle + idx * angle_span
            seg_end = seg_start + angle_span
            wedge = patches.Wedge(
                (0, 0),
                r=radius_outer,
                theta1=seg_start,
                theta2=seg_end,
                facecolor=self._color(rating),
                edgecolor="white",
                linewidth=2,
                width=radius_outer - radius_inner,
            )
            ax.add_patch(wedge)
            theta = np.deg2rad((seg_start + seg_end) / 2)
            ax.text(
                0.0 + 3.4 * np.cos(theta),
                0.0 + 3.4 * np.sin(theta),
                param,
                ha="center",
                va="center",
                fontsize=10,
                color="black",
                rotation=(seg_start + seg_end) / 2 - 90,
            )

    def _draw_annotations(self, ax, building_name: str, rating: Optional[int], date_range: Optional[str]):
        ax.text(
            0,
            -4.5,
            building_name,
            ha="center",
            va="center",
            fontsize=18,
            fontweight="bold",
            color="#424242",
        )
        if rating:
            ax.text(
                0,
                -5.1,
                f"Overall rating: {self.ROMAN_NUMERALS.get(rating, '?')}",
                ha="center",
                va="center",
                fontsize=13,
                color="#616161",
            )
        if date_range:
            ax.text(
                0,
                -5.6,
                date_range,
                ha="center",
                va="center",
                fontsize=11,
                color="#757575",
            )


# ---------------------------------------------------------------------------
# Utility helpers for refactored summary payloads
# ---------------------------------------------------------------------------
def _rating_from_summary(value: Optional[int | str]) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value if 1 <= value <= 4 else None
    lookup = {"I": 1, "II": 2, "III": 3, "IV": 4}
    return lookup.get(value.upper())


def _classify_parameter(name: str) -> str:
    key = name.lower()
    if any(tok in key for tok in ("temp", "thermal")):
        return "thermal"
    if any(tok in key for tok in ("noise", "acoustic", "db", "sound")):
        return "acoustic"
    if any(tok in key for tok in ("lux", "illum", "daylight")):
        return "luminous"
    return "iaq"


def _label_for_iaq_parameter(name: str) -> str:
    norm = name.lower().replace(" ", "")
    return TAILCircularChart.IAQ_PARAMETERS.get(norm, name)


def build_chart_inputs(summary: Dict[str, any]) -> Dict[str, any]:
    domains = summary.get("domains", {})
    parameters = summary.get("parameters", {})

    def dom_rating(domain_key: str) -> Optional[int]:
        dom = domains.get(domain_key)
        if not dom:
            return None
        return _rating_from_summary(dom.get("rating") or dom.get("rating_label"))

    detail_buckets: Dict[str, Dict[str, int]] = {
        "thermal": {},
        "acoustic": {},
        "iaq": {},
        "luminous": {},
    }

    for name, info in parameters.items():
        rating = _rating_from_summary(info.get("rating_value") or info.get("rating"))
        if rating is None:
            continue
        bucket = _classify_parameter(name)
        label = _label_for_iaq_parameter(name) if bucket == "iaq" else name
        detail_buckets[bucket][label] = rating

    return {
        "overall_rating": _rating_from_summary(summary.get("overall_rating") or summary.get("overall_rating_label")),
        "thermal_rating": dom_rating("thermal"),
        "acoustic_rating": dom_rating("acoustic"),
        "iaq_rating": dom_rating("iaq"),
        "luminous_rating": dom_rating("luminous"),
        "thermal_details": detail_buckets["thermal"],
        "acoustic_details": detail_buckets["acoustic"],
        "iaq_details": detail_buckets["iaq"],
        "luminous_details": detail_buckets["luminous"],
    }


def render_tail_chart(
    tail_summary: Dict[str, any],
    building_name: str,
    output_dir: Optional[Path] = None,
    date_range: Optional[str] = None,
) -> Path:
    output_dir = output_dir or Path("output/tail_charts")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = building_name.replace(" ", "_").replace("/", "_")
    output_path = output_dir / f"{safe_name}_TAIL_{timestamp}.png"

    chart_inputs = build_chart_inputs(tail_summary)
    chart = TAILCircularChart()
    chart.create(
        building_name=building_name,
        date_range=date_range,
        save_path=output_path,
        **chart_inputs,
    )

    plt.close("all")
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a TAIL circular chart from summary JSON.")
    parser.add_argument("summary_file", type=Path, help="Path to JSON file with TAIL summary results.")
    parser.add_argument("entity_name", type=str, help="Building or room name to display on the chart.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory where the PNG will be saved.")
    parser.add_argument("--date-range", type=str, default=None, help="Optional label for the analysis period.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    with args.summary_file.open("r") as f:
        summary = json.load(f)

    output_path = render_tail_chart(
        tail_summary=summary,
        building_name=args.entity_name,
        output_dir=args.output_dir,
        date_range=args.date_range,
    )
    print(f"TAIL chart written to {output_path}")


if __name__ == "__main__":
    main()
