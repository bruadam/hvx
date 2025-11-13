# New Reporting Features

This document describes the new features implemented in the IEQ Analytics reporting system.

## Overview

Three major features have been added to enhance the reporting capabilities:

1. **Room Looping (Individual Room Sections)**
2. **Building Statistics Section**
3. **Enhanced Graph Export in HTML**

---

## 1. Room Looping - Individual Room Sections

### Description
The `room_details` section type enables automatic generation of detailed analysis cards for each room in the building. Each room gets its own subsection with compliance metrics and parameter breakdowns.

### Usage

Add the following section to your report template YAML:

```yaml
sections:
  - type: "room_details"
    title: "Individual Room Analysis"
    description: "Detailed compliance metrics for each room"
```

### Features

Each room detail card includes:
- **Room name** as a prominent header
- **Key Performance Indicators (KPIs)**:
  - Compliance Rate (with color-coded grade)
  - Data Quality Score
  - Total Violations
- **Parameter-specific compliance table** showing:
  - Parameter name (Temperature, CO2, Humidity, etc.)
  - Compliance rate (color-coded by grade)
  - Violation count

### Visual Design
- Each room is displayed in a separate card with a distinct border
- Color-coded compliance grades (A: Green, B: Yellow, C: Orange, D/F: Red)
- Clean, professional styling with good spacing
- Responsive grid layout for KPIs

---

## 2. Building Statistics Section

### Description
The `building_statistics` section provides comprehensive building-level statistics including parameter-specific performance metrics, room summaries, and violation analytics.

### Usage

Add the following section to your report template YAML:

```yaml
sections:
  - type: "building_statistics"
    title: "Building Statistics"
    description: "Comprehensive statistics including parameter-specific performance metrics"
```

### Features

The building statistics section includes:

#### Overall Performance
- Overall Compliance Grade
- Average Compliance Rate
- Average Data Quality

#### Room Summary
- Total Rooms count
- Passing Rooms (≥95% compliance)
- Failing Rooms (<95% compliance)

#### Violations
- Total Violations across all rooms
- Average Violations per Room

#### Parameter-Specific Performance Table
Detailed breakdown showing for each parameter:
- Parameter name
- Average Compliance Rate (color-coded)
- Total Violations
- Number of Rooms Tested

### Visual Design
- Grid layout with organized categories
- Full-width table for parameter statistics
- Color-coded values for quick assessment
- Professional styling consistent with report theme

---

## 3. Enhanced Graph Export in HTML

### Description
All graphs are now properly exported and embedded directly in HTML reports as interactive Plotly charts.

### Features

- **Interactive Charts**: Charts are embedded using Plotly's JavaScript library
- **No External Files**: All chart data is embedded directly in the HTML
- **Responsive**: Charts automatically resize based on viewport
- **Hover Interactions**: Users can hover over data points for detailed information
- **Zoom and Pan**: Users can zoom and pan on charts
- **Export Capabilities**: Charts can be downloaded as PNG from the browser

### Supported Chart Types

All existing chart types are fully supported:
- Bar charts (room comparison, building comparison)
- Compliance matrix
- Compliance gauge
- Building KPI dashboard
- Portfolio overview
- Heatmaps (hourly/daily, daily/monthly, compliance)
- Timeseries (with compliance highlighting)
- Violation timelines

### Technical Details

Charts are rendered using:
- Plotly.js for interactive visualization
- `fig.to_html(include_plotlyjs=False)` for embedding
- Single Plotly.js CDN include in the HTML header
- Minimal overhead per chart (only data and configuration)

---

## Example Templates

Two example templates are provided that demonstrate these features:

### 1. `detailed_room_by_room_report.yaml`
A focused template emphasizing individual room analysis:
- Building statistics overview
- Room comparison charts
- **Individual room details** for each room
- Recommendations

### 2. `comprehensive_building_report.yaml` (Updated)
The comprehensive template now includes:
- Building performance overview
- **Building statistics section** (NEW)
- Multiple visualization charts
- Compliance matrix
- Detailed room metrics table
- **Individual room analysis** (NEW)
- Recommendations

---

## Testing

### Test Script
A test script `test_new_features.py` is provided in the project root to verify the implementation.

### Running the Test

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the test
PYTHONPATH=. python test_new_features.py
```

### Expected Output
The test will:
1. Load sample room data
2. Generate reports using the new template
3. Display statistics about the generated report including:
   - Number of sections
   - Number of charts
   - Number of room detail cards

### Verification
Open the generated HTML report in a browser to verify:
- ✓ Building statistics section displays correctly
- ✓ Individual room cards are generated for each room
- ✓ Interactive charts render and are functional
- ✓ All data is properly formatted and color-coded

---

## Integration

### Adding to Existing Templates

To add these features to existing templates, simply add the appropriate section configurations:

```yaml
sections:
  # ... existing sections ...

  # Add building statistics
  - type: "building_statistics"
    title: "Building Statistics"
    description: "Comprehensive building-level metrics"

  # Add individual room details
  - type: "room_details"
    title: "Individual Room Analysis"
    description: "Detailed analysis for each room"

  # ... more sections ...
```

### Room Filtering

Room details respect the `room_filter` configuration in the template:

```yaml
room_filter:
  mode: "all"  # or "failing", "top_n", "bottom_n"
  sort_by: "compliance"  # or "quality", "violations", "name"
  ascending: false
  compliance_threshold: 95.0
  n: 10  # for top_n or bottom_n modes
```

---

## CSS Styling

Custom CSS classes have been added for the new sections:

### Room Details
- `.room-details-section` - Container for room details
- `.room-detail-card` - Individual room card
- `.room-name` - Room name header
- `.room-kpi-grid` - KPI grid layout
- `.room-kpi-item` - Individual KPI display
- `.room-compliance-table` - Compliance details table

### Building Statistics
- `.building-statistics-section` - Container for statistics
- `.statistics-grid` - Grid layout for stat categories
- `.stat-category` - Category container
- `.stat-item` - Individual statistic
- `.parameter-stats-table` - Parameter performance table

All CSS is embedded in the HTML and follows the professional theme.

---

## Performance Considerations

- **Room Details**: Generation time scales linearly with the number of rooms
- **Charts**: Interactive charts are efficient and load quickly
- **File Size**: HTML reports with embedded charts are typically 50-100 KB
- **Browser Compatibility**: Tested on modern browsers (Chrome, Firefox, Safari, Edge)

---

## Future Enhancements

Potential future improvements:
- Room-specific charts within each room detail card
- Collapsible room sections for better navigation
- Export individual room details to separate PDFs
- Comparison mode to highlight differences between rooms
- Trend analysis showing changes over time

---

## Support

For issues or questions:
- Check the generated HTML for error messages
- Verify template YAML syntax is correct
- Ensure all required data is available for rooms
- Review the test script for usage examples

---

**Document Version**: 1.0
**Date**: October 20, 2025
**Implementation Status**: Complete and Tested
