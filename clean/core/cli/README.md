# CLI Implementation Guide

## Overview

This document provides a comprehensive guide for implementing the interactive CLI for the clean architecture. The CLI follows the previous HVX CLI structure but is adapted for the clean architecture's domain-driven design.

## Architecture

### Directory Structure

```
core/cli/
├── README.md                 # This file - implementation guide
├── __init__.py              # CLI entry points
├── main.py                  # Main CLI application
├── commands/                # Command modules
│   ├── __init__.py
│   ├── analyze.py          # Analysis commands
│   ├── report.py           # Report generation commands
│   └── start.py            # Interactive workflow command
├── ui/                      # User interface components
│   ├── __init__.py
│   ├── components/         # Reusable UI components
│   │   ├── __init__.py
│   │   ├── progress.py    # Progress indicators
│   │   ├── tables.py      # Data table formatters
│   │   └── panels.py      # Panel displays
│   └── workflows/          # Interactive workflows
│       ├── __init__.py
│       └── interactive_start.py  # Main interactive workflow
└── utils/                   # CLI utilities
    ├── __init__.py
    ├── validators.py       # Input validators
    └── formatters.py       # Output formatters
```

## Implementation Tasks

### Phase 1: Core CLI Structure (Priority: HIGH)

#### Task 1.1: Main CLI Entry Point
**File**: `core/cli/main.py`

Create the main Click application with command groups:

```python
import click
from rich.console import Console

@click.group()
@click.version_option()
@click.pass_context
def cli(ctx):
    """IEQ Analytics - Indoor Environmental Quality Analysis Tool"""
    ctx.ensure_object(dict)
    ctx.obj['console'] = Console()

@cli.group()
def analyze():
    """Run IEQ analysis on building data"""
    pass

@cli.group()
def report():
    """Generate IEQ reports"""
    pass

if __name__ == '__main__':
    cli()
```

**Dependencies**: click, rich

**Estimated Time**: 30 minutes

#### Task 1.2: Setup Entry Point
**File**: `pyproject.toml` (update)

Add console script entry point:

```toml
[project.scripts]
ieq = "core.cli.main:cli"
```

**Estimated Time**: 10 minutes

### Phase 2: Interactive Workflow (Priority: HIGH)

#### Task 2.1: Interactive Start Command
**File**: `core/cli/commands/start.py`

Implement the main interactive workflow command:

```python
@click.command()
@click.option('--directory', '-d', type=click.Path(exists=True),
              help='Path to data directory')
@click.option('--auto', is_flag=True, help='Run in auto mode')
@click.pass_context
def start(ctx, directory, auto):
    """Start interactive IEQ analysis workflow"""
    from core.cli.ui.workflows.interactive_start import InteractiveWorkflow

    workflow = InteractiveWorkflow(auto_mode=auto)
    if directory:
        workflow.data_directory = Path(directory)
    workflow.run()
```

**Estimated Time**: 1 hour

#### Task 2.2: Interactive Workflow Orchestrator
**File**: `core/cli/ui/workflows/interactive_start.py`

Create the interactive workflow orchestrator with these steps:

1. **Load Data** - Prompt for and load building data from CSV/Excel
2. **Select Standards** - Choose compliance standards (EN16798-1, Danish, custom)
3. **Configure Tests** - Select which tests to run
4. **Run Analysis** - Execute analysis engine
5. **Explore Results** - Interactive result viewing with filters
6. **Generate Reports** - Select template and generate HTML/PDF
7. **Export Data** - Save analysis results

**Key Features**:
- Step-by-step progress tracking
- Collapsible completed steps
- Help system (type '?' for help)
- Exit anytime (type 'quit')
- Auto mode support (skip prompts, use defaults)

**Estimated Time**: 6-8 hours

### Phase 3: UI Components (Priority: MEDIUM)

#### Task 3.1: Progress Indicators
**File**: `core/cli/ui/components/progress.py`

Create reusable progress components:
- Step indicator with checkmarks
- Loading spinners
- Progress bars

**Estimated Time**: 2 hours

#### Task 3.2: Data Tables
**File**: `core/cli/ui/components/tables.py`

Create table formatters for:
- Room analysis results
- Building summaries
- Compliance test results
- Available reports/templates

**Estimated Time**: 2 hours

#### Task 3.3: Panel Displays
**File**: `core/cli/ui/components/panels.py`

Create panel components for:
- Welcome screen
- Step headers
- Error messages
- Completion summaries

**Estimated Time**: 1 hour

