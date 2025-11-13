"""
Comprehensive demonstration of thermal parameter estimation.

This script demonstrates:
1. Synthetic data generation with known parameters
2. Parameter estimation using different methods
3. Model validation and diagnostics
4. Handling real-world data scenarios
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analytics.recommendations.thermal_parameter_estimator import (
    ThermalParameterEstimator,
    ThermalParameters
)
from core.analytics.recommendations.thermal_diagnostics import ThermalDiagnostics


def generate_synthetic_building_data(
    n_days: int = 7,
    samples_per_hour: int = 1,
    R_env: float = 0.015,
    C_in: float = 5e6,
    noise_level: float = 0.2,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate realistic synthetic building thermal data.

    Args:
        n_days: Number of days to simulate
        samples_per_hour: Sampling frequency
        R_env: True thermal resistance (K/W)
        C_in: True thermal capacitance (J/K)
        noise_level: Temperature measurement noise (°C)
        seed: Random seed

    Returns:
        DataFrame with thermal data
    """
    np.random.seed(seed)

    n_points = n_days * 24 * samples_per_hour
    dt = 1.0 / samples_per_hour  # hours

    # Time array
    hours = np.arange(n_points) * dt

    # Outdoor temperature with diurnal and weather variations
    T_out = (
        12  # Base temperature
        + 8 * np.sin(2 * np.pi * hours / 24)  # Diurnal cycle
        + 3 * np.sin(2 * np.pi * hours / (24 * 3))  # Weather pattern (3-day cycle)
        + np.random.normal(0, 1, n_points)  # Random fluctuations
    )

    # Internal heat gains with occupancy patterns
    Q_in = np.zeros(n_points)
    for i, hour in enumerate(hours):
        hour_of_day = hour % 24

        # Weekday vs weekend (simplified)
        day_of_week = int(hour // 24) % 7
        is_weekend = day_of_week >= 5

        if is_weekend:
            # Weekend: lower gains, spread throughout day
            base_gain = 800
            if 8 <= hour_of_day <= 22:
                Q_in[i] = base_gain + 400 * np.sin(np.pi * (hour_of_day - 8) / 14)
            else:
                Q_in[i] = base_gain * 0.3
        else:
            # Weekday: higher gains during business hours
            base_gain = 1000
            if 8 <= hour_of_day <= 17:
                Q_in[i] = base_gain + 800 * np.sin(np.pi * (hour_of_day - 8) / 9)
            elif 17 < hour_of_day <= 20:
                Q_in[i] = base_gain * 0.5
            else:
                Q_in[i] = base_gain * 0.2

        # Add random variations
        Q_in[i] += np.random.normal(0, 100)

    # Simulate indoor temperature using thermal dynamics
    T_in = np.zeros(n_points)
    T_in[0] = 20  # Initial condition (°C)

    for i in range(1, n_points):
        # Heat balance: dT_in/dt = (Q_in - (T_in - T_out) / R_env) / C_in
        heat_loss = (T_in[i-1] - T_out[i-1]) / R_env
        net_heat = Q_in[i-1] - heat_loss
        dT_dt = net_heat / C_in

        T_in[i] = T_in[i-1] + dT_dt * dt * 3600  # Convert hours to seconds

    # Add measurement noise
    T_in += np.random.normal(0, noise_level, n_points)
    T_out += np.random.normal(0, noise_level * 0.5, n_points)

    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n_points, freq=f'{int(60/samples_per_hour)}min'),
        'T_in': T_in,
        'T_out': T_out,
        'Q_in': Q_in,
        'hour_of_day': hours % 24
    })

    return df


