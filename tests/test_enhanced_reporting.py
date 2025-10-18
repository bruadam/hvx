"""
Tests for Enhanced Report Template System

Tests YAML parsing, validation, analytics aggregation, and report generation.
"""

import pytest
from pathlib import Path
import yaml
import json
import tempfile
import shutil

from src.core.reporting.yaml_template_parser import YAMLTemplateParser, ValidationResult
from src.core.reporting.analytics_data_aggregator import AnalyticsDataAggregator


class TestYAMLTemplateParser:
    """Test YAML template parser and validator."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return YAMLTemplateParser()
    
    @pytest.fixture
    def valid_template(self):
        """Create a valid template dictionary."""
        return {
            'template_id': 'test_template',
            'name': 'Test Template',
            'description': 'A test template',
            'version': '1.0',
            'report': {
                'title': 'Test Report',
                'format': 'html',
                'scope': 'building'
            },
            'sections': [
                {
                    'section_id': 'summary',
                    'type': 'summary',
                    'title': 'Summary'
                },
                {
                    'section_id': 'charts',
                    'type': 'charts',
                    'title': 'Charts',
                    'charts': [
                        {
                            'id': 'compliance_overview',
                            'title': 'Compliance Overview'
                        }
                    ]
                }
            ]
        }
    
    @pytest.fixture
    def temp_template_file(self, valid_template):
        """Create temporary template file."""
        temp_dir = Path(tempfile.mkdtemp())
        template_file = temp_dir / "test_template.yaml"
        
        with open(template_file, 'w') as f:
            yaml.dump(valid_template, f)
        
        yield template_file
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_parse_valid_template(self, parser, temp_template_file):
        """Test parsing a valid template file."""
        result = parser.parse_file(temp_template_file)
        
        assert isinstance(result, dict)
        assert result['template_id'] == 'test_template'
        assert result['name'] == 'Test Template'
        assert len(result['sections']) == 2
    
    def test_parse_missing_file(self, parser):
        """Test parsing non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("nonexistent.yaml"))
    
    def test_validate_valid_template(self, parser, valid_template):
        """Test validation of valid template."""
        result = parser.validate(valid_template)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_missing_required_keys(self, parser):
        """Test validation fails for missing required keys."""
        invalid_template = {
            'name': 'Test',
            # Missing 'template_id' and 'description'
        }
        
        result = parser.validate(invalid_template)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any('template_id' in error for error in result.errors)
    
    def test_validate_invalid_section_type(self, parser, valid_template):
        """Test validation fails for invalid section type."""
        valid_template['sections'].append({
            'section_id': 'invalid',
            'type': 'invalid_type'
        })
        
        result = parser.validate(valid_template)
        
        assert not result.is_valid
        assert any('invalid type' in error.lower() for error in result.errors)
    
    def test_validate_duplicate_section_ids(self, parser, valid_template):
        """Test validation fails for duplicate section IDs."""
        valid_template['sections'].append({
            'section_id': 'summary',  # Duplicate ID
            'type': 'summary'
        })
        
        result = parser.validate(valid_template)
        
        assert not result.is_valid
        assert any('duplicate' in error.lower() for error in result.errors)
    
    def test_validate_analytics_requirements(self, parser):
        """Test validation of analytics requirements."""
        template = {
            'template_id': 'test',
            'name': 'Test',
            'description': 'Test',
            'analytics_requirements': {
                'analytics_tags': [
                    'statistics.basic',
                    'compliance.overall',
                    'unknown.tag'  # Invalid tag
                ],
                'required_parameters': ['temperature', 'co2'],
                'min_data_quality': 0.7
            },
            'sections': []
        }
        
        result = parser.validate(template)
        
        # Should have warnings for unknown tag
        assert len(result.warnings) > 0
        assert any('unknown.tag' in warning.lower() for warning in result.warnings)
    
    def test_validate_invalid_data_quality(self, parser):
        """Test validation fails for invalid data quality threshold."""
        template = {
            'template_id': 'test',
            'name': 'Test',
            'description': 'Test',
            'analytics_requirements': {
                'min_data_quality': 1.5  # Invalid: > 1.0
            },
            'sections': []
        }
        
        result = parser.validate(template)
        
        assert not result.is_valid
        assert any('min_data_quality' in error for error in result.errors)
    
    def test_extract_analytics_requirements(self, parser, valid_template):
        """Test extracting analytics requirements from template."""
        # Add analytics requirements
        valid_template['analytics_requirements'] = {
            'analytics_tags': ['statistics.basic', 'compliance.overall'],
            'required_parameters': ['temperature', 'co2']
        }
        
        valid_template['sections'][1]['analytics_requirements'] = {
            'analytics_tags': ['spatial.comparison']
        }
        
        result = parser.extract_analytics_requirements(valid_template)
        
        assert 'all_tags' in result
        assert 'all_parameters' in result
        assert 'statistics.basic' in result['all_tags']
        assert 'compliance.overall' in result['all_tags']
        assert 'spatial.comparison' in result['all_tags']
        assert 'temperature' in result['all_parameters']
        assert 'co2' in result['all_parameters']
    
    def test_parse_and_validate(self, parser, temp_template_file):
        """Test combined parse and validate."""
        template_data, validation_result = parser.parse_and_validate(temp_template_file)
        
        assert isinstance(template_data, dict)
        assert isinstance(validation_result, ValidationResult)
        assert validation_result.is_valid


