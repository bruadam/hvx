#!/usr/bin/env python3
"""
Example: Using the Enhanced Report Template System

This script demonstrates how to use the new enhanced reporting system
to generate HTML and PDF reports from YAML templates.
"""

import json
import logging
from pathlib import Path
from src.core.reporting.enhanced_report_service import EnhancedReportService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def load_sample_analysis_data():
    """Load sample building analysis data."""
    # Check if we have actual analysis data
    building_file = Path("output/analysis/buildings/building_1.json")
    
    if building_file.exists():
        logger.info(f"Loading analysis data from {building_file}")
        with open(building_file, 'r') as f:
            return json.load(f)
    else:
        logger.info("Using mock analysis data")
        # Return mock data for demonstration
        return {
            'building_id': 'demo_building',
            'building_name': 'Demo Building',
            'room_count': 15,
            'level_count': 3,
            'avg_compliance_rate': 82.5,
            'avg_quality_score': 89.3,
            'statistics': {
                'temperature': {
                    'mean': 22.3,
                    'median': 22.1,
                    'std': 1.5,
                    'min': 18.5,
                    'max': 25.8,
                    'count': 5000
                },
                'co2': {
                    'mean': 720,
                    'median': 680,
                    'std': 145,
                    'min': 420,
                    'max': 1180,
                    'count': 5000
                }
            },
            'test_aggregations': {
                'cat_i_co2': {
                    'threshold': 950,
                    'avg_compliance_rate': 73.2,
                    'min_compliance_rate': 55.0,
                    'max_compliance_rate': 95.0,
                    'total_non_compliant_hours': 450
                },
                'cat_ii_co2': {
                    'threshold': 1200,
                    'avg_compliance_rate': 87.5,
                    'min_compliance_rate': 72.0,
                    'max_compliance_rate': 98.0,
                    'total_non_compliant_hours': 185
                }
            },
            'room_ids': [f'room_{i}' for i in range(1, 16)],
            'best_performing_rooms': [
                {'room_id': 'room_1', 'room_name': 'Conference Room A', 'compliance_rate': 95.2},
                {'room_id': 'room_5', 'room_name': 'Office 201', 'compliance_rate': 93.8}
            ],
            'worst_performing_rooms': [
                {'room_id': 'room_12', 'room_name': 'Meeting Room C', 'compliance_rate': 68.5},
                {'room_id': 'room_9', 'room_name': 'Office 105', 'compliance_rate': 71.2}
            ]
        }


def example_1_list_templates():
    """Example 1: List all available templates."""
    logger.info("\n" + "="*60)
    logger.info("Example 1: List Available Templates")
    logger.info("="*60)
    
    service = EnhancedReportService()
    templates = service.list_available_templates()
    
    print(f"\nFound {len(templates)} templates:\n")
    for template in templates:
        print(f"  📄 {template['name']}")
        print(f"     ID: {template['template_id']}")
        print(f"     Description: {template['description']}")
        print(f"     Scope: {template.get('scope', 'N/A')}")
        print(f"     Format: {template.get('format', 'html')}")
        print()


def example_2_validate_template():
    """Example 2: Validate a template."""
    logger.info("\n" + "="*60)
    logger.info("Example 2: Validate Template")
    logger.info("="*60)
    
    service = EnhancedReportService()
    
    # Validate building_detailed template
    template_name = "building_detailed"
    print(f"\nValidating template: {template_name}\n")
    
    validation = service.validate_template_file(template_name)
    
    if validation.is_valid:
        print("✅ Template is valid!")
    else:
        print("❌ Template has errors:")
        for error in validation.errors:
            print(f"  - {error}")
    
    if validation.warnings:
        print("\n⚠️  Warnings:")
        for warning in validation.warnings:
            print(f"  - {warning}")
    
    if validation.info:
        print("\nℹ️  Information:")
        for info in validation.info:
            print(f"  - {info}")


def example_3_show_requirements():
    """Example 3: Show template analytics requirements."""
    logger.info("\n" + "="*60)
    logger.info("Example 3: Show Template Requirements")
    logger.info("="*60)
    
    service = EnhancedReportService()
    
    template_name = "building_detailed"
    print(f"\nAnalytics requirements for '{template_name}':\n")
    
    requirements = service.get_template_requirements(template_name)
    
    print(f"📊 Analytics Tags ({len(requirements['all_tags'])}):")
    for tag in sorted(requirements['all_tags']):
        print(f"   - {tag}")
    
    print(f"\n📈 Required Parameters ({len(requirements['all_parameters'])}):")
    for param in sorted(requirements['all_parameters']):
        print(f"   - {param}")
    
    if requirements['required_level']:
        print(f"\n🎯 Required Level: {requirements['required_level']}")


