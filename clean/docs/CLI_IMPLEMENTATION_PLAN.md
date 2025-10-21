# CLI Implementation Plan

## Executive Summary

This document outlines the plan to migrate and recreate the interactive CLI from the previous HVX system to the clean architecture. The CLI provides a user-friendly, step-by-step interface for IEQ analysis.

## Current State

### What Exists (Old System - `src/cli/`)

✅ **Interactive Workflow** (`src/cli/ui/workflows/ieq_start_interactive.py`):
- 700+ lines of comprehensive interactive workflow
- 7-step guided process
- Rich UI with progress tracking
- Collapsible completed steps
- Help system integration
- Auto mode support

✅ **Start Command** (`src/cli/commands/ieq/start.py`):
- Click-based command interface
- Directory and auto-mode options
- Error handling

✅ **UI Components**:
- Rich-based formatting
- Tables and panels
- Progress indicators

### What Needs to Be Created (Clean System - `clean/core/cli/`)

The clean architecture needs a completely new CLI that:
1. Uses clean architecture components (AnalysisEngine, ReportGenerator, etc.)
2. Works with new domain models (Room, Building, RoomAnalysis, etc.)
3. Maintains the excellent UX of the old CLI
4. Integrates with new config system (YAML-based standards/tests)

## Implementation Roadmap

### ⏱️ Total Estimated Time: 20-25 hours

### Phase 1: Foundation (4-5 hours)

**Goal**: Set up basic CLI infrastructure

#### 1.1 Main CLI Application (1 hour)
- Create `core/cli/main.py` with Click app
- Set up command groups (analyze, report, start)
- Add version and help
- Configure Rich console

**Deliverable**: `ieq --help` works

#### 1.2 Entry Point Setup (30 min)
- Update `pyproject.toml` with console script
- Test installation: `pip install -e .`
- Verify command availability

**Deliverable**: `ieq` command available in terminal

#### 1.3 Basic Commands Structure (30 min)
- Create command files:
  - `core/cli/commands/__init__.py`
  - `core/cli/commands/start.py`
  - `core/cli/commands/analyze.py`
  - `core/cli/commands/report.py`

**Deliverable**: Command skeleton in place

#### 1.4 UI Components Directory (30 min)
- Create directory structure
- Set up component files:
  - `core/cli/ui/components/progress.py`
  - `core/cli/ui/components/tables.py`
  - `core/cli/ui/components/panels.py`

**Deliverable**: UI component structure ready

#### 1.5 Documentation (2 hours)
- ✅ Create `core/cli/README.md` with implementation guide
- ✅ Document all tasks and dependencies
- ✅ Create example usage flows

**Deliverable**: ✅ Comprehensive implementation guide

### Phase 2: Interactive Workflow (8-10 hours)

**Goal**: Implement the main interactive start command

#### 2.1 Workflow Orchestrator Skeleton (2 hours)
- Create `core/cli/ui/workflows/interactive_start.py`
- Set up workflow state management
- Implement step tracking system
- Add collapsible step rendering

**Deliverable**: Workflow shell with progress tracking

#### 2.2 Step 1: Load Data (2 hours)
- Prompt for data directory
- Integrate with CSV/Excel data loaders
- Validate data structure
- Display data summary
- Handle errors gracefully

**Integration**:
- `core.infrastructure.data_loaders.csv_loader`
- `core.domain.models.room.Room`

**Deliverable**: Can load and display building data

#### 2.3 Step 2-3: Configure Analysis (2 hours)
- Show available standards
- Multi-select standards and tests
- Load YAML configs
- Configure filters and periods
- Display configuration summary

**Integration**:
- `config/standards/en16798-1/*.yaml`
- `config/filters/*.yaml`
- `config/periods/*.yaml`

**Deliverable**: Can configure analysis parameters

#### 2.4 Step 4: Run Analysis (1 hour)
- Integrate with AnalysisEngine
- Show progress indicator
- Handle long-running operations
- Display results summary

**Integration**:
- `core.analytics.engine.analysis_engine.AnalysisEngine`
- `core.analytics.aggregators.building_aggregator.BuildingAggregator`

**Deliverable**: Can run analysis and show results

#### 2.5 Step 5: Explore Results (1 hour)
- Create interactive menu
- Show room list with compliance
- Filter and sort options
- Detailed room view
- Building summary

**Integration**:
- `core.domain.models.room_analysis.RoomAnalysis`
- UI table components

**Deliverable**: Interactive result exploration

