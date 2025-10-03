"""
Service for managing report templates.
"""

import yaml
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.core.models import (
    ReportTemplate, ReportSection, SectionType, AnalysisLevel,
    MetadataSection, TextSection, GraphSection, TableSection,
    SummarySection, RecommendationsSection, IssuesSection, LoopSection,
    SortOrder
)


class ReportTemplateService:
    """Service for managing report templates."""

    def __init__(self, templates_dir: Path = Path("config/report_templates")):
        """Initialize with templates directory."""
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> List[ReportTemplate]:
        """List all available templates."""
        templates = []

        for template_file in self.templates_dir.glob("*.yaml"):
            try:
                template = self.load_template(template_file.stem)
                if template:
                    templates.append(template)
            except Exception:
                continue

        # Also check JSON files
        for template_file in self.templates_dir.glob("*.json"):
            try:
                template = self.load_template(template_file.stem)
                if template:
                    templates.append(template)
            except Exception:
                continue

        return templates

    def load_template(self, template_id: str) -> Optional[ReportTemplate]:
        """Load a template by ID."""
        # Try YAML first
        yaml_path = self.templates_dir / f"{template_id}.yaml"
        if yaml_path.exists():
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return ReportTemplate.from_dict(data)

        # Try JSON
        json_path = self.templates_dir / f"{template_id}.json"
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ReportTemplate.from_dict(data)

        return None

    def save_template(self, template: ReportTemplate, format: str = "yaml") -> Path:
        """Save a template to disk."""
        if format == "yaml":
            file_path = self.templates_dir / f"{template.template_id}.yaml"
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(template.to_dict(), f, default_flow_style=False,
                         allow_unicode=True, sort_keys=False)
        else:
            file_path = self.templates_dir / f"{template.template_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, indent=2)

        return file_path

    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        yaml_path = self.templates_dir / f"{template_id}.yaml"
        json_path = self.templates_dir / f"{template_id}.json"

        deleted = False
        if yaml_path.exists():
            yaml_path.unlink()
            deleted = True
        if json_path.exists():
            json_path.unlink()
            deleted = True

        return deleted

    def copy_template(self, source_id: str, new_id: str, new_name: Optional[str] = None) -> Optional[ReportTemplate]:
        """Copy an existing template with a new ID."""
        source = self.load_template(source_id)
        if not source:
            return None

        # Create new template with updated ID
        new_template = ReportTemplate(
            template_id=new_id,
            name=new_name or f"{source.name} (Copy)",
            description=source.description,
            version=source.version,
            author=source.author,
            created_date=datetime.now().isoformat(),
            output_format=source.output_format,
            page_size=source.page_size,
            orientation=source.orientation,
            default_level=source.default_level,
            sections=source.sections.copy(),
            global_filters=source.global_filters.copy(),
            global_config=source.global_config.copy()
        )

        self.save_template(new_template)
        return new_template

    def create_basic_template(self, template_id: str, name: str, description: str) -> ReportTemplate:
        """Create a basic template with metadata section."""
        template = ReportTemplate(
            template_id=template_id,
            name=name,
            description=description,
            author=None,
            created_date=datetime.now().isoformat()
        )

        # Add default metadata section
        metadata_section = ReportSection(
            section_type=SectionType.METADATA,
            section_id="metadata",
            metadata=MetadataSection()
        )
        template.add_section(metadata_section)

        return template

    def create_standard_building_template(self) -> ReportTemplate:
        """Create a standard building analysis template."""
        template = ReportTemplate(
            template_id="standard_building",
            name="Standard Building Analysis",
            description="Comprehensive building performance analysis report",
            created_date=datetime.now().isoformat(),
            default_level=AnalysisLevel.BUILDING
        )

        # Metadata
        template.add_section(ReportSection(
            section_type=SectionType.METADATA,
            section_id="metadata",
            metadata=MetadataSection(
                include_title=True,
                include_author=True,
                include_date=True,
                include_description=True
            )
        ))

        # Executive summary
        template.add_section(ReportSection(
            section_type=SectionType.SUMMARY,
            section_id="executive_summary",
            summary=SummarySection(
                level=AnalysisLevel.BUILDING,
                include_metrics=True,
                include_test_summary=True,
                include_compliance_rates=True
            )
        ))

        # Critical issues
        template.add_section(ReportSection(
            section_type=SectionType.ISSUES,
            section_id="critical_issues",
            issues=IssuesSection(
                level=AnalysisLevel.BUILDING,
                include_critical=True,
                include_high=True,
                max_issues=10
            )
        ))

        # Recommendations
        template.add_section(ReportSection(
            section_type=SectionType.RECOMMENDATIONS,
            section_id="recommendations",
            recommendations=RecommendationsSection(
                level=AnalysisLevel.BUILDING,
                max_recommendations=10
            )
        ))

        return template

    def create_room_loop_template(self) -> ReportTemplate:
        """Create a template that loops over all rooms."""
        template = ReportTemplate(
            template_id="room_detailed",
            name="Detailed Room Analysis",
            description="Detailed analysis for each room",
            created_date=datetime.now().isoformat(),
            default_level=AnalysisLevel.ROOM
        )

        # Metadata
        template.add_section(ReportSection(
            section_type=SectionType.METADATA,
            section_id="metadata",
            metadata=MetadataSection()
        ))

        # Portfolio overview
        template.add_section(ReportSection(
            section_type=SectionType.SUMMARY,
            section_id="portfolio_overview",
            summary=SummarySection(
                level=AnalysisLevel.PORTFOLIO,
                include_best_performing=True,
                include_worst_performing=True,
                top_n=10
            )
        ))

        # Loop over worst performing rooms
        loop_section = ReportSection(
            section_type=SectionType.LOOP,
            section_id="worst_rooms_loop",
            loop=LoopSection(
                loop_over=AnalysisLevel.ROOM,
                sort_order=SortOrder.WORST_FIRST,
                max_iterations=20,
                sections=[
                    ReportSection(
                        section_type=SectionType.SUMMARY,
                        section_id="room_summary",
                        summary=SummarySection(
                            level=AnalysisLevel.ROOM,
                            include_metrics=True,
                            include_test_summary=True
                        )
                    ),
                    ReportSection(
                        section_type=SectionType.ISSUES,
                        section_id="room_issues",
                        issues=IssuesSection(
                            level=AnalysisLevel.ROOM,
                            include_critical=True,
                            include_high=True
                        )
                    ),
                    ReportSection(
                        section_type=SectionType.RECOMMENDATIONS,
                        section_id="room_recommendations",
                        recommendations=RecommendationsSection(
                            level=AnalysisLevel.ROOM,
                            max_recommendations=5
                        )
                    )
                ]
            )
        )
        template.add_section(loop_section)

        return template

    def get_available_graph_types(self) -> List[str]:
        """Get list of available graph types from registry."""
        # This would integrate with the graph registry
        return [
            "compliance_bar_chart",
            "temperature_heatmap",
            "co2_time_series",
            "parameter_distribution",
            "seasonal_comparison",
            "daily_pattern",
            "room_comparison"
        ]

    def get_available_table_types(self) -> List[str]:
        """Get list of available table types."""
        return [
            "test_results",
            "compliance_summary",
            "room_ranking",
            "parameter_statistics",
            "seasonal_comparison",
            "issues_list",
            "recommendations_list"
        ]

    def get_available_parameters(self) -> List[str]:
        """Get list of available parameters."""
        return [
            "temperature",
            "co2",
            "humidity",
            "voc",
            "pm25",
            "pm10",
            "noise",
            "light"
        ]

    def validate_template(self, template: ReportTemplate) -> List[str]:
        """Validate a template and return list of issues."""
        issues = []

        if not template.template_id:
            issues.append("Template ID is required")

        if not template.name:
            issues.append("Template name is required")

        if not template.sections:
            issues.append("Template must have at least one section")

        # Check for duplicate section IDs
        section_ids = [s.section_id for s in template.sections]
        duplicates = set([sid for sid in section_ids if section_ids.count(sid) > 1])
        if duplicates:
            issues.append(f"Duplicate section IDs found: {', '.join(duplicates)}")

        # Validate each section
        for section in template.sections:
            section_issues = self._validate_section(section)
            issues.extend([f"Section '{section.section_id}': {issue}" for issue in section_issues])

        return issues

    def _validate_section(self, section: ReportSection) -> List[str]:
        """Validate a single section."""
        issues = []

        # Check that the appropriate section content exists
        if section.section_type == SectionType.METADATA and not section.metadata:
            issues.append("Metadata section missing metadata content")
        elif section.section_type == SectionType.TEXT and not section.text:
            issues.append("Text section missing text content")
        elif section.section_type == SectionType.GRAPH and not section.graph:
            issues.append("Graph section missing graph content")
        elif section.section_type == SectionType.TABLE and not section.table:
            issues.append("Table section missing table content")
        elif section.section_type == SectionType.SUMMARY and not section.summary:
            issues.append("Summary section missing summary content")
        elif section.section_type == SectionType.RECOMMENDATIONS and not section.recommendations:
            issues.append("Recommendations section missing recommendations content")
        elif section.section_type == SectionType.ISSUES and not section.issues:
            issues.append("Issues section missing issues content")
        elif section.section_type == SectionType.LOOP and not section.loop:
            issues.append("Loop section missing loop content")

        # Validate loop sections recursively
        if section.section_type == SectionType.LOOP and section.loop:
            for subsection in section.loop.sections:
                subsection_issues = self._validate_section(subsection)
                issues.extend([f"Loop subsection '{subsection.section_id}': {issue}"
                             for issue in subsection_issues])

        return issues
