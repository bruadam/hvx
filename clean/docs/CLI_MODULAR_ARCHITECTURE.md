Move this file to docs/CLI_MODULAR_ARCHITECTURE.md


# CLI Modular Architecture - Complete Implementation

## Overview

The CLI has been **completely refactored** into a modular, use-case-driven architecture that follows clean architecture principles. Each workflow step is now a reusable component with automatic persistence and the ability to reload analysis at any stage.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Commands        │  │  Interactive     │                 │
│  │  - data          │  │  Workflows       │                 │
│  │  - analyze       │  │  - IEQ           │                 │
│  │  - report        │  │  - Energy (soon) │                 │
│  └────────┬─────────┘  └────────┬─────────┘                │
└───────────│─────────────────────│──────────────────────────┘
            │                     │
            ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Use Cases (Business Logic)                          │  │
│  │  - LoadDataUseCase                                   │  │
│  │  - RunAnalysisUseCase                                │  │
│  │  - SaveAnalysisUseCase                               │  │
│  │  - LoadAnalysisUseCase                               │  │
│  │  - GenerateReportUseCase                             │  │
│  │  - ExportResultsUseCase                              │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────│──────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│           Domain / Analytics / Infrastructure                │
└─────────────────────────────────────────────────────────────┘
```

## New Command Structure

### Multi-Type Analysis Support

```bash
# IEQ Analysis
hvx ieq start                    # Interactive IEQ workflow
hvx start                        # Default (IEQ)

# Energy Analysis (coming soon)
hvx energy start                 # Interactive Energy workflow
hvx start --type energy         # Energy via default command

# Modular Commands
hvx data load <dir>             # Load data only
hvx analyze run <dir>           # Run analysis only
hvx report generate             # Generate report only
hvx report export --format json # Export results only
```

## Use Cases (Application Layer)

### 1. LoadDataUseCase

**Purpose**: Load building data from directory structures

**Location**: `core/application/use_cases/load_data.py`

**Usage**:
```python
use_case = LoadDataUseCase()
dataset, buildings, levels, rooms = use_case.execute(
    data_directory=Path("data/building-a"),
    dataset_id="my_dataset",
    dataset_name="My Building Dataset"
)
```

**CLI Commands**:
```bash
hvx data load data/building-a
hvx data info data/building-a  # Quick info without full load
```

### 2. RunAnalysisUseCase

**Purpose**: Execute IEQ compliance analysis on rooms and buildings

**Location**: `core/application/use_cases/run_analysis.py`

**Methods**:
- `execute_room_analysis()` - Single room
- `execute_building_analysis()` - Aggregate building
- `execute_batch_analysis()` - Multiple rooms at once

**Usage**:
```python
use_case = RunAnalysisUseCase()

# Batch analysis
room_analyses = use_case.execute_batch_analysis(
    rooms=rooms_list,
    tests=test_configs,
    apply_filters=True
)

# Building aggregation
building_analysis = use_case.execute_building_analysis(
    building=building,
    room_analyses=room_analyses
)
```

**CLI Commands**:
```bash
hvx analyze run data/building-a
hvx analyze run data/building-a --save my_analysis.json
hvx analyze run data/building-a --session-name my_session
hvx analyze list  # List saved sessions
```

### 3. SaveAnalysisUseCase

**Purpose**: Persist analysis results to JSON with automatic session management

**Location**: `core/application/use_cases/save_analysis.py`

**Output Structure**:
```
output/analyses/
├── session_20241020_123456.json        # Session manifest
├── rooms/
│   └── 20241020_123456/
│       ├── room_1.json
│       ├── room_2.json
│       └── ...
└── buildings/
    └── building_a_20241020_123456.json
```

**Usage**:
```python
use_case = SaveAnalysisUseCase()

# Save batch with auto session name
saved_paths = use_case.execute_save_batch(
    room_analyses=room_analyses,
    building_analysis=building_analysis,
    session_name="my_session"  # Optional
)
```

**Features**:
- ✅ Automatic session management
- ✅ Room-level persistence
- ✅ Building-level persistence  
- ✅ Level-level persistence support (ready)
- ✅ Portfolio-level persistence support (ready)
- ✅ Session manifests for easy reload

### 4. LoadAnalysisUseCase

**Purpose**: Reload saved analysis results

**Location**: `core/application/use_cases/load_analysis.py`

**Usage**:
```python
use_case = LoadAnalysisUseCase()

# List available sessions
sessions = use_case.list_sessions()

# Load specific session
session_data = use_case.execute_load_session("my_session")
```

**CLI Commands**:
```bash
hvx analyze list                          # List sessions
hvx report generate --session my_session  # Use saved session
hvx report export --session my_session    # Export from session
```

### 5. GenerateReportUseCase

**Purpose**: Generate HTML/PDF reports from analysis results

**Location**: `core/application/use_cases/generate_report.py`

**Usage**:
```python
use_case = GenerateReportUseCase()

report_path = use_case.execute(
    rooms=rooms_list,
    building_name="My Building",
    output_path=None,  # Auto-generate path
    template_path=Path("config/templates/detailed.yaml"),  # Optional
    building_analysis=building_analysis  # Optional
)
```

**CLI Commands**:
```bash
hvx report generate                           # Basic report
hvx report generate --template detailed.yaml  # Template-based
hvx report generate --output custom.html      # Custom path
hvx report generate --session my_session      # From saved session
```

### 6. ExportResultsUseCase

**Purpose**: Export analysis to various formats

**Location**: `core/application/use_cases/export_results.py`

**Formats**:
- JSON - Complete analysis data
- CSV - Room-level summary
- Excel - Multi-sheet workbook

**Usage**:
```python
use_case = ExportResultsUseCase()

