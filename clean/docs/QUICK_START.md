# Quick Start Guide

## What's Been Created

A professional, clean-architecture IEQ analytics platform with:

✅ **Complete project structure** - All directories organized by layer
✅ **Type-safe domain models** - Pydantic models with full validation
✅ **Comprehensive enums** - ParameterType, StandardType, Status, BuildingType
✅ **Value objects** - Measurement, TimeRange, ComplianceThreshold
✅ **Room entity** - Rich domain model with behavior
✅ **Professional configuration** - pyproject.toml, testing, linting setup

## What Needs to Be Completed

See `IMPLEMENTATION_STATUS.md` for the complete checklist.

**Priority 1 (Core Domain)**:
- Level, Building, Dataset entities
- Analysis result models

**Priority 2 (Analytics Engine)**:
- Analysis engine core
- Evaluators (EN16798-1, BR18)
- Metrics calculators

**Priority 3 (Infrastructure)**:
- CSV/Excel data loaders
- File system operations

**Priority 4 (Reporting)**:
- YAML template engine
- HTML/PDF renderers
- Chart generators

**Priority 5 (CLI)**:
- Command-line interface
- User interaction

## File Organization Pattern

Every file follows this structure:

```python
"""Module docstring explaining purpose."""

# Standard library imports
from datetime import datetime
from typing import Optional, List

# Third-party imports
import pandas as pd
from pydantic import BaseModel, Field

# Local imports
from core.domain.enums import ParameterType


class ClassName(BaseModel):
    """
    Class docstring with clear description.

    Explains what this class represents and its responsibilities.
    """

    # Fields with descriptions
    field_name: str = Field(..., description="Clear description")

    # Properties
    @property
    def computed_value(self) -> int:
        """Docstring for property."""
        return len(self.field_name)

    # Methods
    def do_something(self) -> None:
        """Docstring for method."""
        pass
```

## Key Design Patterns Used

### 1. One Class Per File
```
core/
  domain/
    models/
      room.py          # Only Room class
      building.py      # Only Building class
```

### 2. Type Safety Everywhere
```python
from typing import Optional, List
from pydantic import BaseModel, Field

class Example(BaseModel):
    required_field: str = Field(..., description="Required")
    optional_field: Optional[int] = Field(default=None, description="Optional")
```

### 3. Immutable Value Objects
```python
class Measurement(BaseModel):
    timestamp: datetime
    value: float

    model_config = {"frozen": True}  # Immutable
```

### 4. Rich Domain Models
```python
class Room(BaseModel):
    """Room entity with behavior, not just data."""

    id: str
    name: str

    # Domain behavior
    def get_data_completeness(self) -> float:
        """Calculate completeness."""
        ...
```

### 5. Clean Separation of Concerns
```
Domain      → Pure business logic (no I/O)
Application → Orchestration (use cases)
Infrastructure → External systems (I/O, APIs)
```

## Implementation Guide

### Step 1: Complete Domain Models

Create these files following the `Room` pattern:

**`core/domain/models/level.py`**:
```python
"""Level domain entity."""

from typing import List, Dict, Any
from pydantic import BaseModel, Field

class Level(BaseModel):
    """Building level/floor entity."""

    id: str = Field(..., description="Unique level identifier")
    name: str = Field(..., description="Level name (e.g., 'Ground Floor')")
    building_id: Optional[str] = Field(default=None)
    floor_number: int = Field(..., description="Floor number")
    room_ids: List[str] = Field(default_factory=list)

    def add_room(self, room_id: str) -> None:
        """Add room to this level."""
        if room_id not in self.room_ids:
            self.room_ids.append(room_id)

    def get_room_count(self) -> int:
        """Get number of rooms on this level."""
        return len(self.room_ids)
```

**`core/domain/models/building.py`**:
```python
"""Building domain entity."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from core.domain.enums import BuildingType

class Building(BaseModel):
    """Building entity with hierarchical structure."""

    id: str = Field(..., description="Unique building identifier")
    name: str = Field(..., description="Building name")
    building_type: BuildingType = Field(default=BuildingType.OFFICE)
    level_ids: List[str] = Field(default_factory=list)

    def add_level(self, level_id: str) -> None:
        """Add level to building."""
        if level_id not in self.level_ids:
            self.level_ids.append(level_id)

    def get_level_count(self) -> int:
        """Get number of levels."""
        return len(self.level_ids)
```

**`core/domain/models/dataset.py`**:
```python
"""Dataset collection entity."""

from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel, Field

class Dataset(BaseModel):
    """Collection of buildings with metadata."""

    buildings: List[str] = Field(default_factory=list, description="Building IDs")
    loaded_at: datetime = Field(default_factory=datetime.now)
    source_directory: str = Field(..., description="Source data directory")

    def add_building(self, building_id: str) -> None:
        """Add building to dataset."""
        if building_id not in self.buildings:
            self.buildings.append(building_id)

    def get_building_count(self) -> int:
        """Get number of buildings."""
        return len(self.buildings)
```

### Step 2: Create Analysis Results Models

**`core/domain/models/compliance_result.py`**:
```python
"""Compliance result model."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ComplianceResult(BaseModel):
    """Result of a single compliance check."""

    test_id: str = Field(..., description="Compliance test identifier")
    compliant: bool = Field(..., description="Whether data is compliant")
    compliance_rate: float = Field(..., ge=0, le=100, description="Compliance %")
    total_points: int = Field(..., ge=0)
    compliant_points: int = Field(..., ge=0)
    violations: List[Dict[str, Any]] = Field(default_factory=list)
```

