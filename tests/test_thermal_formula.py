"""
Simple test of the thermal parameter estimation formula.

This script demonstrates the core heat transfer equation without dependencies.
"""

def test_thermal_formula():
    """Test the basic thermal formula implementation."""
    print("=" * 70)
    print("THERMAL FORMULA TEST")
    print("=" * 70)
    print()
    print("Formula: T_out - T_in = R_env * (C_in * dT_in/dt - Q_in)")
    print()

    # Example parameters
    R_env = 0.015  # Thermal resistance (K/W)
    C_in = 5e6  # Thermal capacitance (J/K)

    print(f"Building Parameters:")
    print(f"  R_env (Thermal Resistance): {R_env} K/W")
    print(f"  C_in (Thermal Capacitance): {C_in:.2e} J/K")
    print()

    # Test Case 1: Building is cooling down
    print("Test Case 1: Building Cooling (Cold Winter Night)")
    print("-" * 50)
    T_in = 20  # Indoor temperature (°C)
    T_out = 5  # Outdoor temperature (°C)
    dT_in_dt = -0.2  # Temperature dropping at 0.2°C/hour
    Q_in = 800  # Internal heat gains (W) - low at night

    # Calculate using the formula
    temp_diff_predicted = R_env * (C_in * dT_in_dt - Q_in)
    temp_diff_actual = T_out - T_in
    T_out_predicted = T_in + temp_diff_predicted

    print(f"  T_in: {T_in}°C")
    print(f"  T_out (actual): {T_out}°C")
    print(f"  dT_in/dt: {dT_in_dt}°C/h")
    print(f"  Q_in: {Q_in}W")
    print(f"  Predicted T_out: {T_out_predicted:.2f}°C")
    print(f"  Temperature difference (actual): {temp_diff_actual:.2f}°C")
    print(f"  Temperature difference (predicted): {temp_diff_predicted:.2f}°C")
    print()

    # Test Case 2: Building is heating up
    print("Test Case 2: Building Heating (Sunny Day with Occupants)")
    print("-" * 50)
    T_in = 22  # Indoor temperature (°C)
    T_out = 15  # Outdoor temperature (°C)
    dT_in_dt = 0.3  # Temperature rising at 0.3°C/hour
    Q_in = 2500  # Internal heat gains (W) - high with people and sun

    temp_diff_predicted = R_env * (C_in * dT_in_dt - Q_in)
    temp_diff_actual = T_out - T_in
    T_out_predicted = T_in + temp_diff_predicted

    print(f"  T_in: {T_in}°C")
    print(f"  T_out (actual): {T_out}°C")
    print(f"  dT_in/dt: {dT_in_dt}°C/h")
    print(f"  Q_in: {Q_in}W")
    print(f"  Predicted T_out: {T_out_predicted:.2f}°C")
    print(f"  Temperature difference (actual): {temp_diff_actual:.2f}°C")
    print(f"  Temperature difference (predicted): {temp_diff_predicted:.2f}°C")
    print()

    # Test Case 3: Steady state
    print("Test Case 3: Steady State (Thermostat Controlling)")
    print("-" * 50)
    T_in = 21  # Indoor temperature (°C)
    T_out = 10  # Outdoor temperature (°C)
    dT_in_dt = 0.0  # No temperature change (steady state)
    Q_in = 1100  # Internal heat gains (W)

    temp_diff_predicted = R_env * (C_in * dT_in_dt - Q_in)
    temp_diff_actual = T_out - T_in
    T_out_predicted = T_in + temp_diff_predicted

    print(f"  T_in: {T_in}°C")
    print(f"  T_out (actual): {T_out}°C")
    print(f"  dT_in/dt: {dT_in_dt}°C/h (steady state)")
    print(f"  Q_in: {Q_in}W")
    print(f"  Predicted T_out: {T_out_predicted:.2f}°C")
    print(f"  Temperature difference (actual): {temp_diff_actual:.2f}°C")
    print(f"  Temperature difference (predicted): {temp_diff_predicted:.2f}°C")
    print()

    # Physical interpretation
    print("=" * 70)
    print("PHYSICAL INTERPRETATION")
    print("=" * 70)
    print()
    print("The formula relates indoor and outdoor temperatures through:")
    print()
    print("1. Thermal Resistance (R_env):")
    print("   - Measures how well the building envelope resists heat flow")
    print("   - Higher R = better insulation")
    print("   - Units: K/W (Kelvin per Watt)")
    print()
    print("2. Thermal Capacitance (C_in):")
    print("   - Measures the building's ability to store heat")
    print("   - Higher C = slower temperature changes")
    print("   - Units: J/K (Joules per Kelvin)")
    print()
    print("3. Temperature Rate of Change (dT_in/dt):")
    print("   - How fast the indoor temperature is changing")
    print("   - Negative = cooling, Positive = heating")
    print("   - Units: °C/h or K/s")
    print()
    print("4. Internal Heat Gains (Q_in):")
    print("   - Heat from occupants, equipment, solar radiation")
    print("   - Units: W (Watts)")
    print()
    print("The right side of the equation (R_env * (C_in * dT_in/dt - Q_in))")
    print("represents the temperature difference needed to balance:")
    print("  - Heat storage in the building mass (C_in * dT_in/dt)")
    print("  - Internal heat gains (Q_in)")
    print("  - Heat loss through the envelope (driven by T_out - T_in)")
    print()


if __name__ == '__main__':
    test_thermal_formula()
