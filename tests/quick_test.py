"""
Quick Test - Minimal example showing core functionality
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from datetime import datetime

from core.domain.models.room import Room
from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.standard_type import StandardType
from core.analytics.engine.analysis_engine import AnalysisEngine


def main():
    print("=" * 60)
    print("  IEQ Analytics - Quick Test")
    print("=" * 60)

    # 1. Create sample data
    print("\n1. Creating sample data...")
    timestamps = pd.date_range("2024-01-01", periods=168, freq="H")
    df = pd.DataFrame({
        "temperature": 20 + 2 * np.sin(np.linspace(0, 4 * np.pi, 168)) + np.random.normal(0, 0.5, 168),
        "co2": 400 + 200 * np.sin(np.linspace(0, 4 * np.pi, 168)) + np.random.normal(0, 30, 168),
    }, index=timestamps)
    print(f"   ✓ Generated {len(df)} data points")

    # 2. Create room
    print("\n2. Creating room entity...")
    room = Room(
        id="R001",
        name="Conference Room",
        time_series_data=df,
        data_start=df.index.min(),
        data_end=df.index.max(),
    )
    print(f"   ✓ Room: {room.name}")
    print(f"   ✓ Parameters: {[p.value for p in room.available_parameters]}")
    print(f"   ✓ Completeness: {room.get_data_completeness():.1f}%")

    # 3. Define test
    print("\n3. Defining compliance test...")
    test = {
        "test_id": "temp_cat_i",
        "parameter": ParameterType.TEMPERATURE,
        "standard": StandardType.EN16798_1,
        "threshold": {"lower": 20.0, "upper": 24.0, "unit": "°C"},
        "compliance_level": 95.0,
    }
    print(f"   ✓ Test: {test['test_id']}")
    print(f"   ✓ Threshold: {test['threshold']['lower']}-{test['threshold']['upper']} {test['threshold']['unit']}")

    # 4. Run analysis
    print("\n4. Running analysis...")
    engine = AnalysisEngine()
    analysis = engine.analyze_room(room, tests=[test])
    print(f"   ✓ Analysis complete")

    # 5. Display results
    print("\n5. Results:")
    print(f"   Overall Compliance: {analysis.overall_compliance_rate:.2f}%")
    print(f"   Data Quality: {analysis.data_quality_score:.2f}%")
    print(f"   Tests Performed: {analysis.test_count}")

    for test_id, result in analysis.compliance_results.items():
        print(f"\n   Test: {test_id}")
        print(f"     Status: {'✓ PASS' if result.is_compliant else '✗ FAIL'}")
        print(f"     Compliance Rate: {result.compliance_rate:.2f}%")
        print(f"     Total Points: {result.total_points}")
        print(f"     Violations: {result.violation_count}")

        if result.violation_count > 0:
            worst = result.get_worst_violation()
            if worst:
                print(f"     Worst Violation: {worst.measured_value:.2f} at {worst.timestamp}")

    if analysis.recommendations:
        print(f"\n   Recommendations:")
        for rec in analysis.recommendations:
            print(f"     • {rec}")

    print("\n" + "=" * 60)
    print("  ✓ Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