### Phase 4: Analysis Commands (Priority: MEDIUM)

#### Task 4.1: Analyze Command
**File**: `core/cli/commands/analyze.py`

Implement analysis subcommands:

```bash
ieq analyze run <data-dir> --standard en16798-1 --class II
ieq analyze results <analysis-id>
ieq analyze list
```

**Estimated Time**: 3 hours

#### Task 4.2: Report Command
**File**: `core/cli/commands/report.py`

Implement report subcommands:

```bash
ieq report generate --template building_detailed --output report.html
ieq report list-templates
ieq report list
```

**Estimated Time**: 2 hours

### Phase 5: Utilities (Priority: LOW)

#### Task 5.1: Validators
**File**: `core/cli/utils/validators.py`

Input validation utilities:
- Path validation
- Standard name validation
- Building class validation
- Numeric range validation

**Estimated Time**: 1 hour

#### Task 5.2: Formatters
**File**: `core/cli/utils/formatters.py`

Output formatting utilities:
- Number formatting (compliance rates, etc.)
- Date/time formatting
- Color coding (red/yellow/green based on compliance)

**Estimated Time**: 1 hour

## Workflow Steps Detail

### Step 1: Load Data

**Goal**: Load building data from directory structure

**User Interactions**:
1. Prompt for data directory path
2. Auto-detect structure (hierarchical/flat/single-file)
3. Parse CSV/Excel files
4. Show data summary (buildings, rooms, parameters, date range)

**Integration Points**:
- `core.infrastructure.data_loaders.csv_loader.CSVDataLoader`
- `core.domain.models.room.Room`
- `core.domain.models.building.Building`

### Step 2: Select Standards

**Goal**: Choose which compliance standards to apply

**User Interactions**:
1. Show available standards (EN16798-1, Danish Guidelines, Custom)
2. Multi-select standards
3. For EN16798-1, select building class (I, II, III, IV)
4. Show selected standards summary

**Integration Points**:
- `config/standards/en16798-1/*.yaml`
- `config/standards/danish-guidelines/*.yaml`
- Load YAML configs

### Step 3: Configure Tests

**Goal**: Select specific tests to run

**User Interactions**:
1. Show available tests for selected standards
2. Group by parameter (temperature, CO2, humidity)
3. Multi-select tests
4. Configure filters (opening hours, periods)
5. Show test configuration summary

**Integration Points**:
- `config/filters/*.yaml`
- `config/periods/*.yaml`
- Test configuration builder

### Step 4: Run Analysis

**Goal**: Execute analysis engine with configuration

**User Interactions**:
1. Show progress indicator
2. Real-time status updates (processing room X of Y)
3. Display summary when complete

**Integration Points**:
- `core.analytics.engine.analysis_engine.AnalysisEngine`
- `core.analytics.aggregators.building_aggregator.BuildingAggregator`
- `core.domain.models.room_analysis.RoomAnalysis`

### Step 5: Explore Results

**Goal**: Interactively view and filter analysis results

**User Interactions**:
1. Show overall compliance rate and grade
2. Menu options:
   - View all rooms
   - Filter failing rooms
   - View specific room details
   - View building summary
   - Sort by compliance/quality
3. Navigate back to menu or proceed

**Integration Points**:
- `core.domain.models.room_analysis.RoomAnalysis`
- `core.domain.models.building_analysis.BuildingAnalysis`
- Table formatters

### Step 6: Generate Reports

**Goal**: Create HTML/PDF reports from analysis

**User Interactions**:
1. List available templates
2. Select template or create custom
3. Choose output format (HTML/PDF)
4. Configure report options
5. Generate and show output path

**Integration Points**:
- `core.reporting.report_generator.ReportGenerator`
- `core.reporting.template_engine`
- `config/report_templates/*.yaml`

### Step 7: Export Data

**Goal**: Save analysis results to file

**User Interactions**:
1. Choose export format (JSON/CSV/Excel)
2. Select what to export (all rooms, building summary, specific tests)
3. Specify output path
4. Confirm export success

**Integration Points**:
- JSON serialization
- CSV/Excel exporters
- File system operations

## Key Design Principles

### 1. Progressive Disclosure
- Start simple, reveal complexity as needed
- Collapsible step summaries
- "Show more" options for detailed info

### 2. Error Recovery
- Validate inputs immediately
- Clear error messages
- Suggest corrections
- Allow retry without restarting

### 3. Keyboard-Friendly
- Arrow keys for navigation
- Tab completion where possible
- Sensible defaults
- Quick exit (Ctrl+C handled gracefully)

