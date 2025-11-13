"""
Basic test to verify refactored service structure and imports.
"""

import sys
from pathlib import Path

# Add refactored_service to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing refactored service imports and structure...")
print("=" * 60)

# Test 1: Import calculators
print("\n✓ Test 1: Importing calculators...")
try:
    from calculators import (
        EN16798Calculator,
        TAILCalculator,
        VentilationCalculator,
        OccupancyCalculator,
        RCThermalModel,
    )
    print("  ✓ All calculator imports successful")
except Exception as e:
    print(f"  ✗ Calculator import failed: {e}")
    sys.exit(1)

# Test 2: Import engine
print("\n✓ Test 2: Importing engine...")
try:
    from engine import AnalysisEngine, AnalysisConfig, PortfolioAnalysisResult
    print("  ✓ Engine imports successful")
except Exception as e:
    print(f"  ✗ Engine import failed: {e}")
    sys.exit(1)

# Test 3: Check EN16798 calculator enums
print("\n✓ Test 3: Checking EN16798 calculator...")
try:
    from calculators.en16798_calculator import (
        EN16798Category,
        VentilationType,
        PollutionLevel,
    )
    print(f"  ✓ EN16798 Categories: {[c.value for c in EN16798Category]}")
    print(f"  ✓ Ventilation Types: {[v.value for v in VentilationType]}")
    print(f"  ✓ Pollution Levels: {[p.value for p in PollutionLevel]}")
except Exception as e:
    print(f"  ✗ EN16798 check failed: {e}")
    sys.exit(1)

# Test 4: Check TAIL calculator
print("\n✓ Test 4: Checking TAIL calculator...")
try:
    from calculators.tail_calculator import (
        TAILRating,
        TAILCategory,
    )
    print(f"  ✓ TAIL Ratings: {[r.value for r in TAILRating]}")
    print(f"  ✓ TAIL Categories: {[c.value for c in TAILCategory]}")
except Exception as e:
    print(f"  ✗ TAIL check failed: {e}")
    sys.exit(1)

# Test 5: Check RC model
print("\n✓ Test 5: Checking RC thermal model...")
try:
    from calculators.rc_thermal_model import (
        RCModelType,
        RCModelParameters,
    )
    print(f"  ✓ RC Model Types: {[t.value for t in RCModelType]}")
except Exception as e:
    print(f"  ✗ RC model check failed: {e}")
    sys.exit(1)

# Test 6: Check analysis engine types
print("\n✓ Test 6: Checking analysis engine types...")
try:
    from engine.analysis_engine import (
        AnalysisType,
        SpaceData,
    )
    print(f"  ✓ Analysis Types: {[a.value for a in AnalysisType]}")
except Exception as e:
    print(f"  ✗ Engine types check failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nRefactored service structure is valid and all imports work correctly.")
print("\nNext steps:")
print("  1. Install dependencies: pip install numpy pandas scipy")
print("  2. Run full example: python examples/portfolio_analysis_example.py")