def demo_basic_estimation():
    """Demonstrate basic parameter estimation."""
    print("=" * 80)
    print("DEMO 1: Basic Parameter Estimation")
    print("=" * 80)
    print()

    # True parameters for verification
    R_env_true = 0.015  # K/W
    C_in_true = 5e6  # J/K

    print(f"True Parameters:")
    print(f"  R_env: {R_env_true:.6f} K/W")
    print(f"  C_in:  {C_in_true:.4e} J/K")
    print()

    # Generate data
    print("Generating synthetic data (7 days, hourly)...")
    df = generate_synthetic_building_data(
        n_days=7,
        samples_per_hour=1,
        R_env=R_env_true,
        C_in=C_in_true,
        noise_level=0.15
    )
    print(f"Generated {len(df)} data points")
    print()

    # Fit model
    print("Fitting thermal parameters using nonlinear optimization...")
    estimator = ThermalParameterEstimator(time_unit='hour')

    params = estimator.fit(
        T_in=df['T_in'].values,
        T_out=df['T_out'].values,
        Q_in=df['Q_in'].values,
        dt=1.0,
        method='nonlinear',
        initial_guess=(0.01, 1e6)
    )

    print()
    estimator.print_summary()

    # Calculate errors
    R_env_error = abs(params.R_env - R_env_true) / R_env_true * 100
    C_in_error = abs(params.C_in - C_in_true) / C_in_true * 100

    print(f"\nParameter Recovery Errors:")
    print(f"  R_env error: {R_env_error:.2f}%")
    print(f"  C_in error:  {C_in_error:.2f}%")
    print()

    return estimator, df


def demo_method_comparison():
    """Compare linear and nonlinear estimation methods."""
    print("=" * 80)
    print("DEMO 2: Method Comparison (Linear vs Nonlinear)")
    print("=" * 80)
    print()

    # Generate data
    R_env_true = 0.012
    C_in_true = 6e6

    df = generate_synthetic_building_data(
        n_days=5,
        samples_per_hour=2,
        R_env=R_env_true,
        C_in=C_in_true,
        noise_level=0.2
    )

    print(f"True parameters: R_env={R_env_true:.6f}, C_in={C_in_true:.4e}")
    print()

    # Linear method
    print("Method 1: Linear (Grid Search)")
    print("-" * 40)
    estimator_linear = ThermalParameterEstimator(time_unit='hour')
    params_linear = estimator_linear.fit(
        T_in=df['T_in'].values,
        T_out=df['T_out'].values,
        Q_in=df['Q_in'].values,
        dt=0.5,  # 2 samples per hour
        method='linear'
    )
    print(f"  R_env: {params_linear.R_env:.6f} (RMSE: {params_linear.rmse:.4f})")
    print(f"  C_in:  {params_linear.C_in:.4e} (R²: {params_linear.r_squared:.4f})")
    print()

    # Nonlinear method
    print("Method 2: Nonlinear (L-BFGS-B)")
    print("-" * 40)
    estimator_nonlinear = ThermalParameterEstimator(time_unit='hour')
    params_nonlinear = estimator_nonlinear.fit(
        T_in=df['T_in'].values,
        T_out=df['T_out'].values,
        Q_in=df['Q_in'].values,
        dt=0.5,
        method='nonlinear',
        initial_guess=(0.01, 1e6)
    )
    print(f"  R_env: {params_nonlinear.R_env:.6f} (RMSE: {params_nonlinear.rmse:.4f})")
    print(f"  C_in:  {params_nonlinear.C_in:.4e} (R²: {params_nonlinear.r_squared:.4f})")
    print()

    # Compare
    print("Comparison:")
    print("-" * 40)
    print(f"  Linear RMSE:     {params_linear.rmse:.4f} °C")
    print(f"  Nonlinear RMSE:  {params_nonlinear.rmse:.4f} °C")
    print(f"  Improvement:     {(params_linear.rmse - params_nonlinear.rmse)/params_linear.rmse*100:.1f}%")
    print()