### 4. Visual Hierarchy
- Use Rich library for formatting
- Color coding (cyan for prompts, green for success, red for errors)
- Panels and tables for structure
- Progress indicators for long operations

### 5. Help System
- Type '?' at any prompt for context help
- Type 'help' for general help
- Show examples in help text
- Link to full documentation

## Dependencies

Required packages (add to `requirements.txt`):

```
click>=8.1.0          # CLI framework
rich>=13.0.0          # Terminal formatting
questionary>=2.0.0    # Interactive prompts (optional, alternative to click)
pyyaml>=6.0           # Config loading
```

## Testing Strategy

### Unit Tests
- Test each command independently
- Mock user inputs
- Verify outputs

### Integration Tests
- Test complete workflow end-to-end
- Use sample data
- Verify reports generated

### Manual Testing Checklist
- [ ] Can start interactive workflow
- [ ] Can load data from directory
- [ ] Can select standards
- [ ] Can configure tests
- [ ] Can run analysis
- [ ] Can explore results
- [ ] Can generate reports
- [ ] Can export data
- [ ] Error handling works
- [ ] Help system accessible
- [ ] Auto mode works
- [ ] Can exit gracefully

## Example Usage Flows

### Beginner Flow (Interactive)
```bash
$ ieq start

Welcome to IEQ Analytics!

Step 1: Load Building Data
> Enter data directory: data/my-building
✓ Loaded 15 rooms from Building A

Step 2: Select Standards
> Choose standards: EN16798-1 (Class II)
✓ Selected EN16798-1 Category II

Step 3: Configure Tests
> Select tests: [Temperature, CO2, Humidity]
✓ Configured 6 tests

Step 4: Run Analysis
Running analysis... ━━━━━━━━━━━━━━━━ 100%
✓ Analysis complete: 93.5% compliance

Step 5: Explore Results
[Menu] View all rooms / Filter failing / Details / Summary
> 1

[Table showing all rooms...]

Step 6: Generate Report
> Select template: Building Detailed Report
✓ Report saved to output/reports/building_report_2024-10-20.html

Step 7: Export Data
> Export format: JSON
✓ Data exported to output/analysis_2024-10-20.json

✓ Workflow complete!
```

### Advanced Flow (Non-Interactive)
```bash
$ ieq analyze run data/building-a \
    --standard en16798-1 \
    --class II \
    --output output/analysis.json

$ ieq report generate \
    --template building_detailed \
    --analysis output/analysis.json \
    --output report.html
```

## Migration Notes

### From Old CLI to Clean CLI

**Old Structure** (src/cli):
- Used legacy service layer
- Tightly coupled to old domain models
- Mixed concerns (UI + business logic)

**New Structure** (clean/core/cli):
- Uses clean architecture components
- Domain-driven design
- Separated UI from business logic
- Repository pattern for data access

**Key Changes**:
1. Replace `HierarchicalAnalysisService` → `AnalysisEngine`
2. Replace `BuildingDataset` → `Room` and `Building` domain entities
3. Replace `ReportService` → `ReportGenerator`
4. Use repositories for data loading instead of direct file access
5. Use value objects for compliance results

## Next Steps

1. **Set up basic CLI structure** (Phase 1)
2. **Implement start command skeleton** (Phase 2, Task 2.1)
3. **Create workflow orchestrator** (Phase 2, Task 2.2)
4. **Add UI components** (Phase 3)
5. **Implement analysis commands** (Phase 4)
6. **Add utilities** (Phase 5)
7. **Test and refine**

## Resources

- [Click Documentation](https://click.palletsprojects.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- Previous CLI implementation: `../src/cli/ui/workflows/ieq_start_interactive.py`
- Clean architecture docs: `../ARCHITECTURE.md`

## Questions & Decisions

### Question 1: Command Name
- Option A: `ieq` (short, memorable)
- Option B: `ieq-analytics` (descriptive)
- **Decision**: Use `ieq` for brevity

### Question 2: Auto Mode Behavior
- Skip all prompts and use defaults
- Required for CI/CD pipelines
- **Implementation**: `--auto` flag on `start` command

### Question 3: Data Loading
- Support multiple file formats (CSV, Excel, Parquet)
- Auto-detect structure
- **Implementation**: Use data loaders from infrastructure layer

### Question 4: Report Output
- Support HTML and PDF
- PDF requires additional dependencies (weasyprint)
- **Implementation**: HTML by default, PDF optional with warning if not installed
