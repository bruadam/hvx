"""
HTK Template Charts Configuration

Defines the chart generation functions specific to the HTK report template.
This module integrates with the chart library to generate all required charts
for the Høje-Taastrup Kommune report.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Danish month names for charts
DANISH_MONTHS = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Maj", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dec"
}

DANISH_SEASONS = {
    "spring": "Forår",
    "summer": "Sommer", 
    "autumn": "Efterår",
    "winter": "Vinter"
}

class HTKChartGenerator:
    """Chart generator for HTK reports."""

    def __init__(self, charts_dir: Path, config: Dict[str, Any]):
        self.charts_dir = Path(charts_dir)
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        self.config = config

        # Set up matplotlib for PDF-friendly charts
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['legend.fontsize'] = 10
        plt.rcParams['figure.titlesize'] = 16
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        
        # PDF-optimized settings
        plt.rcParams['figure.figsize'] = (10, 6)  # Good for A4 landscape charts
        plt.rcParams['figure.dpi'] = 150  # High resolution for print
        plt.rcParams['savefig.dpi'] = 300  # Very high DPI for saving
        plt.rcParams['savefig.bbox'] = 'tight'  # Tight bounding box
        plt.rcParams['savefig.pad_inches'] = 0.2  # Small padding
        plt.rcParams['savefig.facecolor'] = 'white'  # White background
        plt.rcParams['figure.facecolor'] = 'white'
        
        # HTK color scheme
        self.colors = {
            'primary': '#0066cc',
            'secondary': '#004499',
            'good': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'neutral': '#6c757d',
            'co2': "#20a4dd",
            'temperature': "#e82913"
        }
    
    def generate_all_charts(self, analysis_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate all charts required for the HTK report."""
        chart_paths = {}
        
        # Executive summary charts
        chart_paths['building_comparison'] = self._generate_building_comparison(analysis_data)
        
        # Data quality charts
        chart_paths['data_completeness'] = self._generate_data_completeness(analysis_data)
        
        # Building-specific charts
        for building_name, building_data in analysis_data.items():
            building_id = building_name.lower().replace(" ", "_")
            
            # Top issues chart
            chart_paths[f'top_issues_{building_id}'] = self._generate_top_issues_chart(
                building_name, building_data
            )
            
            # Non-compliant hours charts
            chart_paths[f'non_compliant_opening_{building_id}'] = self._generate_non_compliant_hours(
                building_name, building_data, "opening_hours"
            )
            chart_paths[f'non_compliant_non_opening_{building_id}'] = self._generate_non_compliant_hours(
                building_name, building_data, "non_opening_hours"
            )
            
            # Room-specific charts
            if "rooms" in building_data:
                for room_name, room_data in building_data["rooms"].items():
                    room_id = f"{building_id}_{room_name.lower().replace(' ', '_')}"
                    
                    chart_paths[f'yearly_trends_{room_id}'] = self._generate_yearly_trends(
                        room_name, room_data
                    )
                    chart_paths[f'seasonal_patterns_{room_id}'] = self._generate_seasonal_patterns(
                        room_name, room_data
                    )
                    chart_paths[f'daily_distribution_{room_id}'] = self._generate_daily_distribution(
                        room_name, room_data
                    )
        
        # Overall recommendation charts
        chart_paths['priority_matrix'] = self._generate_priority_matrix(analysis_data)
        chart_paths['cost_benefit'] = self._generate_cost_benefit_analysis(analysis_data)
        
        return chart_paths
    
    def generate_all_charts_from_mapped_data(self, mapped_data: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """Generate all charts required for the HTK report using actual mapped data."""
        chart_paths = {}
        
        # Group rooms by building
        buildings = {}
        for room_id, room_df in mapped_data.items():
            # Extract building name from room_id (e.g., "ole_rømer_skolen_107" -> "ole_rømer_skolen")
            parts = room_id.split('_')
            if len(parts) >= 2:
                # Find the last part that's not a number
                building_parts = []
                for part in parts:
                    # If it's a number or looks like a room identifier, stop
                    if part.replace('.', '').isdigit() or (len(part) <= 3 and any(c.isdigit() for c in part)):
                        break
                    building_parts.append(part)
                
                if building_parts:
                    building_name = '_'.join(building_parts)
                else:
                    building_name = 'unknown'
            else:
                building_name = 'unknown'
            
            if building_name not in buildings:
                buildings[building_name] = {}
            buildings[building_name][room_id] = room_df
        
        # Convert mapped data to analysis-like structure for compatibility with existing chart methods
        # But also pass the raw mapped_data for charts that can use it
        analysis_data = self._convert_mapped_data_to_analysis_format(buildings)
        
        # Generate executive summary charts using analysis format
        chart_paths['building_comparison'] = self._generate_building_comparison(analysis_data)
        chart_paths['data_completeness'] = self._generate_data_completeness(buildings)

        # Building-specific charts
        for building_name, building_rooms in buildings.items():
            building_id = building_name.lower().replace(" ", "_")
            
            # Building-level aggregated charts (use existing methods)
            chart_paths[f'non_compliant_opening_{building_id}'] = self._generate_non_compliant_hours(
                building_name, building_rooms, "opening_hours"
            )
            chart_paths[f'non_compliant_non_opening_{building_id}'] = self._generate_non_compliant_hours(
                building_name, analysis_data.get(building_name, {}), "non_opening_hours"
            )
            
            # Room-specific charts using REAL mapped data
            for room_id, room_df in building_rooms.items():
                room_simple_id = room_id.replace(f"{building_name}_", "").lower().replace(' ', '_')
                chart_id = f"{building_id}_{room_simple_id}"
                
                chart_paths[f'yearly_trends_{chart_id}'] = self._generate_yearly_trends_from_real_data(
                    room_id, room_df
                )
                chart_paths[f'seasonal_patterns_{chart_id}'] = self._generate_seasonal_patterns_from_real_data(
                    room_id, room_df
                )
                chart_paths[f'daily_distribution_{chart_id}'] = self._generate_daily_distribution_from_real_data(
                    room_id, room_df
                )
                
                # NEW: Temperature and CO2 heatmaps for each room
                chart_paths[f'temperature_heatmap_{chart_id}'] = self._generate_temperature_heatmap(
                    room_id, room_df
                )
                chart_paths[f'co2_heatmap_{chart_id}'] = self._generate_co2_heatmap(
                    room_id, room_df
                )
                
                # NEW: Detailed compliance analysis chart for each room
                chart_paths[f'detailed_compliance_{chart_id}'] = self.generate_detailed_compliance_chart(
                    room_id, room_df
                )
            
            # NEW: Room comparison charts for each building
            chart_paths[f'room_compliance_comparison_{building_id}'] = self._generate_room_compliance_comparison(
                building_name, building_rooms
            )
        
        # Overall recommendation charts (using aggregated data)
        chart_paths['priority_matrix'] = self._generate_priority_matrix(analysis_data)
        chart_paths['cost_benefit'] = self._generate_cost_benefit_analysis(analysis_data)
        
        # NEW: Climate correlation charts
        chart_paths.update(self._generate_climate_correlation_charts(buildings))
        
        return chart_paths
    
    def _convert_mapped_data_to_analysis_format(self, buildings: Dict[str, Dict[str, pd.DataFrame]]) -> Dict[str, Any]:
        """Convert mapped data format to analysis data format for chart compatibility."""
        analysis_data = {}
        
        for building_name, building_rooms in buildings.items():
            analysis_data[building_name] = {
                'building_name': building_name.replace('_', ' ').title(),
                'rooms': {},
                'data_quality': {
                    'completeness': 0,
                    'missing_periods': "To implement",
                    'quality_score': "To implement"
                }
            }
            
            # Process each room
            for room_id, room_df in building_rooms.items():
                room_name = room_id.replace(f"{building_name}_", "")
                
                # Calculate basic metrics from the actual data
                room_data = {
                    'test_results': self._calculate_test_results_from_data(room_df),
                    'statistics': self._calculate_statistics_from_data(room_df)
                }
                
                analysis_data[building_name]['rooms'][room_name] = room_data
        
        return analysis_data
    
    def _calculate_test_results_from_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate test results from actual room data."""
        test_results = {}
        
        if 'co2' in df.columns and 'temperature' in df.columns:
            co2_data = df['co2'].dropna()
            temp_data = df['temperature'].dropna()
            
            # Calculate CO2 compliance (assuming 1000 ppm threshold)
            co2_violations = (co2_data > 1000).sum()
            co2_total = len(co2_data)
            co2_compliance = ((co2_total - co2_violations) / co2_total * 100) if co2_total > 0 else 0
            
            # Calculate temperature compliance (assuming 20-26°C range)
            temp_violations = ((temp_data < 20) | (temp_data > 26)).sum()
            temp_total = len(temp_data)
            temp_compliance = ((temp_total - temp_violations) / temp_total * 100) if temp_total > 0 else 0
            
            test_results['co2_1000_all_year_opening'] = {
                'compliance_rate': co2_compliance,
                'violations_count': int(co2_violations),
                'total_hours': co2_total,
                'mean': float(co2_data.mean()) if len(co2_data) > 0 else 0
            }
            
            test_results['temp_comfort_all_year_opening'] = {
                'compliance_rate': temp_compliance,
                'violations_count': int(temp_violations),
                'total_hours': temp_total,
                'mean': float(temp_data.mean()) if len(temp_data) > 0 else 0
            }
        
        return test_results
    
    def _calculate_statistics_from_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics from actual room data."""
        statistics = {
            'co2': {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0},
            'temperature': {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}
        }
        
        if 'co2' in df.columns:
            co2_data = df['co2'].dropna()
            if len(co2_data) > 0:
                statistics['co2'] = {
                    'mean': float(co2_data.mean()),
                    'std': float(co2_data.std()),
                    'min': float(co2_data.min()),
                    'max': float(co2_data.max())
                }
        
        if 'temperature' in df.columns:
            temp_data = df['temperature'].dropna()
            if len(temp_data) > 0:
                statistics['temperature'] = {
                    'mean': float(temp_data.mean()),
                    'std': float(temp_data.std()),
                    'min': float(temp_data.min()),
                    'max': float(temp_data.max())
                }
        
        return statistics
    
    def _generate_yearly_trends_from_real_data(self, room_name: str, room_df: pd.DataFrame) -> str:
        """Generate yearly trends using actual room data."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        if room_df.empty or 'temperature' not in room_df.columns or 'co2' not in room_df.columns:
            # Fallback to synthetic data if real data unavailable
            return self._generate_yearly_trends(room_name, {})
        
        # Use actual data
        temp_data = room_df['temperature'].dropna()
        co2_data = room_df['co2'].dropna()
        
        # Resample to daily averages to make charts more readable
        if len(temp_data) > 0:
            daily_temp = temp_data.resample('D').mean()
            ax1.plot(daily_temp.index, daily_temp, color=self.colors['primary'], alpha=0.7, linewidth=1)
        
        ax1.axhline(y=20, color='green', linestyle='--', alpha=0.7, label='Min Komfortgrænse')
        ax1.axhline(y=26, color='red', linestyle='--', alpha=0.7, label='Maks Komfortgrænse')
        ax1.set_ylabel('Temperatur (°C)')
        ax1.set_title(f'Årlige Trends - {room_name}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot CO2 using actual data
        if len(co2_data) > 0:
            daily_co2 = co2_data.resample('D').mean()
            ax2.plot(daily_co2.index, daily_co2, color=self.colors['secondary'], alpha=0.7, linewidth=1)
        
        ax2.axhline(y=1000, color='red', linestyle='--', alpha=0.7, label='CO₂ Grænse')
        ax2.set_ylabel('CO₂ (ppm)')
        ax2.set_xlabel('Dato')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        room_id = room_name.lower().replace(" ", "_")
        chart_path = self.charts_dir / f"yearly_trends_{room_id}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _generate_seasonal_patterns_from_real_data(self, room_name: str, room_df: pd.DataFrame) -> str:
        """Generate seasonal patterns using actual room data."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        if room_df.empty or 'temperature' not in room_df.columns or 'co2' not in room_df.columns:
            # Fallback to synthetic data if real data unavailable
            return self._generate_seasonal_patterns(room_name, {})
        
        # Add season column to the data
        room_df_copy = room_df.copy()
        if hasattr(room_df_copy.index, 'month'):
            if not isinstance(room_df_copy.index, pd.DatetimeIndex):
                room_df_copy.index = pd.to_datetime(room_df_copy.index)
            room_df_copy['month'] = room_df_copy.index.month
            room_df_copy['season'] = room_df_copy['month'].map({
                12: 'Vinter', 1: 'Vinter', 2: 'Vinter',
                3: 'Forår', 4: 'Forår', 5: 'Forår',
                6: 'Sommer', 7: 'Sommer', 8: 'Sommer',
                9: 'Efterår', 10: 'Efterår', 11: 'Efterår'
            })
            
            # Temperature box plot by season
            seasons = ['Forår', 'Sommer', 'Efterår', 'Vinter']
            temp_data_by_season = []
            co2_data_by_season = []
            
            for season in seasons:
                season_data = room_df_copy[room_df_copy['season'] == season]
                temp_data_by_season.append(season_data['temperature'].dropna().values)
                co2_data_by_season.append(season_data['co2'].dropna().values)
        else:
            # Fallback to synthetic data if index doesn't have datetime attributes
            return self._generate_seasonal_patterns(room_name, {})
        
        # Temperature box plot
        if any(len(data) > 0 for data in temp_data_by_season):
            bp1 = ax1.boxplot(temp_data_by_season, labels=seasons, patch_artist=True)
            for patch in bp1['boxes']:
                patch.set_facecolor(self.colors['primary'])
                patch.set_alpha(0.7)
        
        ax1.axhline(y=20, color='green', linestyle='--', alpha=0.7)
        ax1.axhline(y=26, color='red', linestyle='--', alpha=0.7)
        ax1.set_ylabel('Temperatur (°C)')
        ax1.set_title('Sæsonmæssige Temperaturmønstre')
        ax1.grid(True, alpha=0.3)
        
        # CO2 box plot
        if any(len(data) > 0 for data in co2_data_by_season):
            bp2 = ax2.boxplot(co2_data_by_season, labels=seasons, patch_artist=True)
            for patch in bp2['boxes']:
                patch.set_facecolor(self.colors['secondary'])
                patch.set_alpha(0.7)
        
        ax2.axhline(y=1000, color='red', linestyle='--', alpha=0.7)
        ax2.set_ylabel('CO₂ (ppm)')
        ax2.set_title('Sæsonmæssige CO₂ Mønstre')
        ax2.grid(True, alpha=0.3)
        
        plt.suptitle(f'Sæsonmønstre - {room_name}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        room_id = room_name.lower().replace(" ", "_")
        chart_path = self.charts_dir / f"seasonal_patterns_{room_id}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _generate_daily_distribution_from_real_data(self, room_name: str, room_df: pd.DataFrame) -> str:
        """Generate daily distribution using actual room data."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        if room_df.empty or 'temperature' not in room_df.columns or 'co2' not in room_df.columns:
            # Fallback to synthetic data if real data unavailable
            return self._generate_daily_distribution(room_name, {})
        
        # Add hour column to the data
        room_df_copy = room_df.copy()
        if hasattr(room_df_copy.index, 'hour'):
            if not isinstance(room_df_copy.index, pd.DatetimeIndex):
                room_df_copy.index = pd.to_datetime(room_df_copy.index)
            room_df_copy['hour'] = room_df_copy.index.hour
            
            # Calculate hourly statistics
            hourly_temp_stats = room_df_copy.groupby('hour')['temperature'].agg(['mean', 'std']).fillna(0)
            hourly_co2_stats = room_df_copy.groupby('hour')['co2'].agg(['mean', 'std']).fillna(0)
            
            hours = range(24)
            
            # Temperature daily pattern
            # Extract temperature statistics safely
            def safe_float(val):
                """Convert pandas scalar to float safely"""
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return float(str(val))
            
            temp_means = [safe_float(hourly_temp_stats.loc[h, 'mean']) if h in hourly_temp_stats.index else 20.0 for h in hours]
            temp_stds = [safe_float(hourly_temp_stats.loc[h, 'std']) if h in hourly_temp_stats.index else 1.0 for h in hours]
            temp_upper = [m + 2*s for m, s in zip(temp_means, temp_stds)]
            temp_lower = [m - 2*s for m, s in zip(temp_means, temp_stds)]
            
            ax1.plot(hours, temp_means, color=self.colors['primary'], linewidth=2, label='Gennemsnit')
            ax1.fill_between(hours, temp_lower, temp_upper, color=self.colors['primary'], 
                            alpha=0.3, label='95% Interval')
            
            # CO2 daily pattern
            co2_means = [safe_float(hourly_co2_stats.loc[h, 'mean']) if h in hourly_co2_stats.index else 600.0 for h in hours]
            co2_stds = [safe_float(hourly_co2_stats.loc[h, 'std']) if h in hourly_co2_stats.index else 100.0 for h in hours]
            co2_upper = [m + 2*s for m, s in zip(co2_means, co2_stds)]
            co2_lower = [max(400.0, m - 2*s) for m, s in zip(co2_means, co2_stds)]
            
            ax2.plot(hours, co2_means, color=self.colors['secondary'], linewidth=2, label='Gennemsnit')
            ax2.fill_between(hours, co2_lower, co2_upper, color=self.colors['secondary'], 
                            alpha=0.3, label='95% Interval')
        else:
            # Fallback to synthetic data if index doesn't have datetime attributes
            return self._generate_daily_distribution(room_name, {})
        
        ax1.axhline(y=20, color='green', linestyle='--', alpha=0.7)
        ax1.axhline(y=26, color='red', linestyle='--', alpha=0.7)
        ax1.set_ylabel('Temperatur (°C)')
        ax1.set_title(f'Daglig Distribution - {room_name}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        ax2.axhline(y=1000, color='red', linestyle='--', alpha=0.7)
        ax2.set_ylabel('CO₂ (ppm)')
        ax2.set_xlabel('Time (24-timer format)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        room_id = room_name.lower().replace(" ", "_")
        chart_path = self.charts_dir / f"daily_distribution_{room_id}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _generate_building_comparison(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate building performance comparison chart.
        """
        buildings = []
        co2_compliance = []
        temp_compliance = []
        
        for building_name, building_data in analysis_data.items():
            buildings.append(building_name)
            
            # Extract or calculate compliance rates
            co2_rate = self._extract_compliance_rate(building_data, "co2_1000_all_year_opening")
            temp_rate = self._extract_compliance_rate(building_data, "temp_comfort_all_year_opening")
            
            co2_compliance.append(co2_rate)
            temp_compliance.append(temp_rate)
        
        # Create the chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(buildings))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, co2_compliance, width, label='CO₂ (<1000 ppm) Overholdelse', 
                  color=self.colors['co2'], alpha=0.8)
        bars2 = ax.bar(x + width/2, temp_compliance, width, label='Temperatur (20-26 °C) Overholdelse', 
                  color=self.colors['temperature'], alpha=0.8)
        
        ax.set_xlabel('Bygninger')
        ax.set_ylabel('Overholdelse (%)')
        ax.set_title('Bygnings Performance Sammenligning')
        ax.set_xticks(x)
        ax.set_xticklabels(buildings, rotation=45, ha='right')
        ax.legend()
        ax.grid(False)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}%',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom')
        
        plt.tight_layout()
        chart_path = self.charts_dir / "building_comparison.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)

    def _generate_data_completeness(self, buildings_dir: Dict[str, Any]) -> str:
        """Generate data completeness heatmap."""
        # Create sample data completeness (in real implementation, extract from actual data)
        buildings = list(buildings_dir.keys())
        months = list(range(1, 13))

        # from buildings_dir, get the missing data per months over the year of the data at a hourly resolution, get the overall numbers over the room and divide by the number of rooms*total records per room of one year of data (be careful with the 2024 leap year)
        completeness_data = np.zeros((len(buildings), 12))
        for i, building in enumerate(buildings):
            # Buildings_dir[building] is a dict with room_id as keys and df as values
            room_completeness = []
            for room_id, df in buildings_dir[building].items():
                # Ensure datetime index
                if not isinstance(df.index, pd.DatetimeIndex):
                    continue
                
                # Resample to hourly frequency, keeping NaN for missing data
                df_hourly = df.resample('H').mean()
                
                # Calculate the completeness for each month
                for month in months:
                    # Get the hourly data for the month
                    monthly_data = df_hourly[df_hourly.index.month == month]
                    if monthly_data.empty:
                        # If no data for the month, set completeness to NaN
                        month_completeness = 0.0
                    else:
                        # Calculate completeness as ratio of non-NaN values to total expected hours
                        non_nan_count = monthly_data.count().max() if not monthly_data.empty else 0
                        total_hours = len(monthly_data)
                        month_completeness = non_nan_count / total_hours if total_hours > 0 else 0.0
                    
                    # Store month completeness for this room
                    if len(room_completeness) <= month - 1:
                        room_completeness.extend([0.0] * (month - len(room_completeness)))
                    if month - 1 < len(room_completeness):
                        room_completeness[month - 1] += month_completeness

            # Average completeness across all rooms in the building
            num_rooms = len(buildings_dir[building])
            if num_rooms > 0:
                for month_idx in range(len(room_completeness)):
                    completeness_data[i, month_idx] = room_completeness[month_idx] / num_rooms

        # Round to 1 decimal place
        completeness_data = np.round(completeness_data, 3) * 100

        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, 6))

        im = ax.imshow(completeness_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
        # Add gridlines
        ax.grid(False)
        # Set ticks and labels
        ax.set_xticks(range(12))
        ax.set_xticklabels([DANISH_MONTHS[i] for i in months])
        ax.set_yticks(range(len(buildings)))
        # Format the ytick labels, bygning_something > Bygning Something
        buildings = [b.replace('_', ' ').title() for b in buildings]
        ax.set_yticklabels(buildings)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Datakomplethed', rotation=270, labelpad=20)
        
        # Add text annotations
        for i in range(len(buildings)):
            for j in range(12):
                text = ax.text(j, i, f'{completeness_data[i, j]:.0f}%',
                             ha="center", va="center", color="black", fontsize=8)
        
        ax.set_title('Datakomplethed Over Tid')
        ax.set_xlabel('Måned')
        ax.set_ylabel('Bygning')
        
        plt.tight_layout()
        chart_path = self.charts_dir / "data_completeness.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _generate_top_issues_chart(self, building_name: str, building_data: Dict[str, Any]) -> str:
        """Generate top 10 rooms with most issues."""
        room_issues = []
        
        if "rooms" in building_data:
            for room_name, room_data in building_data["rooms"].items():
                co2_violations = self._extract_violations(room_data, "co2")
                temp_violations = self._extract_violations(room_data, "temperature")
                total_violations = co2_violations + temp_violations
                
                room_issues.append({
                    'room': room_name,
                    'co2_violations': co2_violations,
                    'temp_violations': temp_violations,
                    'total_violations': total_violations
                })
        
        # Sort by total violations and take top 10
        room_issues.sort(key=lambda x: x['total_violations'], reverse=True)
        top_rooms = room_issues[:10]
        
        if not top_rooms:
            # Create empty chart if no data
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Ingen data tilgængelig', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=14)
            ax.set_title(f'Top Rum med Problemer - {building_name}')
        else:
            # Create horizontal bar chart
            fig, ax = plt.subplots(figsize=(10, 8))
            
            rooms = [r['room'] for r in top_rooms]
            co2_viol = [r['co2_violations'] for r in top_rooms]
            temp_viol = [r['temp_violations'] for r in top_rooms]
            
            y_pos = np.arange(len(rooms))
            
            bars1 = ax.barh(y_pos, co2_viol, 0.4, label='CO₂ Overskridelser', 
                           color=self.colors['primary'], alpha=0.8)
            bars2 = ax.barh(y_pos + 0.4, temp_viol, 0.4, label='Temperatur Overskridelser', 
                           color=self.colors['secondary'], alpha=0.8)
            
            ax.set_yticks(y_pos + 0.2)
            ax.set_yticklabels(rooms)
            ax.set_xlabel('Antal Overskridelser')
            ax.set_title(f'Top 10 Rum med Flest Problemer - {building_name}')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        building_id = building_name.lower().replace(" ", "_")
        chart_path = self.charts_dir / f"top_issues_{building_id}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _generate_non_compliant_hours(self, building_name: str, building_data: Dict[str, Any], 
                                    period: str) -> str:
        """Generate non-compliant hours scatter plot."""
        fig, ax = plt.subplots(figsize=(12, 8))

        # TODO: Implement data extraction for non-compliant hours without hardcoded values
        building_temps_values = {}
        building_co2_values = {}
        for room_name, room_df in building_data.items():
            room_df = room_df.resample('h').mean()
            building_temps_values[room_name] = room_df['temperature']
            building_co2_values[room_name] = room_df['co2']

        # Combine all room data into a single DataFrame
        building_temps_df = pd.concat(building_temps_values, axis=1)
        building_co2_df = pd.concat(building_co2_values, axis=1)

        # Calculate average values
        building_temps_avg = building_temps_df.mean(axis=1)
        building_co2_avg = building_co2_df.mean(axis=1)

        # Filter non compliant hours with OR statements
        non_compliant_mask = (building_co2_avg > 1000) | (building_temps_avg > 26)
        if non_compliant_mask.sum() == 0:
            # If no non-compliant hours, return empty chart
            return self._generate_empty_chart(building_name)
        # Make sure index is in pd.DatetimeIndex
        if not isinstance(building_temps_avg.index, pd.DatetimeIndex):
            building_temps_avg.index = pd.to_datetime(building_temps_avg.index)
        non_compliant_hours = pd.to_datetime(building_temps_avg[non_compliant_mask].index).hour
        non_compliant_co2 = building_co2_avg[non_compliant_mask]
        non_compliant_temps = building_temps_avg[non_compliant_mask]
        
        # Filter based on period
        if period == "opening_hours":
            mask = (non_compliant_hours >= 8) & (non_compliant_hours <= 15)
            title_period = "Åbningstid"
        else:
            mask = (non_compliant_hours < 8) | (non_compliant_hours > 15)
            title_period = "Uden for Åbningstid"

        non_compliant_hours = non_compliant_hours[mask]
        non_compliant_co2 = non_compliant_co2[mask]
        non_compliant_temps = non_compliant_temps[mask]
        
        # Create scatter plot
        # Use a traffic light color map: green for temp <= 26, red for temp > 26
        temp_colors = ['green' if t <= 26 else 'red' for t in non_compliant_temps]
        scatter = ax.scatter(non_compliant_hours, non_compliant_co2, c=temp_colors,
                     alpha=0.6, s=30, edgecolors='black', linewidth=0.5)
        
        # Add thresholds
        ax.axhline(y=1000, color='red', linestyle='--', alpha=0.7, label='CO₂ Grænse (1000 ppm)')
        
        # Formatting
        ax.set_xlabel('Time (24-timer format)')
        ax.set_ylabel('CO₂ Koncentration (ppm)')
        ax.set_title(f'Ikke-overholdende Timer ({title_period}) - {building_name}')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Custom legend for temperature colors
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', label='Temp ≤ 26°C', markerfacecolor='green', markersize=10),
            Line2D([0], [0], marker='o', color='w', label='Temp > 26°C', markerfacecolor='red', markersize=10)
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        plt.tight_layout()
        building_id = building_name.lower().replace(" ", "_")
        chart_path = self.charts_dir / f"non_compliant_{period}_{building_id}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)

    def _generate_empty_chart(self, building_name: str) -> str:
        """Generate an empty chart for a building."""
        fig, ax = plt.subplots(figsize=(12, 6))
        # No axis, not text, Just a square with no data
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f'Ingen Ikke-overholdende Timer Fundet - {building_name}')
        plt.tight_layout()
        chart_path = self.charts_dir / f"non_compliant_empty_{building_name.lower().replace(' ', '_')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        return str(chart_path)

    def _generate_yearly_trends(self, room_name: str, room_data: Dict[str, Any]) -> str:
        """Generate yearly trends for temperature and CO2."""
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        room_df = room_data.get(room_name, None)
        if room_df is not None and not room_df.empty:
            # Use actual data
            dates = room_df.index
            temperature = room_df['temperature'] if 'temperature' in room_df.columns else None
            co2 = room_df['co2'] if 'co2' in room_df.columns else None
            
            # Plot temperature if available
            if temperature is not None:
                ax1.plot(dates, temperature, color=self.colors['primary'], alpha=0.7, linewidth=1)
                ax1.axhline(y=20, color='green', linestyle='--', alpha=0.7, label='Min Komfortgrænse')
                ax1.axhline(y=26, color='red', linestyle='--', alpha=0.7, label='Maks Komfortgrænse')
                ax1.set_ylabel('Temperatur (°C)')
                ax1.set_title(f'Årlige Trends - {room_name} (Faktiske Data)')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
            else:
                ax1.text(0.5, 0.5, 'Ingen temperaturdata tilgængelig', ha='center', va='center', 
                        transform=ax1.transAxes, fontsize=14)
                ax1.set_title(f'Årlige Trends - {room_name}')
            
            # Plot CO2 if available
            if co2 is not None:
                ax2.plot(dates, co2, color=self.colors['secondary'], alpha=0.7, linewidth=1)
                ax2.axhline(y=1000, color='red', linestyle='--', alpha=0.7, label='CO₂ Grænse')
                ax2.set_ylabel('CO₂ (ppm)')
                ax2.set_xlabel('Dato')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(0.5, 0.5, 'Ingen CO₂ data tilgængelig', ha='center', va='center', 
                        transform=ax2.transAxes, fontsize=14)
                ax2.set_xlabel('Dato')
        else:
            # Fall back to sample data generation
            dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
            np.random.seed(hash(room_name) % 2**32)  # Consistent seed based on room name
            
            # Temperature data with seasonal variation
            temp_base = 22 + 3 * np.sin(2 * np.pi * dates.dayofyear / 365.25)
            temp_noise = np.random.normal(0, 1, len(dates))
            temperature = temp_base + temp_noise
            
            # CO2 data with weekly pattern
            co2_base = 800 + 200 * (dates.weekday < 5)  # Higher on weekdays
            co2_noise = np.random.normal(0, 100, len(dates))
            co2 = np.maximum(400, co2_base + co2_noise)
            
            # Plot temperature
            ax1.plot(dates, temperature, color=self.colors['primary'], alpha=0.7, linewidth=1)
            ax1.axhline(y=20, color='green', linestyle='--', alpha=0.7, label='Min Komfortgrænse')
            ax1.axhline(y=26, color='red', linestyle='--', alpha=0.7, label='Maks Komfortgrænse')
            ax1.set_ylabel('Temperatur (°C)')
            ax1.set_title(f'Årlige Trends - {room_name} (Simulerede Data)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot CO2
            ax2.plot(dates, co2, color=self.colors['secondary'], alpha=0.7, linewidth=1)
            ax2.axhline(y=1000, color='red', linestyle='--', alpha=0.7, label='CO₂ Grænse')
            ax2.set_ylabel('CO₂ (ppm)')
            ax2.set_xlabel('Dato')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        room_id = room_name.lower().replace(" ", "_")
        chart_path = self.charts_dir / f"yearly_trends_{room_id}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _generate_seasonal_patterns(self, room_name: str, room_data: Dict[str, Any]) -> str:
        """Generate seasonal box plots."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Generate sample seasonal data
        seasons = ['Forår', 'Sommer', 'Efterår', 'Vinter']
        
        
        # Temperature box plot
        bp1 = ax1.boxplot(temp_data, labels=seasons, patch_artist=True)
        for patch in bp1['boxes']:
            patch.set_facecolor(self.colors['primary'])
            patch.set_alpha(0.7)
        
        ax1.axhline(y=20, color='green', linestyle='--', alpha=0.7)
        ax1.axhline(y=26, color='red', linestyle='--', alpha=0.7)
        ax1.set_ylabel('Temperatur (°C)')
        ax1.set_title('Sæsonmæssige Temperaturmønstre')
        ax1.grid(True, alpha=0.3)
        
        # CO2 box plot
        bp2 = ax2.boxplot(co2_data, labels=seasons, patch_artist=True)
        for patch in bp2['boxes']:
            patch.set_facecolor(self.colors['secondary'])
            patch.set_alpha(0.7)
        
        ax2.axhline(y=1000, color='red', linestyle='--', alpha=0.7)
        ax2.set_ylabel('CO₂ (ppm)')
        ax2.set_title('Sæsonmæssige CO₂ Mønstre')
        ax2.grid(True, alpha=0.3)
        
        plt.suptitle(f'Sæsonmønstre - {room_name}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        room_id = room_name.lower().replace(" ", "_")
        chart_path = self.charts_dir / f"seasonal_patterns_{room_id}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _generate_daily_distribution(self, room_name: str, room_data: Dict[str, Any]) -> str:
        """Generate daily distribution with bounds."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        hours = range(24)
        np.random.seed(hash(room_name) % 2**32)
        
        # Temperature daily pattern
        temp_mean = 20 + 4 * np.sin(2 * np.pi * (np.array(hours) - 6) / 24)  # Peak at noon
        temp_std = 1 + 0.5 * np.sin(2 * np.pi * np.array(hours) / 24)
        temp_upper = temp_mean + 2 * temp_std
        temp_lower = temp_mean - 2 * temp_std
        
        ax1.plot(hours, temp_mean, color=self.colors['primary'], linewidth=2, label='Gennemsnit')
        ax1.fill_between(hours, temp_lower, temp_upper, color=self.colors['primary'], 
                        alpha=0.3, label='95% Interval')
        ax1.axhline(y=20, color='green', linestyle='--', alpha=0.7)
        ax1.axhline(y=26, color='red', linestyle='--', alpha=0.7)
        ax1.set_ylabel('Temperatur (°C)')
        ax1.set_title(f'Daglig Distribution - {room_name}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # CO2 daily pattern (higher during work hours)
        co2_mean = 600 + 400 * (np.array(hours) >= 8) * (np.array(hours) <= 16)
        co2_std = 100 + 50 * (np.array(hours) >= 8) * (np.array(hours) <= 16)
        co2_upper = co2_mean + 2 * co2_std
        co2_lower = np.maximum(400, co2_mean - 2 * co2_std)
        
        ax2.plot(hours, co2_mean, color=self.colors['secondary'], linewidth=2, label='Gennemsnit')
        ax2.fill_between(hours, co2_lower, co2_upper, color=self.colors['secondary'], 
                        alpha=0.3, label='95% Interval')
        ax2.axhline(y=1000, color='red', linestyle='--', alpha=0.7)
        ax2.set_ylabel('CO₂ (ppm)')
        ax2.set_xlabel('Time (24-timer format)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        room_id = room_name.lower().replace(" ", "_")
        chart_path = self.charts_dir / f"daily_distribution_{room_id}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _generate_priority_matrix(self, analysis_data: Dict[str, Any]) -> str:
        """Generate priority matrix for recommendations."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Sample recommendations data
        recommendations = [
            {"name": "Ventilation Upgrade", "impact": 8, "effort": 6, "cost": 150000},
            {"name": "Sensor Calibration", "impact": 6, "effort": 2, "cost": 10000},
            {"name": "HVAC Optimization", "impact": 7, "effort": 4, "cost": 50000},
            {"name": "Window Sealing", "impact": 4, "effort": 3, "cost": 20000},
            {"name": "Smart Controls", "impact": 9, "effort": 8, "cost": 200000},
            {"name": "Insulation Upgrade", "impact": 5, "effort": 7, "cost": 100000},
        ]
        
        # Extract data for plotting
        impacts = [r["impact"] for r in recommendations]
        efforts = [r["effort"] for r in recommendations]
        costs = [r["cost"] for r in recommendations]
        names = [r["name"] for r in recommendations]
        
        # Create bubble chart
        scatter = ax.scatter(efforts, impacts, s=[c/1000 for c in costs], 
                           alpha=0.6, c=costs, cmap='RdYlBu_r', edgecolors='black')
        
        # Add labels
        for i, name in enumerate(names):
            ax.annotate(name, (efforts[i], impacts[i]), xytext=(5, 5), 
                       textcoords='offset points', fontsize=8)
        
        # Quadrant lines
        ax.axhline(y=5, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(x=5, color='gray', linestyle='--', alpha=0.5)
        
        # Quadrant labels
        ax.text(2.5, 8.5, 'Hurtig Gevinst\n(Lav indsats, Høj påvirkning)', 
               ha='center', va='center', fontweight='bold', 
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.7))
        ax.text(7.5, 8.5, 'Store Projekter\n(Høj indsats, Høj påvirkning)', 
               ha='center', va='center', fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.7))
        ax.text(2.5, 1.5, 'Fyld op\n(Lav indsats, Lav påvirkning)', 
               ha='center', va='center', fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow', alpha=0.7))
        ax.text(7.5, 1.5, 'Spørgsmålstegn\n(Høj indsats, Lav påvirkning)', 
               ha='center', va='center', fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.7))
        
        ax.set_xlabel('Implementeringsindsats')
        ax.set_ylabel('Forventet Påvirkning')
        ax.set_title('Prioritetsmatrix for Forbedringer')
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.grid(True, alpha=0.3)
        
        # Color bar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Estimeret Omkostning (DKK)', rotation=270, labelpad=20)
        
        plt.tight_layout()
        chart_path = self.charts_dir / "priority_matrix.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _generate_cost_benefit_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Generate cost-benefit analysis chart."""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Sample cost-benefit data
        projects = [
            {"name": "Ventilation Upgrade", "cost": 150000, "benefit": 200000, "payback": 3.2},
            {"name": "Smart Controls", "cost": 200000, "benefit": 180000, "payback": 4.5},
            {"name": "HVAC Optimization", "cost": 50000, "benefit": 80000, "payback": 2.1},
            {"name": "Sensor Network", "cost": 30000, "benefit": 45000, "payback": 2.8},
            {"name": "Insulation", "cost": 100000, "benefit": 90000, "payback": 5.1},
        ]
        
        costs = [p["cost"] for p in projects]
        benefits = [p["benefit"] for p in projects]
        paybacks = [p["payback"] for p in projects]
        names = [p["name"] for p in projects]
        
        # Create bubble chart
        scatter = ax.scatter(costs, benefits, s=[1000/p for p in paybacks], 
                           alpha=0.6, c=paybacks, cmap='RdYlGn_r', edgecolors='black')
        
        # Add diagonal line for break-even
        max_val = max(max(costs), max(benefits))
        ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='Break-even')
        
        # Add labels
        for i, name in enumerate(names):
            ax.annotate(name, (costs[i], benefits[i]), xytext=(5, 5), 
                       textcoords='offset points', fontsize=9)
        
        ax.set_xlabel('Implementeringsomkostning (DKK)')
        ax.set_ylabel('Forventet Årlig Besparelse (DKK)')
        ax.set_title('Omkostnings-Nytte Analyse')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Color bar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Tilbagebetalingstid (år)', rotation=270, labelpad=20)
        
        plt.tight_layout()
        chart_path = self.charts_dir / "cost_benefit.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _create_gauge(self, ax, value: float, title: str, unit: str):
        """Create a gauge chart."""
        # Create gauge visualization
        theta = np.linspace(0, np.pi, 100)
        
        # Background arc
        ax.plot(np.cos(theta), np.sin(theta), 'k-', linewidth=20, alpha=0.3)
        
        # Value arc
        value_theta = np.linspace(0, np.pi * (value / 100), int(value))
        if len(value_theta) > 0:
            color = self.colors['good'] if value >= 80 else (
                self.colors['warning'] if value >= 60 else self.colors['danger']
            )
            ax.plot(np.cos(value_theta), np.sin(value_theta), color=color, linewidth=20)
        
        # Value text
        ax.text(0, -0.1, f'{value:.1f}{unit}', ha='center', va='center', 
               fontsize=20, fontweight='bold')
        ax.text(0, -0.3, title, ha='center', va='center', fontsize=12)
        
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-0.5, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
    
    def _extract_compliance_rate(self, building_data: Dict[str, Any], test_name: str) -> float:
        """Extract compliance rate from building data."""
        compliance_rates = [k['test_results'][test_name]['compliance_rate'] for k in building_data.get("rooms", {}).values() if 'test_results' in k and test_name in k['test_results']]

        return float(np.mean(compliance_rates)) if compliance_rates else 0.0

    def _extract_violations(self, room_data: Dict[str, Any], parameter: str) -> int:
        """Extract violation count from room data."""
        if 'test_results' not in room_data or parameter not in room_data['test_results']:
            return 0
        else:
            return room_data['test_results'][parameter].get('violations', 0)
        
    def _generate_temperature_heatmap(self, room_id: str, room_df: pd.DataFrame) -> str:
        """Generate temperature heatmap with months on x-axis and hours on y-axis."""
        try:
            if room_df.empty or 'temperature' not in room_df.columns:
                logger.warning(f"No temperature data for {room_id}")
                return ""
            
            # Ensure datetime index
            if not isinstance(room_df.index, pd.DatetimeIndex):
                logger.warning(f"Non-datetime index for {room_id}")
                return ""
            
            # Create hour and month columns
            room_df_copy = room_df.copy()
            room_df_copy['hour'] = pd.to_datetime(room_df_copy.index).hour
            room_df_copy['month'] = pd.to_datetime(room_df_copy.index).month
            
            # Create pivot table for heatmap
            heatmap_data = room_df_copy.pivot_table(
                values='temperature',
                index='hour',
                columns='month',
                aggfunc='mean'
            )
            
            # Create figure
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Generate heatmap
            sns.heatmap(
                heatmap_data,
                cmap='RdYlBu_r',
                center=23,  # Center around comfort temperature
                annot=False,
                fmt='.1f',
                cbar_kws={'label': 'Temperatur (°C)'},
                ax=ax
            )
            
            # Formatting
            ax.set_title(f'Temperatur Heatmap - {room_id.replace("_", " ").title()}', fontsize=14, fontweight='bold')
            ax.set_xlabel('Måned', fontsize=12)
            ax.set_ylabel('Time på dagen', fontsize=12)
            
            # Set month labels
            month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']
            # Handle month column labels safely
            if len(heatmap_data.columns) > 0:
                current_months = list(heatmap_data.columns)
                month_labels_subset = []
                for month in current_months:
                    try:
                        month_int = int(month)
                        if 1 <= month_int <= 12:
                            month_labels_subset.append(month_labels[month_int-1])
                        else:
                            month_labels_subset.append(str(month))
                    except (ValueError, TypeError):
                        month_labels_subset.append(str(month))
                ax.set_xticklabels(month_labels_subset, rotation=0)
            
            # Set hour labels
            ax.set_yticklabels([f'{h:02d}:00' for h in heatmap_data.index], rotation=0)
            
            plt.tight_layout()
            
            # Save chart
            filename = f"temperature_heatmap_{room_id.lower().replace(' ', '_')}.png"
            filepath = self.charts_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating temperature heatmap for {room_id}: {e}")
            plt.close()
            return ""

    def _generate_co2_heatmap(self, room_id: str, room_df: pd.DataFrame) -> str:
        """Generate CO2 heatmap with months on x-axis and hours on y-axis."""
        try:
            if room_df.empty or 'co2' not in room_df.columns:
                logger.warning(f"No CO2 data for {room_id}")
                return ""
            
            # Ensure datetime index
            if not isinstance(room_df.index, pd.DatetimeIndex):
                logger.warning(f"Non-datetime index for {room_id}")
                return ""
            
            # Create hour and month columns
            room_df_copy = room_df.copy()
            room_df_copy['hour'] = pd.to_datetime(room_df_copy.index).hour
            room_df_copy['month'] = pd.to_datetime(room_df_copy.index).month
            
            # Create pivot table for heatmap
            heatmap_data = room_df_copy.pivot_table(
                values='co2',
                index='hour',
                columns='month',
                aggfunc='mean'
            )
            
            # Create figure
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Generate heatmap
            sns.heatmap(
                heatmap_data,
                cmap='YlOrRd',
                annot=False,
                fmt='.0f',
                cbar_kws={'label': 'CO₂ (ppm)'},
                ax=ax
            )
            
            # Formatting
            ax.set_title(f'CO₂ Heatmap - {room_id.replace("_", " ").title()}', fontsize=14, fontweight='bold')
            ax.set_xlabel('Måned', fontsize=12)
            ax.set_ylabel('Time på dagen', fontsize=12)
            
            # Set month labels
            month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']
            # Handle month column labels safely
            if len(heatmap_data.columns) > 0:
                current_months = list(heatmap_data.columns)
                month_labels_subset = []
                for month in current_months:
                    try:
                        month_int = int(month)
                        if 1 <= month_int <= 12:
                            month_labels_subset.append(month_labels[month_int-1])
                        else:
                            month_labels_subset.append(str(month))
                    except (ValueError, TypeError):
                        month_labels_subset.append(str(month))
                ax.set_xticklabels(month_labels_subset, rotation=0)
            
            # Set hour labels
            ax.set_yticklabels([f'{h:02d}:00' for h in heatmap_data.index], rotation=0)
            
            plt.tight_layout()
            
            # Save chart
            filename = f"co2_heatmap_{room_id.lower().replace(' ', '_')}.png"
            filepath = self.charts_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating CO2 heatmap for {room_id}: {e}")
            plt.close()
            return ""

    def _generate_room_compliance_comparison(self, building_name: str, building_rooms: Dict[str, pd.DataFrame]) -> str:
        """Generate bar chart comparing room compliance rates, sorted from worst to best."""
        try:
            room_data = []
            
            # Calculate compliance rates for each room
            for room_id, room_df in building_rooms.items():
                if room_df.empty:
                    continue
                
                room_name = room_id.replace(f"{building_name}_", "").replace("_", " ").title()
                
                # Calculate temperature compliance (20-26°C)
                temp_compliance = 0
                co2_compliance = 0
                
                if 'temperature' in room_df.columns:
                    temp_in_range = ((room_df['temperature'] >= 20) & (room_df['temperature'] <= 26)).sum()
                    temp_total = len(room_df['temperature'].dropna())
                    temp_compliance = (temp_in_range / temp_total * 100) if temp_total > 0 else 0
                
                # Calculate CO2 compliance (<1000 ppm)
                if 'co2' in room_df.columns:
                    co2_in_range = (room_df['co2'] <= 1000).sum()
                    co2_total = len(room_df['co2'].dropna())
                    co2_compliance = (co2_in_range / co2_total * 100) if co2_total > 0 else 0
                
                room_data.append({
                    'room': room_name,
                    'temp_compliance': temp_compliance,
                    'co2_compliance': co2_compliance,
                    'average_compliance': (temp_compliance + co2_compliance) / 2
                })
            
            if not room_data:
                logger.warning(f"No room data for building {building_name}")
                return ""
            
            # Sort rooms by average compliance (worst to best)
            room_data.sort(key=lambda x: x['average_compliance'])
            
            # Prepare data for plotting
            rooms = [r['room'] for r in room_data]
            temp_compliance = [r['temp_compliance'] for r in room_data]
            co2_compliance = [r['co2_compliance'] for r in room_data]
            
            # Create figure
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Set positions for bars
            x = np.arange(len(rooms))
            width = 0.35
            
            # Create bars
            bars1 = ax.bar(x - width/2, temp_compliance, width, label='Temperatur (20-26°C)', 
                          color='#ff7f0e', alpha=0.8)
            bars2 = ax.bar(x + width/2, co2_compliance, width, label='CO₂ (<1000 ppm)', 
                          color='#2ca02c', alpha=0.8)
            
            # Formatting
            ax.set_title(f'Overholdelse af Grænseværdier per Rum - {building_name.replace("_", " ").title()}', 
                        fontsize=14, fontweight='bold')
            ax.set_xlabel('Rum (sorteret fra værst til bedst)', fontsize=12)
            ax.set_ylabel('Overholdelse (%)', fontsize=12)
            ax.set_xticks(x)
            ax.set_xticklabels(rooms, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)
            
            # Add value labels on bars
            def add_labels(bars):
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                           f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
            
            add_labels(bars1)
            add_labels(bars2)
            
            plt.tight_layout()
            
            # Save chart
            building_id = building_name.lower().replace(" ", "_")
            filename = f"room_compliance_comparison_{building_id}.png"
            filepath = self.charts_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating room compliance comparison for {building_name}: {e}")
            plt.close()
            return ""

    def _generate_climate_correlation_charts(self, buildings: Dict[str, Dict[str, pd.DataFrame]]) -> Dict[str, str]:
        """Generate climate correlation charts for all buildings."""
        chart_paths = {}
        
        try:
            # Import climate analytics
            from ieq_analytics.climate_analytics import ClimateAnalytics
            
            # Initialize climate analytics with correct paths
            # Find the actual data directories relative to the current working directory
            climate_data_dir = Path("data/climate")
            if not climate_data_dir.exists():
                # Try alternative paths
                alt_paths = [
                    Path("../data/climate"),
                    Path("../../data/climate"),
                    Path.cwd() / "data" / "climate"
                ]
                for alt_path in alt_paths:
                    if alt_path.exists():
                        climate_data_dir = alt_path
                        break
            
            indoor_data_dir = Path("output/mapped_data") 
            if not indoor_data_dir.exists():
                # Try alternative paths
                alt_paths = [
                    Path("../output/mapped_data"),
                    Path("../../output/mapped_data"),
                    Path.cwd() / "output" / "mapped_data"
                ]
                for alt_path in alt_paths:
                    if alt_path.exists():
                        indoor_data_dir = alt_path
                        break
            
            if not climate_data_dir.exists():
                logger.warning(f"Climate data directory not found at {climate_data_dir} - skipping climate correlation charts")
                return chart_paths
                
            climate_analytics = ClimateAnalytics(str(climate_data_dir), str(indoor_data_dir))
            
            # Generate building-level climate correlation charts
            for building_name, building_rooms in buildings.items():
                building_id = building_name.lower().replace(" ", "_")
                
                # Generate climate correlation heatmap for building
                chart_paths[f'climate_correlation_heatmap_{building_id}'] = self._generate_climate_correlation_heatmap(
                    building_name, building_rooms, climate_analytics
                )
                
                # Generate solar sensitivity chart for building
                chart_paths[f'solar_sensitivity_{building_id}'] = self._generate_solar_sensitivity_chart(
                    building_name, building_rooms, climate_analytics
                )
                
                # Generate seasonal climate correlation chart
                chart_paths[f'seasonal_climate_correlation_{building_id}'] = self._generate_seasonal_climate_correlation(
                    building_name, building_rooms, climate_analytics
                )
        
        except Exception as e:
            logger.error(f"Error generating climate correlation charts: {e}")
        
        return chart_paths
    
    def _generate_climate_correlation_heatmap(self, building_name: str, building_rooms: Dict[str, pd.DataFrame], 
                                            climate_analytics: Any) -> str:
        """Generate climate correlation heatmap for a building."""
        try:
            # Get building mapping from Fløng to Ole Rømer for missing data
            school_mapping = {
                'floeng-skole': 'ole-roemer-skolen',
                'fløng-skole': 'ole-roemer-skolen'
            }
            
            # Load climate data for the building
            climate_analytics.load_climate_data()
            
            # Get a representative room from the building for analysis
            if not building_rooms:
                return ""
                
            sample_room_id = list(building_rooms.keys())[0]
            sample_room_df = building_rooms[sample_room_id]
            
            if sample_room_df.empty or 'temperature' not in sample_room_df.columns:
                return ""
            
            # Convert room ID to format expected by climate analytics
            # Remove '_processed' suffix if present and extract room identifier
            climate_room_id = sample_room_id.replace('_processed', '')
            
            # Determine climate school name using the same normalization as ClimateAnalytics
            # Extract school name from building_name and normalize like the indoor data loading
            if building_name.lower() in ['ole_roemer_skolen', 'ole_rømer_skolen']:
                climate_school_key = 'ole_romer'  # Normalized indoor data key
            elif building_name.lower() in ['fløng_skole', 'floeng_skole']:
                climate_school_key = 'flong_skole'  # Normalized indoor data key
            elif building_name.lower().startswith('reerslev'):
                climate_school_key = building_name.lower()  # Keep as is for reerslev
            else:
                # Default normalization
                climate_school_key = building_name.lower().replace('ø', 'o').replace('å', 'a')
                
            logger.info(f"Trying to get correlation for building: {building_name} -> climate_school_key: {climate_school_key}, room: {climate_room_id}")
            
            # Try to get correlation analysis
            correlation_results = {}
            try:
                results = climate_analytics.generate_correlation_report(
                    school_name=climate_school_key,
                    room_id=climate_room_id
                )
                if 'error' in results:
                    logger.warning(f"Climate correlation error for {building_name}: {results['error']}")
                    return ""
                correlation_results = results.get('correlations', {})
            except Exception as e:
                logger.warning(f"Could not get climate correlation for {building_name}: {e}")
                return ""
            
            if not correlation_results:
                return ""
            
            # Prepare data for heatmap
            parameters = ['mean_temp', 'mean_radiation', 'mean_relative_hum', 'bright_sunshine']
            periods = ['overall', 'high_temperature_correlation']
            
            # Create correlation matrix
            corr_matrix = []
            for period in periods:
                period_data = correlation_results.get(period, {})
                row = []
                for param in parameters:
                    correlation = period_data.get(param, {}).get('correlation', 0.0)
                    if isinstance(correlation, (tuple, list)) and len(correlation) > 0:
                        correlation = correlation[0]  # Take correlation coefficient
                    elif not isinstance(correlation, (int, float)):
                        correlation = 0.0
                    row.append(correlation)
                corr_matrix.append(row)
            
            corr_df = pd.DataFrame(corr_matrix, index=periods, columns=parameters)
            
            # Create heatmap
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create Danish labels
            period_labels = {
                'overall': 'Samlet',
                'high_temperature_correlation': 'Høje Temperaturer'
            }
            param_labels = {
                'mean_temp': 'Gennemsnits Temp.',
                'mean_radiation': 'Solindstråling',
                'mean_relative_hum': 'Fugtighed',
                'bright_sunshine': 'Solskin Timer'
            }
            
            danish_periods = [period_labels.get(p, p) for p in periods]
            danish_params = [param_labels.get(p, p) for p in parameters]
            
            # Create heatmap
            im = ax.imshow(corr_matrix, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
            
            # Set ticks and labels
            ax.set_xticks(range(len(parameters)))
            ax.set_yticks(range(len(periods)))
            ax.set_xticklabels(danish_params, rotation=45, ha='right')
            ax.set_yticklabels(danish_periods)
            
            # Add correlation values as text
            for i in range(len(periods)):
                for j in range(len(parameters)):
                    value = corr_matrix[i][j]
                    color = 'white' if abs(value) > 0.5 else 'black'
                    ax.text(j, i, f'{value:.2f}', ha='center', va='center', color=color, fontweight='bold')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Korrelation med Indendørs Temperatur', rotation=270, labelpad=20)
            
            # Formatting
            ax.set_title(f'Klima Korrelation - {building_name.replace("_", " ").title()}', 
                        fontsize=14, fontweight='bold')
            plt.tight_layout()
            
            # Save chart
            building_id = building_name.lower().replace(" ", "_")
            filename = f"climate_correlation_heatmap_{building_id}.png"
            filepath = self.charts_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating climate correlation heatmap for {building_name}: {e}")
            plt.close()
            return ""
    
    def _generate_solar_sensitivity_chart(self, building_name: str, building_rooms: Dict[str, pd.DataFrame], 
                                         climate_analytics: Any) -> str:
        """Generate solar sensitivity chart showing radiation impact on temperature."""
        try:
            # Similar setup as correlation heatmap
            school_mapping = {
                'floeng-skole': 'ole-roemer-skolen',
                'fløng-skole': 'ole-roemer-skolen'
            }
            
            if not building_rooms:
                return ""
                
            sample_room_id = list(building_rooms.keys())[0]
            
            # Convert room ID to format expected by climate analytics
            climate_room_id = sample_room_id.replace('_processed', '')
            
            # Determine climate school name using the same normalization as ClimateAnalytics
            if building_name.lower() in ['ole_roemer_skolen', 'ole_rømer_skolen']:
                climate_school_key = 'ole_romer'  # Normalized indoor data key
            elif building_name.lower() in ['fløng_skole', 'floeng_skole']:
                climate_school_key = 'flong_skole'  # Normalized indoor data key
            elif building_name.lower().startswith('reerslev'):
                climate_school_key = building_name.lower()  # Keep as is for reerslev
            else:
                # Default normalization
                climate_school_key = building_name.lower().replace('ø', 'o').replace('å', 'a')
            
            # Get sensitivity analysis
            try:
                results = climate_analytics.generate_correlation_report(
                    school_name=climate_school_key,
                    room_id=climate_room_id
                )
                sensitivity_data = results.get('solar_analysis', {})
            except Exception as e:
                logger.warning(f"Could not get solar sensitivity for {building_name}: {e}")
                return ""
            
            if not sensitivity_data:
                return ""
            
            # Create solar sensitivity chart
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Chart 1: Radiation-temperature relationship
            radiation_temp_relationship = sensitivity_data.get('radiation_temperature_relationship', {})
            peak_impact = sensitivity_data.get('peak_radiation_impact', {})
            
            # Use actual data from the analysis with safe extraction
            def safe_float_extract(data, key, default=0.0):
                """Safely extract a float value from potentially nested data."""
                try:
                    value = data.get(key, default)
                    if isinstance(value, dict):
                        # If it's a dict, try to find a numeric value
                        for k, v in value.items():
                            if isinstance(v, (int, float)):
                                return float(v)
                        return default
                    return float(value) if value is not None else default
                except (ValueError, TypeError):
                    return default
            
            categories = ['Lav Solindstråling', 'Høj Solindstråling', 'Maksimal Påvirkning']
            temp_values = [
                safe_float_extract(radiation_temp_relationship, 'low_radiation_temp', 20.0),
                safe_float_extract(radiation_temp_relationship, 'high_radiation_temp', 22.0),
                safe_float_extract(peak_impact, 'max_temp_increase', 3.0)
            ]
            
            bars1 = ax1.bar(categories, temp_values, color=['#3498db', '#f39c12', '#e74c3c'])
            ax1.set_title('Solindstrålingens Påvirkning på Temperatur', fontweight='bold')
            ax1.set_ylabel('Temperatur/Stigning (°C)')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # Add value labels
            for bar in bars1:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{height:.1f}°C', ha='center', va='bottom', fontweight='bold')
            
            # Chart 2: Shading recommendation
            recommendation = sensitivity_data.get('shading_recommendation', 'none')
            
            # Handle case where recommendation might be a dict
            if isinstance(recommendation, dict):
                # Try to extract a string value from dict
                recommendation = recommendation.get('level', 'none')
            
            # Ensure it's a string and normalize
            recommendation = str(recommendation).lower() if recommendation else 'none'
            
            recommendation_text = {
                'none': 'Ingen Solafskærmning Nødvendig',
                'consider': 'Overvej Solafskærmning',
                'priority': 'Prioriter Solafskærmning',
                'low': 'Lav Prioritet',
                'medium': 'Medium Prioritet', 
                'high': 'Høj Prioritet'
            }
            
            recommendation_colors = {
                'none': '#27ae60',
                'low': '#27ae60',
                'consider': '#f39c12',
                'medium': '#f39c12', 
                'priority': '#e74c3c',
                'high': '#e74c3c'
            }
            
            rec_text = recommendation_text.get(recommendation, 'Ukendt')
            rec_color = recommendation_colors.get(recommendation, '#95a5a6')
            
            ax2.pie([1], labels=[rec_text], colors=[rec_color], startangle=90)
            ax2.set_title('Anbefalede Foranstaltninger', fontweight='bold')
            
            plt.tight_layout()
            
            # Save chart
            building_id = building_name.lower().replace(" ", "_")
            filename = f"solar_sensitivity_{building_id}.png"
            filepath = self.charts_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating solar sensitivity chart for {building_name}: {e}")
            plt.close()
            return ""
    
    def _generate_seasonal_climate_correlation(self, building_name: str, building_rooms: Dict[str, pd.DataFrame], 
                                             climate_analytics: Any) -> str:
        """Generate seasonal climate correlation trends chart."""
        try:
            school_mapping = {
                'floeng-skole': 'ole-roemer-skolen',
                'fløng-skole': 'ole-roemer-skolen'
            }
            
            if not building_rooms:
                return ""
                
            sample_room_id = list(building_rooms.keys())[0]
            
            # Convert room ID to format expected by climate analytics
            climate_room_id = sample_room_id.replace('_processed', '')
            
            # Determine climate school name using the same normalization as ClimateAnalytics
            if building_name.lower() in ['ole_roemer_skolen', 'ole_rømer_skolen']:
                climate_school_key = 'ole_romer'  # Normalized indoor data key
            elif building_name.lower() in ['fløng_skole', 'floeng_skole']:
                climate_school_key = 'flong_skole'  # Normalized indoor data key
            elif building_name.lower().startswith('reerslev'):
                climate_school_key = building_name.lower()  # Keep as is for reerslev
            else:
                # Default normalization
                climate_school_key = building_name.lower().replace('ø', 'o').replace('å', 'a')
            
            # Get correlation analysis
            try:
                results = climate_analytics.generate_correlation_report(
                    school_name=climate_school_key,
                    room_id=climate_room_id
                )
                seasonal_correlations = results.get('correlations', {}).get('by_season', {})
            except Exception as e:
                logger.warning(f"Could not get seasonal correlation for {building_name}: {e}")
                return ""
            
            if not seasonal_correlations:
                return ""
            
            # Prepare seasonal data
            seasons = ['Winter', 'Spring', 'Summer', 'Autumn']
            season_labels = ['Vinter', 'Forår', 'Sommer', 'Efterår']
            
            parameters = ['mean_temp', 'mean_radiation']
            param_labels = ['Udendørs Temperatur', 'Solindstråling']
            param_colors = ['#e74c3c', '#f39c12']
            
            # Create line chart
            fig, ax = plt.subplots(figsize=(12, 8))
            
            for i, param in enumerate(parameters):
                correlations = []
                for season in seasons:
                    season_data = seasonal_correlations.get(season, {})
                    correlation = season_data.get(param, {}).get('correlation', 0.0)
                    if isinstance(correlation, (tuple, list)) and len(correlation) > 0:
                        correlation = correlation[0]
                    elif not isinstance(correlation, (int, float)):
                        correlation = 0.0
                    correlations.append(correlation)
                
                ax.plot(season_labels, correlations, marker='o', linewidth=3, 
                       label=param_labels[i], color=param_colors[i], markersize=8)
                
                # Add value labels
                for j, corr in enumerate(correlations):
                    ax.text(j, corr + 0.02, f'{corr:.2f}', ha='center', va='bottom', 
                           fontweight='bold', color=param_colors[i])
            
            # Formatting
            ax.set_title(f'Sæsonmæssig Klima Korrelation - {building_name.replace("_", " ").title()}', 
                        fontsize=14, fontweight='bold')
            ax.set_ylabel('Korrelation med Indendørs Temperatur', fontsize=12)
            ax.set_xlabel('Årstid', fontsize=12)
            ax.legend(fontsize=11)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(-0.1, 1.0)
            
            # Add horizontal reference lines
            ax.axhline(y=0.3, color='gray', linestyle='--', alpha=0.5, label='Svag korrelation')
            ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Moderat korrelation')
            ax.axhline(y=0.7, color='red', linestyle='--', alpha=0.5, label='Stærk korrelation')
            
            plt.tight_layout()
            
            # Save chart
            building_id = building_name.lower().replace(" ", "_")
            filename = f"seasonal_climate_correlation_{building_id}.png"
            filepath = self.charts_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating seasonal climate correlation for {building_name}: {e}")
            plt.close()
            return ""

    def generate_detailed_compliance_chart(self, room_name: str, compliance_data: Dict[str, Any]) -> str:
        """Generate detailed compliance analysis chart with separated temperature and CO2 thresholds."""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # Initialize variables
            periods = []
            period_labels = []
            
            # Temperature compliance breakdown
            temp_data = compliance_data.get('temperature_compliance', {})
            if temp_data:
                periods = list(temp_data.keys())
                period_labels = [compliance_data.get('period_analysis', {}).get(p, {}).get('description', p).split(':')[0] for p in periods]
                
                # Temperature thresholds
                below_20 = [temp_data[p].get('below_20_percentage', 0) for p in periods]
                comfort_20_26 = [temp_data[p].get('comfort_zone_20_26_percentage', 0) for p in periods]
                optimal_21_24 = [temp_data[p].get('optimal_zone_21_24_percentage', 0) for p in periods]
                above_26 = [temp_data[p].get('above_26_percentage', 0) for p in periods]
                above_27 = [temp_data[p].get('above_27_percentage', 0) for p in periods]
                
                x = np.arange(len(periods))
                width = 0.15
                
                ax1.bar(x - 2*width, below_20, width, label='< 20°C', color='#3498db', alpha=0.8)
                ax1.bar(x - width, comfort_20_26, width, label='20-26°C (Komfort)', color='#2ecc71', alpha=0.8)
                ax1.bar(x, optimal_21_24, width, label='21-24°C (Optimal)', color='#27ae60', alpha=0.8)
                ax1.bar(x + width, above_26, width, label='> 26°C', color='#f39c12', alpha=0.8)
                ax1.bar(x + 2*width, above_27, width, label='> 27°C', color='#e74c3c', alpha=0.8)
                
                ax1.set_title(f'Temperatur Overholdelse - {room_name}', fontweight='bold')
                ax1.set_ylabel('Procentdel af Timer (%)')
                ax1.set_xticks(x)
                ax1.set_xticklabels(period_labels, rotation=45, ha='right')
                ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                ax1.grid(True, alpha=0.3)
                ax1.set_ylim(0, 100)
            
            # CO2 compliance breakdown
            co2_data = compliance_data.get('co2_compliance', {})
            if co2_data:
                below_1000 = [co2_data[p].get('below_1000_percentage', 0) for p in periods]
                below_2000 = [co2_data[p].get('below_2000_percentage', 0) for p in periods]
                between_1000_2000 = [co2_data[p].get('between_1000_2000_percentage', 0) for p in periods]
                above_2000 = [co2_data[p].get('above_2000_percentage', 0) for p in periods]
                
                x = np.arange(len(periods))
                width = 0.2
                
                ax2.bar(x - 1.5*width, below_1000, width, label='< 1000ppm', color='#2ecc71', alpha=0.8)
                ax2.bar(x - 0.5*width, below_2000, width, label='< 2000ppm', color='#3498db', alpha=0.8)
                ax2.bar(x + 0.5*width, between_1000_2000, width, label='1000-2000ppm', color='#f39c12', alpha=0.8)
                ax2.bar(x + 1.5*width, above_2000, width, label='> 2000ppm', color='#e74c3c', alpha=0.8)
                
                ax2.set_title(f'CO₂ Overholdelse - {room_name}', fontweight='bold')
                ax2.set_ylabel('Procentdel af Timer (%)')
                ax2.set_xticks(x)
                ax2.set_xticklabels(period_labels, rotation=45, ha='right')
                ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                ax2.grid(True, alpha=0.3)
                ax2.set_ylim(0, 100)
            
            # Period analysis summary (pie chart of hours)
            period_analysis = compliance_data.get('period_analysis', {})
            if period_analysis:
                period_hours = [period_analysis[p].get('total_hours', 0) for p in periods]
                if sum(period_hours) > 0:
                    colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6'][:len(periods)]
                    ax3.pie(period_hours, labels=period_labels, autopct='%1.1f%%', colors=colors, startangle=90)
                    ax3.set_title('Fordeling af Analyseperioder', fontweight='bold')
            
            # Combined compliance heatmap
            if temp_data and co2_data:
                # Create heatmap data
                metrics = ['< 20°C', '20-26°C', '> 26°C', '> 27°C', '< 1000ppm', '< 2000ppm', '> 2000ppm']
                heatmap_data = []
                
                for period in periods:
                    period_data = [
                        temp_data[period].get('below_20_percentage', 0),
                        temp_data[period].get('comfort_zone_20_26_percentage', 0),
                        temp_data[period].get('above_26_percentage', 0),
                        temp_data[period].get('above_27_percentage', 0),
                        co2_data[period].get('below_1000_percentage', 0),
                        co2_data[period].get('below_2000_percentage', 0),
                        co2_data[period].get('above_2000_percentage', 0)
                    ]
                    heatmap_data.append(period_data)
                
                heatmap_data = np.array(heatmap_data)
                
                # Create custom colormap for compliance (green good, red bad)
                from matplotlib.colors import LinearSegmentedColormap
                from matplotlib.lines import Line2D
                cmap = plt.cm.get_cmap('RdYlGn_r')  # Reversed so red is high (bad for violations)
                
                im = ax4.imshow(heatmap_data.T, cmap=cmap, aspect='auto', vmin=0, vmax=100)
                
                ax4.set_xticks(range(len(periods)))
                ax4.set_xticklabels(period_labels, rotation=45, ha='right')
                ax4.set_yticks(range(len(metrics)))
                ax4.set_yticklabels(metrics)
                ax4.set_title('Overholdelsesmønster', fontweight='bold')
                
                # Add text annotations
                for i in range(len(periods)):
                    for j in range(len(metrics)):
                        text = ax4.text(i, j, f'{heatmap_data[i, j]:.1f}%', 
                                      ha="center", va="center", color="black" if heatmap_data[i, j] < 50 else "white",
                                      fontsize=8, fontweight='bold')
                
                # Add colorbar
                cbar = fig.colorbar(im, ax=ax4, shrink=0.8)
                cbar.set_label('Procentdel (%)', rotation=270, labelpad=20)
            
            plt.tight_layout()
            
            room_id = room_name.lower().replace(" ", "_").replace("-", "_")
            chart_path = self.charts_dir / f"detailed_compliance_{room_id}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"Error generating detailed compliance chart for {room_name}: {e}")
            plt.close()
            return ""

    def generate_building_compliance_summary(self, building_name: str, building_rooms: Dict[str, Any]) -> str:
        """Generate building-level compliance summary chart."""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))
            
            # Collect room compliance data
            room_names = []
            temp_below_20 = []
            temp_above_26 = []
            temp_above_27 = []
            co2_above_1000 = []
            co2_above_2000 = []
            
            for room_name, room_data in building_rooms.items():
                if 'basic_statistics' in room_data and 'compliance_analysis' in room_data['basic_statistics']:
                    compliance = room_data['basic_statistics']['compliance_analysis']
                    
                    # Get opening hours data (most relevant)
                    opening_hours_temp = compliance.get('temperature_compliance', {}).get('opening_hours', {})
                    opening_hours_co2 = compliance.get('co2_compliance', {}).get('opening_hours', {})
                    
                    if opening_hours_temp and opening_hours_co2:
                        room_names.append(room_name[:15] + '...' if len(room_name) > 15 else room_name)
                        temp_below_20.append(opening_hours_temp.get('below_20_percentage', 0))
                        temp_above_26.append(opening_hours_temp.get('above_26_percentage', 0))
                        temp_above_27.append(opening_hours_temp.get('above_27_percentage', 0))
                        co2_above_1000.append(opening_hours_co2.get('above_1000_percentage', 0))
                        co2_above_2000.append(opening_hours_co2.get('above_2000_percentage', 0))
            
            if not room_names:
                # No data available
                ax1.text(0.5, 0.5, 'Ingen data tilgængelig', ha='center', va='center', transform=ax1.transAxes)
                ax2.text(0.5, 0.5, 'Ingen data tilgængelig', ha='center', va='center', transform=ax2.transAxes)
            else:
                # Temperature violations chart
                x = np.arange(len(room_names))
                width = 0.25
                
                bars1 = ax1.bar(x - width, temp_below_20, width, label='< 20°C', color='#3498db', alpha=0.8)
                bars2 = ax1.bar(x, temp_above_26, width, label='> 26°C', color='#f39c12', alpha=0.8)
                bars3 = ax1.bar(x + width, temp_above_27, width, label='> 27°C', color='#e74c3c', alpha=0.8)
                
                ax1.set_title(f'Temperatur Problemer (Åbningstid) - {building_name.replace("_", " ").title()}', fontweight='bold')
                ax1.set_ylabel('Procentdel af Timer (%)')
                ax1.set_xlabel('Rum')
                ax1.set_xticks(x)
                ax1.set_xticklabels(room_names, rotation=45, ha='right')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # Add value labels on bars
                for bars in [bars1, bars2, bars3]:
                    for bar in bars:
                        height = bar.get_height()
                        if height > 0:
                            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                                   f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
                
                # CO2 violations chart
                bars4 = ax2.bar(x - width/2, co2_above_1000, width, label='> 1000ppm', color='#f39c12', alpha=0.8)
                bars5 = ax2.bar(x + width/2, co2_above_2000, width, label='> 2000ppm', color='#e74c3c', alpha=0.8)
                
                ax2.set_title(f'CO₂ Problemer (Åbningstid) - {building_name.replace("_", " ").title()}', fontweight='bold')
                ax2.set_ylabel('Procentdel af Timer (%)')
                ax2.set_xlabel('Rum')
                ax2.set_xticks(x)
                ax2.set_xticklabels(room_names, rotation=45, ha='right')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                
                # Add value labels on bars
                for bars in [bars4, bars5]:
                    for bar in bars:
                        height = bar.get_height()
                        if height > 0:
                            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                                   f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
            
            plt.tight_layout()
            
            building_id = building_name.lower().replace(" ", "_").replace("-", "_")
            chart_path = self.charts_dir / f"building_compliance_summary_{building_id}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"Error generating building compliance summary for {building_name}: {e}")
            plt.close()
            return ""


def generate_htk_charts_from_mapped_data(mapped_data: Dict[str, pd.DataFrame], charts_dir: Path, config) -> Dict[str, str]:
    """Generate all HTK charts using actual mapped data."""
    generator = HTKChartGenerator(charts_dir, config)
    return generator.generate_all_charts_from_mapped_data(mapped_data)
