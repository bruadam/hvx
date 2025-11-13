# Refactored Building Analytics Service

A comprehensive, scalable service for building portfolio analytics that consolidates all calculation standards and special analyses into a unified architecture.

## 🏗️ Architecture

The refactored service follows a modular, calculator-based architecture:

```
refactored_service/
├── calculators/          # Core calculation modules
│   ├── en16798_calculator.py      # EN 16798-1 standard
│   ├── tail_calculator.py         # TAIL rating scheme
│   ├── ventilation_calculator.py  # Ventilation rate estimation
│   ├── occupancy_calculator.py    # Occupancy detection
│   └── rc_thermal_model.py        # RC thermal modeling
├── engine/              # Unified analysis orchestration
│   └── analysis_engine.py         # Main analysis engine
├── core/                # Data models
│   └── models/
├── examples/            # Usage examples
│   └── portfolio_analysis_example.py
└── README.md
```

## 🎯 Features

### 1. EN 16798-1 Calculator (`calculators/en16798_calculator.py`)

Complete implementation of EN 16798-1 indoor environmental input parameters:

- **Temperature thresholds**: Fixed (heating/cooling seasons) and adaptive comfort model
- **CO2 limits**: Category-based concentration thresholds
- **Humidity thresholds**: Relative humidity ranges for each category
- **Ventilation requirements**: Required ventilation rates based on occupancy and building pollution
- **Compliance assessment**: Instant values and time series analysis
- **Category determination**: Automatic category achievement based on measurements

**Categories**: I (High), II (Normal), III (Moderate), IV (Low)

### 2. TAIL Calculator (`calculators/tail_calculator.py`)

TAIL rating scheme for comprehensive indoor environmental quality:

- **Four categories**: Thermal, Acoustic, Indoor Air Quality (IAQ), Luminous
- **Rating scale**: I (Excellent ≥95%), II (Good 70-95%), III (Fair 50-70%), IV (Poor <50%)
- **Parameter classification**: Automatic categorization of parameters
- **Time series analysis**: Compliance over time
- **Aggregation**: Portfolio-level aggregation with "worst" or "average" methods

### 3. Ventilation Calculator (`calculators/ventilation_calculator.py`)

Estimate ventilation rates from CO2 decay analysis:

- **CO2 decay analysis**: Exponential decay curve fitting
- **ACH estimation**: Air changes per hour
- **Quality categories**: Excellent (≥6 ACH), Good (≥4), Fair (≥2), Poor (<2)
- **Confidence metrics**: R² goodness of fit and confidence intervals
- **Multiple period averaging**: Weighted by fit quality

### 4. Occupancy Calculator (`calculators/occupancy_calculator.py`)

Detect occupancy patterns from CO2 data:

- **Pattern detection**: Identify occupied vs unoccupied periods
- **Occupancy rate**: Fraction of time occupied
- **Typical hours**: When space is typically occupied
- **Occupant estimation**: Estimate number of occupants from CO2 levels
- **CO2 mass balance**: Physics-based occupant count estimation

### 5. RC Thermal Model (`calculators/rc_thermal_model.py`)

Building thermal dynamics simulation:

- **Model types**: 1R1C, 2R2C, 3R3C resistance-capacitance models
- **Temperature prediction**: Indoor temperature based on outdoor conditions
- **HVAC loads**: Heating and cooling power requirements
- **Solar gains**: Window solar heat gain calculation
- **Parameter estimation**: Auto-estimate from building properties
- **Thermal metrics**: U-value, time constant

## 🚀 Unified Analysis Engine

The `AnalysisEngine` orchestrates all calculations across a building portfolio:

```python
from refactored_service.engine import AnalysisEngine, AnalysisConfig
from refactored_service.engine.analysis_engine import SpaceData, AnalysisType

# Configure analysis
config = AnalysisConfig(
    analyses_to_run=[
        AnalysisType.EN16798,
        AnalysisType.TAIL,
        AnalysisType.VENTILATION,
        AnalysisType.OCCUPANCY,
    ],
    season="heating",
)

# Create engine
engine = AnalysisEngine(config)

# Analyze single space
space = SpaceData(
    id="room_1",
    name="Office 101",
    type="room",
    area_m2=25.0,
    volume_m3=75.0,
    temperature=temperature_series,
    co2=co2_series,
    humidity=humidity_series,
)

result = engine.analyze_space(space)

# Analyze portfolio
spaces = [...]  # List of SpaceData
portfolio_result = engine.analyze_portfolio(
    spaces=spaces,
    portfolio_id="my_portfolio",
    portfolio_name="My Building Portfolio"
)
```