def example_4_generate_html_report():
    """Example 4: Generate HTML report."""
    logger.info("\n" + "="*60)
    logger.info("Example 4: Generate HTML Report")
    logger.info("="*60)
    
    service = EnhancedReportService()
    analysis_data = load_sample_analysis_data()
    
    template_name = "building_detailed"
    print(f"\nGenerating HTML report from '{template_name}' template...\n")
    
    result = service.generate_report(
        template_name=template_name,
        analysis_results=analysis_data,
        output_format='html',
        validate_data=True
    )
    
    if result['status'] == 'success':
        print("✅ Report generated successfully!")
        print(f"\n📄 HTML Report:")
        print(f"   Path: {result['html_report']['path']}")
        print(f"   Size: {result['html_report']['size']:,} bytes")
        
        print(f"\n⏱️  Generation time: {result['generation_time_seconds']:.2f} seconds")
        
        if result['validation_result']['warnings']:
            print(f"\n⚠️  Template had {len(result['validation_result']['warnings'])} warnings")
        
        # Show analytics coverage
        metadata = result.get('analytics_coverage', {})
        if 'data_available' in metadata:
            available = [k for k, v in metadata['data_available'].items() if v]
            print(f"\n📊 Analytics Categories Available: {len(available)}")
    else:
        print(f"❌ Report generation failed: {result.get('error')}")


def example_5_generate_pdf_report():
    """Example 5: Generate PDF report."""
    logger.info("\n" + "="*60)
    logger.info("Example 5: Generate PDF Report")
    logger.info("="*60)
    
    service = EnhancedReportService()
    analysis_data = load_sample_analysis_data()
    
    template_name = "building_detailed"
    print(f"\nGenerating PDF report from '{template_name}' template...\n")
    
    result = service.generate_report(
        template_name=template_name,
        analysis_results=analysis_data,
        output_format='both',  # Generate both HTML and PDF
        validate_data=True
    )
    
    if result['status'] == 'success':
        print("✅ Reports generated successfully!")
        
        print(f"\n📄 HTML Report:")
        print(f"   Path: {result['html_report']['path']}")
        print(f"   Size: {result['html_report']['size']:,} bytes")
        
        if 'pdf_report' in result:
            pdf_info = result['pdf_report']
            if pdf_info['status'] == 'success':
                print(f"\n📕 PDF Report:")
                print(f"   Path: {pdf_info['output_path']}")
                print(f"   Size: {pdf_info['file_size']:,} bytes")
                print(f"   Backend: {pdf_info['backend']}")
                if 'pages' in pdf_info and pdf_info['pages']:
                    print(f"   Pages: {pdf_info['pages']}")
            else:
                print(f"\n❌ PDF generation failed: {pdf_info.get('message')}")
                print(f"   Backend: {pdf_info.get('backend')}")
        
        print(f"\n⏱️  Total generation time: {result['generation_time_seconds']:.2f} seconds")
    else:
        print(f"❌ Report generation failed: {result.get('error')}")


def example_6_batch_generation():
    """Example 6: Generate multiple reports."""
    logger.info("\n" + "="*60)
    logger.info("Example 6: Batch Report Generation")
    logger.info("="*60)
    
    service = EnhancedReportService()
    analysis_data = load_sample_analysis_data()
    
    # Generate reports from multiple templates
    templates = []
    
    # Check which templates exist
    if (Path("config/report_templates/building_detailed.yaml").exists()):
        templates.append("building_detailed")
    if (Path("config/report_templates/standard_building.yaml").exists()):
        templates.append("standard_building")
    
    if not templates:
        print("No templates found for batch generation")
        return
    
    print(f"\nGenerating {len(templates)} reports...\n")
    
    results = service.generate_batch_reports(
        template_names=templates,
        analysis_results=analysis_data,
        output_format='html'
    )
    
    print(f"\n📊 Batch Generation Summary:")
    print(f"   Total: {results['total']}")
    print(f"   ✅ Successful: {results['successful']}")
    print(f"   ❌ Failed: {results['failed']}")
    
    print(f"\n📄 Results:")
    for template_name, result in results['results'].items():
        if result['status'] == 'success':
            print(f"   ✅ {template_name}: {result['html_report']['path']}")
        else:
            print(f"   ❌ {template_name}: {result.get('error', 'Unknown error')}")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Enhanced Report Template System - Examples")
    print("="*60)
    
    try:
        # Run examples
        example_1_list_templates()
        example_2_validate_template()
        example_3_show_requirements()
        example_4_generate_html_report()
        example_5_generate_pdf_report()
        example_6_batch_generation()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == '__main__':
    main()
