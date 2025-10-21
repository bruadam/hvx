#!/usr/bin/env python3
"""Quick test to demonstrate the new parameter type functionality."""

import sys
import os

# Add the current directory to path and import directly
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

# Import the enums directly without going through core module
from core.domain.enums.measurement_type import MeasurementType
from core.domain.enums.tail_category import TAILCategory

# Now we need to manually add the parameter type since it depends on the others
exec(open(os.path.join(current_dir, 'core/domain/enums/parameter_type.py')).read())


def test_parameter_types():
    """Test the new parameter type functionality."""
    print("=== Parameter Type Demo ===\n")
    
    # Test parameters with multiple measurement types
    multi_type_params = [
        ParameterType.RADON,
        ParameterType.VENTILATION,
        ParameterType.NOISE,
        ParameterType.ILLUMINANCE
    ]
    
    print("Parameters with multiple measurement types:")
    for param in multi_type_params:
        print(f"  {param.display_name}:")
        print(f"    Measurement types: {[mt.display_name for mt in param.measurement_types]}")
        print(f"    Primary type: {param.primary_measurement_type.display_name}")
        print(f"    TAIL category: {param.tail_category.display_name}")
        print(f"    Default unit: {param.default_unit}")
        print()
    
    # Test TAIL categories
    print("TAIL Categories and their parameters:")
    for category in TAILCategory:
        if category != TAILCategory.OTHER:
            params = ParameterType.get_parameters_by_tail_category(category)
            print(f"  {category.display_name}:")
            for param in params:
                print(f"    - {param.display_name}")
            print()
    
    # Test measurement type filtering
    print("Parameters by measurement type:")
    for mt in MeasurementType:
        params = ParameterType.get_parameters_by_measurement_type(mt)
        print(f"  {mt.display_name}: {len(params)} parameters")
        for param in sorted(params, key=lambda p: p.display_name):
            print(f"    - {param.display_name}")
        print()
    
    # Test specific parameter capabilities
    print("Parameter capabilities:")
    test_param = ParameterType.RADON
    print(f"  {test_param.display_name}:")
    print(f"    Supports continuous: {test_param.supports_measurement_type(MeasurementType.CONTINUOUS)}")
    print(f"    Supports inspection: {test_param.supports_measurement_type(MeasurementType.INSPECTION)}")
    print(f"    Supports simulation: {test_param.supports_measurement_type(MeasurementType.SIMULATED)}")
    print(f"    Is TAIL parameter: {test_param.is_tail_parameter}")


if __name__ == "__main__":
    test_parameter_types()