def demo_validation():
    """Demonstrate train-test validation."""
    print("=" * 80)
    print("DEMO 3: Model Validation (Train-Test Split)")
    print("=" * 80)
    print()

    # Generate longer dataset
    df = generate_synthetic_building_data(
        n_days=14,
        samples_per_hour=1,
        R_env=0.018,
        C_in=4.5e6,
        noise_level=0.25
    )

    # Split into train/test
    split_idx = int(len(df) * 0.7)
    df_train = df.iloc[:split_idx]
    df_test = df.iloc[split_idx:]

    print(f"Total samples: {len(df)}")
    print(f"Training samples: {len(df_train)}")
    print(f"Test samples: {len(df_test)}")
    print()

    # Fit on training data
    print("Fitting on training data...")
    estimator = ThermalParameterEstimator(time_unit='hour')
    estimator.fit(
        T_in=df_train['T_in'].values,
        T_out=df_train['T_out'].values,
        Q_in=df_train['Q_in'].values,
        dt=1.0,
        method='nonlinear'
    )
    print()

    # Validate on test data
    print("Validating on test data...")
    validation = estimator.validate(
        T_in=df_test['T_in'].values,
        T_out=df_test['T_out'].values,
        Q_in=df_test['Q_in'].values,
        dt=1.0
    )

    print(f"\nValidation Results:")
    print(f"  RMSE:      {validation.rmse:.4f} °C")
    print(f"  MAE:       {validation.mae:.4f} °C")
    print(f"  R-squared: {validation.r_squared:.4f}")
    print()

    # Compare train vs test performance
    print("Performance Comparison:")
    print(f"  Training RMSE:   {estimator.parameters.rmse:.4f} °C")
    print(f"  Test RMSE:       {validation.rmse:.4f} °C")
    print(f"  Overfitting:     {(validation.rmse - estimator.parameters.rmse):.4f} °C")
    print()


def demo_diagnostics():
    """Generate comprehensive diagnostic plots."""
    print("=" * 80)
    print("DEMO 4: Diagnostic Visualizations")
    print("=" * 80)
    print()

    # Generate and fit data
    print("Generating data and fitting model...")
    df = generate_synthetic_building_data(
        n_days=7,
        samples_per_hour=1,
        R_env=0.015,
        C_in=5e6,
        noise_level=0.2
    )

    estimator = ThermalParameterEstimator(time_unit='hour')
    estimator.fit(
        T_in=df['T_in'].values,
        T_out=df['T_out'].values,
        Q_in=df['Q_in'].values,
        dt=1.0,
        method='nonlinear'
    )

    # Compute derivative for diagnostics
    dT_in_dt = estimator.compute_temperature_derivative(df['T_in'].values, dt=1.0)

    # Create diagnostics
    print("Generating diagnostic plots...")
    diagnostics = ThermalDiagnostics(estimator)

    # Generate all plots
    diagnostics.plot_fit_diagnostics(
        T_in=df['T_in'].values,
        T_out=df['T_out'].values,
        Q_in=df['Q_in'].values,
        dT_in_dt=dT_in_dt,
        timestamps=np.arange(len(df))
    )

    diagnostics.plot_parameter_uncertainty()

    diagnostics.plot_thermal_response(
        T_in=df['T_in'].values,
        T_out=df['T_out'].values,
        Q_in=df['Q_in'].values,
        dT_in_dt=dT_in_dt,
        timestamps=np.arange(len(df))
    )

    print("Displaying plots...")
    plt.show()
    print()


