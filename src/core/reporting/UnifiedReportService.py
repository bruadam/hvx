"""
Unified Report Service

Orchestrates HTML and PDF report generation from YAML templates.
Supports charts, recommendations, and custom sections.
Includes analytics validation to ensure all required analytics are present.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.reporting.HTMLReportRenderer import HTMLReportRenderer
from src.core.reporting.PDFGenerator import PDFGenerator
from src.core.analytics.analytics_validator import AnalyticsValidator
from src.core.analytics.analytics_orchestrator import AnalyticsOrchestrator

logger = logging.getLogger(__name__)


class UnifiedReportService:
    """
    Unified service for generating HTML and PDF reports from YAML configuration.
    Includes analytics validation and automatic execution of missing analytics.
    """

    def __init__(
        self, 
        config_dir: Optional[Path] = None,
        enable_validation: bool = True,
        auto_execute_missing: bool = True
    ):
        """
        Initialize unified report service.

        Args:
            config_dir: Directory containing YAML report templates
            enable_validation: Enable analytics validation before report generation
            auto_execute_missing: Automatically execute missing analytics
        """
        if config_dir is None:
            config_dir = Path("config/report_templates")

        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Initialize renderers
        self.html_renderer = HTMLReportRenderer()
        self.pdf_generator = PDFGenerator()
        
        # Initialize analytics validation
        self.enable_validation = enable_validation
        self.auto_execute_missing = auto_execute_missing
        
        if enable_validation:
            self.validator = AnalyticsValidator()
            if auto_execute_missing:
                self.orchestrator = AnalyticsOrchestrator()
            else:
                self.orchestrator = None
        else:
            self.validator = None
            self.orchestrator = None

    def generate_report(
        self,
        template_name: str,
        analysis_results: Any,
        dataset: Any = None,
        weather_data: Any = None,
        format: str = 'html',
        output_filename: Optional[str] = None,
        skip_validation: bool = False,
        generate_per_building: bool = True
    ) -> Dict[str, Any]:
        """
        Generate report from template with analytics validation.

        Args:
            template_name: Name of YAML template (without .yaml extension)
            analysis_results: HierarchicalAnalysisResult object or AnalysisResults
            dataset: BuildingDataset object (optional, needed for missing analytics)
            weather_data: Weather DataFrame (optional)
            format: Output format ('html', 'pdf', or 'both')
            output_filename: Custom output filename (optional)
            skip_validation: Skip analytics validation (not recommended)
            generate_per_building: Generate one report per building for building-level templates

        Returns:
            Dictionary with generation results including validation info
        """
        # Load template configuration
        config_path = self.config_dir / f"{template_name}.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Template not found: {config_path}")
        
        # Load template config
        with open(config_path, 'r') as f:
            template_config = yaml.safe_load(f)
        
        # Check if this is a building-level template and we have multiple buildings
        template_scope = template_config.get('report', {}).get('scope', 'building')
        
        if (
            generate_per_building and 
            template_scope == 'building' and 
            hasattr(analysis_results, 'buildings') and 
            len(analysis_results.buildings) > 1
        ):
            # Generate one report per building
            logger.info(f"Detected {len(analysis_results.buildings)} buildings - generating separate reports")
            return self._generate_multiple_building_reports(
                template_name=template_name,
                config_path=config_path,
                template_config=template_config,
                analysis_results=analysis_results,
                dataset=dataset,
                weather_data=weather_data,
                format=format,
                skip_validation=skip_validation
            )
        
        # Single building or portfolio report - use standard generation
        result = self._generate_single_report(
            template_name=template_name,
            config_path=config_path,
            template_config=template_config,
            analysis_results=analysis_results,
            dataset=dataset,
            weather_data=weather_data,
            format=format,
            output_filename=output_filename,
            skip_validation=skip_validation
        )
        
        # Display CLI warnings for missing implementations (if any)
        if self.enable_validation and self.orchestrator:
            self.orchestrator.print_missing_implementations_warning()
        
        return result

    def _generate_multiple_building_reports(
        self,
        template_name: str,
        config_path: Path,
        template_config: Dict[str, Any],
        analysis_results: Any,
        dataset: Any,
        weather_data: Any,
        format: str,
        skip_validation: bool
    ) -> Dict[str, Any]:
        """
        Generate one report per building when multiple buildings exist.
        
        Args:
            template_name: Template name
            config_path: Path to template config
            template_config: Template configuration dict
            analysis_results: Analysis results with multiple buildings
            dataset: Dataset
            weather_data: Weather data
            format: Output format
            skip_validation: Skip validation flag
            
        Returns:
            Dictionary with all generated reports
        """
        from src.core.models.results.analysis_results import AnalysisResults
        
        generated_reports = []
        buildings = analysis_results.buildings
        
        logger.info(f"Generating {len(buildings)} building reports...")
        
        for building_id, building_analysis in buildings.items():
            logger.info(f"Generating report for building: {building_analysis.building_name}")
            
            # Create a single-building analysis results object
            # For building-scoped reports, pass the BuildingAnalysis object directly
            # This allows the renderer to access building-level data directly
            
            # Generate custom filename including building name
            building_name_safe = building_analysis.building_name.replace(' ', '_').replace('/', '_')
            custom_filename = f"{template_name}_{building_name_safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            try:
                # Call the standard generate_report but disable per-building generation to avoid recursion
                # Pass the BuildingAnalysis object directly instead of wrapped in HierarchicalAnalysisResult
                report_result = self._generate_single_report(
                    template_name=template_name,
                    config_path=config_path,
                    template_config=template_config,
                    analysis_results=building_analysis,  # Pass BuildingAnalysis directly
                    dataset=dataset,
                    weather_data=weather_data,
                    format=format,
                    output_filename=custom_filename,
                    skip_validation=skip_validation
                )
                
                report_result['building_id'] = building_id
                report_result['building_name'] = building_analysis.building_name
                generated_reports.append(report_result)
                
            except Exception as e:
                logger.error(f"Error generating report for building {building_analysis.building_name}: {e}")
                generated_reports.append({
                    'building_id': building_id,
                    'building_name': building_analysis.building_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Return summary of all generated reports
        successful = [r for r in generated_reports if r.get('status') == 'success']
        failed = [r for r in generated_reports if r.get('status') != 'success']
        
        return {
            'status': 'success' if successful else 'error',
            'template_name': template_name,
            'format': format,
            'total_buildings': len(buildings),
            'successful_reports': len(successful),
            'failed_reports': len(failed),
            'reports': generated_reports,
            'primary_outputs': [r.get('primary_output') for r in successful],
            'generated_at': datetime.now().isoformat()
        }
    
    def _generate_single_report(
        self,
        template_name: str,
        config_path: Path,
        template_config: Dict[str, Any],
        analysis_results: Any,
        dataset: Any,
        weather_data: Any,
        format: str,
        output_filename: Optional[str],
        skip_validation: bool
    ) -> Dict[str, Any]:
        """
        Generate a single report (internal method used by both single and multi-building generation).
        
        This is the core report generation logic extracted from generate_report.
        """
        # Validate and ensure analytics requirements
        validation_result = None
        if self.enable_validation and not skip_validation and self.validator:
            logger.info("Validating analytics requirements...")
            
            # Extract capability from analysis results
            capability = self.validator.extract_capability_from_analysis(analysis_results)
            
            # Validate template requirements
            validation_results = self.validator.validate_template_requirements(
                template_config, capability
            )
            
            # Get summary of missing analytics
            missing_summary = self.validator.get_missing_analytics_summary(validation_results)
            
            validation_result = {
                'validation_results': {k: v.to_dict() for k, v in validation_results.items()},
                'missing_summary': missing_summary
            }
            
            # Check if we need to execute missing analytics
            if missing_summary['failed_validations'] > 0:
                logger.warning(
                    f"Analytics validation found {missing_summary['failed_validations']} "
                    f"sections/graphs with missing analytics"
                )
                
                if self.auto_execute_missing and self.orchestrator and dataset:
                    logger.info("Auto-executing missing analytics...")
                    
                    # Create aggregate requirement from all missing analytics
                    from src.core.analytics.analytics_tags import AnalyticsRequirement, AnalyticsTag
                    
                    aggregate_req = AnalyticsRequirement()
                    
                    # Add all missing tags
                    for tag_str in missing_summary['missing_tags']:
                        try:
                            tag = AnalyticsTag(tag_str)
                            aggregate_req.add_analytics_tag(tag)
                        except ValueError:
                            pass
                    
                    # Add all missing tests and standards
                    for test in missing_summary['missing_tests']:
                        aggregate_req.add_test(test)
                    for standard in missing_summary['missing_standards']:
                        aggregate_req.add_standard(standard)
                    
                    # Execute missing analytics
                    try:
                        orchestration_result = self.orchestrator.ensure_requirements(
                            analysis_results=analysis_results,
                            requirement=aggregate_req,
                            dataset=dataset,
                            weather_data=weather_data
                        )
                        
                        # Update analysis results with executed analytics
                        if orchestration_result['status'] == 'updated':
                            analysis_results = orchestration_result['analysis_results']
                            logger.info("Successfully executed missing analytics")
                            validation_result['auto_execution'] = orchestration_result.get('executed_analytics')
                        
                    except Exception as e:
                        logger.error(f"Error executing missing analytics: {e}")
                        validation_result['auto_execution_error'] = str(e)
                
                elif not self.auto_execute_missing:
                    logger.warning(
                        "Auto-execution disabled. Report may be incomplete. "
                        "Enable auto_execute_missing or provide complete analysis results."
                    )
                elif not dataset:
                    logger.warning(
                        "Dataset not provided. Cannot execute missing analytics. "
                        "Provide dataset parameter to enable auto-execution."
                    )
            else:
                logger.info("All analytics requirements satisfied")

        # Generate HTML first
        html_result = self.html_renderer.render_report(
            config_path=config_path,
            analysis_results=analysis_results,
            dataset=dataset,
            weather_data=weather_data,
            output_filename=output_filename
        )

        if html_result['status'] != 'success':
            return html_result

        results = {
            'template_name': template_name,
            'html': html_result
        }
        
        # Include validation result if performed
        if validation_result:
            results['validation'] = validation_result

        # Generate PDF if requested
        if format in ['pdf', 'both']:
            html_path = Path(html_result['output_path'])
            pdf_path = html_path.with_suffix('.pdf')

            pdf_result = self.pdf_generator.html_to_pdf(
                html_path=html_path,
                pdf_path=pdf_path
            )

            results['pdf'] = pdf_result

            # Clean up HTML if only PDF was requested
            if format == 'pdf' and pdf_result['status'] == 'success':
                results['primary_output'] = pdf_path
                results['format'] = 'pdf'
            else:
                results['primary_output'] = html_path
                results['format'] = 'html'
        else:
            results['primary_output'] = Path(html_result['output_path'])
            results['format'] = 'html'

        results['status'] = 'success'
        results['generated_at'] = datetime.now().isoformat()

        return results

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available report templates."""
        templates = []

        for yaml_file in self.config_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    config = yaml.safe_load(f)

                templates.append({
                    'template_id': config.get('template_id', yaml_file.stem),
                    'name': config.get('name', yaml_file.stem),
                    'description': config.get('description', ''),
                    'version': config.get('version', '1.0'),
                    'author': config.get('author', 'Unknown'),
                    'sections_count': len(config.get('sections', [])),
                    'file_path': str(yaml_file)
                })
            except Exception as e:
                # Skip invalid templates
                continue

        return sorted(templates, key=lambda x: x['name'])

    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a template."""
        config_path = self.config_dir / f"{template_name}.yaml"

        if not config_path.exists():
            return None

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        sections_info = []
        for section in config.get('sections', []):
            sections_info.append({
                'id': section.get('section_id'),
                'type': section.get('type'),
                'title': section.get('title', 'Untitled')
            })

        return {
            'template_id': config.get('template_id'),
            'name': config.get('name'),
            'description': config.get('description'),
            'version': config.get('version'),
            'author': config.get('author'),
            'format': config.get('report', {}).get('format', 'html'),
            'theme': config.get('report', {}).get('theme', 'modern'),
            'sections': sections_info,
            'file_path': str(config_path)
        }

    def validate_template(self, template_name: str) -> Dict[str, Any]:
        """
        Validate a template configuration.

        Returns:
            Dictionary with validation results
        """
        config_path = self.config_dir / f"{template_name}.yaml"

        if not config_path.exists():
            return {
                'valid': False,
                'errors': [f"Template file not found: {config_path}"]
            }

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return {
                'valid': False,
                'errors': [f"Invalid YAML: {str(e)}"]
            }

        errors = []
        warnings = []

        # Required fields
        if not config.get('template_id'):
            errors.append("Missing required field: template_id")

        if not config.get('name'):
            errors.append("Missing required field: name")

        if not config.get('sections'):
            errors.append("Template must have at least one section")

        # Validate sections
        section_ids = []
        for i, section in enumerate(config.get('sections', [])):
            section_id = section.get('section_id')
            section_type = section.get('type')

            if not section_id:
                errors.append(f"Section {i}: Missing section_id")
            elif section_id in section_ids:
                errors.append(f"Section {i}: Duplicate section_id: {section_id}")
            else:
                section_ids.append(section_id)

            if not section_type:
                errors.append(f"Section {section_id}: Missing type")

            # Validate chart sections
            if section_type == 'charts':
                charts = section.get('charts', [])
                if not charts:
                    warnings.append(f"Section {section_id}: No charts defined")

                for chart in charts:
                    if not chart.get('id'):
                        errors.append(f"Section {section_id}: Chart missing id")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'section_count': len(config.get('sections', [])),
            'template_info': {
                'id': config.get('template_id'),
                'name': config.get('name'),
                'version': config.get('version', '1.0')
            }
        }

    def get_pdf_backend_info(self) -> Dict[str, Any]:
        """Get information about PDF generation backend."""
        return self.pdf_generator.get_backend_info()

    def create_template_from_dict(
        self,
        template_name: str,
        config_dict: Dict[str, Any]
    ) -> Path:
        """
        Create a new template from dictionary configuration.

        Args:
            template_name: Name for the template
            config_dict: Template configuration dictionary

        Returns:
            Path to created template file
        """
        config_path = self.config_dir / f"{template_name}.yaml"

        # Add metadata if not present
        if 'template_id' not in config_dict:
            config_dict['template_id'] = template_name

        if 'version' not in config_dict:
            config_dict['version'] = '1.0'

        # Save to file
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

        return config_path
