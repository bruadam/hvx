"""Diagnostic tools and visualizations for thermal parameter estimation."""


import matplotlib.pyplot as plt
import numpy as np

from .thermal_parameter_estimator import ThermalParameterEstimator


class ThermalDiagnostics:
    """Generate diagnostic plots and statistics for thermal models."""

    def __init__(self, estimator: ThermalParameterEstimator):
        """
        Initialize diagnostics with a fitted estimator.

        Args:
            estimator: Fitted ThermalParameterEstimator instance
        """
        if estimator.parameters is None:
            raise ValueError("Estimator must be fitted before creating diagnostics")

        self.estimator = estimator
        self.parameters = estimator.parameters

    def plot_fit_diagnostics(
        self,
        T_in: np.ndarray,
        T_out: np.ndarray,
        Q_in: np.ndarray,
        dT_in_dt: np.ndarray,
        timestamps: np.ndarray | None = None,
        figsize: tuple[int, int] = (14, 10)
    ):
        """
        Create comprehensive diagnostic plots.

        Args:
            T_in: Indoor temperature
            T_out: Outdoor temperature
            Q_in: Internal heat gains
            dT_in_dt: Temperature derivative
            timestamps: Optional time axis for plotting
            figsize: Figure size
        """
        # Get predictions
        T_out_pred = self.estimator.predict(T_in, dT_in_dt, Q_in)
        residuals = T_out - T_out_pred

        # Create time axis
        if timestamps is None:
            time_axis = np.arange(len(T_in))
            time_label = 'Sample Index'
        else:
            time_axis = timestamps
            time_label = 'Time'

        # Create figure with subplots
        fig, axes = plt.subplots(3, 2, figsize=figsize)
        fig.suptitle('Thermal Parameter Estimation Diagnostics', fontsize=16, fontweight='bold')

        # 1. Actual vs Predicted outdoor temperature
        ax = axes[0, 0]
        ax.plot(time_axis, T_out, label='Actual T_out', alpha=0.7, linewidth=1)
        ax.plot(time_axis, T_out_pred, label='Predicted T_out', alpha=0.7, linewidth=1)
        ax.set_xlabel(time_label)
        ax.set_ylabel('Temperature (°C)')
        ax.set_title('Outdoor Temperature: Actual vs Predicted')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 2. Residuals over time
        ax = axes[0, 1]
        ax.plot(time_axis, residuals, alpha=0.7, linewidth=0.8)
        ax.axhline(0, color='red', linestyle='--', linewidth=1)
        ax.axhline(2*self.parameters.residual_std, color='orange', linestyle=':', linewidth=1, label='±2σ')
        ax.axhline(-2*self.parameters.residual_std, color='orange', linestyle=':', linewidth=1)
        ax.set_xlabel(time_label)
        ax.set_ylabel('Residual (°C)')
        ax.set_title('Residuals Over Time')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 3. Scatter: Actual vs Predicted
        ax = axes[1, 0]
        ax.scatter(T_out_pred, T_out, alpha=0.5, s=10)
        min_val = min(T_out.min(), T_out_pred.min())
        max_val = max(T_out.max(), T_out_pred.max())
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect fit')
        ax.set_xlabel('Predicted T_out (°C)')
        ax.set_ylabel('Actual T_out (°C)')
        ax.set_title(f'Actual vs Predicted (R² = {self.parameters.r_squared:.4f})')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal', adjustable='box')

        # 4. Residual histogram
        ax = axes[1, 1]
        ax.hist(residuals, bins=50, density=True, alpha=0.7, edgecolor='black')

        # Overlay normal distribution
        x_norm = np.linspace(residuals.min(), residuals.max(), 100)
        from scipy.stats import norm
        ax.plot(x_norm, norm.pdf(x_norm, 0, self.parameters.residual_std),
                'r-', linewidth=2, label='Normal(0, σ)')

        ax.set_xlabel('Residual (°C)')
        ax.set_ylabel('Density')
        ax.set_title('Residual Distribution')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 5. Q-Q plot
        ax = axes[2, 0]
        from scipy.stats import probplot
        probplot(residuals, dist="norm", plot=ax)
        ax.set_title('Q-Q Plot (Normality Check)')
        ax.grid(True, alpha=0.3)

        # 6. Autocorrelation of residuals
        ax = axes[2, 1]
        nlags = min(100, len(residuals) // 4)
        ax.acorr(residuals - residuals.mean(), maxlags=nlags, usevlines=True, normed=True, lw=2)
        ax.set_xlabel('Lag')
        ax.set_ylabel('Autocorrelation')
        ax.set_title('Residual Autocorrelation')
        ax.grid(True, alpha=0.3)
        ax.set_ylim([-0.2, 1.0])

        plt.tight_layout()
        return fig

    def plot_parameter_uncertainty(self, figsize: tuple[int, int] = (10, 5)):
        """
        Plot parameter estimates with error bands.

        Args:
            figsize: Figure size
        """
        fig, axes = plt.subplots(1, 2, figsize=figsize)

        params = [
            ('R_env', 'Thermal Resistance', 'K/W'),
            ('C_in', 'Thermal Capacitance', 'J/K')
        ]

        for idx, (param_name, title, unit) in enumerate(params):
            ax = axes[idx]

            estimate = getattr(self.parameters, param_name)
            ci_lower = getattr(self.parameters, f'{param_name}_ci_lower')
            ci_upper = getattr(self.parameters, f'{param_name}_ci_upper')

            # Bar plot with error bars
            ax.bar(0, estimate, width=0.5, color='steelblue', alpha=0.7, label='Estimate')
            ax.errorbar(0, estimate, yerr=[[estimate - ci_lower], [ci_upper - estimate]],
                       fmt='none', ecolor='black', capsize=10, capthick=2, label='95% CI')

            ax.set_xlim(-0.5, 0.5)
            ax.set_xticks([])
            ax.set_ylabel(f'{title} ({unit})')
            ax.set_title(f'{title}\n{estimate:.4e} ± {getattr(self.parameters, param_name + "_std"):.4e}')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        return fig

    def plot_thermal_response(
        self,
        T_in: np.ndarray,
        T_out: np.ndarray,
        Q_in: np.ndarray,
        dT_in_dt: np.ndarray,
        timestamps: np.ndarray | None = None,
        figsize: tuple[int, int] = (14, 8)
    ):
        """
        Plot thermal response components.

        Args:
            T_in: Indoor temperature
            T_out: Outdoor temperature
            Q_in: Internal heat gains
            dT_in_dt: Temperature derivative
            timestamps: Optional time axis
            figsize: Figure size
        """
        # Create time axis
        if timestamps is None:
            time_axis = np.arange(len(T_in))
            time_label = 'Sample Index'
        else:
            time_axis = timestamps
            time_label = 'Time'

        # Calculate components
        R_env = self.parameters.R_env
        C_in = self.parameters.C_in

        thermal_storage = R_env * C_in * dT_in_dt
        heat_gain_effect = -R_env * Q_in
        total_effect = thermal_storage + heat_gain_effect
        actual_diff = T_out - T_in

        fig, axes = plt.subplots(3, 1, figsize=figsize)
        fig.suptitle('Thermal Response Components', fontsize=16, fontweight='bold')

        # 1. Temperature difference components
        ax = axes[0]
        ax.plot(time_axis, thermal_storage, label='R×C×dT/dt (Thermal Storage)', alpha=0.7)
        ax.plot(time_axis, heat_gain_effect, label='-R×Q_in (Heat Gain)', alpha=0.7)
        ax.plot(time_axis, total_effect, label='Total (Model)', alpha=0.7, linewidth=2)
        ax.plot(time_axis, actual_diff, label='T_out - T_in (Actual)', alpha=0.7, linestyle='--', linewidth=2)
        ax.set_xlabel(time_label)
        ax.set_ylabel('Temperature Difference (°C)')
        ax.set_title('Heat Balance Components')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 2. Temperature dynamics
        ax = axes[1]
        ax2 = ax.twinx()
        ax.plot(time_axis, T_in, label='T_in', color='blue', alpha=0.7)
        ax.plot(time_axis, T_out, label='T_out', color='red', alpha=0.7)
        ax2.plot(time_axis, dT_in_dt, label='dT_in/dt', color='green', alpha=0.5, linestyle='--')
        ax.set_xlabel(time_label)
        ax.set_ylabel('Temperature (°C)', color='black')
        ax2.set_ylabel('Temperature Rate (°C/h)', color='green')
        ax.set_title('Temperature Dynamics')
        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        ax2.tick_params(axis='y', labelcolor='green')

        # 3. Internal heat gains
        ax = axes[2]
        ax.plot(time_axis, Q_in, color='orange', alpha=0.7)
        ax.set_xlabel(time_label)
        ax.set_ylabel('Heat Gains (W)')
        ax.set_title('Internal Heat Gains')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def generate_report(
        self,
        T_in: np.ndarray,
        T_out: np.ndarray,
        Q_in: np.ndarray,
        dT_in_dt: np.ndarray,
        timestamps: np.ndarray | None = None,
        save_path: str | None = None
    ):
        """
        Generate a complete diagnostic report.

        Args:
            T_in: Indoor temperature
            T_out: Outdoor temperature
            Q_in: Internal heat gains
            dT_in_dt: Temperature derivative
            timestamps: Optional time axis
            save_path: Optional path to save figures (without extension)
        """
        print("Generating diagnostic report...")

        # Parameter summary
        self.estimator.print_summary()

        # Generate plots
        fig1 = self.plot_fit_diagnostics(T_in, T_out, Q_in, dT_in_dt, timestamps)
        if save_path:
            fig1.savefig(f'{save_path}_diagnostics.png', dpi=150, bbox_inches='tight')

        fig2 = self.plot_parameter_uncertainty()
        if save_path:
            fig2.savefig(f'{save_path}_parameters.png', dpi=150, bbox_inches='tight')

        fig3 = self.plot_thermal_response(T_in, T_out, Q_in, dT_in_dt, timestamps)
        if save_path:
            fig3.savefig(f'{save_path}_response.png', dpi=150, bbox_inches='tight')

        plt.show()

        print("\nDiagnostic report generated successfully!")
        if save_path:
            print(f"Figures saved with prefix: {save_path}")


def example_diagnostics():
    """Example usage of thermal diagnostics."""
    from .thermal_parameter_estimator import ThermalParameterEstimator

    # Generate synthetic data
    np.random.seed(42)
    n_points = 500

    # True parameters
    R_env_true = 0.012
    C_in_true = 6e6

    hours = np.arange(n_points)
    T_out = 10 + 8 * np.sin(2 * np.pi * hours / 24) + np.random.normal(0, 1, n_points)
    Q_in = 1200 + 600 * np.sin(2 * np.pi * hours / 24 - np.pi/4) + np.random.normal(0, 100, n_points)

    T_in = np.zeros(n_points)
    T_in[0] = 20
    dt = 1

    for i in range(1, n_points):
        dT_dt = (Q_in[i-1] - (T_in[i-1] - T_out[i-1]) / R_env_true) / C_in_true
        T_in[i] = T_in[i-1] + dT_dt * dt * 3600

    T_in += np.random.normal(0, 0.15, n_points)

    # Fit model
    estimator = ThermalParameterEstimator(time_unit='hour')
    estimator.fit(T_in=T_in, T_out=T_out, Q_in=Q_in, dt=dt, method='nonlinear')

    # Compute derivative for diagnostics
    dT_in_dt = estimator.compute_temperature_derivative(T_in, dt=dt)

    # Generate diagnostics
    diagnostics = ThermalDiagnostics(estimator)
    diagnostics.generate_report(T_in, T_out, Q_in, dT_in_dt, timestamps=hours)


if __name__ == '__main__':
    example_diagnostics()