class TestAnalyticsDataAggregator:
    """Test analytics data aggregator."""
    
    @pytest.fixture
    def aggregator(self):
        """Create aggregator instance."""
        return AnalyticsDataAggregator()
    
    @pytest.fixture
    def sample_analysis_results(self):
        """Create sample analysis results."""
        return {
            'building_id': 'test_building',
            'building_name': 'Test Building',
            'room_count': 10,
            'level_count': 3,
            'avg_compliance_rate': 85.5,
            'avg_quality_score': 92.3,
            'statistics': {
                'temperature': {
                    'mean': 22.5,
                    'median': 22.3,
                    'std': 1.2,
                    'min': 18.0,
                    'max': 26.0,
                    'count': 1000
                },
                'co2': {
                    'mean': 750,
                    'median': 700,
                    'std': 150,
                    'min': 400,
                    'max': 1200,
                    'count': 1000
                }
            },
            'test_results': {
                'cat_ii_co2': {
                    'threshold': 1200,
                    'compliance_rate': 88.5,
                    'total_non_compliant_hours': 120
                }
            },
            'test_aggregations': {
                'cat_i_co2': {
                    'threshold': 950,
                    'avg_compliance_rate': 75.2
                },
                'cat_ii_co2': {
                    'threshold': 1200,
                    'avg_compliance_rate': 88.5
                }
            },
            'room_ids': ['room_1', 'room_2', 'room_3'],
            'best_performing_rooms': [
                {'room_id': 'room_1', 'compliance_rate': 95.0}
            ],
            'worst_performing_rooms': [
                {'room_id': 'room_3', 'compliance_rate': 65.0}
            ]
        }
    
    def test_collect_statistics(self, aggregator, sample_analysis_results):
        """Test collecting statistical data."""
        required_tags = {'statistics.basic'}
        required_params = {'temperature', 'co2'}
        
        result = aggregator.collect_required_analytics(
            sample_analysis_results,
            required_tags,
            required_params,
            required_level='building'
        )
        
        assert 'statistics' in result
        assert 'temperature' in result['statistics']
        assert 'co2' in result['statistics']
        assert result['statistics']['temperature']['mean'] == 22.5
        assert result['statistics']['co2']['mean'] == 750
    
    def test_collect_compliance(self, aggregator, sample_analysis_results):
        """Test collecting compliance data."""
        required_tags = {'compliance.overall', 'compliance.threshold'}
        required_params = set()
        
        result = aggregator.collect_required_analytics(
            sample_analysis_results,
            required_tags,
            required_params
        )
        
        assert 'compliance' in result
        assert 'overall' in result['compliance']
        assert result['compliance']['overall']['avg_compliance_rate'] == 85.5
        assert 'thresholds' in result['compliance']
    
    def test_collect_spatial(self, aggregator, sample_analysis_results):
        """Test collecting spatial data."""
        required_tags = {'spatial.room_level', 'spatial.ranking'}
        required_params = set()
        
        result = aggregator.collect_required_analytics(
            sample_analysis_results,
            required_tags,
            required_params
        )
        
        assert 'spatial' in result
        assert 'rooms' in result['spatial']
        assert result['spatial']['rooms']['room_count'] == 10
        assert 'rankings' in result['spatial']
    
    def test_metadata_generation(self, aggregator, sample_analysis_results):
        """Test metadata is included in result."""
        required_tags = {'statistics.basic'}
        required_params = {'temperature'}
        
        result = aggregator.collect_required_analytics(
            sample_analysis_results,
            required_tags,
            required_params,
            required_level='building'
        )
        
        assert '_metadata' in result
        assert 'tags_requested' in result['_metadata']
        assert 'parameters_requested' in result['_metadata']
        assert 'level_requested' in result['_metadata']
        assert result['_metadata']['level_requested'] == 'building'
    
    def test_validate_requirements_met(self, aggregator, sample_analysis_results):
        """Test validation of collected data."""
        required_tags = {'statistics.basic', 'compliance.overall'}
        required_params = {'temperature', 'co2'}
        
        collected_data = aggregator.collect_required_analytics(
            sample_analysis_results,
            required_tags,
            required_params
        )
        
        validation = aggregator.validate_requirements_met(
            collected_data,
            required_tags
        )
        
        assert 'all_requirements_met' in validation
        assert 'coverage_percentage' in validation
        assert validation['coverage_percentage'] > 0


