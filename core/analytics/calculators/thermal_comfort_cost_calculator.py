"""Thermal Comfort Cost Calculator.

Calculates the cost implications of thermal comfort control strategies based on:
- Energy consumption (district heating, electricity)
- Energy production (PV)
- EN 16798-1 comfort boundaries
- Temperature control strategies
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from core.domain.enums.en16798_category import EN16798Category
from core.analytics.calculators.en16798_calculator import EN16798StandardCalculator


@dataclass
class EnergyCosts:
    """Energy cost configuration."""

    district_heating_cost_per_kwh: float  # €/kWh
    electricity_cost_per_kwh: float  # €/kWh
    pv_feed_in_tariff: float  # €/kWh (revenue from excess PV)


@dataclass
class ThermalComfortCostResult:
    """Result from thermal comfort cost analysis."""

    period_start: pd.Timestamp
    period_end: pd.Timestamp
    category: EN16798Category
    
    # Temperature statistics
    avg_indoor_temp: float
    avg_outdoor_temp: float
    temp_lower_bound: float
    temp_upper_bound: float
    
    # Energy consumption
    total_heating_kwh: float
    total_electricity_kwh: float
    total_pv_production_kwh: float
    net_electricity_kwh: float  # grid - PV
    
    # Costs
    heating_cost: float
    electricity_cost: float
    pv_revenue: float
    total_energy_cost: float
    
    # Efficiency metrics
    cost_per_degree_hour: float  # Cost per degree-hour of comfort
    heating_per_delta_t: float  # kWh heating per degree delta from outdoor
    cost_per_delta_t: float  # € per degree delta from outdoor
    
    # Comfort metrics
    hours_in_comfort: int
    hours_below_comfort: int
    hours_above_comfort: int
    comfort_compliance_rate: float


@dataclass
class OptimizationResult:
    """Result from comfort optimization analysis."""

    original_category: EN16798Category
    optimized_category: EN16798Category
    
    # Original performance
    original_avg_temp: float
    original_total_cost: float
    original_comfort_rate: float
    
    # Optimized performance
    optimized_avg_temp: float
    optimized_total_cost: float
    optimized_comfort_rate: float
    
    # Savings
    cost_savings: float
    cost_savings_percent: float
    temp_reduction: float
    
    # Strategy details
    strategy: str
    feasibility_score: float  # 0-100, likelihood of success
    estimated_roi_months: float | None = None


class ThermalComfortCostCalculator:
    """
    Calculator for thermal comfort cost analysis.
    
    Analyzes the relationship between thermal comfort control strategies,
    energy consumption, and costs. Enables optimization by targeting the
    lower boundary of EN 16798 comfort categories.
    """

    def __init__(self, energy_costs: EnergyCosts):
        """
        Initialize calculator with energy cost configuration.
        
        Args:
            energy_costs: Energy pricing configuration
        """
        self.energy_costs = energy_costs
        self.en16798_calc = EN16798StandardCalculator()

    def calculate_comfort_cost(
        self,
        indoor_temp_series: pd.Series,
        outdoor_temp_series: pd.Series,
        heating_kwh_series: pd.Series,
        electricity_kwh_series: pd.Series,
        pv_production_kwh_series: pd.Series,
        category: EN16798Category,
        season: str = "heating"
    ) -> ThermalComfortCostResult:
        """
        Calculate cost of maintaining thermal comfort for a specific category.
        
        Args:
            indoor_temp_series: Indoor temperature measurements (°C)
            outdoor_temp_series: Outdoor temperature measurements (°C)
            heating_kwh_series: District heating consumption (kWh)
            electricity_kwh_series: Grid electricity consumption (kWh)
            pv_production_kwh_series: PV electricity production (kWh)
            category: EN 16798-1 category to evaluate
            season: "heating" or "cooling"
            
        Returns:
            ThermalComfortCostResult with detailed cost analysis
        """
        # Get temperature thresholds for this category
        thresholds = self.en16798_calc.get_temperature_thresholds(
            category=category,
            season=season
        )
        
        temp_lower = thresholds["lower"]
        temp_upper = thresholds["upper"]
        
        # Calculate comfort compliance
        in_comfort = (indoor_temp_series >= temp_lower) & (indoor_temp_series <= temp_upper)
        hours_in_comfort = int(in_comfort.sum())
        hours_below = int((indoor_temp_series < temp_lower).sum())
        hours_above = int((indoor_temp_series > temp_upper).sum())
        comfort_rate = (hours_in_comfort / len(indoor_temp_series)) * 100
        
        # Calculate energy totals
        total_heating = float(heating_kwh_series.sum())
        total_electricity = float(electricity_kwh_series.sum())
        total_pv = float(pv_production_kwh_series.sum())
        net_electricity = total_electricity - total_pv
        
        # Calculate costs
        heating_cost = total_heating * self.energy_costs.district_heating_cost_per_kwh
        electricity_cost = max(0, net_electricity) * self.energy_costs.electricity_cost_per_kwh
        pv_revenue = max(0, total_pv - total_electricity) * self.energy_costs.pv_feed_in_tariff
        total_cost = heating_cost + electricity_cost - pv_revenue
        
        # Calculate efficiency metrics
        # Cost per degree-hour of comfort
        degree_hours = float(((indoor_temp_series - temp_lower) * in_comfort).sum())
        cost_per_degree_hour = total_cost / degree_hours if degree_hours > 0 else 0
        
        # Heating per delta T (average)
        temp_delta = indoor_temp_series - outdoor_temp_series
        avg_temp_delta = float(temp_delta.mean())
        heating_per_delta_t = total_heating / avg_temp_delta if avg_temp_delta > 0 else 0
        cost_per_delta_t = total_cost / avg_temp_delta if avg_temp_delta > 0 else 0
        
        return ThermalComfortCostResult(
            period_start=indoor_temp_series.index[0],
            period_end=indoor_temp_series.index[-1],
            category=category,
            avg_indoor_temp=float(indoor_temp_series.mean()),
            avg_outdoor_temp=float(outdoor_temp_series.mean()),
            temp_lower_bound=temp_lower,
            temp_upper_bound=temp_upper,
            total_heating_kwh=total_heating,
            total_electricity_kwh=total_electricity,
            total_pv_production_kwh=total_pv,
            net_electricity_kwh=net_electricity,
            heating_cost=heating_cost,
            electricity_cost=electricity_cost,
            pv_revenue=pv_revenue,
            total_energy_cost=total_cost,
            cost_per_degree_hour=cost_per_degree_hour,
            heating_per_delta_t=heating_per_delta_t,
            cost_per_delta_t=cost_per_delta_t,
            hours_in_comfort=hours_in_comfort,
            hours_below_comfort=hours_below,
            hours_above_comfort=hours_above,
            comfort_compliance_rate=comfort_rate
        )

    def optimize_to_lower_boundary(
        self,
        indoor_temp_series: pd.Series,
        outdoor_temp_series: pd.Series,
        heating_kwh_series: pd.Series,
        electricity_kwh_series: pd.Series,
        pv_production_kwh_series: pd.Series,
        current_category: EN16798Category,
        season: str = "heating"
    ) -> OptimizationResult:
        """
        Simulate cost savings by optimizing temperature control to lower boundary.
        
        Strategy: Reduce setpoint to the lower comfort boundary of the current
        EN 16798 category to minimize heating costs while maintaining compliance.
        
        Args:
            indoor_temp_series: Current indoor temperatures
            outdoor_temp_series: Outdoor temperatures
            heating_kwh_series: Current heating consumption
            electricity_kwh_series: Current electricity consumption
            pv_production_kwh_series: PV production
            current_category: Current EN 16798 category
            season: "heating" or "cooling"
            
        Returns:
            OptimizationResult with cost savings and recommendations
        """
        # Get current performance
        current_result = self.calculate_comfort_cost(
            indoor_temp_series,
            outdoor_temp_series,
            heating_kwh_series,
            electricity_kwh_series,
            pv_production_kwh_series,
            current_category,
            season
        )
        
        # Get temperature thresholds
        thresholds = self.en16798_calc.get_temperature_thresholds(
            category=current_category,
            season=season
        )
        
        temp_lower = thresholds["lower"]
        current_avg = current_result.avg_indoor_temp
        
        # Calculate temperature reduction potential
        temp_reduction = max(0, current_avg - temp_lower)
        
        if temp_reduction < 0.1:
            # Already at lower boundary
            return OptimizationResult(
                original_category=current_category,
                optimized_category=current_category,
                original_avg_temp=current_avg,
                original_total_cost=current_result.total_energy_cost,
                original_comfort_rate=current_result.comfort_compliance_rate,
                optimized_avg_temp=current_avg,
                optimized_total_cost=current_result.total_energy_cost,
                optimized_comfort_rate=current_result.comfort_compliance_rate,
                cost_savings=0,
                cost_savings_percent=0,
                temp_reduction=0,
                strategy="Already optimized - operating at lower comfort boundary",
                feasibility_score=100
            )
        
        # Estimate energy savings
        # Rule of thumb: 6-10% heating savings per 1°C reduction in heating season
        # Using conservative 6% per degree
        heating_savings_rate = 0.06 * temp_reduction
        optimized_heating = current_result.total_heating_kwh * (1 - heating_savings_rate)
        
        # Electricity typically doesn't change much with temperature
        # Small reduction in fan/pump energy
        optimized_electricity = current_result.total_electricity_kwh * 0.98
        
        # Simulate optimized cost
        optimized_heating_cost = optimized_heating * self.energy_costs.district_heating_cost_per_kwh
        net_elec = optimized_electricity - current_result.total_pv_production_kwh
        optimized_electricity_cost = max(0, net_elec) * self.energy_costs.electricity_cost_per_kwh
        optimized_pv_revenue = current_result.pv_revenue
        optimized_total_cost = optimized_heating_cost + optimized_electricity_cost - optimized_pv_revenue
        
        # Calculate savings
        cost_savings = current_result.total_energy_cost - optimized_total_cost
        cost_savings_percent = (cost_savings / current_result.total_energy_cost) * 100
        
        # Estimate comfort compliance with optimized setpoint
        # Assume we'll maintain ~95% compliance at lower boundary
        optimized_comfort_rate = 95.0
        
        # Calculate feasibility score
        feasibility_score = self._calculate_feasibility(
            temp_reduction=temp_reduction,
            current_comfort_rate=current_result.comfort_compliance_rate,
            season=season
        )
        
        # Estimate ROI (assuming implementation cost of ~€500 per zone for controls)
        implementation_cost = 500  # €
        if cost_savings > 0:
            # Calculate monthly savings
            days_in_period = (current_result.period_end - current_result.period_start).days
            monthly_savings = cost_savings * (30 / days_in_period)
            roi_months = implementation_cost / monthly_savings if monthly_savings > 0 else None
        else:
            roi_months = None
        
        strategy = self._generate_optimization_strategy(
            temp_reduction=temp_reduction,
            category=current_category,
            season=season
        )
        
        return OptimizationResult(
            original_category=current_category,
            optimized_category=current_category,
            original_avg_temp=current_avg,
            original_total_cost=current_result.total_energy_cost,
            original_comfort_rate=current_result.comfort_compliance_rate,
            optimized_avg_temp=temp_lower,
            optimized_total_cost=optimized_total_cost,
            optimized_comfort_rate=optimized_comfort_rate,
            cost_savings=cost_savings,
            cost_savings_percent=cost_savings_percent,
            temp_reduction=temp_reduction,
            strategy=strategy,
            feasibility_score=feasibility_score,
            estimated_roi_months=roi_months
        )

    def compare_categories(
        self,
        indoor_temp_series: pd.Series,
        outdoor_temp_series: pd.Series,
        heating_kwh_series: pd.Series,
        electricity_kwh_series: pd.Series,
        pv_production_kwh_series: pd.Series,
        season: str = "heating"
    ) -> dict[str, ThermalComfortCostResult]:
        """
        Compare cost implications across all EN 16798 categories.
        
        Args:
            indoor_temp_series: Indoor temperatures
            outdoor_temp_series: Outdoor temperatures
            heating_kwh_series: Heating consumption
            electricity_kwh_series: Electricity consumption
            pv_production_kwh_series: PV production
            season: "heating" or "cooling"
            
        Returns:
            Dictionary mapping category names to cost results
        """
        results = {}
        
        for category in [
            EN16798Category.CATEGORY_I,
            EN16798Category.CATEGORY_II,
            EN16798Category.CATEGORY_III,
            EN16798Category.CATEGORY_IV
        ]:
            results[category.name] = self.calculate_comfort_cost(
                indoor_temp_series,
                outdoor_temp_series,
                heating_kwh_series,
                electricity_kwh_series,
                pv_production_kwh_series,
                category,
                season
            )
        
        return results

    def _calculate_feasibility(
        self,
        temp_reduction: float,
        current_comfort_rate: float,
        season: str
    ) -> float:
        """
        Calculate feasibility score for optimization strategy.
        
        Returns:
            Score from 0-100 indicating likelihood of successful implementation
        """
        score = 100.0
        
        # Penalize large temperature reductions
        if temp_reduction > 2.0:
            score -= 30
        elif temp_reduction > 1.0:
            score -= 15
        
        # Penalize if already struggling with comfort
        if current_comfort_rate < 90:
            score -= 20
        elif current_comfort_rate < 95:
            score -= 10
        
        # Cooling season is harder to optimize
        if season == "cooling":
            score -= 10
        
        return max(0, score)

    def _generate_optimization_strategy(
        self,
        temp_reduction: float,
        category: EN16798Category,
        season: str
    ) -> str:
        """Generate human-readable optimization strategy description."""
        if temp_reduction < 0.1:
            return "Already optimized - operating at lower comfort boundary"
        
        season_name = "heating" if season == "heating" else "cooling"
        
        strategies = [
            f"Reduce {season_name} setpoint by {temp_reduction:.1f}°C to reach lower boundary of {category.value}",
            f"Target temperature at {category.value} lower limit during {season_name} season",
            "Implement adaptive control to minimize overshooting comfort targets",
            "Enable night setback and weekend temperature optimization",
            "Consider weather-compensated control curves for proactive adjustments"
        ]
        
        return " | ".join(strategies)


def calculate_cost_per_room(
    room_data: pd.DataFrame,
    climate_data: pd.DataFrame,
    energy_data: pd.DataFrame,
    energy_costs: EnergyCosts,
    room_category: EN16798Category,
    season: str = "heating"
) -> tuple[ThermalComfortCostResult, OptimizationResult]:
    """
    Convenience function for calculating room-level costs and optimization.
    
    Args:
        room_data: DataFrame with 'temperature' column
        climate_data: DataFrame with 'outdoor_temperature' column
        energy_data: DataFrame with 'district_heating_kwh', 'pv_production_kwh', 
                     'grid_electricity_kwh' columns
        energy_costs: Energy cost configuration
        room_category: EN 16798 category for this room
        season: "heating" or "cooling"
        
    Returns:
        Tuple of (cost_result, optimization_result)
    """
    calculator = ThermalComfortCostCalculator(energy_costs)
    
    # Align timestamps
    merged = room_data.join(climate_data, how='inner').join(energy_data, how='inner')
    
    cost_result = calculator.calculate_comfort_cost(
        indoor_temp_series=merged['temperature'],
        outdoor_temp_series=merged['outdoor_temperature'],
        heating_kwh_series=merged['district_heating_kwh'],
        electricity_kwh_series=merged['grid_electricity_kwh'],
        pv_production_kwh_series=merged['pv_production_kwh'],
        category=room_category,
        season=season
    )
    
    optimization_result = calculator.optimize_to_lower_boundary(
        indoor_temp_series=merged['temperature'],
        outdoor_temp_series=merged['outdoor_temperature'],
        heating_kwh_series=merged['district_heating_kwh'],
        electricity_kwh_series=merged['grid_electricity_kwh'],
        pv_production_kwh_series=merged['pv_production_kwh'],
        current_category=room_category,
        season=season
    )
    
    return cost_result, optimization_result