def demo_sensitivity_analysis():
    """Analyze sensitivity to noise and data quality."""
    print("=" * 80)
    print("DEMO 5: Sensitivity Analysis")
    print("=" * 80)
    print()

    R_env_true = 0.015
    C_in_true = 5e6

    noise_levels = [0.05, 0.1, 0.2, 0.5, 1.0]
    results = []

    print("Testing different noise levels...")
    print()

    for noise in noise_levels:
        # Generate data with varying noise
        df = generate_synthetic_building_data(
            n_days=7,
            samples_per_hour=1,
            R_env=R_env_true,
            C_in=C_in_true,
            noise_level=noise,
            seed=42
        )

        # Fit model
        estimator = ThermalParameterEstimator(time_unit='hour')
        params = estimator.fit(
            T_in=df['T_in'].values,
            T_out=df['T_out'].values,
            Q_in=df['Q_in'].values,
            dt=1.0,
            method='nonlinear'
        )

        # Calculate errors
        R_error = abs(params.R_env - R_env_true) / R_env_true * 100
        C_error = abs(params.C_in - C_in_true) / C_in_true * 100

        results.append({
            'noise': noise,
            'R_env': params.R_env,
            'C_in': params.C_in,
            'R_error': R_error,
            'C_error': C_error,
            'rmse': params.rmse,
            'r_squared': params.r_squared
        })

        print(f"Noise: {noise:.2f} °C")
        print(f"  R_env error: {R_error:.2f}%")
        print(f"  C_in error:  {C_error:.2f}%")
        print(f"  RMSE:        {params.rmse:.4f} °C")
        print(f"  R²:          {params.r_squared:.4f}")
        print()

    # Plot results
    results_df = pd.DataFrame(results)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Sensitivity to Measurement Noise', fontsize=14, fontweight='bold')

    axes[0, 0].plot(results_df['noise'], results_df['R_error'], 'o-', linewidth=2, markersize=8)
    axes[0, 0].set_xlabel('Noise Level (°C)')
    axes[0, 0].set_ylabel('R_env Error (%)')
    axes[0, 0].set_title('R_env Estimation Error')
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].plot(results_df['noise'], results_df['C_error'], 'o-', linewidth=2, markersize=8)
    axes[0, 1].set_xlabel('Noise Level (°C)')
    axes[0, 1].set_ylabel('C_in Error (%)')
    axes[0, 1].set_title('C_in Estimation Error')
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].plot(results_df['noise'], results_df['rmse'], 'o-', linewidth=2, markersize=8)
    axes[1, 0].set_xlabel('Noise Level (°C)')
    axes[1, 0].set_ylabel('RMSE (°C)')
    axes[1, 0].set_title('Model RMSE')
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].plot(results_df['noise'], results_df['r_squared'], 'o-', linewidth=2, markersize=8)
    axes[1, 1].set_xlabel('Noise Level (°C)')
    axes[1, 1].set_ylabel('R²')
    axes[1, 1].set_title('Model R²')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("THERMAL PARAMETER ESTIMATION - COMPREHENSIVE DEMONSTRATION")
    print("=" * 80)
    print("\nThis demo showcases thermal parameter estimation using the formula:")
    print("  T_out - T_in = R_env * (C_in * dT_in/dt - Q_in)")
    print("\nWhere:")
    print("  - R_env: Thermal resistance (building envelope)")
    print("  - C_in: Thermal capacitance (internal mass)")
    print("  - Q_in: Internal heat gains")
    print("\n")

    # Run demos
    try:
        # Demo 1: Basic estimation
        estimator, df = demo_basic_estimation()
        input("\nPress Enter to continue to next demo...")

        # Demo 2: Method comparison
        demo_method_comparison()
        input("\nPress Enter to continue to next demo...")

        # Demo 3: Validation
        demo_validation()
        input("\nPress Enter to continue to next demo...")

        # Demo 4: Diagnostics
        demo_diagnostics()
        input("\nPress Enter to continue to next demo...")

        # Demo 5: Sensitivity
        demo_sensitivity_analysis()

        print("\n" + "=" * 80)
        print("ALL DEMONSTRATIONS COMPLETED")
        print("=" * 80)
        print("\nKey Takeaways:")
        print("  1. Nonlinear optimization typically provides better fits")
        print("  2. Model uncertainty quantification is crucial")
        print("  3. Validation on held-out data prevents overfitting")
        print("  4. Diagnostic plots reveal model assumptions")
        print("  5. Parameter estimates degrade with measurement noise")
        print()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
