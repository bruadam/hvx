"""Building performance evaluation and retrofit recommendation system.

This module evaluates building thermal performance using estimated R_env and C_in,
integrates energy consumption data, and generates specific recommendations for:
- Insulation improvements
- Solar shading
- HVAC system upgrades
- Renewable energy integration
- Ventilation optimization
"""

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd

from .thermal_parameter_estimator import ThermalParameterEstimator, ThermalParameters


class BuildingType(Enum):
    """Building type classifications."""
    RESIDENTIAL_DETACHED = "residential_detached"
    RESIDENTIAL_APARTMENT = "residential_apartment"
    OFFICE_SMALL = "office_small"
    OFFICE_LARGE = "office_large"
    SCHOOL = "school"
    RETAIL = "retail"
    WAREHOUSE = "warehouse"
    HEALTHCARE = "healthcare"


class InterventionType(Enum):
    """Types of building interventions."""
    INSULATION_WALLS = "insulation_walls"
    INSULATION_ROOF = "insulation_roof"
    INSULATION_FLOOR = "insulation_floor"
    WINDOWS_UPGRADE = "windows_upgrade"
    SOLAR_SHADING_EXTERNAL = "solar_shading_external"
    SOLAR_SHADING_INTERNAL = "solar_shading_internal"
    HVAC_UPGRADE = "hvac_upgrade"
    HEAT_PUMP = "heat_pump"
    SOLAR_PV = "solar_pv"
    VENTILATION_HRV = "ventilation_hrv"
    THERMAL_MASS = "thermal_mass"
    AIR_SEALING = "air_sealing"


@dataclass
class ThermalBenchmark:
    """Benchmark values for thermal parameters by building type."""

    building_type: BuildingType

    # Thermal resistance (K/W per m²) - specific values
    R_env_excellent: float  # Well-insulated modern building
    R_env_good: float       # Above average
    R_env_average: float    # Typical existing building
    R_env_poor: float       # Poorly insulated

    # Thermal capacitance (J/K per m²)
    C_in_heavy: float       # Heavy construction (concrete, brick)
    C_in_medium: float      # Medium construction
    C_in_light: float       # Light construction (wood frame)

    # Heating/cooling efficiency benchmarks (COP)
    heating_cop_excellent: float
    heating_cop_good: float
    heating_cop_poor: float


# Standard benchmarks based on building physics literature
THERMAL_BENCHMARKS = {
    BuildingType.RESIDENTIAL_DETACHED: ThermalBenchmark(
        building_type=BuildingType.RESIDENTIAL_DETACHED,
        R_env_excellent=0.025,  # Well-insulated modern home
        R_env_good=0.015,
        R_env_average=0.010,
        R_env_poor=0.005,
        C_in_heavy=150000,      # Per m² floor area
        C_in_medium=80000,
        C_in_light=40000,
        heating_cop_excellent=4.0,  # Heat pump
        heating_cop_good=0.95,      # Condensing boiler
        heating_cop_poor=0.75       # Old boiler
    ),
    BuildingType.OFFICE_SMALL: ThermalBenchmark(
        building_type=BuildingType.OFFICE_SMALL,
        R_env_excellent=0.020,
        R_env_good=0.012,
        R_env_average=0.008,
        R_env_poor=0.004,
        C_in_heavy=200000,
        C_in_medium=100000,
        C_in_light=50000,
        heating_cop_excellent=4.5,
        heating_cop_good=0.92,
        heating_cop_poor=0.70
    ),
    # Add more building types as needed
}


@dataclass
class Intervention:
    """Recommended building intervention."""

    intervention_type: InterventionType
    priority: int  # 1 (highest) to 5 (lowest)
    description: str
    estimated_cost_per_m2: float  # €/m² or $/m²
    estimated_savings_percent: float  # % reduction in energy use
    estimated_r_env_improvement: float  # Improvement in K/W
    payback_years: float
    co2_reduction_kg_per_year: float
    additional_benefits: list[str] = field(default_factory=list)


