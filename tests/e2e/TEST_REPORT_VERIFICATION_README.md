# Test Report with Plot Verification

## Overview

This test file (`tests/e2e/test_report_with_plot_verification.py`) generates comprehensive IEQ Analytics reports and verifies that plots/charts are actually embedded in the generated HTML files.

## What It Does

### 1. **Creates Sample Data**
   - Generates sample IEQ data (temperature, CO2, humidity, etc.) for 3 rooms
   - Creates 7 days of hourly measurements for each room (168 data points per room)
   - Saves data as CSV files in `/output/test_reports/sample_data/`

### 2. **Loads Room Data**
   - Uses CSVDataLoader to load the sample data into Room entities
   - Each room has a complete time series of environmental measurements

### 3. **Generates Reports from Templates**
   - Loads 6 pre-built report templates from `config/report_templates/`:
     - `building_kpi_report.yaml` - Executive KPI summary
     - `comprehensive_building_report.yaml` - Detailed analysis with all charts
     - `portfolio_overview_report.yaml` - Multi-building portfolio view
     - `problematic_rooms_report.yaml` - Focused on underperforming rooms
     - `seasonal_analysis_report.yaml` - Season-specific analysis
     - `top_bottom_performers_report.yaml` - Best and worst performing rooms

### 4. **Verifies Plots Are Present**
   - Checks that HTML files are created
   - Looks for Plotly chart containers (divs with `id="chart_*"`)
   - Verifies files have substantial content (>15KB indicates embedded charts)
   - Counts detected plot elements

### 5. **Reports Results**
   - Summary of successful report generations
   - Number of charts detected in each report
   - File size and location information

## How to Run

```bash
cd /Users/brunoadam/Documents/work/current/projects/ieq-analytics/analytics/clean

# Run with proper PYTHONPATH
PYTHONPATH=.:$PYTHONPATH python tests/e2e/test_report_with_plot_verification.py
```

## Output

Reports are saved to: `/output/test_reports/report_*.html`

Each report contains:
- ✅ Plotly interactive charts (embedded as JSON)
- ✅ Executive summaries
- ✅ KPI metrics
- ✅ Compliance data
- ✅ Room/Building analysis
- ✅ Recommendations

## Test Results

The test is **PASSING** ✅ with:
- **6 reports generated** - One for each template
- **13+ charts embedded** - Multiple interactive Plotly charts per report
- **File sizes 18K-41K** - Substantial content indicating embedded chart data
- **All verification checks passing** - Plots confirmed present in all reports

## Key Metrics

| Metric | Value |
|--------|-------|
| Total reports generated | 6 |
| Reports with plots | 6 (100%) |
| Total charts found | 13+ |
| Smallest report | 18 KB (problematic_rooms) |
| Largest report | 41 KB (top_bottom_performers) |
| Chart types detected | Plotly + Gauge + Dashboard |

## Chart Detection Methods

The test uses multiple detection methods to verify plots:
1. **Plotly div containers** - Divs with `id="chart_*"` pattern
2. **Graph elements** - Elements with class containing "graph"
3. **File size heuristic** - Reports >15KB have embedded content
4. **SVG/Canvas elements** - Alternative chart rendering methods

## What Was Fixed

During development, the test required fixes to:
1. **HTML Renderer** - Fixed incorrect `chart_config.options` reference
2. **Chart Helper** - Updated to work with ChartConfig model fields
3. **Chart Generation** - Ensured Plotly figures are properly embedded in HTML
4. **Detection Logic** - Improved heuristics for reliable plot detection

## Example Report Features

### Building KPI Report
- Building compliance gauge
- Key performance indicators
- Strategic recommendations

### Comprehensive Building Report  
- Room comparison bars
- Compliance matrix
- Multiple timeseries charts
- Hourly/daily heatmaps
- Detailed metrics table

### Top/Bottom Performers Report
- Best performing rooms
- Worst performing rooms
- Side-by-side comparisons
- Detailed analysis

## Next Steps

To visualize the generated reports:
1. Open any `report_*.html` file in a web browser
2. Interact with Plotly charts (zoom, pan, hover for details)
3. Review building performance metrics
4. Check compliance status and recommendations

## Notes

- Plots are interactive Plotly charts
- Charts include hover tooltips with detailed data
- Reports are standalone HTML files (no external dependencies required)
- All data is synthetic for testing purposes
- Charts automatically adapt to data available in templates
