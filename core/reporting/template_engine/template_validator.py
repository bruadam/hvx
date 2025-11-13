"""Validator for report templates."""


from core.domain.enums.parameter_type import ParameterType
from core.reporting.template_engine.report_template import (
    ChartConfig,
    ReportTemplate,
    SectionConfig,
)


class TemplateValidator:
    """Validate report template configurations."""

    @staticmethod
    def validate(template: ReportTemplate) -> tuple[bool, list[str]]:
        """
        Validate complete report template.

        Args:
            template: Template to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Validate sections
        if not template.sections:
            errors.append("Template must have at least one section")

        for i, section in enumerate(template.sections):
            section_errors = TemplateValidator._validate_section(section, i)
            errors.extend(section_errors)

        # Validate room filter
        filter_errors = TemplateValidator._validate_room_filter(template.room_filter)
        errors.extend(filter_errors)

        # Validate report type compatibility
        type_errors = TemplateValidator._validate_report_type(template)
        errors.extend(type_errors)

        return len(errors) == 0, errors

    @staticmethod
    def _validate_section(section: SectionConfig, index: int) -> list[str]:
        """Validate individual section."""
        errors = []

        if section.type == "chart":
            if not section.chart:
                errors.append(f"Section {index}: Chart section requires 'chart' configuration")
            else:
                chart_errors = TemplateValidator._validate_chart(section.chart, index)
                errors.extend(chart_errors)

        return errors

    @staticmethod
    def _validate_chart(chart: ChartConfig, section_index: int) -> list[str]:
        """Validate chart configuration."""
        errors = []

        # Charts requiring parameters
        param_required_charts = [
            "heatmap_hourly_daily",
            "heatmap_daily_monthly",
            "heatmap_compliance",
            "timeseries_compliance",
            "timeseries_multi_parameter",
            "violation_timeline",
        ]

        if chart.type in param_required_charts:
            if not chart.parameters:
                errors.append(
                    f"Section {section_index}: Chart type '{chart.type}' requires 'parameters'"
                )
            else:
                # Validate parameter names
                valid_params = {p.value for p in ParameterType}
                for param in chart.parameters:
                    if param not in valid_params:
                        errors.append(
                            f"Section {section_index}: Invalid parameter '{param}'. "
                            f"Valid options: {', '.join(sorted(valid_params))}"
                        )

        # Multi-parameter charts need multiple parameters
        if chart.type == "timeseries_multi_parameter":
            if chart.parameters and len(chart.parameters) < 2:
                errors.append(
                    f"Section {section_index}: Multi-parameter chart requires at least 2 parameters"
                )

        # Bar comparison charts requiring metric
        metric_required_charts = ["bar_room_comparison"]
        if chart.type in metric_required_charts:
            if not chart.metric:
                errors.append(
                    f"Section {section_index}: Chart type '{chart.type}' requires 'metric' "
                    "(compliance, quality, or violations)"
                )

        # Validate threshold ranges
        if chart.failing_threshold is not None:
            if not 0 <= chart.failing_threshold <= 100:
                errors.append(
                    f"Section {section_index}: failing_threshold must be between 0 and 100"
                )

        return errors

    @staticmethod
    def _validate_room_filter(room_filter) -> list[str]:
        """Validate room filter configuration."""
        errors = []

        if room_filter.mode in ["top_n", "bottom_n"]:
            if room_filter.n is None or room_filter.n <= 0:
                errors.append(
                    f"Room filter mode '{room_filter.mode}' requires positive 'n' value"
                )

        if not 0 <= room_filter.compliance_threshold <= 100:
            errors.append("Room filter compliance_threshold must be between 0 and 100")

        return errors

    @staticmethod
    def _validate_report_type(template: ReportTemplate) -> list[str]:
        """Validate report type compatibility with sections."""
        errors = []

        # Portfolio reports should use portfolio-level charts
        if template.report_type == "portfolio":
            for i, section in enumerate(template.sections):
                if section.chart and section.chart.type in [
                    "timeseries_compliance",
                    "heatmap_hourly_daily",
                ]:
                    errors.append(
                        f"Section {i}: Chart type '{section.chart.type}' "
                        "not suitable for portfolio reports"
                    )

        # Building reports should have building-level charts
        if template.report_type == "building":
            has_building_chart = False
            for section in template.sections:
                if section.chart and section.chart.type in [
                    "building_kpi_dashboard",
                    "bar_room_comparison",
                ]:
                    has_building_chart = True
                    break
            if not has_building_chart:
                errors.append(
                    "Building report should include at least one building-level chart "
                    "(building_kpi_dashboard or bar_room_comparison)"
                )

        return errors