#### 2.6 Step 6-7: Reports & Export (2 hours)
- List available templates
- Generate HTML/PDF reports
- Export data (JSON/CSV)
- Show output paths

**Integration**:
- `core.reporting.report_generator.ReportGenerator`
- Template engine
- Chart integration (Plotly/Matplotlib)

**Deliverable**: Can generate reports and export data

### Phase 3: UI Components (3-4 hours)

**Goal**: Create reusable UI components

#### 3.1 Progress Components (1 hour)
- Step indicator with checkmarks
- Loading spinners
- Progress bars
- Status messages

**Deliverable**: Reusable progress indicators

#### 3.2 Table Formatters (1.5 hours)
- Room analysis table
- Building summary table
- Test results table
- Compliance color coding (red/yellow/green)

**Deliverable**: Formatted table displays

#### 3.3 Panel Components (30 min)
- Welcome panel
- Step headers
- Error panels
- Success messages
- Completion summary

**Deliverable**: Consistent panel styling

#### 3.4 Help System (1 hour)
- Context-sensitive help
- Type '?' for help
- Examples in help text
- Quick reference guide

**Deliverable**: Integrated help system

### Phase 4: Non-Interactive Commands (3-4 hours)

**Goal**: Add direct commands for advanced users

#### 4.1 Analyze Commands (2 hours)
```bash
ieq analyze run <data-dir> --standard en16798-1 --class II
ieq analyze list
ieq analyze show <analysis-id>
```

**Deliverable**: Non-interactive analysis

#### 4.2 Report Commands (2 hours)
```bash
ieq report generate --template building_detailed
ieq report list-templates
ieq report list
```

**Deliverable**: Non-interactive report generation

### Phase 5: Polish & Testing (2-3 hours)

#### 5.1 Error Handling (1 hour)
- Graceful error recovery
- Clear error messages
- Suggestions for fixes
- Log debugging info

**Deliverable**: Robust error handling

#### 5.2 Testing (1 hour)
- Unit tests for commands
- Integration tests for workflow
- Manual testing checklist
- Test with sample data

**Deliverable**: Tested CLI

#### 5.3 Documentation (1 hour)
- User guide
- Command reference
- Examples
- Troubleshooting

**Deliverable**: Complete documentation

## Technical Specifications

### Technology Stack

**Core**:
- **Click** (8.1+): Command-line framework
- **Rich** (13.0+): Terminal formatting, colors, progress bars
- **Python** (3.10+): Language runtime

**Integration**:
- **PyYAML**: Config file loading
- **Pandas**: Data manipulation
- **Matplotlib/Plotly**: Chart generation (already integrated)

### Architecture Integration

```
CLI Layer (core/cli/)
    ↓ Commands
Domain Layer (core/domain/)
    ↓ Domain Models
Application Layer (core/application/)
    ↓ Use Cases
Analytics Layer (core/analytics/)
    ↓ Analysis Engine
Infrastructure Layer (core/infrastructure/)
    ↓ Data Loaders, Repositories
```

### Data Flow

```
User Input (CLI)
    ↓
Command Handler
    ↓
Workflow Orchestrator
    ↓
1. Data Loaders → Room/Building entities
2. Config Loaders → Test configurations
3. Analysis Engine → RoomAnalysis results
4. Aggregators → BuildingAnalysis
5. Report Generator → HTML/PDF reports
6. Exporters → JSON/CSV files
    ↓
Terminal Output (Rich)
```

## Key Features

### 1. Progressive Workflow

7 clear steps that guide users from data to reports:
1. Load Data
2. Select Standards
3. Configure Tests
4. Run Analysis
5. Explore Results
6. Generate Reports
7. Export Data

### 2. Visual Progress Tracking

```
✓ 1. Load Building Data: 15 rooms from Building A
✓ 2. Select Standards: EN16798-1 Category II
✓ 3. Configure Tests: 6 tests selected
▶ 4. Run Analysis
  5. Explore Results
  6. Generate Reports
  7. Export Data
```

### 3. Interactive Result Exploration

```
Building Analysis Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Compliance: 93.5% (Grade A)
Quality:    97.2%
Rooms:      15
Violations: 12

What would you like to do?
1. View all rooms
2. View failing rooms only
3. View specific room
4. View building summary
5. Continue to reports
```

### 4. Intelligent Defaults

- Auto-detect data structure
- Suggest appropriate standards
- Pre-select common tests
- Default output paths
- Smart file naming

### 5. Help System

- Context help at any prompt (type '?')
- Command help (--help flag)
- Examples in help text
- Link to full docs

