#!/bin/bash

# HTK Report Generator with WeasyPrint Support
# This script sets up the correct environment for PDF generation on macOS

# Set library path for WeasyPrint
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH

# Change to the analytics directory
cd "$(dirname "$0")"

echo "🏢 HTK Report Generator"
echo "📚 Setting up environment for PDF generation..."

# Check if required dependencies are available
if ! command -v brew &> /dev/null; then
    echo "⚠️  Homebrew not found. Install from https://brew.sh/"
    exit 1
fi

# Install required system dependencies if not present
echo "🔧 Checking system dependencies..."
brew list pango gdk-pixbuf libffi cairo gobject-introspection glib &> /dev/null || {
    echo "📦 Installing required dependencies..."
    brew install pango gdk-pixbuf libffi cairo gobject-introspection glib
}

# Test WeasyPrint
echo "🧪 Testing WeasyPrint..."
if python -c "import weasyprint; print('✅ WeasyPrint version:', weasyprint.__version__)" 2>/dev/null; then
    echo "🎉 WeasyPrint is working correctly!"
else
    echo "❌ WeasyPrint test failed"
    exit 1
fi

# Default parameters
DATA_DIR="output/mapped_data"
OUTPUT_DIR="output/reports/htk_$(date +%Y%m%d_%H%M%S)"
FORMAT="pdf"
BUILDINGS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --buildings)
            BUILDINGS="$BUILDINGS --buildings $2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --data-dir PATH      Directory containing analyzed data (default: output/mapped_data)"
            echo "  --output-dir PATH    Report output directory (default: output/reports/htk_TIMESTAMP)"
            echo "  --format FORMAT      Export format: html or pdf (default: pdf)"
            echo "  --buildings NAME     Specific buildings to include (can be used multiple times)"
            echo "  --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                           # Generate PDF report with all buildings"
            echo "  $0 --format html                            # Generate HTML report"
            echo "  $0 --buildings 'ole_rømer_skolen'           # Generate report for specific building"
            echo "  $0 --output-dir custom_output --format pdf  # Custom output directory"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo ""
echo "📊 Generating HTK Report..."
echo "📂 Data directory: $DATA_DIR"
echo "📤 Output directory: $OUTPUT_DIR"
echo "📄 Format: $FORMAT"
if [[ -n "$BUILDINGS" ]]; then
    echo "🏗️ Buildings: $BUILDINGS"
else
    echo "🏗️ Buildings: All"
fi
echo ""

# Run the HTK report generation
python -m cli report htk --data-dir "$DATA_DIR" --output-dir "$OUTPUT_DIR" --format "$FORMAT" $BUILDINGS

# Check if the report was generated successfully
if [[ $? -eq 0 ]]; then
    echo ""
    echo "🎉 HTK Report generated successfully!"
    echo "📁 Report location: $OUTPUT_DIR"
    
    # Try to open the report
    if [[ "$FORMAT" == "pdf" ]] && [[ -f "$OUTPUT_DIR/htk_report.pdf" ]]; then
        echo "📖 Opening PDF report..."
        open "$OUTPUT_DIR/htk_report.pdf" 2>/dev/null || echo "💡 Open the PDF manually: $OUTPUT_DIR/htk_report.pdf"
    elif [[ -f "$OUTPUT_DIR/htk_report.html" ]]; then
        echo "🌐 Opening HTML report..."
        open "$OUTPUT_DIR/htk_report.html" 2>/dev/null || echo "💡 Open the HTML manually: $OUTPUT_DIR/htk_report.html"
    fi
else
    echo "❌ Report generation failed"
    exit 1
fi