class TestIntegration:
    """Integration tests for the complete workflow."""
    
    @pytest.fixture
    def sample_template_file(self):
        """Create a realistic template file for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        template_file = temp_dir / "integration_test.yaml"
        
        template = {
            'template_id': 'integration_test',
            'name': 'Integration Test Template',
            'description': 'Template for integration testing',
            'version': '1.0',
            'analytics_requirements': {
                'analytics_tags': [
                    'statistics.basic',
                    'compliance.overall'
                ],
                'required_parameters': ['temperature', 'co2'],
                'min_data_quality': 0.6
            },
            'report': {
                'title': 'Test Report',
                'format': 'html',
                'scope': 'building'
            },
            'sections': [
                {
                    'section_id': 'summary',
                    'type': 'summary',
                    'title': 'Building Summary'
                },
                {
                    'section_id': 'charts',
                    'type': 'charts',
                    'title': 'Analysis Charts',
                    'charts': [
                        {
                            'id': 'compliance_overview',
                            'title': 'Compliance Overview',
                            'analytics_requirements': {
                                'analytics_tags': ['compliance.overall']
                            }
                        }
                    ]
                }
            ]
        }
        
        with open(template_file, 'w') as f:
            yaml.dump(template, f)
        
        yield template_file
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_full_workflow(self, sample_template_file):
        """Test complete workflow from template to data collection."""
        # Parse template
        parser = YAMLTemplateParser()
        template_data, validation_result = parser.parse_and_validate(sample_template_file)
        
        assert validation_result.is_valid
        
        # Extract requirements
        requirements = parser.extract_analytics_requirements(template_data)
        
        assert 'statistics.basic' in requirements['all_tags']
        assert 'compliance.overall' in requirements['all_tags']
        assert 'temperature' in requirements['all_parameters']
        assert 'co2' in requirements['all_parameters']
        
        # Create sample analysis data
        analysis_results = {
            'building_id': 'test',
            'avg_compliance_rate': 85.0,
            'statistics': {
                'temperature': {'mean': 22.0, 'std': 1.5},
                'co2': {'mean': 800, 'std': 100}
            },
            'test_aggregations': {
                'cat_ii_co2': {'avg_compliance_rate': 85.0}
            }
        }
        
        # Collect analytics
        aggregator = AnalyticsDataAggregator()
        collected_data = aggregator.collect_required_analytics(
            analysis_results,
            requirements['all_tags'],
            requirements['all_parameters'],
            requirements['required_level']
        )
        
        assert 'statistics' in collected_data
        assert 'compliance' in collected_data
        
        # Validate data
        validation = aggregator.validate_requirements_met(
            collected_data,
            requirements['all_tags']
        )
        
        assert validation['coverage_percentage'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