### 6. Auto Mode

```bash
$ ieq start --auto --directory data/building-a

Running in auto mode...
✓ Loaded data: 15 rooms
✓ Applied: EN16798-1 Category II
✓ Configured: 6 tests
✓ Analysis complete: 93.5% compliance
✓ Report generated: output/report_2024-10-20.html
✓ Data exported: output/analysis_2024-10-20.json

Done!
```

## Migration Strategy

### From Old CLI to Clean CLI

**Step 1**: Copy UI patterns (NOT code)
- Study old workflow structure
- Copy UX decisions
- Copy prompt texts
- Copy help messages

**Step 2**: Rewrite with clean architecture
- Use AnalysisEngine instead of HierarchicalAnalysisService
- Use domain entities (Room, Building) instead of BuildingDataset
- Use ReportGenerator instead of ReportService
- Use repositories for data access

**Step 3**: Enhance with new features
- Integrate matplotlib chart generation
- Use new YAML config system
- Add portfolio-level analysis
- Improve error messages

## Success Criteria

### Must Have (MVP)
- ✅ [x] Interactive start command works end-to-end
- ✅ [x] Can load data from directory
- ✅ [x] Can select standards and tests
- ✅ [x] Can run analysis
- ✅ [x] Can generate HTML reports
- ✅ [x] Error handling works
- ✅ [x] Progress tracking visible

### Should Have
- [ ] Can explore results interactively
- [ ] Can export to multiple formats
- [ ] Non-interactive commands work
- [ ] Help system complete
- [ ] Tests pass

### Nice to Have
- [ ] PDF report generation
- [ ] Chart preview in terminal
- [ ] Configuration save/load
- [ ] History of past analyses

## Risk Mitigation

### Risk 1: Complexity
**Mitigation**: Start with MVP, iterate

### Risk 2: Integration Issues
**Mitigation**: Test each integration point separately

### Risk 3: UX Regressions
**Mitigation**: Compare with old CLI, maintain same flow

### Risk 4: Performance
**Mitigation**: Add progress indicators for long operations

## Deliverables

### Code
- [ ] `core/cli/main.py` - Main CLI app
- [ ] `core/cli/commands/start.py` - Start command
- [ ] `core/cli/ui/workflows/interactive_start.py` - Workflow orchestrator
- [ ] `core/cli/ui/components/*.py` - UI components
- [ ] Tests for CLI

### Documentation
- [x] `core/cli/README.md` - Implementation guide
- [x] `docs/CLI_IMPLEMENTATION_PLAN.md` - This document
- [ ] User guide
- [ ] Command reference

### Infrastructure
- [ ] Entry point in pyproject.toml
- [ ] Updated requirements.txt
- [ ] Installation instructions

## Timeline

### Week 1 (Phase 1 + 2)
- Days 1-2: Foundation (Phase 1)
- Days 3-5: Interactive workflow (Phase 2)

### Week 2 (Phase 3 + 4 + 5)
- Days 1-2: UI components (Phase 3)
- Days 3-4: Non-interactive commands (Phase 4)
- Day 5: Polish & testing (Phase 5)

### Total: ~2 weeks part-time or 1 week full-time

## Next Steps

1. ✅ Review and approve this plan
2. ✅ Set up development environment
3. Start Phase 1.1: Create main CLI application
4. Work through phases sequentially
5. Test continuously
6. Document as you go

## Questions to Resolve

1. **Command name**: `ieq` or `ieq-analytics`?
   - **Recommendation**: `ieq` (shorter, memorable)

2. **PDF support**: Required or optional?
   - **Recommendation**: Optional (HTML by default)

3. **Data formats**: CSV only or also Excel/Parquet?
   - **Recommendation**: CSV + Excel (Parquet optional)

4. **Auto mode behavior**: What are the defaults?
   - **Recommendation**: EN16798-1 Cat II, all tests, opening hours

5. **Results storage**: Save analysis results by default?
   - **Recommendation**: Yes, to `output/analyses/`

## References

- Old CLI code: `../src/cli/ui/workflows/ieq_start_interactive.py`
- Clean architecture: `../ARCHITECTURE.md`
- Chart system: `../CHARTS_MIGRATION_SUMMARY.md`
- Config system: `../config/`
- Click docs: https://click.palletsprojects.com/
- Rich docs: https://rich.readthedocs.io/

---

**Status**: ✅ Plan Complete - Ready for Implementation
**Last Updated**: 2024-10-20
**Author**: System
