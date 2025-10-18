"""
YAML Template Parser with Validation

Parses and validates YAML-based report templates to ensure they contain
all required data and analytics specifications.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of template validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]


class YAMLTemplateParser:
    """
    Parser and validator for YAML report templates.
    
    Validates template structure, analytics requirements, and configuration.
    """
    
    # Required top-level keys in template
    REQUIRED_TEMPLATE_KEYS = {'template_id', 'name', 'description'}
    
    # Valid section types
    VALID_SECTION_TYPES = {
        'cover', 'summary', 'text', 'charts', 'recommendations',
        'issues', 'table', 'loop'
    }
    
    # Valid analytics tags (these should match actual analytics capabilities)
    VALID_ANALYTICS_TAGS = {
        'statistics.basic', 'statistics.trends', 'statistics.distribution',
        'compliance.overall', 'compliance.temporal', 'compliance.spatial',
        'compliance.threshold',
        'temporal.hourly', 'temporal.daily', 'temporal.weekly',
        'temporal.monthly', 'temporal.seasonal',
        'spatial.room_level', 'spatial.level_level', 'spatial.building_level',
        'spatial.comparison', 'spatial.ranking',
        'recommendations.operational', 'recommendations.hvac',
        'recommendations.ventilation', 'recommendations.maintenance',
        'data_quality.completeness', 'data_quality.accuracy',
        'performance.scoring', 'performance.ranking',
        'weather.correlation', 'weather.impact'
    }
    
    # Valid parameters
    VALID_PARAMETERS = {
        'temperature', 'co2', 'humidity', 'voc', 'pm25', 'pm10',
        'noise', 'light', 'occupancy'
    }
    
    def __init__(self):
        """Initialize the parser."""
        self.current_file = None
    
    def parse_file(self, template_path: Path) -> Dict[str, Any]:
        """
        Parse YAML template file.
        
        Args:
            template_path: Path to YAML template file
            
        Returns:
            Parsed template as dictionary
            
        Raises:
            FileNotFoundError: If template file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        self.current_file = template_path
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
            
            if not isinstance(template_data, dict):
                raise ValueError("Template must be a YAML dictionary/object")
            
            logger.info(f"Parsed template: {template_data.get('name', 'Unknown')}")
            return template_data
            
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {template_path}: {e}")
            raise
    
    def validate(self, template_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate template structure and content.
        
        Args:
            template_data: Parsed template dictionary
            
        Returns:
            ValidationResult with errors, warnings, and info
        """
        errors = []
        warnings = []
        info = []
        
        # Validate required top-level keys
        missing_keys = self.REQUIRED_TEMPLATE_KEYS - set(template_data.keys())
        if missing_keys:
            errors.append(f"Missing required keys: {', '.join(missing_keys)}")
        
        # Validate template metadata
        template_id = template_data.get('template_id', '')
        if not template_id:
            errors.append("template_id cannot be empty")
        elif not template_id.replace('_', '').replace('-', '').isalnum():
            warnings.append(f"template_id '{template_id}' contains special characters")
        
        # Validate report configuration
        report_config = template_data.get('report', {})
        if report_config:
            self._validate_report_config(report_config, errors, warnings, info)
        
        # Validate sections
        sections = template_data.get('sections', [])
        if not sections:
            warnings.append("Template has no sections defined")
        else:
            self._validate_sections(sections, errors, warnings, info)
        
        # Validate analytics requirements
        analytics_reqs = template_data.get('analytics_requirements', {})
        if analytics_reqs:
            self._validate_analytics_requirements(analytics_reqs, errors, warnings, info)
        
        # Check for duplicate section IDs
        section_ids = [s.get('section_id', '') for s in sections if s.get('section_id')]
        duplicates = set([sid for sid in section_ids if section_ids.count(sid) > 1])
        if duplicates:
            errors.append(f"Duplicate section IDs found: {', '.join(duplicates)}")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            info=info
        )
    
    def _validate_report_config(
        self,
        config: Dict[str, Any],
        errors: List[str],
        warnings: List[str],
        info: List[str]
    ) -> None:
        """Validate report configuration section."""
        # Validate format
        report_format = config.get('format', 'html')
        if report_format not in ['html', 'pdf', 'markdown', 'docx']:
            warnings.append(f"Unknown format '{report_format}', using 'html'")
        
        # Validate scope
        scope = config.get('scope')
        if scope and scope not in ['portfolio', 'building', 'level', 'room']:
            warnings.append(f"Unknown scope '{scope}'")
        
        info.append(f"Report format: {report_format}")
        if scope:
            info.append(f"Report scope: {scope}")
    
    def _validate_sections(
        self,
        sections: List[Dict[str, Any]],
        errors: List[str],
        warnings: List[str],
        info: List[str]
    ) -> None:
        """Validate all sections in template."""
        info.append(f"Total sections: {len(sections)}")
        
        section_types_count = {}
        
        for idx, section in enumerate(sections):
            section_id = section.get('section_id', f'section_{idx}')
            section_type = section.get('type')
            
            # Count section types
            section_types_count[section_type] = section_types_count.get(section_type, 0) + 1
            
            # Validate section type
            if not section_type:
                errors.append(f"Section '{section_id}' missing 'type' field")
                continue
            
            if section_type not in self.VALID_SECTION_TYPES:
                errors.append(
                    f"Section '{section_id}' has invalid type '{section_type}'. "
                    f"Valid types: {', '.join(self.VALID_SECTION_TYPES)}"
                )
                continue
            
            # Validate section-specific content
            if section_type == 'charts':
                self._validate_charts_section(section, section_id, errors, warnings)
            elif section_type == 'loop':
                self._validate_loop_section(section, section_id, errors, warnings)
            elif section_type == 'recommendations':
                self._validate_recommendations_section(section, section_id, warnings)
            
            # Validate analytics requirements for this section
            section_analytics = section.get('analytics_requirements', {})
            if section_analytics:
                self._validate_analytics_requirements(
                    section_analytics, errors, warnings, info,
                    context=f"section '{section_id}'"
                )
        
        # Report section type statistics
        for stype, count in section_types_count.items():
            info.append(f"  {stype} sections: {count}")
    
    def _validate_charts_section(
        self,
        section: Dict[str, Any],
        section_id: str,
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Validate charts section."""
        charts = section.get('charts', [])
        
        if not charts:
            warnings.append(f"Charts section '{section_id}' has no charts defined")
            return
        
        for chart in charts:
            chart_id = chart.get('id')
            if not chart_id:
                errors.append(f"Chart in section '{section_id}' missing 'id' field")
                continue
            
            # Validate chart analytics requirements
            chart_analytics = chart.get('analytics_requirements', {})
            if chart_analytics:
                self._validate_analytics_requirements(
                    chart_analytics, errors, warnings, [],
                    context=f"chart '{chart_id}' in section '{section_id}'"
                )
    
    def _validate_loop_section(
        self,
        section: Dict[str, Any],
        section_id: str,
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Validate loop section."""
        loop_over = section.get('loop_over')
        
        if not loop_over:
            errors.append(f"Loop section '{section_id}' missing 'loop_over' field")
            return
        
        if loop_over not in ['rooms', 'levels', 'buildings']:
            errors.append(
                f"Loop section '{section_id}' has invalid loop_over '{loop_over}'. "
                f"Valid values: rooms, levels, buildings"
            )
        
        # Validate sort configuration
        sort_by = section.get('sort_by')
        if sort_by and sort_by not in ['compliance_rate', 'quality_score', 'name', 'id']:
            warnings.append(
                f"Loop section '{section_id}' has unknown sort_by '{sort_by}'"
            )
    
    def _validate_recommendations_section(
        self,
        section: Dict[str, Any],
        section_id: str,
        warnings: List[str]
    ) -> None:
        """Validate recommendations section."""
        priority_filter = section.get('priority_filter', [])
        
        if priority_filter:
            valid_priorities = {'critical', 'high', 'medium', 'low'}
            invalid = set(priority_filter) - valid_priorities
            if invalid:
                warnings.append(
                    f"Recommendations section '{section_id}' has invalid priorities: "
                    f"{', '.join(invalid)}"
                )
    
    def _validate_analytics_requirements(
        self,
        analytics_reqs: Dict[str, Any],
        errors: List[str],
        warnings: List[str],
        info: List[str],
        context: str = "template"
    ) -> None:
        """Validate analytics requirements."""
        # Validate analytics tags
        tags = analytics_reqs.get('analytics_tags', [])
        if tags:
            invalid_tags = set(tags) - self.VALID_ANALYTICS_TAGS
            if invalid_tags:
                warnings.append(
                    f"Unknown analytics tags in {context}: {', '.join(invalid_tags)}"
                )
            
            if info is not None:
                info.append(f"Analytics tags in {context}: {len(tags)}")
        
        # Validate required parameters
        params = analytics_reqs.get('required_parameters', [])
        if params:
            invalid_params = set(params) - self.VALID_PARAMETERS
            if invalid_params:
                warnings.append(
                    f"Unknown parameters in {context}: {', '.join(invalid_params)}"
                )
        
        # Validate required level
        required_level = analytics_reqs.get('required_level')
        if required_level and required_level not in ['portfolio', 'building', 'level', 'room']:
            warnings.append(
                f"Invalid required_level '{required_level}' in {context}"
            )
        
        # Validate data quality threshold
        min_quality = analytics_reqs.get('min_data_quality')
        if min_quality is not None:
            if not isinstance(min_quality, (int, float)):
                errors.append(f"min_data_quality must be a number in {context}")
            elif not (0 <= min_quality <= 1):
                errors.append(f"min_data_quality must be between 0 and 1 in {context}")
    
    def parse_and_validate(self, template_path: Path) -> tuple[Dict[str, Any], ValidationResult]:
        """
        Parse and validate template in one call.
        
        Args:
            template_path: Path to YAML template file
            
        Returns:
            Tuple of (parsed_template, validation_result)
        """
        template_data = self.parse_file(template_path)
        validation_result = self.validate(template_data)
        
        return template_data, validation_result
    
    def extract_analytics_requirements(self, template_data: Dict[str, Any]) -> Dict[str, Set[str]]:
        """
        Extract all analytics requirements from template.
        
        Args:
            template_data: Parsed template dictionary
            
        Returns:
            Dictionary with:
                - all_tags: Set of all required analytics tags
                - all_parameters: Set of all required parameters
                - required_level: Highest required analysis level
        """
        all_tags = set()
        all_parameters = set()
        required_levels = []
        
        # Get template-level requirements
        template_reqs = template_data.get('analytics_requirements', {})
        if template_reqs:
            all_tags.update(template_reqs.get('analytics_tags', []))
            all_parameters.update(template_reqs.get('required_parameters', []))
            if template_reqs.get('required_level'):
                required_levels.append(template_reqs['required_level'])
        
        # Get section-level requirements
        sections = template_data.get('sections', [])
        for section in sections:
            section_reqs = section.get('analytics_requirements', {})
            if section_reqs:
                all_tags.update(section_reqs.get('analytics_tags', []))
                all_parameters.update(section_reqs.get('required_parameters', []))
                if section_reqs.get('required_level'):
                    required_levels.append(section_reqs['required_level'])
            
            # Check charts
            charts = section.get('charts', [])
            for chart in charts:
                chart_reqs = chart.get('analytics_requirements', {})
                if chart_reqs:
                    all_tags.update(chart_reqs.get('analytics_tags', []))
                    all_parameters.update(chart_reqs.get('required_parameters', []))
        
        # Determine highest required level
        level_hierarchy = ['room', 'level', 'building', 'portfolio']
        highest_level = None
        if required_levels:
            for level in reversed(level_hierarchy):
                if level in required_levels:
                    highest_level = level
                    break
        
        return {
            'all_tags': all_tags,
            'all_parameters': all_parameters,
            'required_level': highest_level
        }
