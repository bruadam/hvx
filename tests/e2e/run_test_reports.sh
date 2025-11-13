#!/bin/bash
# Quick script to run the report verification test

set -e

# Navigate to project root
cd "$(dirname "$0")/../.."

echo "🚀 Running IEQ Analytics Report Generation with Plot Verification Test"
echo "=================================================================="

# Set PYTHONPATH to include current directory
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Run the test
python tests/e2e/test_report_with_plot_verification.py

# Show output files
echo ""
echo "📁 Generated reports are located in:"
echo "   ./output/test_reports/report_*.html"
echo ""
echo "📊 Open any of these HTML files in a web browser to view the reports with interactive plots!"
