"""
Models for report template configuration.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class AnalysisLevel(Enum):
    """Analysis hierarchy levels."""
    PORTFOLIO = "portfolio"
    BUILDING = "building"
    LEVEL = "level"
    ROOM = "room"


class SectionType(Enum):
    """Report section types."""
    METADATA = "metadata"
    TEXT = "text"
    GRAPH = "graph"
    TABLE = "table"
    SUMMARY = "summary"
    RECOMMENDATIONS = "recommendations"
    ISSUES = "issues"
    LOOP = "loop"


class SortOrder(Enum):
    """Sorting order for entities."""
    BEST_FIRST = "best_first"
    WORST_FIRST = "worst_first"
    ALPHABETICAL = "alphabetical"
    NONE = "none"


@dataclass
class MetadataSection:
    """Report metadata configuration."""
    include_title: bool = True
    title: Optional[str] = None  # None = auto-generate
    include_author: bool = True
    author: Optional[str] = None
    include_date: bool = True
    include_description: bool = True
    description: Optional[str] = None
    include_notes: bool = False
    notes: Optional[str] = None
    custom_fields: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'include_title': self.include_title,
            'title': self.title,
            'include_author': self.include_author,
            'author': self.author,
            'include_date': self.include_date,
            'include_description': self.include_description,
            'description': self.description,
            'include_notes': self.include_notes,
            'notes': self.notes,
            'custom_fields': self.custom_fields
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetadataSection':
        return cls(
            include_title=data.get('include_title', True),
            title=data.get('title'),
            include_author=data.get('include_author', True),
            author=data.get('author'),
            include_date=data.get('include_date', True),
            include_description=data.get('include_description', True),
            description=data.get('description'),
            include_notes=data.get('include_notes', False),
            notes=data.get('notes'),
            custom_fields=data.get('custom_fields', {})
        )


@dataclass
class TextSection:
    """Free-form text section."""
    content: str
    heading: Optional[str] = None
    heading_level: int = 2  # H2 by default
    markdown: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'heading': self.heading,
            'heading_level': self.heading_level,
            'markdown': self.markdown
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextSection':
        return cls(
            content=data['content'],
            heading=data.get('heading'),
            heading_level=data.get('heading_level', 2),
            markdown=data.get('markdown', True)
        )


@dataclass
class GraphSection:
    """Graph/visualization section."""
    graph_type: str  # Reference to graph registry
    title: Optional[str] = None
    level: AnalysisLevel = AnalysisLevel.BUILDING
    parameters: List[str] = field(default_factory=list)  # e.g., ['temperature', 'co2']
    tests: List[str] = field(default_factory=list)  # Specific tests to include
    filters: Dict[str, Any] = field(default_factory=dict)  # Additional filters
    config: Dict[str, Any] = field(default_factory=dict)  # Graph-specific config
    caption: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'graph_type': self.graph_type,
            'title': self.title,
            'level': self.level.value,
            'parameters': self.parameters,
            'tests': self.tests,
            'filters': self.filters,
            'config': self.config,
            'caption': self.caption
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GraphSection':
        return cls(
            graph_type=data['graph_type'],
            title=data.get('title'),
            level=AnalysisLevel(data.get('level', 'building')),
            parameters=data.get('parameters', []),
            tests=data.get('tests', []),
            filters=data.get('filters', {}),
            config=data.get('config', {}),
            caption=data.get('caption')
        )


@dataclass
class TableSection:
    """Table section configuration."""
    table_type: str  # e.g., 'test_results', 'compliance_summary', 'room_ranking'
    title: Optional[str] = None
    level: AnalysisLevel = AnalysisLevel.BUILDING
    columns: List[str] = field(default_factory=list)  # Columns to include
    tests: List[str] = field(default_factory=list)  # Tests to include
    parameters: List[str] = field(default_factory=list)  # Parameters to include
    sort_by: Optional[str] = None  # Column to sort by
    sort_order: SortOrder = SortOrder.NONE
    max_rows: Optional[int] = None  # Limit number of rows
    filters: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)  # Table-specific config
    caption: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'table_type': self.table_type,
            'title': self.title,
            'level': self.level.value,
            'columns': self.columns,
            'tests': self.tests,
            'parameters': self.parameters,
            'sort_by': self.sort_by,
            'sort_order': self.sort_order.value,
            'max_rows': self.max_rows,
            'filters': self.filters,
            'config': self.config,
            'caption': self.caption
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TableSection':
        return cls(
            table_type=data['table_type'],
            title=data.get('title'),
            level=AnalysisLevel(data.get('level', 'building')),
            columns=data.get('columns', []),
            tests=data.get('tests', []),
            parameters=data.get('parameters', []),
            sort_by=data.get('sort_by'),
            sort_order=SortOrder(data.get('sort_order', 'none')),
            max_rows=data.get('max_rows'),
            filters=data.get('filters', {}),
            config=data.get('config', {}),
            caption=data.get('caption')
        )


@dataclass
class SummarySection:
    """Summary statistics section."""
    level: AnalysisLevel = AnalysisLevel.BUILDING
    include_metrics: bool = True
    include_test_summary: bool = True
    include_compliance_rates: bool = True
    include_quality_scores: bool = True
    include_best_performing: bool = True
    include_worst_performing: bool = True
    top_n: int = 5  # Number of top/bottom items to show
    custom_metrics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'level': self.level.value,
            'include_metrics': self.include_metrics,
            'include_test_summary': self.include_test_summary,
            'include_compliance_rates': self.include_compliance_rates,
            'include_quality_scores': self.include_quality_scores,
            'include_best_performing': self.include_best_performing,
            'include_worst_performing': self.include_worst_performing,
            'top_n': self.top_n,
            'custom_metrics': self.custom_metrics
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SummarySection':
        return cls(
            level=AnalysisLevel(data.get('level', 'building')),
            include_metrics=data.get('include_metrics', True),
            include_test_summary=data.get('include_test_summary', True),
            include_compliance_rates=data.get('include_compliance_rates', True),
            include_quality_scores=data.get('include_quality_scores', True),
            include_best_performing=data.get('include_best_performing', True),
            include_worst_performing=data.get('include_worst_performing', True),
            top_n=data.get('top_n', 5),
            custom_metrics=data.get('custom_metrics', [])
        )


@dataclass
class RecommendationsSection:
    """Recommendations section configuration."""
    level: AnalysisLevel = AnalysisLevel.BUILDING
    max_recommendations: Optional[int] = None
    priority_filter: Optional[str] = None  # 'high', 'medium', 'low'
    group_by: Optional[str] = None  # 'parameter', 'severity', 'location'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'level': self.level.value,
            'max_recommendations': self.max_recommendations,
            'priority_filter': self.priority_filter,
            'group_by': self.group_by
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecommendationsSection':
        return cls(
            level=AnalysisLevel(data.get('level', 'building')),
            max_recommendations=data.get('max_recommendations'),
            priority_filter=data.get('priority_filter'),
            group_by=data.get('group_by')
        )


@dataclass
class IssuesSection:
    """Issues section configuration."""
    level: AnalysisLevel = AnalysisLevel.BUILDING
    include_critical: bool = True
    include_high: bool = True
    include_medium: bool = False
    include_low: bool = False
    max_issues: Optional[int] = None
    group_by: Optional[str] = None  # 'severity', 'parameter', 'location'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'level': self.level.value,
            'include_critical': self.include_critical,
            'include_high': self.include_high,
            'include_medium': self.include_medium,
            'include_low': self.include_low,
            'max_issues': self.max_issues,
            'group_by': self.group_by
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IssuesSection':
        return cls(
            level=AnalysisLevel(data.get('level', 'building')),
            include_critical=data.get('include_critical', True),
            include_high=data.get('include_high', True),
            include_medium=data.get('include_medium', False),
            include_low=data.get('include_low', False),
            max_issues=data.get('max_issues'),
            group_by=data.get('group_by')
        )


@dataclass
class LoopSection:
    """Loop over entities configuration."""
    loop_over: AnalysisLevel  # BUILDING or ROOM
    sort_order: SortOrder = SortOrder.NONE
    filters: Dict[str, Any] = field(default_factory=dict)
    max_iterations: Optional[int] = None
    sections: List['ReportSection'] = field(default_factory=list)  # Sections to repeat

    def to_dict(self) -> Dict[str, Any]:
        return {
            'loop_over': self.loop_over.value,
            'sort_order': self.sort_order.value,
            'filters': self.filters,
            'max_iterations': self.max_iterations,
            'sections': [s.to_dict() for s in self.sections]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoopSection':
        return cls(
            loop_over=AnalysisLevel(data['loop_over']),
            sort_order=SortOrder(data.get('sort_order', 'none')),
            filters=data.get('filters', {}),
            max_iterations=data.get('max_iterations'),
            sections=[ReportSection.from_dict(s) for s in data.get('sections', [])]
        )


@dataclass
class ReportSection:
    """Generic report section wrapper."""
    section_type: SectionType
    section_id: str  # Unique identifier
    enabled: bool = True
    page_break_before: bool = False
    page_break_after: bool = False

    # One of these will be set based on section_type
    metadata: Optional[MetadataSection] = None
    text: Optional[TextSection] = None
    graph: Optional[GraphSection] = None
    table: Optional[TableSection] = None
    summary: Optional[SummarySection] = None
    recommendations: Optional[RecommendationsSection] = None
    issues: Optional[IssuesSection] = None
    loop: Optional[LoopSection] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            'section_type': self.section_type.value,
            'section_id': self.section_id,
            'enabled': self.enabled,
            'page_break_before': self.page_break_before,
            'page_break_after': self.page_break_after
        }

        # Add the specific section content
        if self.metadata:
            result['metadata'] = self.metadata.to_dict()
        elif self.text:
            result['text'] = self.text.to_dict()
        elif self.graph:
            result['graph'] = self.graph.to_dict()
        elif self.table:
            result['table'] = self.table.to_dict()
        elif self.summary:
            result['summary'] = self.summary.to_dict()
        elif self.recommendations:
            result['recommendations'] = self.recommendations.to_dict()
        elif self.issues:
            result['issues'] = self.issues.to_dict()
        elif self.loop:
            result['loop'] = self.loop.to_dict()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportSection':
        section_type = SectionType(data['section_type'])

        # Parse the specific section based on type
        kwargs = {
            'section_type': section_type,
            'section_id': data['section_id'],
            'enabled': data.get('enabled', True),
            'page_break_before': data.get('page_break_before', False),
            'page_break_after': data.get('page_break_after', False)
        }

        if section_type == SectionType.METADATA and 'metadata' in data:
            kwargs['metadata'] = MetadataSection.from_dict(data['metadata'])
        elif section_type == SectionType.TEXT and 'text' in data:
            kwargs['text'] = TextSection.from_dict(data['text'])
        elif section_type == SectionType.GRAPH and 'graph' in data:
            kwargs['graph'] = GraphSection.from_dict(data['graph'])
        elif section_type == SectionType.TABLE and 'table' in data:
            kwargs['table'] = TableSection.from_dict(data['table'])
        elif section_type == SectionType.SUMMARY and 'summary' in data:
            kwargs['summary'] = SummarySection.from_dict(data['summary'])
        elif section_type == SectionType.RECOMMENDATIONS and 'recommendations' in data:
            kwargs['recommendations'] = RecommendationsSection.from_dict(data['recommendations'])
        elif section_type == SectionType.ISSUES and 'issues' in data:
            kwargs['issues'] = IssuesSection.from_dict(data['issues'])
        elif section_type == SectionType.LOOP and 'loop' in data:
            kwargs['loop'] = LoopSection.from_dict(data['loop'])

        return cls(**kwargs)


@dataclass
class ReportTemplate:
    """Complete report template configuration."""
    template_id: str
    name: str
    description: str
    version: str = "1.0"
    author: Optional[str] = None
    created_date: Optional[str] = None

    # Output configuration
    output_format: str = "pdf"  # pdf, html, markdown, docx
    page_size: str = "A4"
    orientation: str = "portrait"  # portrait, landscape

    # Default analysis level
    default_level: AnalysisLevel = AnalysisLevel.BUILDING

    # Sections to include
    sections: List[ReportSection] = field(default_factory=list)

    # Global filters and settings
    global_filters: Dict[str, Any] = field(default_factory=dict)
    global_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'created_date': self.created_date,
            'output_format': self.output_format,
            'page_size': self.page_size,
            'orientation': self.orientation,
            'default_level': self.default_level.value,
            'sections': [s.to_dict() for s in self.sections],
            'global_filters': self.global_filters,
            'global_config': self.global_config
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportTemplate':
        return cls(
            template_id=data['template_id'],
            name=data['name'],
            description=data['description'],
            version=data.get('version', '1.0'),
            author=data.get('author'),
            created_date=data.get('created_date'),
            output_format=data.get('output_format', 'pdf'),
            page_size=data.get('page_size', 'A4'),
            orientation=data.get('orientation', 'portrait'),
            default_level=AnalysisLevel(data.get('default_level', 'building')),
            sections=[ReportSection.from_dict(s) for s in data.get('sections', [])],
            global_filters=data.get('global_filters', {}),
            global_config=data.get('global_config', {})
        )

    def add_section(self, section: ReportSection) -> None:
        """Add a section to the template."""
        self.sections.append(section)

    def remove_section(self, section_id: str) -> bool:
        """Remove a section by ID."""
        original_length = len(self.sections)
        self.sections = [s for s in self.sections if s.section_id != section_id]
        return len(self.sections) < original_length

    def get_section(self, section_id: str) -> Optional[ReportSection]:
        """Get a section by ID."""
        for section in self.sections:
            if section.section_id == section_id:
                return section
        return None

    def reorder_section(self, section_id: str, new_index: int) -> bool:
        """Move a section to a new position."""
        section = self.get_section(section_id)
        if not section:
            return False

        self.sections.remove(section)
        self.sections.insert(new_index, section)
        return True
