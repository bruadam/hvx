"""Thermal parameter estimation using heat transfer equations.

This module implements parameter estimation for building thermal models based on:
    T_out - T_in = R_env * (C_in * dT_in/dt - Q_in)

Where:
    - T_out: Outdoor temperature (°C)
    - T_in: Indoor temperature (°C)
    - R_env: Thermal resistance (K/W or °C/W)
    - C_in: Thermal capacitance (J/K or Wh/K)
    - dT_in/dt: Rate of change of indoor temperature (°C/h or K/s)
    - Q_in: Internal heat gains (W)
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import minimize
from scipy.stats import t as t_dist


@dataclass
class ThermalParameters:
    """Estimated thermal parameters with uncertainty."""

    R_env: float  # Thermal resistance (K/W)
    C_in: float  # Thermal capacitance (J/K or Wh/K)
    R_env_std: float  # Standard error of R_env
    C_in_std: float  # Standard error of C_in
    R_env_ci_lower: float  # Lower bound of 95% confidence interval
    R_env_ci_upper: float  # Upper bound of 95% confidence interval
    C_in_ci_lower: float  # Lower bound of 95% confidence interval
    C_in_ci_upper: float  # Upper bound of 95% confidence interval
    rmse: float  # Root mean square error
    r_squared: float  # Coefficient of determination
    residual_std: float  # Standard deviation of residuals
    n_samples: int  # Number of data points used


@dataclass
class ValidationMetrics:
    """Model validation metrics."""

    rmse: float
    mae: float  # Mean absolute error
    r_squared: float
    residuals: np.ndarray
    predictions: np.ndarray


class ThermalParameterEstimator:
    """Estimate thermal parameters from temperature and heat flow data."""

    def __init__(self, time_unit: str = 'hour'):
        """
        Initialize the estimator.

        Args:
            time_unit: Time unit for derivatives ('hour' or 'second')
        """
        self.time_unit = time_unit
        self.parameters: ThermalParameters | None = None

    def compute_temperature_derivative(
        self,
        T_in: np.ndarray,
        timestamps: np.ndarray | None = None,
        dt: float | None = None
    ) -> np.ndarray:
        """
        Compute the time derivative of indoor temperature.

        Args:
            T_in: Indoor temperature time series
            timestamps: Unix timestamps or datetime index (optional)
            dt: Time step in hours/seconds (if timestamps not provided)

        Returns:
            dT_in/dt array (same length as T_in, padded at edges)
        """
        if timestamps is not None:
            # Calculate time differences
            dt_array = np.diff(timestamps)
            if self.time_unit == 'hour':
                dt_array = dt_array / 3600  # Convert seconds to hours
        elif dt is not None:
            dt_array = np.full(len(T_in) - 1, dt)
        else:
            raise ValueError("Either timestamps or dt must be provided")

        # Central difference for interior points
        dT_dt = np.zeros_like(T_in)
        dT_dt[1:-1] = (T_in[2:] - T_in[:-2]) / (dt_array[1:] + dt_array[:-1])

        # Forward/backward difference for edges
        dT_dt[0] = (T_in[1] - T_in[0]) / dt_array[0]
        dT_dt[-1] = (T_in[-1] - T_in[-2]) / dt_array[-1]

        return dT_dt

    def fit(
        self,
        T_in: np.ndarray,
        T_out: np.ndarray,
        Q_in: np.ndarray,
        dT_in_dt: np.ndarray | None = None,
        timestamps: np.ndarray | None = None,
        dt: float | None = None,
        initial_guess: tuple[float, float] | None = None,
        method: str = 'nonlinear'
    ) -> ThermalParameters:
        """
        Fit thermal parameters to data.

        Args:
            T_in: Indoor temperature array (°C)
            T_out: Outdoor temperature array (°C)
            Q_in: Internal heat gains array (W)
            dT_in_dt: Pre-computed temperature derivative (optional)
            timestamps: Time stamps for computing derivatives (optional)
            dt: Time step if timestamps not provided
            initial_guess: (R_env, C_in) initial values
            method: 'linear' or 'nonlinear' optimization

        Returns:
            ThermalParameters object with estimates and uncertainties
        """
        # Compute derivative if not provided
        if dT_in_dt is None:
            dT_in_dt = self.compute_temperature_derivative(T_in, timestamps, dt)

        # Remove any NaN or infinite values
        mask = np.isfinite(T_in) & np.isfinite(T_out) & np.isfinite(Q_in) & np.isfinite(dT_in_dt)
        T_in = T_in[mask]
        T_out = T_out[mask]
        Q_in = Q_in[mask]
        dT_in_dt = dT_in_dt[mask]

        n_samples = len(T_in)

        if method == 'linear':
            params, uncertainties = self._fit_linear(T_in, T_out, Q_in, dT_in_dt)
        else:
            params, uncertainties = self._fit_nonlinear(
                T_in, T_out, Q_in, dT_in_dt, initial_guess
            )

        R_env, C_in = params
        R_env_std, C_in_std = uncertainties

        # Calculate predictions and residuals
        predictions = self._predict(T_in, dT_in_dt, Q_in, R_env, C_in)
        residuals = (T_out - T_in) - predictions
        rmse = np.sqrt(np.mean(residuals**2))
        residual_std = np.std(residuals)

        # R-squared
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum(((T_out - T_in) - np.mean(T_out - T_in))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # 95% confidence intervals (t-distribution)
        alpha = 0.05
        df = n_samples - 2  # degrees of freedom
        t_val = t_dist.ppf(1 - alpha/2, df)

        R_env_ci = (R_env - t_val * R_env_std, R_env + t_val * R_env_std)
        C_in_ci = (C_in - t_val * C_in_std, C_in + t_val * C_in_std)

        self.parameters = ThermalParameters(
            R_env=R_env,
            C_in=C_in,
            R_env_std=R_env_std,
            C_in_std=C_in_std,
            R_env_ci_lower=R_env_ci[0],
            R_env_ci_upper=R_env_ci[1],
            C_in_ci_lower=C_in_ci[0],
            C_in_ci_upper=C_in_ci[1],
            rmse=rmse,
            r_squared=r_squared,
            residual_std=residual_std,
            n_samples=n_samples
        )

        return self.parameters

    def _fit_linear(
        self,
        T_in: np.ndarray,
        T_out: np.ndarray,
        Q_in: np.ndarray,
        dT_in_dt: np.ndarray
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        """
        Linear least squares fitting.

        Rearranges to: (T_out - T_in) / (C_in * dT_in/dt - Q_in) = R_env
        This is challenging due to the product R_env * C_in.

        We use a two-step approach:
        1. Grid search over C_in
        2. Linear fit for R_env given C_in
        """
        # Grid search over reasonable C_in values (Wh/K)
        C_in_range = np.logspace(3, 7, 100)  # 1e3 to 1e7 J/K
        best_rmse = np.inf
        best_params = (0.0, 0.0)

        for C_in_test in C_in_range:
            # Given C_in, solve for R_env
            X = (C_in_test * dT_in_dt - Q_in).reshape(-1, 1)
            y = (T_out - T_in)

            # Least squares: y = R_env * X
            if np.sum(X**2) > 0:
                R_env_test = np.sum(X.flatten() * y) / np.sum(X**2)

                # Calculate RMSE
                predictions = R_env_test * X.flatten()
                rmse = np.sqrt(np.mean((y - predictions)**2))

                if rmse < best_rmse:
                    best_rmse = rmse
                    best_params = (R_env_test, C_in_test)

        R_env, C_in = best_params

        # Estimate uncertainties via bootstrap or analytical approximation
        X = (C_in * dT_in_dt - Q_in)
        residuals = (T_out - T_in) - R_env * X
        residual_var = np.var(residuals)

        # Variance of R_env estimate
        R_env_var = residual_var / np.sum(X**2) if np.sum(X**2) > 0 else 0
        R_env_std = np.sqrt(R_env_var)

        # C_in uncertainty from grid search resolution
        C_in_std = (C_in_range[1] - C_in_range[0]) / 2

        return (R_env, C_in), (R_env_std, C_in_std)

    def _fit_nonlinear(
        self,
        T_in: np.ndarray,
        T_out: np.ndarray,
        Q_in: np.ndarray,
        dT_in_dt: np.ndarray,
        initial_guess: tuple[float, float] | None = None
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        """
        Nonlinear optimization to fit both R_env and C_in.

        Minimizes: sum((T_out - T_in - R_env * (C_in * dT_in/dt - Q_in))^2)
        """
        if initial_guess is None:
            # Reasonable defaults for a building
            initial_guess = (0.01, 1e6)  # R_env=0.01 K/W, C_in=1e6 J/K

        def objective(params):
            R_env, C_in = params
            predictions = R_env * (C_in * dT_in_dt - Q_in)
            residuals = (T_out - T_in) - predictions
            return np.sum(residuals**2)

        # Bounds to ensure physical validity
        bounds = [(1e-6, 1.0), (1e3, 1e8)]  # R_env: 1µK/W to 1 K/W, C_in: 1e3 to 1e8 J/K

        result = minimize(objective, initial_guess, bounds=bounds, method='L-BFGS-B')

        if not result.success:
            print(f"Warning: Optimization did not converge. Message: {result.message}")

        R_env, C_in = result.x

        # Estimate covariance matrix using Hessian approximation
        # Jacobian matrix
        epsilon = 1e-8
        n = len(T_in)

        def residuals_func(params):
            R_env, C_in = params
            predictions = R_env * (C_in * dT_in_dt - Q_in)
            return (T_out - T_in) - predictions

        residuals = residuals_func(result.x)
        residual_var = np.var(residuals)

        # Numerical Jacobian
        J = np.zeros((n, 2))
        for i in range(2):
            params_plus = result.x.copy()
            params_plus[i] += epsilon
            res_plus = residuals_func(params_plus)
            J[:, i] = (residuals - res_plus) / epsilon

        # Covariance matrix: (J^T J)^-1 * sigma^2
        try:
            JTJ = J.T @ J
            cov_matrix = np.linalg.inv(JTJ) * residual_var
            R_env_std = np.sqrt(cov_matrix[0, 0])
            C_in_std = np.sqrt(cov_matrix[1, 1])
        except np.linalg.LinAlgError:
            # Singular matrix, use conservative estimates
            R_env_std = R_env * 0.1
            C_in_std = C_in * 0.1

        return (R_env, C_in), (R_env_std, C_in_std)

    def _predict(
        self,
        T_in: np.ndarray,
        dT_in_dt: np.ndarray,
        Q_in: np.ndarray,
        R_env: float,
        C_in: float
    ) -> np.ndarray:
        """
        Predict temperature difference using the model.

        Returns:
            Predicted (T_out - T_in)
        """
        return R_env * (C_in * dT_in_dt - Q_in)

    def predict(
        self,
        T_in: np.ndarray,
        dT_in_dt: np.ndarray,
        Q_in: np.ndarray
    ) -> np.ndarray:
        """
        Predict outdoor temperature using fitted parameters.

        Returns:
            Predicted T_out
        """
        if self.parameters is None:
            raise ValueError("Model must be fitted before prediction")

        temp_diff = self._predict(
            T_in, dT_in_dt, Q_in,
            self.parameters.R_env,
            self.parameters.C_in
        )
        return T_in + temp_diff

    def validate(
        self,
        T_in: np.ndarray,
        T_out: np.ndarray,
        Q_in: np.ndarray,
        dT_in_dt: np.ndarray | None = None,
        timestamps: np.ndarray | None = None,
        dt: float | None = None
    ) -> ValidationMetrics:
        """
        Validate the fitted model on new data.

        Returns:
            ValidationMetrics with performance measures
        """
        if self.parameters is None:
            raise ValueError("Model must be fitted before validation")

        if dT_in_dt is None:
            dT_in_dt = self.compute_temperature_derivative(T_in, timestamps, dt)

        predictions = self.predict(T_in, dT_in_dt, Q_in)
        residuals = T_out - predictions

        rmse = np.sqrt(np.mean(residuals**2))
        mae = np.mean(np.abs(residuals))

        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((T_out - np.mean(T_out))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        return ValidationMetrics(
            rmse=rmse,
            mae=mae,
            r_squared=r_squared,
            residuals=residuals,
            predictions=predictions
        )

    def get_summary(self) -> dict[str, Any]:
        """
        Get a summary of the fitted parameters and statistics.

        Returns:
            Dictionary with parameter estimates and statistics
        """
        if self.parameters is None:
            raise ValueError("Model must be fitted before getting summary")

        p = self.parameters

        return {
            'Thermal Resistance (R_env)': {
                'estimate': p.R_env,
                'std_error': p.R_env_std,
                'ci_95': (p.R_env_ci_lower, p.R_env_ci_upper),
                'unit': 'K/W'
            },
            'Thermal Capacitance (C_in)': {
                'estimate': p.C_in,
                'std_error': p.C_in_std,
                'ci_95': (p.C_in_ci_lower, p.C_in_ci_upper),
                'unit': 'J/K (or Wh/K if hourly data)'
            },
            'Model Fit': {
                'RMSE': p.rmse,
                'R-squared': p.r_squared,
                'Residual Std': p.residual_std,
                'N Samples': p.n_samples
            }
        }

    def print_summary(self):
        """Print a formatted summary of the estimation results."""
        if self.parameters is None:
            print("Model has not been fitted yet.")
            return

        summary = self.get_summary()

        print("=" * 70)
        print("THERMAL PARAMETER ESTIMATION RESULTS")
        print("=" * 70)
        print()

        for param_name, stats in summary.items():
            if param_name == 'Model Fit':
                print(f"\n{param_name}:")
                print("-" * 40)
                for metric, value in stats.items():
                    print(f"  {metric:20s}: {value:12.4f}")
            else:
                print(f"\n{param_name}:")
                print("-" * 40)
                estimate = stats['estimate']
                std_err = stats['std_error']
                ci_lower, ci_upper = stats['ci_95']
                unit = stats['unit']

                print(f"  Estimate:     {estimate:12.4e} {unit}")
                print(f"  Std Error:    {std_err:12.4e} {unit}")
                print(f"  95% CI:       [{ci_lower:12.4e}, {ci_upper:12.4e}] {unit}")
                print(f"  Rel. Error:   {100 * std_err / estimate:12.2f} %")

        print("\n" + "=" * 70)


def example_usage():
    """Example usage of the thermal parameter estimator."""
    # Generate synthetic data
    np.random.seed(42)
    n_points = 1000

    # True parameters
    R_env_true = 0.015  # K/W
    C_in_true = 5e6  # J/K

    # Time series (hourly data)
    hours = np.arange(n_points)

    # Outdoor temperature with diurnal variation
    T_out = 10 + 8 * np.sin(2 * np.pi * hours / 24) + np.random.normal(0, 1, n_points)

    # Internal heat gains (varying with occupancy patterns)
    Q_in = 1000 + 500 * np.sin(2 * np.pi * hours / 24 - np.pi/4) + np.random.normal(0, 100, n_points)

    # Simulate indoor temperature using the heat equation
    T_in = np.zeros(n_points)
    T_in[0] = 20  # Initial condition
    dt = 1  # hour

    for i in range(1, n_points):
        # dT_in/dt = (Q_in - (T_in - T_out) / R_env) / C_in
        dT_dt = (Q_in[i-1] - (T_in[i-1] - T_out[i-1]) / R_env_true) / C_in_true
        T_in[i] = T_in[i-1] + dT_dt * dt * 3600  # Convert hours to seconds

    # Add measurement noise
    T_in += np.random.normal(0, 0.1, n_points)

    # Fit the model
    estimator = ThermalParameterEstimator(time_unit='hour')
    estimator.fit(
        T_in=T_in,
        T_out=T_out,
        Q_in=Q_in,
        dt=dt,
        method='nonlinear',
        initial_guess=(0.01, 1e6)
    )

    # Print results
    estimator.print_summary()

    print("\nTrue values:")
    print(f"  R_env: {R_env_true:.6f} K/W")
    print(f"  C_in:  {C_in_true:.4e} J/K")

    # Validate on same data (for demonstration)
    validation = estimator.validate(T_in, T_out, Q_in, dt=dt)
    print("\nValidation Metrics:")
    print(f"  RMSE: {validation.rmse:.4f} °C")
    print(f"  MAE:  {validation.mae:.4f} °C")
    print(f"  R²:   {validation.r_squared:.4f}")


if __name__ == '__main__':
    example_usage()
