"""
Climate Analytics Module

This module provides correlation analysis between outdoor climate conditions
and indoor environmental parameters, with focus on identifying sensitivity
to solar radiation and temperature for solar shading assessment.
"""

import pandas as pd
import numpy as np
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr
from scipy import stats

logger = logging.getLogger(__name__)


class ClimateAnalytics:
    """Analytics engine for climate-indoor correlation analysis."""
    
    def __init__(self, climate_data_dir: str, indoor_data_dir: str):
        """Initialize climate analytics with data directories."""
        self.climate_data_dir = Path(climate_data_dir)
        self.indoor_data_dir = Path(indoor_data_dir)
        self.climate_data = {}
        self.indoor_data = {}
        
    def load_climate_data(self) -> Dict[str, pd.DataFrame]:
        """Load and pivot all climate data files."""
        logger.info("Loading climate data...")
        
        climate_files = glob.glob(str(self.climate_data_dir / "climate_data_*.csv"))
        
        for file_path in climate_files:
            file_name = Path(file_path).stem
            school_name = file_name.replace("climate_data_", "").replace("_2024-01-01_to_2024-12-31", "")
            
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Pivot the data: columns as parameters, index as timestamp, values as value
            pivoted_df = df.pivot_table(
                index='timestamp', 
                columns='parameter', 
                values='value', 
                aggfunc='first'
            ).reset_index()
            
            # Clean column names and ensure they're valid
            pivoted_df.columns.name = None
            
            self.climate_data[school_name] = pivoted_df
            logger.info(f"Loaded climate data for {school_name}: {pivoted_df.shape[0]} records, parameters: {list(pivoted_df.columns[1:])}")
            
        return self.climate_data
    
    def load_indoor_data(self) -> Dict[str, pd.DataFrame]:
        """Load all indoor sensor data files."""
        logger.info("Loading indoor data...")
        
        indoor_files = glob.glob(str(self.indoor_data_dir / "*_processed.csv"))
        
        for file_path in indoor_files:
            file_name = Path(file_path).stem.replace("_processed", "")
            
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Extract school name from filename
            school_name = file_name.split('_')[0] + '_' + file_name.split('_')[1] if '_' in file_name else file_name
            school_name = school_name.replace('ø', 'o').replace('å', 'a')  # normalize names
            
            if school_name not in self.indoor_data:
                self.indoor_data[school_name] = {}
            
            self.indoor_data[school_name][file_name] = df
            logger.info(f"Loaded indoor data for {file_name}: {df.shape[0]} records")
            
        return self.indoor_data
    
    def merge_climate_indoor_data(self, school_name: str, room_id: str) -> pd.DataFrame:
        """Merge climate and indoor data for a specific school and room."""
        # Find matching climate data based on school mapping
        climate_df = None
        
        # Map indoor school names to climate school names
        school_mapping = {
            'flong_skole': 'floeng-skole',
            'ole_romer': 'ole-roemer-skolen',
            'reerslev': 'reerslev'
        }
        
        # Handle reerslev special cases (multiple entries)
        if school_name.startswith('reerslev_'):
            climate_key = 'reerslev'
        else:
            climate_key = school_mapping.get(school_name, school_name)
        
        # Get climate data
        if climate_key in self.climate_data:
            climate_df = self.climate_data[climate_key].copy()
        
        # Special handling for Fløng Skolen - use Ole Rømer Skolen data for missing parameters
        if climate_key == 'floeng-skole':
            logger.info(f"Processing Fløng Skolen with fallback data for missing parameters")
            
            # Get Fløng Skolen's own data (for radiation)
            floeng_df = self.climate_data.get('floeng-skole')
            
            # Get Ole Rømer Skolen data as fallback
            ole_roemer_df = self.climate_data.get('ole-roemer-skolen')
            
            if ole_roemer_df is not None:
                if floeng_df is not None:
                    # Merge Fløng's radiation data with Ole Rømer's other parameters
                    logger.info("Combining Fløng Skolen radiation data with Ole Rømer Skolen other parameters")
                    
                    # Use Ole Rømer as base
                    climate_df = ole_roemer_df.copy()
                    
                    # Replace radiation data with Fløng's if available
                    if 'mean_radiation' in floeng_df.columns and 'mean_radiation' in climate_df.columns:
                        # Merge on timestamp to get Fløng's radiation
                        floeng_radiation = floeng_df[['timestamp', 'mean_radiation']].copy()
                        floeng_radiation.columns = ['timestamp', 'floeng_radiation']
                        
                        climate_df = climate_df.merge(floeng_radiation, on='timestamp', how='left')
                        # Use Fløng's radiation where available, fallback to Ole Rømer's
                        climate_df['mean_radiation'] = climate_df['floeng_radiation'].fillna(climate_df['mean_radiation'])
                        climate_df = climate_df.drop('floeng_radiation', axis=1)
                    
                    if 'bright_sunshine' in floeng_df.columns and 'bright_sunshine' in climate_df.columns:
                        # Same for sunshine data
                        floeng_sunshine = floeng_df[['timestamp', 'bright_sunshine']].copy()
                        floeng_sunshine.columns = ['timestamp', 'floeng_sunshine']
                        
                        climate_df = climate_df.merge(floeng_sunshine, on='timestamp', how='left')
                        climate_df['bright_sunshine'] = climate_df['floeng_sunshine'].fillna(climate_df['bright_sunshine'])
                        climate_df = climate_df.drop('floeng_sunshine', axis=1)
                        
                    logger.info("Successfully combined climate data for Fløng Skolen")
                else:
                    # Use Ole Rømer data entirely
                    climate_df = ole_roemer_df.copy()
                    logger.info("Using Ole Rømer Skolen climate data entirely for Fløng Skolen")
            else:
                logger.warning(f"No Ole Rømer fallback data available")
        
        if climate_df is None:
            logger.warning(f"No climate data found for school: {school_name} (mapped to {climate_key})")
            return pd.DataFrame()
        
        # Get indoor data
        if school_name not in self.indoor_data or room_id not in self.indoor_data[school_name]:
            logger.warning(f"No indoor data found for {school_name} - {room_id}")
            return pd.DataFrame()
        
        indoor_df = self.indoor_data[school_name][room_id].copy()
        
        # Merge on timestamp (hourly alignment)
        climate_df['timestamp_hour'] = climate_df['timestamp'].dt.floor('h')
        indoor_df['timestamp_hour'] = indoor_df['timestamp'].dt.floor('h')
        
        # Handle timezone issues by converting both to UTC
        if climate_df['timestamp_hour'].dt.tz is not None:
            climate_df['timestamp_hour'] = climate_df['timestamp_hour'].dt.tz_convert('UTC')
        else:
            climate_df['timestamp_hour'] = climate_df['timestamp_hour'].dt.tz_localize('UTC')
            
        if indoor_df['timestamp_hour'].dt.tz is not None:
            indoor_df['timestamp_hour'] = indoor_df['timestamp_hour'].dt.tz_convert('UTC')
        else:
            indoor_df['timestamp_hour'] = indoor_df['timestamp_hour'].dt.tz_localize('UTC')
        
        merged_df = pd.merge(
            indoor_df, 
            climate_df, 
            on='timestamp_hour', 
            how='inner',
            suffixes=('_indoor', '_climate')
        )
        
        logger.info(f"Merged data for {school_name} - {room_id}: {merged_df.shape[0]} records")
        return merged_df
    
    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features for temporal analysis."""
        df = df.copy()
        df['hour'] = df['timestamp_hour'].dt.hour
        df['month'] = df['timestamp_hour'].dt.month
        df['season'] = df['month'].map({
            12: 'Winter', 1: 'Winter', 2: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Autumn', 10: 'Autumn', 11: 'Autumn'
        })
        df['day_period'] = df['hour'].map(lambda x: 
            'Night' if x < 6 or x >= 22 else
            'Morning' if x < 12 else
            'Afternoon' if x < 18 else
            'Evening'
        )
        df['weekday'] = df['timestamp_hour'].dt.dayofweek
        df['is_weekend'] = df['weekday'].isin([5, 6])
        
        return df
    
    def calculate_correlations(self, df: pd.DataFrame, 
                             climate_params: Optional[List[str]] = None,
                             indoor_param: str = 'temperature') -> Dict[str, Any]:
        """Calculate correlations between climate and indoor parameters."""
        if df.empty:
            return {}
        
        if climate_params is None:
            # Default climate parameters
            available_climate = [col for col in df.columns if col not in 
                               ['timestamp_indoor', 'timestamp_climate', 'timestamp_hour', 
                                'temperature', 'humidity', 'co2', 'hour', 'month', 
                                'season', 'day_period', 'weekday', 'is_weekend']]
            climate_params = available_climate
        
        results = {
            'overall': {},
            'by_month': {},
            'by_season': {},
            'by_day_period': {},
            'high_temperature_correlation': {}
        }
        
        # Overall correlations
        for param in climate_params:
            if param in df.columns and indoor_param in df.columns:
                valid_data = df[[param, indoor_param]].dropna()
                if len(valid_data) > 10:  # Need sufficient data
                    pearson_r, pearson_p = pearsonr(valid_data[param], valid_data[indoor_param])
                    spearman_r, spearman_p = spearmanr(valid_data[param], valid_data[indoor_param])
                    
                    results['overall'][param] = {
                        'pearson_r': pearson_r,
                        'pearson_p': pearson_p,
                        'spearman_r': spearman_r,
                        'spearman_p': spearman_p,
                        'n_samples': len(valid_data)
                    }
        
        # Correlations by month
        for month in df['month'].unique():
            if pd.isna(month):
                continue
            month_data = df[df['month'] == month]
            month_results = {}
            
            for param in climate_params:
                if param in month_data.columns and indoor_param in month_data.columns:
                    valid_data = month_data[[param, indoor_param]].dropna()
                    if len(valid_data) > 10:
                        pearson_r, pearson_p = pearsonr(valid_data[param], valid_data[indoor_param])
                        month_results[param] = {
                            'pearson_r': pearson_r,
                            'pearson_p': pearson_p,
                            'n_samples': len(valid_data)
                        }
            
            results['by_month'][int(month)] = month_results
        
        # Correlations by season
        for season in df['season'].unique():
            if pd.isna(season):
                continue
            season_data = df[df['season'] == season]
            season_results = {}
            
            for param in climate_params:
                if param in season_data.columns and indoor_param in season_data.columns:
                    valid_data = season_data[[param, indoor_param]].dropna()
                    if len(valid_data) > 10:
                        pearson_r, pearson_p = pearsonr(valid_data[param], valid_data[indoor_param])
                        season_results[param] = {
                            'pearson_r': pearson_r,
                            'pearson_p': pearson_p,
                            'n_samples': len(valid_data)
                        }
            
            results['by_season'][season] = season_results
        
        # Correlations by day period
        for period in df['day_period'].unique():
            if pd.isna(period):
                continue
            period_data = df[df['day_period'] == period]
            period_results = {}
            
            for param in climate_params:
                if param in period_data.columns and indoor_param in period_data.columns:
                    valid_data = period_data[[param, indoor_param]].dropna()
                    if len(valid_data) > 10:
                        pearson_r, pearson_p = pearsonr(valid_data[param], valid_data[indoor_param])
                        period_results[param] = {
                            'pearson_r': pearson_r,
                            'pearson_p': pearson_p,
                            'n_samples': len(valid_data)
                        }
            
            results['by_day_period'][period] = period_results
        
        # High temperature correlation analysis (focus on temperatures > 75th percentile)
        if indoor_param in df.columns:
            temp_threshold = df[indoor_param].quantile(0.75)
            high_temp_data = df[df[indoor_param] >= temp_threshold]
            
            for param in climate_params:
                if param in high_temp_data.columns:
                    valid_data = high_temp_data[[param, indoor_param]].dropna()
                    if len(valid_data) > 10:
                        pearson_r, pearson_p = pearsonr(valid_data[param], valid_data[indoor_param])
                        results['high_temperature_correlation'][param] = {
                            'pearson_r': pearson_r,
                            'pearson_p': pearson_p,
                            'n_samples': len(valid_data),
                            'temperature_threshold': temp_threshold
                        }
        
        return results
    
    def analyze_solar_sensitivity(self, df: pd.DataFrame, 
                                 radiation_param: str = 'mean_radiation',
                                 indoor_param: str = 'temperature') -> Dict[str, Any]:
        """Specific analysis for solar radiation sensitivity assessment."""
        if df.empty or radiation_param not in df.columns or indoor_param not in df.columns:
            return {}
        
        results = {
            'radiation_temperature_relationship': {},
            'peak_radiation_impact': {},
            'seasonal_sensitivity': {},
            'shading_recommendation': {}
        }
        
        # Filter valid data
        valid_data = df[[radiation_param, indoor_param, 'hour', 'month', 'season']].dropna()
        
        if len(valid_data) < 10:
            return results
        
        # Overall radiation-temperature relationship
        pearson_result = pearsonr(valid_data[radiation_param], valid_data[indoor_param])
        pearson_r = float(pearson_result[0])  # type: ignore
        pearson_p = float(pearson_result[1])  # type: ignore
        
        results['radiation_temperature_relationship'] = {
            'correlation': pearson_r,
            'p_value': pearson_p,
            'strength': 'Strong' if abs(pearson_r) > 0.7 else 'Moderate' if abs(pearson_r) > 0.4 else 'Weak',
            'significance': 'Significant' if pearson_p < 0.05 else 'Not significant'
        }
        
        # Peak radiation impact (high radiation periods)
        radiation_threshold = valid_data[radiation_param].quantile(0.8)
        high_radiation = valid_data[valid_data[radiation_param] >= radiation_threshold]
        
        if len(high_radiation) > 5:
            temp_increase = high_radiation[indoor_param].mean() - valid_data[indoor_param].mean()
            results['peak_radiation_impact'] = {
                'temperature_increase_celsius': temp_increase,
                'high_radiation_threshold': radiation_threshold,
                'high_radiation_periods': len(high_radiation),
                'max_temperature_during_high_radiation': high_radiation[indoor_param].max()
            }
        
        # Seasonal sensitivity
        for season in valid_data['season'].unique():
            season_data = valid_data[valid_data['season'] == season]
            if len(season_data) > 10:
                pearson_r, pearson_p = pearsonr(season_data[radiation_param], season_data[indoor_param])
                results['seasonal_sensitivity'][season] = {
                    'correlation': pearson_r,
                    'p_value': pearson_p,
                    'mean_radiation': season_data[radiation_param].mean(),
                    'mean_temperature': season_data[indoor_param].mean()
                }
        
        # Shading recommendation logic
        overall_corr = results['radiation_temperature_relationship']['correlation']
        significance = results['radiation_temperature_relationship']['significance']
        
        if significance == 'Significant' and overall_corr > 0.5:
            if overall_corr > 0.7:
                recommendation = "HIGH PRIORITY: Strong solar sensitivity detected. Solar shading strongly recommended."
                priority = "High"
            elif overall_corr > 0.5:
                recommendation = "MODERATE PRIORITY: Moderate solar sensitivity. Consider solar shading solutions."
                priority = "Medium"
            else:
                recommendation = "LOW PRIORITY: Weak solar sensitivity. Solar shading may provide minor benefits."
                priority = "Low"
        else:
            recommendation = "Solar shading not necessary. Room shows little sensitivity to solar radiation."
            priority = "None"
        
        results['shading_recommendation'] = {
            'recommendation': recommendation,
            'priority': priority,
            'correlation_strength': overall_corr
        }
        
        return results
    
    def generate_correlation_report(self, school_name: str, room_id: str) -> Dict[str, Any]:
        """Generate comprehensive correlation report for a specific room."""
        logger.info(f"Generating correlation report for {school_name} - {room_id}")
        
        # Ensure data is loaded
        if not self.climate_data:
            self.load_climate_data()
        if not self.indoor_data:
            self.load_indoor_data()
        
        # Merge data
        merged_df = self.merge_climate_indoor_data(school_name, room_id)
        if merged_df.empty:
            return {'error': f'No data available for {school_name} - {room_id}'}
        
        # Add time features
        merged_df = self.add_time_features(merged_df)
        
        # Available climate parameters
        climate_params = [col for col in merged_df.columns if col not in 
                         ['timestamp_indoor', 'timestamp_climate', 'timestamp_hour', 
                          'temperature', 'humidity', 'co2', 'hour', 'month', 
                          'season', 'day_period', 'weekday', 'is_weekend']]
        
        report = {
            'metadata': {
                'school_name': school_name,
                'room_id': room_id,
                'analysis_period': {
                    'start': merged_df['timestamp_hour'].min().isoformat(),
                    'end': merged_df['timestamp_hour'].max().isoformat()
                },
                'total_records': len(merged_df),
                'climate_parameters': climate_params
            },
            'correlations': self.calculate_correlations(merged_df, climate_params),
            'solar_analysis': self.analyze_solar_sensitivity(merged_df) if 'mean_radiation' in climate_params else {},
            'summary_statistics': {
                'indoor_temperature': {
                    'mean': merged_df['temperature'].mean(),
                    'std': merged_df['temperature'].std(),
                    'min': merged_df['temperature'].min(),
                    'max': merged_df['temperature'].max(),
                    'q75': merged_df['temperature'].quantile(0.75)
                }
            }
        }
        
        # Add summary for each climate parameter
        for param in climate_params:
            if param in merged_df.columns:
                report['summary_statistics'][param] = {
                    'mean': merged_df[param].mean(),
                    'std': merged_df[param].std(),
                    'min': merged_df[param].min(),
                    'max': merged_df[param].max()
                }
        
        return report
    
    def analyze_all_rooms(self) -> Dict[str, Dict[str, Any]]:
        """Generate correlation reports for all available rooms."""
        logger.info("Analyzing all rooms for climate correlations...")
        
        # Load data
        self.load_climate_data()
        self.load_indoor_data()
        
        all_reports = {}
        
        for school_name, rooms in self.indoor_data.items():
            for room_id in rooms.keys():
                try:
                    report = self.generate_correlation_report(school_name, room_id)
                    all_reports[f"{school_name}_{room_id}"] = report
                except Exception as e:
                    logger.error(f"Error analyzing {school_name} - {room_id}: {str(e)}")
                    all_reports[f"{school_name}_{room_id}"] = {'error': str(e)}
        
        return all_reports
    
    def create_correlation_visualization(self, merged_df: pd.DataFrame, 
                                       climate_param: str = 'mean_radiation',
                                       indoor_param: str = 'temperature',
                                       output_path: Optional[str] = None) -> str:
        """Create correlation visualization plots."""
        if merged_df.empty or climate_param not in merged_df.columns:
            return ""
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Climate-Indoor Correlation Analysis: {climate_param} vs {indoor_param}', fontsize=16)
        
        # Overall scatter plot
        axes[0, 0].scatter(merged_df[climate_param], merged_df[indoor_param], alpha=0.6)
        axes[0, 0].set_xlabel(climate_param.replace('_', ' ').title())
        axes[0, 0].set_ylabel(indoor_param.replace('_', ' ').title())
        axes[0, 0].set_title('Overall Correlation')
        
        # Add trend line
        z = np.polyfit(merged_df[climate_param].dropna(), merged_df[indoor_param].dropna(), 1)
        p = np.poly1d(z)
        axes[0, 0].plot(merged_df[climate_param], p(merged_df[climate_param]), "r--", alpha=0.8)
        
        # Seasonal correlation
        for season in merged_df['season'].unique():
            if not pd.isna(season):
                season_data = merged_df[merged_df['season'] == season]
                axes[0, 1].scatter(season_data[climate_param], season_data[indoor_param], 
                                 label=season, alpha=0.6)
        axes[0, 1].set_xlabel(climate_param.replace('_', ' ').title())
        axes[0, 1].set_ylabel(indoor_param.replace('_', ' ').title())
        axes[0, 1].set_title('Seasonal Correlation')
        axes[0, 1].legend()
        
        # Daily pattern
        def compute_hourly_corr(group):
            try:
                if len(group) > 5:
                    corr_result = pearsonr(group[climate_param].dropna(), group[indoor_param].dropna())
                    return float(corr_result[0])  # type: ignore
                else:
                    return np.nan
            except:
                return np.nan
        
        hourly_corr = merged_df.groupby('hour').apply(compute_hourly_corr)
        axes[1, 0].plot(hourly_corr.index, hourly_corr.values, marker='o')
        axes[1, 0].set_xlabel('Hour of Day')
        axes[1, 0].set_ylabel('Correlation Coefficient')
        axes[1, 0].set_title('Hourly Correlation Pattern')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Monthly correlation
        def compute_monthly_corr(group):
            try:
                if len(group) > 10:
                    corr_result = pearsonr(group[climate_param].dropna(), group[indoor_param].dropna())
                    return float(corr_result[0])  # type: ignore
                else:
                    return np.nan
            except:
                return np.nan
                
        monthly_corr = merged_df.groupby('month').apply(compute_monthly_corr)
        axes[1, 1].bar(monthly_corr.index, monthly_corr.values)
        axes[1, 1].set_xlabel('Month')
        axes[1, 1].set_ylabel('Correlation Coefficient')
        axes[1, 1].set_title('Monthly Correlation')
        axes[1, 1].set_xticks(range(1, 13))
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            return output_path
        else:
            plt.show()
            return ""
