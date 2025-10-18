"""
Enhanced Report Generation Service

Integrates YAML template parsing, analytics data aggregation,
HTML rendering, and PDF generation into a unified workflow.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.reporting.yaml_template_parser import YAMLTemplateParser, ValidationResult
from src.core.reporting.analytics_data_aggregator import AnalyticsDataAggregator
from src.core.reporting.HTMLReportRenderer import HTMLReportRenderer
from src.core.reporting.PDFGenerator import PDFGenerator

logger = logging.getLogger(__name__)


class EnhancedReportService:
    """
    Enhanced report generation service with full YAML template support.
    
    Workflow:
    1. Parse and validate YAML template
    2. Extract analytics requirements
    3. Collect required analytics data
    4. Validate data availability
    5. Generate HTML report
    6. Convert to PDF if requested
    """
    
    def __init__(
        self,
        templates_dir: Path = Path("config/report_templates"),
        output_dir: Path = Path("output/reports"),
        enable_validation: bool = True
    ):
        """
        Initialize enhanced report service.
        
        Args:
            templates_dir: Directory containing YAML templates
            output_dir: Directory for generated reports
            enable_validation: Enable template validation (recommended)
        """
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        self.enable_validation = enable_validation
        
        # Initialize components
        self.yaml_parser = YAMLTemplateParser()
        self.analytics_aggregator = AnalyticsDataAggregator()
        self.html_renderer = HTMLReportRenderer()
        self.pdf_generator = PDFGenerator()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Enhanced Report Service initialized")
        logger.info(f"  Templates dir: {templates_dir}")
        logger.info(f"  Output dir: {output_dir}")
        logger.info(f"  Validation: {'enabled' if enable_validation else 'disabled'}")
    
    def generate_report(
        self,
        template_name: str,
        analysis_results: Any,
        dataset: Any = None,
        weather_data: Any = None,
        output_format: str = 'html',
        output_filename: Optional[str] = None,
        validate_data: bool = True
    ) -> Dict[str, Any]:
        """
        Generate report from template and analysis data.
        
        Args:
            template_name: Name of template (without .yaml extension)
            analysis_results: Analysis results object or dict
            dataset: Building dataset (optional, needed for recommendations)
            weather_data: Weather data (optional)
            output_format: 'html', 'pdf', or 'both'
            output_filename: Custom output filename (optional)
            validate_data: Validate analytics data availability
            
        Returns:
            Dictionary with generation results and file paths
        """
        start_time = datetime.now()
        
        logger.info(f"Starting report generation: {template_name}")
        logger.info(f"  Output format: {output_format}")
        
        try:
            # Step 1: Parse and validate template
            template_path = self.templates_dir / f"{template_name}.yaml"
            template_data, validation_result = self._load_and_validate_template(template_path)
            
            if not validation_result.is_valid and self.enable_validation:
                return {
                    'status': 'error',
                    'error': 'Template validation failed',
                    'validation_errors': validation_result.errors,
                    'validation_warnings': validation_result.warnings
                }
            
            # Step 2: Extract analytics requirements
            analytics_reqs = self.yaml_parser.extract_analytics_requirements(template_data)
            logger.info(f"  Required analytics tags: {len(analytics_reqs['all_tags'])}")
            logger.info(f"  Required parameters: {len(analytics_reqs['all_parameters'])}")
            
            # Step 3: Collect analytics data
            collected_data = self.analytics_aggregator.collect_required_analytics(
                analysis_results,
                analytics_reqs['all_tags'],
                analytics_reqs['all_parameters'],
                analytics_reqs['required_level']
            )
            
            # Step 4: Validate data availability
            if validate_data:
                data_validation = self.analytics_aggregator.validate_requirements_met(
                    collected_data,
                    analytics_reqs['all_tags']
                )
                
                logger.info(f"  Data coverage: {data_validation['coverage_percentage']:.1f}%")
                
                if not data_validation['all_requirements_met']:
                    logger.warning(f"  Missing data categories: {data_validation['missing_categories']}")
                    
                    if data_validation['coverage_percentage'] < 50:
                        return {
                            'status': 'error',
                            'error': 'Insufficient data for report generation',
                            'data_validation': data_validation
                        }
            
            # Step 5: Generate HTML report
            html_result = self._generate_html(
                template_path,
                template_data,
                analysis_results,
                dataset,
                weather_data,
                output_filename
            )
            
            if html_result['status'] != 'success':
                return html_result
            
            html_path = Path(html_result['output_path'])
            
            # Step 6: Generate PDF if requested
            pdf_result = None
            if output_format in ['pdf', 'both']:
                pdf_result = self._generate_pdf(html_path)
            
            # Calculate elapsed time
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare final result
            result = {
                'status': 'success',
                'template_name': template_name,
                'output_format': output_format,
                'html_report': {
                    'path': str(html_path),
                    'size': html_path.stat().st_size,
                    'exists': html_path.exists()
                },
                'validation_result': {
                    'is_valid': validation_result.is_valid,
                    'errors': validation_result.errors,
                    'warnings': validation_result.warnings,
                    'info': validation_result.info
                },
                'analytics_coverage': collected_data.get('_metadata', {}),
                'generation_time_seconds': elapsed_time
            }
            
            if pdf_result:
                result['pdf_report'] = pdf_result
            
            logger.info(f"Report generation completed in {elapsed_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'template_name': template_name
            }
    
    def _load_and_validate_template(
        self,
        template_path: Path
    ) -> tuple[Dict[str, Any], ValidationResult]:
        """Load and validate template."""
        logger.info(f"Loading template: {template_path.name}")
        
        template_data, validation_result = self.yaml_parser.parse_and_validate(template_path)
        
        # Log validation results
        if validation_result.errors:
            logger.error(f"Validation errors: {len(validation_result.errors)}")
            for error in validation_result.errors:
                logger.error(f"  - {error}")
        
        if validation_result.warnings:
            logger.warning(f"Validation warnings: {len(validation_result.warnings)}")
            for warning in validation_result.warnings:
                logger.warning(f"  - {warning}")
        
        if validation_result.info:
            for info in validation_result.info:
                logger.info(f"  {info}")
        
        return template_data, validation_result
    
    def _generate_html(
        self,
        template_path: Path,
        template_data: Dict[str, Any],
        analysis_results: Any,
        dataset: Any,
        weather_data: Any,
        output_filename: Optional[str]
    ) -> Dict[str, Any]:
        """Generate HTML report."""
        logger.info("Generating HTML report...")
        
        try:
            html_result = self.html_renderer.render_report(
                config_path=template_path,
                analysis_results=analysis_results,
                dataset=dataset,
                weather_data=weather_data,
                output_filename=output_filename
            )
            
            logger.info(f"  HTML generated: {html_result['output_path']}")
            logger.info(f"  File size: {html_result['file_size']} bytes")
            logger.info(f"  Charts: {html_result['charts_generated']}")
            
            return html_result
            
        except Exception as e:
            logger.error(f"HTML generation failed: {e}")
            return {
                'status': 'error',
                'error': f"HTML generation failed: {str(e)}"
            }
    
    def _generate_pdf(self, html_path: Path) -> Dict[str, Any]:
        """Generate PDF from HTML."""
        logger.info("Converting HTML to PDF...")
        
        try:
            pdf_path = html_path.with_suffix('.pdf')
            pdf_result = self.pdf_generator.html_to_pdf(html_path, pdf_path)
            
            if pdf_result['status'] == 'success':
                logger.info(f"  PDF generated: {pdf_result['output_path']}")
                logger.info(f"  File size: {pdf_result['file_size']} bytes")
                logger.info(f"  Backend: {pdf_result['backend']}")
                
                if 'pages' in pdf_result:
                    logger.info(f"  Pages: {pdf_result['pages']}")
            else:
                logger.error(f"  PDF generation failed: {pdf_result.get('message', 'Unknown error')}")
            
            return pdf_result
            
        except Exception as e:
            logger.error(f"PDF conversion failed: {e}")
            return {
                'status': 'error',
                'error': f"PDF conversion failed: {str(e)}",
                'backend': self.pdf_generator.backend
            }
    
    def list_available_templates(self) -> List[Dict[str, Any]]:
        """
        List all available report templates.
        
        Returns:
            List of template metadata dictionaries
        """
        templates = []
        
        for template_file in self.templates_dir.glob("*.yaml"):
            try:
                template_data = self.yaml_parser.parse_file(template_file)
                
                templates.append({
                    'template_id': template_data.get('template_id'),
                    'name': template_data.get('name'),
                    'description': template_data.get('description'),
                    'version': template_data.get('version', '1.0'),
                    'file': template_file.name,
                    'scope': template_data.get('report', {}).get('scope'),
                    'format': template_data.get('report', {}).get('format', 'html')
                })
            except Exception as e:
                logger.warning(f"Could not load template {template_file}: {e}")
                continue
        
        return templates
    
    def validate_template_file(self, template_name: str) -> ValidationResult:
        """
        Validate a template without generating a report.
        
        Args:
            template_name: Name of template to validate
            
        Returns:
            ValidationResult
        """
        template_path = self.templates_dir / f"{template_name}.yaml"
        _, validation_result = self._load_and_validate_template(template_path)
        return validation_result
    
    def get_template_requirements(self, template_name: str) -> Dict[str, Any]:
        """
        Get analytics requirements for a template.
        
        Args:
            template_name: Name of template
            
        Returns:
            Dictionary with analytics requirements
        """
        template_path = self.templates_dir / f"{template_name}.yaml"
        template_data = self.yaml_parser.parse_file(template_path)
        
        return self.yaml_parser.extract_analytics_requirements(template_data)
    
    def generate_batch_reports(
        self,
        template_names: List[str],
        analysis_results: Any,
        dataset: Any = None,
        weather_data: Any = None,
        output_format: str = 'html'
    ) -> Dict[str, Any]:
        """
        Generate multiple reports from different templates.
        
        Args:
            template_names: List of template names
            analysis_results: Analysis results
            dataset: Building dataset (optional)
            weather_data: Weather data (optional)
            output_format: Output format for all reports
            
        Returns:
            Dictionary with results for each template
        """
        results = {}
        
        for template_name in template_names:
            logger.info(f"\nGenerating report from template: {template_name}")
            
            result = self.generate_report(
                template_name=template_name,
                analysis_results=analysis_results,
                dataset=dataset,
                weather_data=weather_data,
                output_format=output_format
            )
            
            results[template_name] = result
        
        # Summary
        successful = sum(1 for r in results.values() if r['status'] == 'success')
        failed = len(results) - successful
        
        logger.info(f"\nBatch generation complete:")
        logger.info(f"  Successful: {successful}/{len(results)}")
        logger.info(f"  Failed: {failed}/{len(results)}")
        
        return {
            'status': 'complete',
            'total': len(results),
            'successful': successful,
            'failed': failed,
            'results': results
        }
