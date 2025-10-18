"""
PDF Generator

Converts HTML reports to PDF using weasyprint or pdfkit.
Falls back to reportlab if HTML-to-PDF libraries are not available.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import sys
import logging


logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generates PDF from HTML reports."""

    def __init__(self):
        """Initialize PDF generator with available backend."""
        self.backend = self._detect_backend()

    def _detect_backend(self) -> str:
        """Detect which PDF generation backend is available."""
        # Try weasyprint first (best for HTML/CSS rendering)
        try:
            import weasyprint
            return 'weasyprint'
        except (ImportError, OSError) as e:
            # OS error happens when weasyprint dependencies are missing
            pass

        # Try pdfkit (requires wkhtmltopdf)
        try:
            import pdfkit
            return 'pdfkit'
        except (ImportError, OSError):
            pass

        # Fallback to reportlab (basic PDF generation)
        try:
            import reportlab
            return 'reportlab'
        except (ImportError, OSError):
            return 'none'

    def html_to_pdf(
        self,
        html_path: Path,
        pdf_path: Optional[Path] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert HTML file to PDF.

        Args:
            html_path: Path to HTML file
            pdf_path: Output PDF path (optional)
            options: Additional options for PDF generation

        Returns:
            Dictionary with conversion results
        """
        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path}")

        # Set default output path
        if pdf_path is None:
            pdf_path = html_path.with_suffix('.pdf')

        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        # Use appropriate backend
        if self.backend == 'weasyprint':
            return self._convert_with_weasyprint(html_path, pdf_path, options)
        elif self.backend == 'pdfkit':
            return self._convert_with_pdfkit(html_path, pdf_path, options)
        elif self.backend == 'reportlab':
            return self._convert_with_reportlab(html_path, pdf_path, options)
        else:
            return {
                'status': 'error',
                'message': 'No PDF generation backend available. Install weasyprint or pdfkit.',
                'backend': 'none'
            }

    def _convert_with_weasyprint(
        self,
        html_path: Path,
        pdf_path: Path,
        options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Convert using weasyprint (best quality)."""
        try:
            import weasyprint
            from weasyprint import CSS

            # Default options for better PDF quality
            default_options = {
                'presentational_hints': True,
                'optimize_size': ('fonts',),
            }
            
            if options:
                default_options.update(options)

            # Additional CSS for better PDF rendering
            pdf_css = CSS(string='''
                @page {
                    size: A4;
                    margin: 2cm;
                    
                    @top-center {
                        content: "IEQ Analysis Report";
                        font-size: 10pt;
                        color: #666;
                    }
                    
                    @bottom-right {
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 9pt;
                        color: #666;
                    }
                }
                
                /* Ensure charts and images don't break across pages */
                .chart-container, .room-card, .compliance-card {
                    page-break-inside: avoid;
                }
                
                /* Better table rendering in PDF */
                table {
                    page-break-inside: auto;
                }
                
                tr {
                    page-break-inside: avoid;
                    page-break-after: auto;
                }
                
                /* Ensure section headings stay with content */
                h1, h2, h3, h4 {
                    page-break-after: avoid;
                }
            ''')

            # Generate PDF with enhanced options
            html = weasyprint.HTML(filename=str(html_path))
            html.write_pdf(
                str(pdf_path),
                stylesheets=[pdf_css],
                **default_options
            )

            return {
                'status': 'success',
                'output_path': str(pdf_path),
                'backend': 'weasyprint',
                'file_size': pdf_path.stat().st_size,
                'pages': self._count_pdf_pages(pdf_path)
            }
        except Exception as e:
            logger.error(f"Weasyprint conversion error: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'backend': 'weasyprint'
            }
    
    def _count_pdf_pages(self, pdf_path: Path) -> Optional[int]:
        """Count pages in generated PDF."""
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                return len(pdf_reader.pages)
        except:
            return None

    def _convert_with_pdfkit(
        self,
        html_path: Path,
        pdf_path: Path,
        options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Convert using pdfkit (requires wkhtmltopdf)."""
        try:
            import pdfkit

            # Default options
            pdf_options = {
                'page-size': 'A4',
                'encoding': 'UTF-8',
                'enable-local-file-access': None
            }

            if options:
                pdf_options.update(options)

            # Generate PDF
            pdfkit.from_file(str(html_path), str(pdf_path), options=pdf_options)

            return {
                'status': 'success',
                'output_path': str(pdf_path),
                'backend': 'pdfkit',
                'file_size': pdf_path.stat().st_size
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'backend': 'pdfkit'
            }

    def _convert_with_reportlab(
        self,
        html_path: Path,
        pdf_path: Path,
        options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fallback: Simple PDF generation with reportlab.
        Note: This doesn't render full HTML/CSS, just extracts text.
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet

            # Read HTML
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Strip HTML tags (very basic)
            import re
            text = re.sub('<[^<]+?>', '', html_content)

            # Create PDF
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # Add content
            for line in text.split('\n'):
                line = line.strip()
                if line:
                    story.append(Paragraph(line, styles['Normal']))
                    story.append(Spacer(1, 0.2))

            doc.build(story)

            return {
                'status': 'success',
                'output_path': str(pdf_path),
                'backend': 'reportlab',
                'warning': 'Basic PDF generated. Install weasyprint for better HTML rendering.',
                'file_size': pdf_path.stat().st_size
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'backend': 'reportlab'
            }

    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about available PDF generation backend."""
        backends = {
            'weasyprint': {
                'available': False,
                'quality': 'excellent',
                'description': 'Best HTML/CSS rendering, supports modern CSS features'
            },
            'pdfkit': {
                'available': False,
                'quality': 'good',
                'description': 'Good rendering, requires wkhtmltopdf binary'
            },
            'reportlab': {
                'available': False,
                'quality': 'basic',
                'description': 'Basic PDF generation, limited HTML/CSS support'
            }
        }

        # Check which backends are available
        try:
            import weasyprint
            backends['weasyprint']['available'] = True
        except (ImportError, OSError):
            pass

        try:
            import pdfkit
            backends['pdfkit']['available'] = True
        except (ImportError, OSError):
            pass

        try:
            import reportlab
            backends['reportlab']['available'] = True
        except (ImportError, OSError):
            pass

        return {
            'current_backend': self.backend,
            'backends': backends,
            'recommendation': 'Install weasyprint for best results: pip install weasyprint'
        }
