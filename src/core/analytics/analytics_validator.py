"""
Analytics Validator

Validates that analysis results contain all required analytics, tests, and standards
needed for report generation. Identifies missing analytics and orchestrates their execution.
"""

import logging
from typing import Dict, List, Set, Optional, Any, Union
from pathlib import Path

from src.core.analytics.analytics_tags import (
    AnalyticsTag,
    AnalyticsRequirement,
    AnalyticsCapability,
    ValidationResult
)

logger = logging.getLogger(__name__)


class AnalyticsValidator:
    """
    Validates analysis results against report requirements.
    
    Checks if all required analytics, tests, and standards are present.
    Identifies missing analytics that need to be executed.
    """
    
    def __init__(self):
        """Initialize the validator."""
        pass
    
    def validate_requirements(
        self,
        requirement: AnalyticsRequirement,
        capability: AnalyticsCapability
    ) -> ValidationResult:
        """
        Validate that capabilities meet requirements.
        
        Args:
            requirement: What analytics are required
            capability: What analytics are available
        
        Returns:
            ValidationResult with details about missing analytics
        """
        result = ValidationResult(is_valid=True)
        
        # Check analytics tags
        missing_tags = requirement.analytics_tags - capability.available_tags
        if missing_tags:
            result.is_valid = False
            result.missing_tags = missing_tags
            for tag in missing_tags:
                result.add_message(f"Missing analytics: {tag.value}")
        
        # Check tests
        missing_tests = requirement.required_tests - capability.completed_tests
        if missing_tests:
            result.is_valid = False
            result.missing_tests = missing_tests
            for test in missing_tests:
                result.add_message(f"Missing test: {test}")
        
        # Check standards
        missing_standards = requirement.required_standards - capability.applied_standards
        if missing_standards:
            result.is_valid = False
            result.missing_standards = missing_standards
            for standard in missing_standards:
                result.add_message(f"Missing standard: {standard}")
        
        # Check parameters
        missing_parameters = requirement.required_parameters - capability.available_parameters
        if missing_parameters:
            result.is_valid = False
            result.missing_parameters = missing_parameters
            for param in missing_parameters:
                result.add_message(f"Missing parameter: {param}")
        
        # Check level
        if requirement.required_level:
            if capability.analysis_level != requirement.required_level:
                result.is_valid = False
                result.add_message(
                    f"Level mismatch: required {requirement.required_level}, "
                    f"got {capability.analysis_level}"
                )
        
        # Check data quality
        if requirement.min_data_quality is not None:
            if capability.data_quality_score is None:
                result.add_warning("Data quality score not available")
            elif capability.data_quality_score < requirement.min_data_quality:
                result.add_warning(
                    f"Data quality below threshold: "
                    f"{capability.data_quality_score:.2f} < {requirement.min_data_quality:.2f}"
                )
        
        # Check time range
        if requirement.min_time_range_days is not None:
            if capability.time_range_days is None:
                result.add_warning("Time range not available")
            elif capability.time_range_days < requirement.min_time_range_days:
                result.add_warning(
                    f"Time range too short: "
                    f"{capability.time_range_days} < {requirement.min_time_range_days} days"
                )
        
        # Log validation result
        if result.is_valid:
            logger.info("Analytics validation passed")
        else:
            logger.warning(
                f"Analytics validation failed: {len(result.missing_tags)} missing tags, "
                f"{len(result.missing_tests)} missing tests, "
                f"{len(result.missing_standards)} missing standards"
            )
        
        return result
    
    def extract_capability_from_analysis(
        self,
        analysis_results: Any
    ) -> AnalyticsCapability:
        """
        Extract analytics capability from analysis results.
        
        Args:
            analysis_results: HierarchicalAnalysisResult or similar object
        
        Returns:
            AnalyticsCapability describing what's available
        """
        capability = AnalyticsCapability()
        
        # Try to extract from HierarchicalAnalysisResult
        if hasattr(analysis_results, '__dict__'):
            # Detect available parameters
            if hasattr(analysis_results, 'building_results'):
                building_results = analysis_results.building_results
                if building_results and hasattr(building_results, 'room_results'):
                    # Extract from first room to get parameters
                    room_results = building_results.room_results
                    if room_results:
                        first_room = next(iter(room_results.values()), None)
                        if first_room:
                            # Check for test results
                            if hasattr(first_room, 'user_rules'):
                                for rule_result in first_room.user_rules:
                                    if hasattr(rule_result, 'parameter'):
                                        capability.available_parameters.add(rule_result.parameter)
                                    if hasattr(rule_result, 'rule_id'):
                                        capability.completed_tests.add(rule_result.rule_id)
                            
                            # Check for standard results
                            if hasattr(first_room, 'standard_results'):
                                for standard_id, standard_result in first_room.standard_results.items():
                                    capability.applied_standards.add(standard_id)
                                    # Add compliance tag
                                    capability.available_tags.add(AnalyticsTag.COMPLIANCE_OVERALL)
            
            # Detect analysis level
            if hasattr(analysis_results, 'level'):
                capability.analysis_level = analysis_results.level
            elif hasattr(analysis_results, 'building_results'):
                if hasattr(analysis_results.building_results, 'room_results'):
                    capability.analysis_level = 'room'
                else:
                    capability.analysis_level = 'building'
            
            # Extract data quality if available
            if hasattr(analysis_results, 'data_quality_score'):
                capability.data_quality_score = analysis_results.data_quality_score
            elif hasattr(analysis_results, 'building_results'):
                if hasattr(analysis_results.building_results, 'data_quality'):
                    capability.data_quality_score = analysis_results.building_results.data_quality
            
            # Extract time range if available
            if hasattr(analysis_results, 'time_range_days'):
                capability.time_range_days = analysis_results.time_range_days
            
            # Detect statistics
            if hasattr(analysis_results, 'building_results'):
                building_results = analysis_results.building_results
                if hasattr(building_results, 'statistics') or \
                   (hasattr(building_results, 'room_results') and building_results.room_results):
                    capability.available_tags.add(AnalyticsTag.STATISTICS_BASIC)
            
            # Detect recommendations
            if hasattr(analysis_results, 'recommendations'):
                capability.available_tags.add(AnalyticsTag.RECOMMENDATIONS_OPERATIONAL)
                if analysis_results.recommendations:
                    # Check recommendation types
                    for rec in analysis_results.recommendations[:5]:  # Sample first few
                        if hasattr(rec, 'category'):
                            if 'hvac' in str(rec.category).lower():
                                capability.available_tags.add(AnalyticsTag.RECOMMENDATIONS_HVAC)
                            elif 'ventilation' in str(rec.category).lower():
                                capability.available_tags.add(AnalyticsTag.RECOMMENDATIONS_VENTILATION)
            
            # Detect weather correlation
            if hasattr(analysis_results, 'weather_correlation') or \
               hasattr(analysis_results, 'weather_data'):
                capability.available_tags.add(AnalyticsTag.WEATHER_OUTDOOR_CONDITIONS)
        
        # Try dictionary access as fallback
        elif isinstance(analysis_results, dict):
            # Extract from dictionary format
            if 'parameters' in analysis_results:
                capability.available_parameters.update(analysis_results['parameters'])
            
            if 'tests' in analysis_results or 'user_rules' in analysis_results:
                tests_key = 'tests' if 'tests' in analysis_results else 'user_rules'
                for test in analysis_results.get(tests_key, []):
                    if isinstance(test, dict) and 'rule_id' in test:
                        capability.completed_tests.add(test['rule_id'])
                    if isinstance(test, dict) and 'parameter' in test:
                        capability.available_parameters.add(test['parameter'])
                capability.available_tags.add(AnalyticsTag.COMPLIANCE_OVERALL)
            
            if 'standards' in analysis_results:
                for standard in analysis_results['standards']:
                    if isinstance(standard, str):
                        capability.applied_standards.add(standard)
                    elif isinstance(standard, dict) and 'standard_id' in standard:
                        capability.applied_standards.add(standard['standard_id'])
            
            if 'recommendations' in analysis_results:
                capability.available_tags.add(AnalyticsTag.RECOMMENDATIONS_OPERATIONAL)
            
            if 'data_quality' in analysis_results:
                capability.data_quality_score = analysis_results['data_quality']
            
            if 'level' in analysis_results:
                capability.analysis_level = analysis_results['level']
        
        return capability
    
    def validate_section_requirements(
        self,
        section_config: Dict[str, Any],
        capability: AnalyticsCapability
    ) -> ValidationResult:
        """
        Validate requirements for a specific report section.
        
        Args:
            section_config: Section configuration from template
            capability: Available analytics capability
        
        Returns:
            ValidationResult for this section
        """
        # Extract requirements from section config
        requirement = self._extract_requirement_from_config(section_config)
        
        # Validate
        return self.validate_requirements(requirement, capability)
    
    def validate_graph_requirements(
        self,
        graph_config: Dict[str, Any],
        capability: AnalyticsCapability
    ) -> ValidationResult:
        """
        Validate requirements for a specific graph.
        
        Args:
            graph_config: Graph configuration from template
            capability: Available analytics capability
        
        Returns:
            ValidationResult for this graph
        """
        # Extract requirements from graph config
        requirement = self._extract_requirement_from_config(graph_config)
        
        # Add graph-specific requirements
        graph_id = graph_config.get('id', '')
        
        # Infer requirements from graph ID
        if 'compliance' in graph_id.lower():
            requirement.add_analytics_tag(AnalyticsTag.COMPLIANCE_OVERALL)
        
        if 'heatmap' in graph_id.lower():
            requirement.add_analytics_tag(AnalyticsTag.TEMPORAL_HOURLY)
            requirement.add_analytics_tag(AnalyticsTag.TEMPORAL_DAILY)
        
        if 'correlation' in graph_id.lower() or 'weather' in graph_id.lower():
            requirement.add_analytics_tag(AnalyticsTag.WEATHER_OUTDOOR_CONDITIONS)
            requirement.add_analytics_tag(AnalyticsTag.STATISTICS_CORRELATION)
        
        if 'recommendation' in graph_id.lower():
            requirement.add_analytics_tag(AnalyticsTag.RECOMMENDATIONS_OPERATIONAL)
        
        # Validate
        return self.validate_requirements(requirement, capability)
    
    def validate_template_requirements(
        self,
        template_config: Dict[str, Any],
        capability: AnalyticsCapability
    ) -> Dict[str, ValidationResult]:
        """
        Validate requirements for entire template.
        
        Args:
            template_config: Full template configuration
            capability: Available analytics capability
        
        Returns:
            Dictionary mapping section/graph IDs to validation results
        """
        results = {}
        
        # Validate each section
        for section in template_config.get('sections', []):
            section_id = section.get('section_id', section.get('id', 'unknown'))
            
            # Validate section itself
            section_result = self.validate_section_requirements(section, capability)
            results[f"section:{section_id}"] = section_result
            
            # Validate graphs within section
            if section.get('type') == 'charts' and 'charts' in section:
                for chart in section['charts']:
                    chart_id = chart.get('id', 'unknown')
                    chart_result = self.validate_graph_requirements(chart, capability)
                    results[f"graph:{section_id}:{chart_id}"] = chart_result
        
        return results
    
    def get_missing_analytics_summary(
        self,
        validation_results: Dict[str, ValidationResult]
    ) -> Dict[str, Any]:
        """
        Get summary of all missing analytics across all validations.
        
        Args:
            validation_results: Results from validate_template_requirements
        
        Returns:
            Summary of missing analytics
        """
        all_missing_tags = set()
        all_missing_tests = set()
        all_missing_standards = set()
        all_missing_parameters = set()
        
        for result in validation_results.values():
            all_missing_tags.update(result.missing_tags)
            all_missing_tests.update(result.missing_tests)
            all_missing_standards.update(result.missing_standards)
            all_missing_parameters.update(result.missing_parameters)
        
        return {
            'missing_tags': [tag.value for tag in all_missing_tags],
            'missing_tests': list(all_missing_tests),
            'missing_standards': list(all_missing_standards),
            'missing_parameters': list(all_missing_parameters),
            'total_validations': len(validation_results),
            'failed_validations': sum(1 for r in validation_results.values() if not r.is_valid)
        }
    
    def _extract_requirement_from_config(
        self,
        config: Dict[str, Any]
    ) -> AnalyticsRequirement:
        """
        Extract analytics requirement from configuration dictionary.
        
        Args:
            config: Section or graph configuration
        
        Returns:
            AnalyticsRequirement object
        """
        requirement = AnalyticsRequirement()
        
        # Extract from 'requirements' or 'analytics_requirements' key
        req_config = config.get('requirements') or config.get('analytics_requirements')
        
        if req_config:
            if isinstance(req_config, dict):
                requirement = AnalyticsRequirement.from_dict(req_config)
            elif isinstance(req_config, str):
                # Reference to a template
                from src.core.analytics.analytics_tags import REQUIREMENT_TEMPLATES
                template = REQUIREMENT_TEMPLATES.get(req_config)
                if template:
                    requirement = template
        
        # Also check for direct keys in config
        if 'analytics_tags' in config:
            for tag_str in config['analytics_tags']:
                try:
                    tag = AnalyticsTag(tag_str)
                    requirement.add_analytics_tag(tag)
                except ValueError:
                    pass
        
        if 'required_tests' in config:
            for test in config['required_tests']:
                requirement.add_test(test)
        
        if 'required_standards' in config:
            for standard in config['required_standards']:
                requirement.add_standard(standard)
        
        if 'required_parameters' in config:
            for param in config['required_parameters']:
                requirement.add_parameter(param)
        
        return requirement


__all__ = ['AnalyticsValidator']
