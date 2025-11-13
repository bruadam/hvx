"""Report template data models."""

from typing import Literal

from pydantic import BaseModel, Field


class ChartConfig(BaseModel):
    """Configuration for a single chart."""

    type: Literal[
        "heatmap_hourly_daily",
        "heatmap_daily_monthly",
        "heatmap_compliance",
        "timeseries_compliance",
        "timeseries_multi_parameter",
        "violation_timeline",
        "bar_room_comparison",
        "bar_building_comparison",
        "bar_test_comparison",
        "bar_stacked_comparison",
        "compliance_matrix",
        "compliance_gauge",
        "building_kpi_dashboard",
        "portfolio_overview",
    ]
    title: str | None = None
    parameters: list[str] | None = None  # Parameter names for charts requiring them
    season: Literal["winter", "summer", "spring", "fall", "heating", "cooling", "all"] | None = None
    metric: Literal["compliance", "quality", "violations"] | None = None
    sort: bool = True
    ascending: bool = False
    show_only_failing: bool = False
    failing_threshold: float = 95.0
    show_threshold: bool = True
    year: int | None = None


class SectionConfig(BaseModel):
    """Configuration for a report section."""

    type: Literal[
        "summary",
        "kpi_cards",
        "chart",
        "table",
        "recommendations",
        "executive_summary",
        "room_details",
        "building_statistics",
    ]
    title: str | None = None
    description: str | None = None
    chart: ChartConfig | None = None
    include_data_quality: bool = True
    include_recommendations: bool = True
    max_recommendations: int = 5


class RoomFilterConfig(BaseModel):
    """Configuration for filtering rooms."""

    mode: Literal["all", "failing", "top_n", "bottom_n"] = "all"
    n: int | None = None
    compliance_threshold: float = 95.0
    sort_by: Literal["compliance", "quality", "violations", "name"] = "compliance"
    ascending: bool = False


class ReportTemplate(BaseModel):
    """Complete report template configuration."""

    template_name: str
    report_type: Literal["room", "building", "portfolio"]

    # Report metadata
    title: str
    description: str | None = None
    author: str | None = None

    # Filtering and sorting
    room_filter: RoomFilterConfig = Field(default_factory=RoomFilterConfig)

    # Report sections
    sections: list[SectionConfig] = Field(default_factory=list)

    # Output settings
    output_format: list[Literal["html", "pdf"]] = ["html"]
    include_interactive_charts: bool = True
    theme: Literal["light", "dark", "professional"] = "professional"

    # Compliance settings
    compliance_standard: str = "EN16798-1"
    building_class: str | None = None

    class Config:
        """Pydantic config."""

        extra = "forbid"  # Don't allow extra fields