# JSON export
path = use_case.execute_export_json(
    room_analyses=room_analyses,
    building_analysis=building_analysis
)

# Excel with multiple sheets
path = use_case.execute_export_excel(
    room_analyses=room_analyses,
    building_analysis=building_analysis
)
```

**CLI Commands**:
```bash
hvx report export --format json
hvx report export --format csv
hvx report export --format excel --output results.xlsx
```

## Interactive Workflow

The interactive workflow (`hvx ieq start`) now uses all the use cases internally:

### Workflow Steps with Auto-Save

1. **Load Data** → Uses `LoadDataUseCase`
2. **Select Standards** → Loads YAML configs
3. **Configure Tests** → Prepares test configurations
4. **Run Analysis** → Uses `RunAnalysisUseCase`
   - **Auto-saves** analysis results to session
5. **Explore Results** → Interactive tables
6. **Generate Reports** → Uses `GenerateReportUseCase`
7. **Export Data** → Uses `ExportResultsUseCase`

### Auto-Persistence

Analysis results are **automatically saved** after Step 4 (Run Analysis):
```
✓ Step 4: Run Analysis complete
  Analysis saved to: output/analyses/session_20241020_123456.json
```

This enables:
- Resume from any point
- Generate multiple reports from same analysis
- Export to different formats later
- Share analysis results

## Command Examples

### Complete Workflow (Modular)

```bash
# 1. Load data
hvx data load data/building-a

# 2. Run analysis with auto-save
hvx analyze run data/building-a --session-name building_a_oct20

# 3. Generate report from saved session
hvx report generate --session building_a_oct20

# 4. Export in multiple formats
hvx report export --session building_a_oct20 --format json
hvx report export --session building_a_oct20 --format excel
```

### Interactive Workflow

```bash
# IEQ analysis (step-by-step with auto-save)
hvx ieq start

# Energy analysis (coming soon)
hvx energy start

# Default (IEQ)
hvx start
```

### Quick Analysis

```bash
# One command with auto mode
hvx analyze run data/building-a --session-name quick_analysis

# List what was saved
hvx analyze list
```

### Advanced Usage

```bash
# Chain commands with saved session
hvx analyze run data/building-a --session-name my_session && \
hvx report generate --session my_session --output report.html && \
hvx report export --session my_session --format excel
```

## File Organization

```
core/
├── application/              # NEW: Application layer
│   └── use_cases/           # Business logic use cases
│       ├── load_data.py
│       ├── run_analysis.py
│       ├── save_analysis.py
│       ├── load_analysis.py
│       ├── generate_report.py
│       └── export_results.py
│
├── cli/
│   ├── commands/            # Modular CLI commands
│   │   ├── data.py         # Data management
│   │   ├── analyze.py      # Analysis commands
│   │   └── report.py       # Reporting commands
│   │
│   ├── ui/
│   │   └── workflows/
│   │       └── ieq_interactive.py  # IEQ workflow
│   │
│   └── main.py             # Main CLI with multi-type support
│
└── ...
```

## Benefits

### 1. **Modularity**
- Each step is independent and reusable
- Commands can be used standalone or chained
- Easy to add new analysis types (energy, carbon)

### 2. **Persistence**
- Automatic session saving
- Resume from any point
- Generate multiple reports from one analysis
- Share results easily

### 3. **Clean Architecture**
- Business logic in application layer
- CLI is thin presentation layer
- Easy to test and maintain
- Clear separation of concerns

### 4. **Flexibility**
- Interactive or command-line
- Full workflow or individual steps
- Different analysis types (IEQ, energy)
- Multiple export formats

### 5. **Extensibility**
- Easy to add new commands
- Easy to add new analysis types
- Easy to add new export formats
- Easy to add new workflows

## Migration from Old CLI

### Old Way:
```bash
ieq start  # Everything in one monolithic workflow
```

### New Way (Options):

```bash
# Option 1: Still works! Interactive workflow
hvx ieq start

# Option 2: Modular approach
hvx data load data/building-a
hvx analyze run data/building-a --session-name my_session
hvx report generate --session my_session

# Option 3: Quick command
hvx analyze run data/building-a  # Auto-saves, can report later
```

## Future Extensions

### Energy Analysis (Planned)

```bash
hvx energy start                    # Interactive energy workflow
hvx energy analyze data/building-a  # Energy analysis
hvx energy report --session my_session
```

### Carbon Analysis (Planned)

```bash
hvx carbon start
hvx carbon analyze data/building-a
```

### Portfolio Analysis (Planned)

```bash
hvx portfolio analyze data/           # All buildings
hvx portfolio report --session portfolio_2024
```

## Summary

✅ **Modular** - Each step is a reusable use case  
✅ **Persistent** - Auto-save with session management  
✅ **Flexible** - Interactive or CLI, full or partial  
✅ **Extensible** - Easy to add new types (energy, carbon)  
✅ **Clean** - Proper separation of concerns  
✅ **Professional** - Production-ready architecture  

The CLI is now a **truly modular, enterprise-grade** interface to the IEQ Analytics system!

---

**Commands to Try**:
```bash
hvx --help
hvx ieq --help
hvx data --help
hvx analyze --help
hvx report --help

# Try the interactive workflow
hvx ieq start --directory data

# Or go modular
hvx analyze run data --session-name test
hvx analyze list
```