### Step 3: Create Analytics Engine

**`core/analytics/engine/analysis_engine.py`**:
```python
"""Core analysis engine."""

import pandas as pd
from typing import Dict, List, Optional, Any
from core.domain.models.room import Room
from core.domain.enums import StandardType

class AnalysisEngine:
    """Main analytics engine for IEQ analysis."""

    def __init__(self):
        """Initialize analysis engine."""
        self.evaluators = {}  # Will hold standard evaluators

    def analyze_room(
        self,
        room: Room,
        standards: List[StandardType]
    ) -> Dict[str, Any]:
        """
        Analyze room data against specified standards.

        Args:
            room: Room with time series data
            standards: List of standards to evaluate against

        Returns:
            Dictionary with analysis results
        """
        if not room.has_data:
            return {"error": "No data available"}

        results = {
            "room_id": room.id,
            "room_name": room.name,
            "standards": {},
        }

        for standard in standards:
            evaluator = self.get_evaluator(standard)
            if evaluator:
                results["standards"][standard.value] = evaluator.evaluate(room)

        return results

    def get_evaluator(self, standard: StandardType):
        """Get evaluator for standard (placeholder)."""
        # TODO: Implement evaluator factory
        return None
```

### Step 4: Create Data Loaders

**`core/infrastructure/data_loaders/csv_loader.py`**:
```python
"""CSV data loader."""

import pandas as pd
from pathlib import Path
from typing import Optional
from core.domain.models.room import Room

class CSVDataLoader:
    """Load room data from CSV files."""

    def load_room(self, file_path: Path, room_id: str, room_name: str) -> Room:
        """
        Load room data from CSV file.

        Args:
            file_path: Path to CSV file
            room_id: Room identifier
            room_name: Room name

        Returns:
            Room entity with loaded data
        """
        # Load CSV with first column as datetime index
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)

        # Create room entity
        room = Room(
            id=room_id,
            name=room_name,
            data_file_path=file_path,
            time_series_data=df,
            data_start=df.index.min() if not df.empty else None,
            data_end=df.index.max() if not df.empty else None,
        )

        return room
```

### Step 5: Create Report Templates

**`config/report_templates/simple_building.yaml`**:
```yaml
template_id: simple_building
name: Simple Building Report
version: "1.0"

analytics_requirements:
  analytics_tags:
    - statistics.basic
    - compliance.overall
  required_parameters:
    - temperature

report:
  title: "Building Report"
  format: html
  theme: modern
  scope: building

sections:
  - section_id: summary
    type: summary
    title: "Building Summary"

  - section_id: compliance
    type: charts
    title: "Compliance Overview"
    charts:
      - id: compliance_bar
        title: "Compliance Rates"
        type: bar_chart
```

### Step 6: Create CLI

**`core/cli/main.py`**:
```python
"""CLI main entry point."""

import click
from pathlib import Path

@click.group()
@click.version_option(version="2.0.0")
def cli():
    """IEQ Analytics - Indoor Environmental Quality Analysis Tool."""
    pass

@cli.command()
@click.argument('data_dir', type=click.Path(exists=True))
@click.option('--output', '-o', default='output/', help='Output directory')
def analyze(data_dir: str, output: str):
    """Analyze building data."""
    click.echo(f"Analyzing data from: {data_dir}")
    click.echo(f"Output will be saved to: {output}")
    # TODO: Implement analysis logic

@cli.command()
@click.argument('template')
@click.option('--analysis', '-a', required=True, help='Analysis file')
@click.option('--output', '-o', default='output/', help='Output directory')
def report(template: str, analysis: str, output: str):
    """Generate report from template."""
    click.echo(f"Generating report using template: {template}")
    # TODO: Implement report generation

if __name__ == '__main__':
    cli()
```

## Testing

Run tests with:
```bash
pytest tests/ -v
```

Create test files following this pattern:

**`tests/unit/domain/test_room.py`**:
```python
"""Tests for Room entity."""

import pytest
import pandas as pd
from datetime import datetime
from core.domain.models.room import Room
from core.domain.enums import ParameterType

def test_room_creation():
    """Test creating a room."""
    room = Room(id="R001", name="Room 001")
    assert room.id == "R001"
    assert room.name == "Room 001"
    assert not room.has_data

def test_room_with_data():
    """Test room with time series data."""
    df = pd.DataFrame({
        'temperature': [20.5, 21.0, 20.8],
        'co2': [450, 480, 460],
    }, index=pd.date_range('2024-01-01', periods=3, freq='h'))

    room = Room(
        id="R001",
        name="Room 001",
        time_series_data=df,
        data_start=df.index.min(),
        data_end=df.index.max(),
    )

    assert room.has_data
    assert ParameterType.TEMPERATURE in room.available_parameters
    assert room.get_measurement_count() == 3
```

## Next Steps

1. Complete remaining domain models (Level, Building, Dataset)
2. Implement analytics engine and evaluators
3. Create data loaders for CSV/Excel
4. Build report template engine
5. Implement chart generators
6. Create CLI commands
7. Add comprehensive tests
8. Write user documentation

## Getting Help

- See `ARCHITECTURE.md` for design details
- See `IMPLEMENTATION_STATUS.md` for progress tracking
- Check existing code for patterns to follow
- All classes use Pydantic - refer to Pydantic docs for validation

## Code Style

This project uses:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking
- **Pytest** for testing

Run quality checks:
```bash
black core/
ruff check core/
mypy core/
pytest tests/
```