## 📊 Example: Portfolio Analysis

See `examples/portfolio_analysis_example.py` for a complete example with:

- 3 buildings (Office, School, Retail)
- 2 floors per building
- 3-5 rooms per floor
- Generated environmental data (temperature, CO2, humidity)
- Complete analysis pipeline
- Portfolio-level aggregation

Run the example:

```bash
cd refactored_service/examples
python portfolio_analysis_example.py
```

## 🎨 Key Design Principles

### 1. **Scalability**
- Modular calculator design
- Independent calculators that can be used standalone
- Hierarchical aggregation (room → floor → building → portfolio)

### 2. **Configurability**
- Config-driven analysis
- Flexible thresholds and parameters
- Optional analyses (run only what you need)

### 3. **Type Safety**
- Dataclasses for structured data
- Enums for categorical values
- Type hints throughout

### 4. **Extensibility**
- Easy to add new calculators
- Pluggable into analysis engine
- Standard interfaces

## 📈 Comparison: Core vs Refactored

| Aspect | Core (Legacy) | Refactored Service |
|--------|--------------|-------------------|
| **Size** | 1.2MB, 150+ files | Focused, ~20 key files |
| **Approach** | Object-oriented entities | Calculator-based services |
| **Data** | pandas in entities | Separate data models |
| **Self-analysis** | Entities compute metrics | External calculators |
| **Standards** | Hardcoded | Modular calculators |
| **Scalability** | Limited | Portfolio-scale ready |
| **Testing** | Entity-centric | Calculator-centric |

## 🔧 Technical Details

### Dependencies

```
pandas
numpy
scipy
pythermalcomfort (optional, for EN 16798 adaptive comfort)
```

### Data Flow

```
SpaceData (input)
    ↓
AnalysisEngine
    ↓
┌─────────────┬─────────────┬─────────────┬─────────────┐
│  EN 16798   │    TAIL     │ Ventilation │  Occupancy  │
│ Calculator  │ Calculator  │ Calculator  │ Calculator  │
└─────────────┴─────────────┴─────────────┴─────────────┘
    ↓
SpaceAnalysisResult
    ↓
Portfolio Aggregation
    ↓
PortfolioAnalysisResult (output)
```

### Performance

- Designed for portfolio-scale analysis (1000+ rooms)
- Efficient time series operations using pandas
- Parallel-ready architecture (spaces can be analyzed independently)

## 📝 Usage Patterns

### Pattern 1: Single Room Analysis

```python
from refactored_service.calculators import EN16798Calculator

calculator = EN16798Calculator()
result = calculator.assess_timeseries_compliance(
    temperature=temp_series,
    co2=co2_series,
    season="heating"
)
```

### Pattern 2: Portfolio Analysis

```python
from refactored_service.engine import AnalysisEngine

engine = AnalysisEngine()
result = engine.analyze_portfolio(spaces)
```

### Pattern 3: Custom Analysis

```python
from refactored_service.calculators import (
    VentilationCalculator,
    OccupancyCalculator,
)

# Estimate ventilation
vent_calc = VentilationCalculator()
vent_result = vent_calc.estimate_from_co2_decay(co2_series, volume_m3)

# Detect occupancy
occ_calc = OccupancyCalculator()
occ_pattern = occ_calc.detect_occupancy(co2_series)
```

## 🎯 Future Enhancements

- [ ] Add more standards (ASHRAE, WELL, etc.)
- [ ] Parallel processing for portfolio analysis
- [ ] Real-time streaming analysis
- [ ] Machine learning-based anomaly detection
- [ ] Cost optimization recommendations
- [ ] Integration with BMS/SCADA systems

## 📚 References

- EN 16798-1: Energy performance of buildings - Indoor environmental input parameters
- TAIL Rating Scheme: ALDREN project
- pythermalcomfort: https://github.com/CenterForTheBuiltEnvironment/pythermalcomfort

## 🤝 Contributing

This refactored service is designed to be maintainable and extensible. To add a new calculator:

1. Create new file in `calculators/`
2. Implement calculation logic
3. Add to `AnalysisEngine` in `engine/analysis_engine.py`
4. Update `AnalysisType` enum
5. Add tests and examples

---

**Built with ❤️ for scalable building analytics**
