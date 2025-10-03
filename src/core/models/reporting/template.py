"""Report template model."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from src.core.models.enums import AnalysisLevel
from src.core.models.reporting.sections import ReportSection


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