@dataclass
class BuildingPerformanceReport:
    """Comprehensive building performance evaluation report."""

    # Thermal parameters
    thermal_params: ThermalParameters

    # Benchmarking
    building_type: BuildingType
    floor_area_m2: float
    r_env_per_m2: float
    c_in_per_m2: float
    r_env_rating: str  # "Excellent", "Good", "Average", "Poor"
    c_in_rating: str   # "Heavy", "Medium", "Light"

    # Energy consumption
    annual_heating_kwh: float
    annual_electricity_kwh: float
    annual_energy_cost: float
    heating_cop_estimated: float

    # Performance metrics
    heat_loss_coefficient: float  # W/K (total building)
    specific_heat_loss: float     # W/(K·m²)
    annual_heat_loss_kwh: float

    # Climate data
    avg_indoor_temp: float
    avg_outdoor_temp: float
    heating_degree_days: float
    cooling_degree_days: float

    # Recommendations
    interventions: list[Intervention]
    total_savings_potential_percent: float
    total_savings_potential_kwh: float
    total_savings_potential_cost: float

    # Sustainability
    current_co2_kg_per_year: float
    potential_co2_reduction_kg_per_year: float
    renewable_energy_potential: dict[str, float]


class BuildingPerformanceEvaluator:
    """Evaluate building performance and generate improvement recommendations."""

    def __init__(
        self,
        building_type: BuildingType,
        floor_area_m2: float,
        energy_cost_per_kwh: float = 0.15,  # €/kWh or $/kWh
        co2_per_kwh_heating: float = 0.25,   # kg CO2/kWh (district heating typical)
        co2_per_kwh_electricity: float = 0.40  # kg CO2/kWh (grid mix)
    ):
        """
        Initialize the evaluator.

        Args:
            building_type: Type of building
            floor_area_m2: Total floor area in m²
            energy_cost_per_kwh: Energy cost
            co2_per_kwh_heating: CO2 emissions factor for heating
            co2_per_kwh_electricity: CO2 emissions factor for electricity
        """
        self.building_type = building_type
        self.floor_area_m2 = floor_area_m2
        self.energy_cost_per_kwh = energy_cost_per_kwh
        self.co2_per_kwh_heating = co2_per_kwh_heating
        self.co2_per_kwh_electricity = co2_per_kwh_electricity

        # Get benchmarks
        self.benchmark = THERMAL_BENCHMARKS.get(
            building_type,
            THERMAL_BENCHMARKS[BuildingType.RESIDENTIAL_DETACHED]  # Default
        )

        self.estimator: ThermalParameterEstimator | None = None
        self.thermal_params: ThermalParameters | None = None

    def estimate_thermal_parameters(
        self,
        T_in: np.ndarray,
        T_out: np.ndarray,
        heating_power: np.ndarray,  # Heating system power (W)
        electricity_power: np.ndarray,  # Electrical power (W)
        solar_gains: np.ndarray | None = None,
        dt: float = 1.0,
        method: str = 'nonlinear'
    ) -> ThermalParameters:
        """
        Estimate thermal parameters from building data.

        Args:
            T_in: Indoor temperature time series (°C)
            T_out: Outdoor temperature time series (°C)
            heating_power: District heating or boiler power (W)
            electricity_power: Electrical consumption (W)
            solar_gains: Estimated solar gains (W), optional
            dt: Time step (hours)
            method: Estimation method

        Returns:
            ThermalParameters with estimates
        """
        # Calculate total internal heat gains
        # Q_in = heating delivered + electricity (portion that becomes heat) + solar

        # Assume 80% of electricity becomes heat (conservative)
        electricity_heat_fraction = 0.80

        Q_in = heating_power + (electricity_power * electricity_heat_fraction)

        if solar_gains is not None:
            Q_in = Q_in + solar_gains

        # Estimate parameters
        self.estimator = ThermalParameterEstimator(time_unit='hour')
        self.thermal_params = self.estimator.fit(
            T_in=T_in,
            T_out=T_out,
            Q_in=Q_in,
            dt=dt,
            method=method
        )

        return self.thermal_params

    def evaluate_performance(
        self,
        thermal_params: ThermalParameters,
        T_in: np.ndarray,
        T_out: np.ndarray,
        heating_energy_kwh: float,  # Annual heating consumption
        electricity_kwh: float,      # Annual electricity consumption
        timestamps: pd.DatetimeIndex | None = None
    ) -> BuildingPerformanceReport:
        """
        Evaluate building performance and generate recommendations.

        Args:
            thermal_params: Estimated thermal parameters
            T_in: Indoor temperature time series
            T_out: Outdoor temperature time series
            heating_energy_kwh: Annual heating energy consumption
            electricity_kwh: Annual electricity consumption
            timestamps: Timestamps for climate analysis

        Returns:
            BuildingPerformanceReport with findings and recommendations
        """
        self.thermal_params = thermal_params

        # Normalize by floor area
        r_env_per_m2 = thermal_params.R_env * self.floor_area_m2
        c_in_per_m2 = thermal_params.C_in / self.floor_area_m2

        # Rate thermal performance
        r_env_rating = self._rate_thermal_resistance(r_env_per_m2)
        c_in_rating = self._rate_thermal_mass(c_in_per_m2)

        # Calculate heat loss metrics
        heat_loss_coefficient = 1.0 / thermal_params.R_env  # W/K
        specific_heat_loss = heat_loss_coefficient / self.floor_area_m2  # W/(K·m²)

        # Climate metrics
        avg_indoor_temp = np.mean(T_in)
        avg_outdoor_temp = np.mean(T_out)

        if timestamps is not None:
            hdd, cdd = self._calculate_degree_days(T_in, T_out, timestamps)
        else:
            hdd = max(0, (18 - avg_outdoor_temp) * 365)  # Estimate
            cdd = max(0, (avg_outdoor_temp - 22) * 365)

        # Estimate heating system efficiency
        theoretical_heat_loss = heat_loss_coefficient * (avg_indoor_temp - avg_outdoor_temp) * 8760  # W·h/year
        theoretical_heat_loss_kwh = theoretical_heat_loss / 1000

        if theoretical_heat_loss_kwh > 0:
            heating_cop = theoretical_heat_loss_kwh / heating_energy_kwh
            heating_cop = np.clip(heating_cop, 0.4, 5.0)  # Reasonable bounds
        else:
            heating_cop = 0.85  # Default assumption

        # Energy costs
        annual_energy_cost = (heating_energy_kwh + electricity_kwh) * self.energy_cost_per_kwh

        # CO2 emissions
        current_co2 = (
            heating_energy_kwh * self.co2_per_kwh_heating +
            electricity_kwh * self.co2_per_kwh_electricity
        )

        # Generate recommendations
        interventions = self._generate_interventions(
            r_env_rating,
            c_in_rating,
            heating_cop,
            heating_energy_kwh,
            electricity_kwh,
            avg_indoor_temp,
            avg_outdoor_temp
        )

        # Calculate savings potential
        total_savings_percent = sum(i.estimated_savings_percent for i in interventions[:3])  # Top 3
        total_savings_kwh = (heating_energy_kwh + electricity_kwh) * total_savings_percent / 100
        total_savings_cost = total_savings_kwh * self.energy_cost_per_kwh
        potential_co2_reduction = sum(i.co2_reduction_kg_per_year for i in interventions[:3])

        # Renewable energy potential
        renewable_potential = self._estimate_renewable_potential(
            self.floor_area_m2,
            electricity_kwh
        )

        return BuildingPerformanceReport(
            thermal_params=thermal_params,
            building_type=self.building_type,
            floor_area_m2=self.floor_area_m2,
            r_env_per_m2=r_env_per_m2,
            c_in_per_m2=c_in_per_m2,
            r_env_rating=r_env_rating,
            c_in_rating=c_in_rating,
            annual_heating_kwh=heating_energy_kwh,
            annual_electricity_kwh=electricity_kwh,
            annual_energy_cost=annual_energy_cost,
            heating_cop_estimated=heating_cop,
            heat_loss_coefficient=heat_loss_coefficient,
            specific_heat_loss=specific_heat_loss,
            annual_heat_loss_kwh=theoretical_heat_loss_kwh,
            avg_indoor_temp=avg_indoor_temp,
            avg_outdoor_temp=avg_outdoor_temp,
            heating_degree_days=hdd,
            cooling_degree_days=cdd,
            interventions=interventions,
            total_savings_potential_percent=total_savings_percent,
            total_savings_potential_kwh=total_savings_kwh,
            total_savings_potential_cost=total_savings_cost,
            current_co2_kg_per_year=current_co2,
            potential_co2_reduction_kg_per_year=potential_co2_reduction,
            renewable_energy_potential=renewable_potential
        )

    def _rate_thermal_resistance(self, r_env_per_m2: float) -> str:
        """Rate thermal resistance quality."""
        if r_env_per_m2 >= self.benchmark.R_env_excellent:
            return "Excellent"
        elif r_env_per_m2 >= self.benchmark.R_env_good:
            return "Good"
        elif r_env_per_m2 >= self.benchmark.R_env_average:
            return "Average"
        else:
            return "Poor"

    def _rate_thermal_mass(self, c_in_per_m2: float) -> str:
        """Rate thermal mass."""
        if c_in_per_m2 >= self.benchmark.C_in_heavy:
            return "Heavy"
        elif c_in_per_m2 >= self.benchmark.C_in_medium:
            return "Medium"
        else:
            return "Light"

    def _calculate_degree_days(
        self,
        T_in: np.ndarray,
        T_out: np.ndarray,
        timestamps: pd.DatetimeIndex
    ) -> tuple[float, float]:
        """Calculate heating and cooling degree days."""
        df = pd.DataFrame({'T_out': T_out}, index=timestamps)
        daily_temps = df.resample('D').mean()

        hdd = np.maximum(18 - daily_temps['T_out'], 0).sum()
        cdd = np.maximum(daily_temps['T_out'] - 22, 0).sum()

        return hdd, cdd

    def _generate_interventions(
        self,
        r_env_rating: str,
        c_in_rating: str,
        heating_cop: float,
        heating_kwh: float,
        electricity_kwh: float,
        avg_t_in: float,
        avg_t_out: float
    ) -> list[Intervention]:
        """Generate prioritized intervention recommendations."""
        interventions = []

        # 1. Insulation improvements (if poor R_env)
        if r_env_rating in ["Poor", "Average"]:
            if r_env_rating == "Poor":
                savings_percent = 35
                r_improvement = 0.010
                cost_per_m2 = 80
                priority = 1
            else:
                savings_percent = 20
                r_improvement = 0.005
                cost_per_m2 = 60
                priority = 2

            co2_reduction = heating_kwh * (savings_percent / 100) * self.co2_per_kwh_heating
            annual_savings = (heating_kwh * savings_percent / 100) * self.energy_cost_per_kwh
            total_cost = cost_per_m2 * self.floor_area_m2
            payback = total_cost / annual_savings if annual_savings > 0 else 999

            interventions.append(Intervention(
                intervention_type=InterventionType.INSULATION_WALLS,
                priority=priority,
                description=f"Improve wall and roof insulation to reduce heat loss. "
                           f"Current thermal resistance is {r_env_rating.lower()}.",
                estimated_cost_per_m2=cost_per_m2,
                estimated_savings_percent=savings_percent,
                estimated_r_env_improvement=r_improvement,
                payback_years=payback,
                co2_reduction_kg_per_year=co2_reduction,
                additional_benefits=[
                    "Improved thermal comfort",
                    "Reduced temperature fluctuations",
                    "Lower peak heating demand",
                    "Increased property value"
                ]
            ))

        # 2. Window upgrades (if poor insulation)
        if r_env_rating in ["Poor", "Average"]:
            savings_percent = 15
            cost_per_m2 = 120  # Windows are expensive
            co2_reduction = heating_kwh * (savings_percent / 100) * self.co2_per_kwh_heating
            annual_savings = (heating_kwh * savings_percent / 100) * self.energy_cost_per_kwh
            total_cost = cost_per_m2 * self.floor_area_m2 * 0.2  # ~20% of floor area
            payback = total_cost / annual_savings if annual_savings > 0 else 999

            interventions.append(Intervention(
                intervention_type=InterventionType.WINDOWS_UPGRADE,
                priority=2,
                description="Upgrade to triple-glazed low-E windows to reduce heat loss.",
                estimated_cost_per_m2=cost_per_m2 * 0.2,
                estimated_savings_percent=savings_percent,
                estimated_r_env_improvement=0.003,
                payback_years=payback,
                co2_reduction_kg_per_year=co2_reduction,
                additional_benefits=[
                    "Reduced drafts and cold spots",
                    "Better noise insulation",
                    "Reduced condensation"
                ]
            ))

        # 3. HVAC efficiency upgrade (if poor COP)
        if heating_cop < self.benchmark.heating_cop_good:
            savings_percent = 25
            cost_per_m2 = 50
            co2_reduction = heating_kwh * (savings_percent / 100) * self.co2_per_kwh_heating
            annual_savings = (heating_kwh * savings_percent / 100) * self.energy_cost_per_kwh
            total_cost = cost_per_m2 * self.floor_area_m2
            payback = total_cost / annual_savings if annual_savings > 0 else 999

            interventions.append(Intervention(
                intervention_type=InterventionType.HVAC_UPGRADE,
                priority=1,
                description=f"Upgrade heating system. Current efficiency (COP: {heating_cop:.2f}) "
                           f"is below recommended ({self.benchmark.heating_cop_good:.2f}).",
                estimated_cost_per_m2=cost_per_m2,
                estimated_savings_percent=savings_percent,
                estimated_r_env_improvement=0.0,
                payback_years=payback,
                co2_reduction_kg_per_year=co2_reduction,
                additional_benefits=[
                    "More consistent temperatures",
                    "Lower maintenance costs",
                    "Smart control capabilities"
                ]
            ))

        # 4. Heat pump installation (always worth considering)
        if heating_cop < 3.0:  # Not already a heat pump
            savings_percent = 45
            cost_per_m2 = 100
            co2_reduction = heating_kwh * (savings_percent / 100) * self.co2_per_kwh_heating * 1.5
            annual_savings = (heating_kwh * savings_percent / 100) * self.energy_cost_per_kwh
            total_cost = cost_per_m2 * self.floor_area_m2
            payback = total_cost / annual_savings if annual_savings > 0 else 999

            interventions.append(Intervention(
                intervention_type=InterventionType.HEAT_PUMP,
                priority=2,
                description="Install air-source or ground-source heat pump system.",
                estimated_cost_per_m2=cost_per_m2,
                estimated_savings_percent=savings_percent,
                estimated_r_env_improvement=0.0,
                payback_years=payback,
                co2_reduction_kg_per_year=co2_reduction,
                additional_benefits=[
                    "Renewable heating source",
                    "Cooling capability in summer",
                    "Very low carbon emissions",
                    "Government incentives may apply"
                ]
            ))

        # 5. Solar shading (if overheating risk - high indoor temp)
        if avg_t_in > 24:
            savings_percent = 10
            cost_per_m2 = 30
            co2_reduction = electricity_kwh * (savings_percent / 100) * self.co2_per_kwh_electricity
            annual_savings = (electricity_kwh * savings_percent / 100) * self.energy_cost_per_kwh
            total_cost = cost_per_m2 * self.floor_area_m2 * 0.3  # Windows only
            payback = total_cost / annual_savings if annual_savings > 0 else 999

            interventions.append(Intervention(
                intervention_type=InterventionType.SOLAR_SHADING_EXTERNAL,
                priority=3,
                description="Install external solar shading (blinds, awnings) to reduce cooling load.",
                estimated_cost_per_m2=cost_per_m2 * 0.3,
                estimated_savings_percent=savings_percent,
                estimated_r_env_improvement=0.0,
                payback_years=payback,
                co2_reduction_kg_per_year=co2_reduction,
                additional_benefits=[
                    "Reduced overheating",
                    "Better visual comfort",
                    "Lower cooling energy"
                ]
            ))

        # 6. Solar PV
        pv_potential_kwh = self.floor_area_m2 * 100  # ~100 kWh/m²/year
        if pv_potential_kwh > electricity_kwh * 0.3:  # Can offset >30% of electricity
            savings_percent = min(pv_potential_kwh / electricity_kwh * 100, 80)
            cost_per_m2 = 150
            co2_reduction = pv_potential_kwh * self.co2_per_kwh_electricity
            annual_savings = pv_potential_kwh * self.energy_cost_per_kwh
            total_cost = cost_per_m2 * self.floor_area_m2 * 0.5  # Roof area
            payback = total_cost / annual_savings if annual_savings > 0 else 999

            interventions.append(Intervention(
                intervention_type=InterventionType.SOLAR_PV,
                priority=3,
                description=f"Install solar PV panels. Potential generation: {pv_potential_kwh:.0f} kWh/year.",
                estimated_cost_per_m2=cost_per_m2 * 0.5,
                estimated_savings_percent=savings_percent,
                estimated_r_env_improvement=0.0,
                payback_years=payback,
                co2_reduction_kg_per_year=co2_reduction,
                additional_benefits=[
                    "Renewable energy generation",
                    "Energy independence",
                    "Grid feed-in revenue",
                    "Increased property value"
                ]
            ))

        # 7. Thermal mass enhancement (if light construction and temperature swings)
        if c_in_rating == "Light":
            savings_percent = 8
            cost_per_m2 = 40
            co2_reduction = (heating_kwh + electricity_kwh) * (savings_percent / 100) * \
                           (self.co2_per_kwh_heating + self.co2_per_kwh_electricity) / 2
            annual_savings = (heating_kwh + electricity_kwh) * (savings_percent / 100) * self.energy_cost_per_kwh
            total_cost = cost_per_m2 * self.floor_area_m2
            payback = total_cost / annual_savings if annual_savings > 0 else 999

            interventions.append(Intervention(
                intervention_type=InterventionType.THERMAL_MASS,
                priority=4,
                description="Add thermal mass (phase change materials, masonry) to stabilize temperatures.",
                estimated_cost_per_m2=cost_per_m2,
                estimated_savings_percent=savings_percent,
                estimated_r_env_improvement=0.0,
                payback_years=payback,
                co2_reduction_kg_per_year=co2_reduction,
                additional_benefits=[
                    "Reduced temperature swings",
                    "Better thermal comfort",
                    "Peak load reduction"
                ]
            ))

        # Sort by priority
        interventions.sort(key=lambda x: (x.priority, -x.estimated_savings_percent))

        return interventions

    def _estimate_renewable_potential(
        self,
        floor_area_m2: float,
        annual_electricity_kwh: float
    ) -> dict[str, float]:
        """Estimate renewable energy generation potential."""
        # Solar PV potential (assuming 50% of floor area is suitable roof)
        roof_area = floor_area_m2 * 0.5
        pv_potential_kwh_per_year = roof_area * 150  # ~150 kWh/m²/year typical

        # Solar thermal potential for hot water
        solar_thermal_potential_kwh = roof_area * 200  # Higher efficiency for thermal

        return {
            'solar_pv_kwh_per_year': pv_potential_kwh_per_year,
            'solar_pv_percent_of_electricity': min(pv_potential_kwh_per_year / annual_electricity_kwh * 100, 100),
            'solar_thermal_kwh_per_year': solar_thermal_potential_kwh,
            'suitable_roof_area_m2': roof_area
        }

    def print_report(self, report: BuildingPerformanceReport):
        """Print a formatted performance report."""
        print("=" * 80)
        print("BUILDING PERFORMANCE EVALUATION REPORT")
        print("=" * 80)
        print()

        # Building info
        print(f"Building Type: {report.building_type.value}")
        print(f"Floor Area: {report.floor_area_m2:.0f} m²")
        print()

        # Thermal performance
        print("THERMAL PERFORMANCE")
        print("-" * 80)
        print(f"Thermal Resistance (R_env): {report.thermal_params.R_env:.6f} K/W")
        print(f"  Per m²: {report.r_env_per_m2:.6f} K·m²/W")
        print(f"  Rating: {report.r_env_rating}")
        print(f"  Confidence Interval: [{report.thermal_params.R_env_ci_lower:.6f}, "
              f"{report.thermal_params.R_env_ci_upper:.6f}]")
        print()
        print(f"Thermal Capacitance (C_in): {report.thermal_params.C_in:.4e} J/K")
        print(f"  Per m²: {report.c_in_per_m2:.0f} J/(K·m²)")
        print(f"  Rating: {report.c_in_rating} construction")
        print()
        print(f"Heat Loss Coefficient: {report.heat_loss_coefficient:.1f} W/K")
        print(f"Specific Heat Loss: {report.specific_heat_loss:.2f} W/(K·m²)")
        print()

        # Energy consumption
        print("ENERGY CONSUMPTION")
        print("-" * 80)
        print(f"Annual Heating: {report.annual_heating_kwh:.0f} kWh "
              f"({report.annual_heating_kwh/report.floor_area_m2:.0f} kWh/m²)")
        print(f"Annual Electricity: {report.annual_electricity_kwh:.0f} kWh "
              f"({report.annual_electricity_kwh/report.floor_area_m2:.0f} kWh/m²)")
        print(f"Annual Cost: €{report.annual_energy_cost:.2f}")
        print(f"Heating System COP: {report.heating_cop_estimated:.2f}")
        print()

        # Climate
        print("CLIMATE DATA")
        print("-" * 80)
        print(f"Average Indoor Temperature: {report.avg_indoor_temp:.1f}°C")
        print(f"Average Outdoor Temperature: {report.avg_outdoor_temp:.1f}°C")
        print(f"Heating Degree Days: {report.heating_degree_days:.0f}")
        print(f"Cooling Degree Days: {report.cooling_degree_days:.0f}")
        print()

        # Environmental impact
        print("ENVIRONMENTAL IMPACT")
        print("-" * 80)
        print(f"Current CO₂ Emissions: {report.current_co2_kg_per_year:.0f} kg/year "
              f"({report.current_co2_kg_per_year/report.floor_area_m2:.1f} kg/m²/year)")
        print()

        # Recommendations
        print("RECOMMENDED INTERVENTIONS")
        print("=" * 80)
        for i, intervention in enumerate(report.interventions, 1):
            print(f"\n{i}. {intervention.intervention_type.value.upper().replace('_', ' ')}")
            print(f"   Priority: {intervention.priority} (1=highest)")
            print(f"   {intervention.description}")
            print(f"   Estimated Cost: €{intervention.estimated_cost_per_m2 * report.floor_area_m2:.0f} "
                  f"(€{intervention.estimated_cost_per_m2:.0f}/m²)")
            print(f"   Energy Savings: {intervention.estimated_savings_percent:.0f}%")
            print(f"   CO₂ Reduction: {intervention.co2_reduction_kg_per_year:.0f} kg/year")
            print(f"   Simple Payback: {intervention.payback_years:.1f} years")
            if intervention.additional_benefits:
                print("   Additional Benefits:")
                for benefit in intervention.additional_benefits:
                    print(f"     • {benefit}")

        print()
        print("SUMMARY OF TOP 3 INTERVENTIONS")
        print("-" * 80)
        print(f"Total Energy Savings: {report.total_savings_potential_kwh:.0f} kWh/year "
              f"({report.total_savings_potential_percent:.0f}%)")
        print(f"Total Cost Savings: €{report.total_savings_potential_cost:.0f}/year")
        print(f"Total CO₂ Reduction: {report.potential_co2_reduction_kg_per_year:.0f} kg/year")
        print()

        # Renewable potential
        print("RENEWABLE ENERGY POTENTIAL")
        print("-" * 80)
        print(f"Solar PV Generation Potential: {report.renewable_energy_potential['solar_pv_kwh_per_year']:.0f} kWh/year")
        print(f"  Can offset: {report.renewable_energy_potential['solar_pv_percent_of_electricity']:.0f}% of electricity use")
        print(f"Solar Thermal Potential: {report.renewable_energy_potential['solar_thermal_kwh_per_year']:.0f} kWh/year")
        print(f"Suitable Roof Area: {report.renewable_energy_potential['suitable_roof_area_m2']:.0f} m²")
        print()

        print("=" * 80)
