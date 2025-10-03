#!/usr/bin/env python3
"""
Example: Using the Analytics Validation System

Demonstrates how to use analytics validation and auto-execution
when generating reports.
"""

from pathlib import Path
from src.core.reporting.UnifiedReportService import UnifiedReportService
from src.core.analytics.analytics_validator import AnalyticsValidator
from src.core.analytics.analytics_orchestrator import AnalyticsOrchestrator
from src.core.analytics.analytics_tags import (
    AnalyticsRequirement, 
    AnalyticsTag,
    REQUIREMENT_TEMPLATES
)


def example_1_basic_report_with_validation():
    """Example 1: Generate report with automatic validation."""
    print("=" * 60)
    print("Example 1: Basic Report with Validation")
    print("=" * 60)
    
    # Initialize service with validation enabled
    service = UnifiedReportService(
        enable_validation=True,
        auto_execute_missing=True
    )
    
    # Simulate analysis results and dataset
    # In real usage, these would come from your analysis pipeline
    analysis_results = {
        'building_name': 'Example Building',
        'user_rules': [
            {
                'rule_id': 'temperature_comfort',
                'parameter': 'temperature',
                'compliance_rate': 85.5
            }
        ],
        'parameters': ['temperature', 'co2']
    }
    
    dataset = None  # Would be your BuildingDataset object
    
    # Generate report
    print("\nGenerating report with validation...")
    try:
        result = service.generate_report(
            template_name='standard_building',
            analysis_results=analysis_results,
            dataset=dataset,  # Needed for auto-execution
            format='html'
        )
        
        print(f"\n✓ Report generated: {result.get('primary_output')}")
        
        # Check validation results
        if 'validation' in result:
            validation = result['validation']
            print("\nValidation Summary:")
            print(f"  Failed validations: {validation['missing_summary']['failed_validations']}")
            print(f"  Missing tags: {len(validation['missing_summary']['missing_tags'])}")
            print(f"  Missing tests: {len(validation['missing_summary']['missing_tests'])}")
            
            if 'auto_execution' in validation:
                print("\nAuto-executed analytics:")
                print(f"  Tags: {validation['auto_execution'].get('tags', [])}")
                print(f"  Tests: {validation['auto_execution'].get('tests', [])}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_2_manual_validation():
    """Example 2: Manual validation before report generation."""
    print("\n" + "=" * 60)
    print("Example 2: Manual Validation")
    print("=" * 60)
    
    # Create validator
    validator = AnalyticsValidator()
    
    # Simulate analysis results
    analysis_results = {
        'parameters': ['temperature'],
        'user_rules': [
            {'rule_id': 'temp_test', 'parameter': 'temperature'}
        ]
    }
    
    # Extract capability from results
    print("\nExtracting analytics capability from results...")
    capability = validator.extract_capability_from_analysis(analysis_results)
    
    print(f"  Available parameters: {capability.available_parameters}")
    print(f"  Completed tests: {capability.completed_tests}")
    print(f"  Available tags: {[t.value for t in capability.available_tags]}")
    
    # Define requirements
    print("\nDefining requirements...")
    requirement = AnalyticsRequirement()
    requirement.add_analytics_tag(AnalyticsTag.STATISTICS_BASIC)
    requirement.add_analytics_tag(AnalyticsTag.COMPLIANCE_OVERALL)
    requirement.add_parameter('temperature')
    requirement.add_parameter('co2')  # This will be missing
    
    print(f"  Required tags: {[t.value for t in requirement.analytics_tags]}")
    print(f"  Required parameters: {requirement.required_parameters}")
    
    # Validate
    print("\nValidating requirements...")
    validation = validator.validate_requirements(requirement, capability)
    
    if validation.is_valid:
        print("  ✓ All requirements met")
    else:
        print("  ✗ Requirements not met:")
        if validation.missing_tags:
            print(f"    Missing tags: {[t.value for t in validation.missing_tags]}")
        if validation.missing_parameters:
            print(f"    Missing parameters: {validation.missing_parameters}")
        if validation.messages:
            print("    Messages:")
            for msg in validation.messages:
                print(f"      - {msg}")


def example_3_custom_orchestration():
    """Example 3: Custom analytics orchestration."""
    print("\n" + "=" * 60)
    print("Example 3: Custom Analytics Orchestration")
    print("=" * 60)
    
    # Create orchestrator
    orchestrator = AnalyticsOrchestrator()
    
    # Simulate dataset
    dataset = None  # Would be your BuildingDataset
    
    # Existing results
    analysis_results = {
        'parameters': ['temperature']
    }
    
    print("\nExecuting specific analytics by tags...")
    
    # Execute specific analytics
    tags_to_execute = {
        AnalyticsTag.STATISTICS_BASIC,
        AnalyticsTag.DATA_QUALITY_COMPLETENESS
    }
    
    print(f"  Tags to execute: {[t.value for t in tags_to_execute]}")
    
    try:
        updated_results = orchestrator.execute_analytics_by_tags(
            tags=tags_to_execute,
            dataset=dataset,
            analysis_results=analysis_results
        )
        
        print("  ✓ Analytics executed")
        print(f"  Updated results keys: {list(updated_results.keys())}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")


def example_4_requirement_templates():
    """Example 4: Using predefined requirement templates."""
    print("\n" + "=" * 60)
    print("Example 4: Requirement Templates")
    print("=" * 60)
    
    print("\nAvailable requirement templates:")
    for template_name, template in REQUIREMENT_TEMPLATES.items():
        print(f"\n  {template_name}:")
        print(f"    Tags: {[t.value for t in template.analytics_tags]}")
    
    # Use a template
    print("\n\nUsing 'basic_summary' template...")
    requirement = REQUIREMENT_TEMPLATES['basic_summary']
    
    print(f"  Required tags: {[t.value for t in requirement.analytics_tags]}")
    
    # Create capability
    from src.core.analytics.analytics_tags import AnalyticsCapability
    
    capability = AnalyticsCapability()
    capability.available_tags.add(AnalyticsTag.STATISTICS_BASIC)
    capability.available_tags.add(AnalyticsTag.COMPLIANCE_OVERALL)
    capability.available_tags.add(AnalyticsTag.DATA_QUALITY_COMPLETENESS)
    
    # Validate
    validator = AnalyticsValidator()
    validation = validator.validate_requirements(requirement, capability)
    
    if validation.is_valid:
        print("  ✓ Template requirements met")
    else:
        print(f"  ✗ Missing: {[t.value for t in validation.missing_tags]}")


def example_5_template_validation():
    """Example 5: Validate entire report template."""
    print("\n" + "=" * 60)
    print("Example 5: Template Validation")
    print("=" * 60)
    
    validator = AnalyticsValidator()
    
    # Simulate template config
    template_config = {
        'template_id': 'example_template',
        'sections': [
            {
                'section_id': 'summary',
                'type': 'summary',
                'analytics_requirements': {
                    'analytics_tags': ['statistics.basic', 'compliance.overall'],
                    'required_parameters': ['temperature']
                }
            },
            {
                'section_id': 'charts',
                'type': 'charts',
                'charts': [
                    {
                        'id': 'temp_heatmap',
                        'analytics_requirements': {
                            'analytics_tags': ['temporal.hourly'],
                            'required_parameters': ['temperature']
                        }
                    }
                ]
            }
        ]
    }
    
    # Create capability
    from src.core.analytics.analytics_tags import AnalyticsCapability
    
    capability = AnalyticsCapability()
    capability.available_tags.add(AnalyticsTag.STATISTICS_BASIC)
    capability.available_tags.add(AnalyticsTag.COMPLIANCE_OVERALL)
    capability.available_parameters.add('temperature')
    
    print("\nValidating template requirements...")
    validation_results = validator.validate_template_requirements(
        template_config, capability
    )
    
    print(f"\n  Total validations: {len(validation_results)}")
    
    for section_id, result in validation_results.items():
        status = "✓" if result.is_valid else "✗"
        print(f"  {status} {section_id}")
        if not result.is_valid and result.missing_tags:
            print(f"      Missing: {[t.value for t in result.missing_tags]}")
    
    # Get summary
    summary = validator.get_missing_analytics_summary(validation_results)
    print(f"\n  Summary:")
    print(f"    Failed validations: {summary['failed_validations']}")
    print(f"    Total missing tags: {len(summary['missing_tags'])}")
    print(f"    Total missing tests: {len(summary['missing_tests'])}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Analytics Validation System - Examples")
    print("=" * 60)
    
    try:
        example_1_basic_report_with_validation()
    except Exception as e:
        print(f"Example 1 failed: {e}")
    
    try:
        example_2_manual_validation()
    except Exception as e:
        print(f"Example 2 failed: {e}")
    
    try:
        example_3_custom_orchestration()
    except Exception as e:
        print(f"Example 3 failed: {e}")
    
    try:
        example_4_requirement_templates()
    except Exception as e:
        print(f"Example 4 failed: {e}")
    
    try:
        example_5_template_validation()
    except Exception as e:
        print(f"Example 5 failed: {e}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
