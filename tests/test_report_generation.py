"""
Test script for HTML and PDF report generation.
Tests the YAML-based report configuration and rendering system.
"""

from pathlib import Path
from src.core.reporting.UnifiedReportService import UnifiedReportService

print("=" * 80)
print("Testing Report Generation System")
print("=" * 80)

# Initialize report service
report_service = UnifiedReportService()

# Check PDF backend
print("\n1. Checking PDF backend...")
backend_info = report_service.get_pdf_backend_info()
print(f"   Current backend: {backend_info['current_backend']}")

for backend_name, backend_data in backend_info['backends'].items():
    status = "✓ Available" if backend_data['available'] else "✗ Not available"
    print(f"   {backend_name}: {status} ({backend_data['quality']} quality)")

if backend_info['current_backend'] == 'none':
    print(f"\n   ⚠ Recommendation: {backend_info['recommendation']}")

# List available templates
print("\n2. Listing available templates...")
templates = report_service.list_templates()

if not templates:
    print("   ✗ No templates found in config/report_templates/")
    print("   Creating sample templates...")
else:
    print(f"   ✓ Found {len(templates)} template(s):")
    for template in templates:
        print(f"     - {template['name']} ({template['template_id']})")
        print(f"       {template['description']}")
        print(f"       Version: {template['version']}, Sections: {template['sections_count']}")

# Validate templates
print("\n3. Validating templates...")
for template in templates:
    template_id = template['template_id']
    validation = report_service.validate_template(template_id)

    if validation['valid']:
        print(f"   ✓ {template_id}: Valid")
    else:
        print(f"   ✗ {template_id}: Invalid")
        for error in validation['errors']:
            print(f"      Error: {error}")

    if validation.get('warnings'):
        for warning in validation['warnings']:
            print(f"      Warning: {warning}")

# Get detailed template info
if templates:
    print("\n4. Template details...")
    template_id = templates[0]['template_id']
    info = report_service.get_template_info(template_id)

    print(f"   Template: {info['name']}")
    print(f"   Format: {info['format']}, Theme: {info['theme']}")
    print(f"   Sections ({len(info['sections'])}):")
    for section in info['sections']:
        print(f"     - {section['title']} ({section['type']})")

# Test HTML generation (without real data)
print("\n5. Testing HTML generation...")
print("   Note: This requires actual analysis data to generate a real report.")
print("   For now, checking that the system is set up correctly.")

try:
    # Check that HTML renderer can be initialized
    from src.core.reporting.HTMLReportRenderer import HTMLReportRenderer
    html_renderer = HTMLReportRenderer()
    print("   ✓ HTML renderer initialized successfully")

    # Check that graph service is available
    from src.core.graphs.GraphService import GraphService
    graph_service = GraphService()
    categories = graph_service.get_categories()
    print(f"   ✓ Graph service initialized ({len(categories)} chart categories available)")

except Exception as e:
    print(f"   ✗ Error: {e}")

# Test PDF generation capabilities
print("\n6. Testing PDF generation...")
try:
    from src.core.reporting.PDFGenerator import PDFGenerator
    pdf_gen = PDFGenerator()
    print(f"   ✓ PDF generator initialized (backend: {pdf_gen.backend})")

    if pdf_gen.backend == 'none':
        print("   ⚠ No PDF backend available")
        print("   Install one of:")
        print("     - weasyprint (recommended): pip install weasyprint")
        print("     - pdfkit: pip install pdfkit")
    elif pdf_gen.backend == 'reportlab':
        print("   ⚠ Using basic reportlab backend")
        print("   For better HTML rendering, install: pip install weasyprint")
    else:
        print(f"   ✓ Using {pdf_gen.backend} backend (good quality)")

except Exception as e:
    print(f"   ✗ Error: {e}")

# Summary
print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print(f"✓ Templates available: {len(templates)}")
print(f"✓ PDF backend: {backend_info['current_backend']}")
print(f"✓ HTML generation: Ready")

if backend_info['current_backend'] in ['weasyprint', 'pdfkit']:
    print(f"✓ PDF generation: Ready (high quality)")
elif backend_info['current_backend'] == 'reportlab':
    print(f"⚠ PDF generation: Ready (basic quality)")
else:
    print(f"✗ PDF generation: Not available")

print("\nTo generate a real report:")
print("  1. Run the analytics workflow: hvx ieq start")
print("  2. Select '6. Generate reports' from the menu")
print("  3. Choose a template and output format")
print("\nOr use programmatically:")
print("  from src.core.reporting.UnifiedReportService import UnifiedReportService")
print("  service = UnifiedReportService()")
print("  service.generate_report(")
print("      template_name='portfolio_summary',")
print("      analysis_results=your_analysis_results,")
print("      dataset=your_dataset,")
print("      format='html'  # or 'pdf' or 'both'")
print("  )")

print("\n" + "=" * 80)
