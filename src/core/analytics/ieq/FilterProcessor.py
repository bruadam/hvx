
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from pathlib import Path
import logging
import yaml
import json

from .types import Method, RuleType

logger = logging.getLogger(__name__)

import holidays

class FilterProcessor:
    """Unified processor for all time-based filtering."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, years: Optional[List[int]] = None):
        """Initialize with configuration."""
        self.config = config or {}
        self.periods = self.config.get('periods', {})
        self.filters = self.config.get('filters', {})
        self.holidays_config = self.config.get('holidays', {})
        self.holiday_cache = {}
        self.years = years or [datetime.now().year]
        
        # Default configurations
        self.default_opening_hours = [8, 9, 10, 11, 12, 13, 14, 15]
        self._load_default_periods()
        self._load_default_filters()
        
        # Log loaded filters for debugging
        logger.info(f"UnifiedFilterProcessor initialized with {len(self.filters)} filters: {list(self.filters.keys())}")
    
    def _load_default_periods(self):
        """Load default period definitions."""
        if not self.periods:
            self.periods = {
                'all_year': {'months': list(range(1, 13))},
                'spring': {'months': [3, 4, 5]},
                'summer': {'months': [6, 7, 8]},
                'autumn': {'months': [9, 10, 11]},
                'winter': {'months': [12, 1, 2]},
            }
    
    def _load_default_filters(self):
        """Load default filter definitions and merge with config filters."""
        default_filters = {
            'opening_hours': {
                'hours': self.default_opening_hours,
                'weekdays_only': True,
                'exclude_holidays': True
            },
            'school_opening_hours': {
                'hours': self.default_opening_hours,
                'weekdays_only': True,
                'exclude_holidays': True
            },
            'all_hours': {
                'hours': list(range(24)),
                'weekdays_only': False,
                'exclude_holidays': False
            },
            'weekends_only': {
                'hours': list(range(24)),
                'weekdays_only': False,
                'weekends_only': True,
                'exclude_holidays': False
            },
            'outside_hours': {
                'exclude_opening_hours': True,
                'include_weekends': True,
                'include_holidays': True
            }
        }
        
        # Merge defaults with config filters (config takes precedence)
        if self.filters:
            # Config has filters, merge defaults for any missing ones
            for key, value in default_filters.items():
                if key not in self.filters:
                    self.filters[key] = value
        else:
            # No config filters, use all defaults
            self.filters = default_filters
    
    def apply_filter(
        self, 
        df: pd.DataFrame, 
        filter_name: str = 'all_hours',
        period_name: str = 'all_year'
    ) -> pd.DataFrame:
        """
        Apply time-based filter to DataFrame.
        
        Args:
            df: DataFrame with datetime index
            filter_name: Name of filter to apply
            period_name: Name of period to apply
            
        Returns:
            Filtered DataFrame
        """
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return df
        
        # Apply period filter first
        filtered_df = self._apply_period_filter(df, period_name)
        
        # Apply time filter
        filtered_df = self._apply_time_filter(filtered_df, filter_name)
        
        return filtered_df
    
    def _apply_period_filter(self, df: pd.DataFrame, period_name: str) -> pd.DataFrame:
        """Apply period-based filtering."""
        if period_name == 'all_year' or period_name not in self.periods:
            return df
        
        period_config = self.periods[period_name]
        months = period_config.get('months', [])
        
        if months:
            # Ensure index is datetime
            df.index = pd.to_datetime(df.index)
            return df[df.index.month.isin(months)]
        
        return df
    
    def _apply_time_filter(self, df: pd.DataFrame, filter_name: str) -> pd.DataFrame:
        """Apply time-based filtering."""
        if filter_name == 'all_hours':
            return df
        
        if filter_name not in self.filters:
            logger.warning(f"Filter '{filter_name}' not found in configuration. Available filters: {list(self.filters.keys())}")
            return df
        
        filter_config = self.filters[filter_name]
        filtered_df = df.copy()
        # Ensure index is datetime on filtered_df
        filtered_df.index = pd.to_datetime(filtered_df.index)
        
        # Handle special outside_hours filter
        if filter_config.get('exclude_opening_hours', False):
            opening_hours = self.default_opening_hours
            outside_hours = [h for h in range(24) if h not in opening_hours]
            mask = filtered_df.index.hour.isin(outside_hours)
            
            if filter_config.get('include_weekends', True):
                mask |= filtered_df.index.weekday >= 5
            
            if filter_config.get('include_holidays', True):
                holiday_mask = self._get_holiday_mask(filtered_df)
                mask |= holiday_mask
            
            return filtered_df[mask]
        
        # Regular hour filtering
        hours = filter_config.get('hours', list(range(24)))
        filtered_df = filtered_df[filtered_df.index.hour.isin(hours)]
        
        # Weekday filtering
        if filter_config.get('weekdays_only', False):
            if isinstance(filtered_df.index, pd.DatetimeIndex):
                filtered_df = filtered_df[filtered_df.index.weekday < 5]
        elif filter_config.get('weekends_only', False):
            if isinstance(filtered_df.index, pd.DatetimeIndex):
                filtered_df = filtered_df[filtered_df.index.weekday >= 5]
        
        # Holiday filtering
        if filter_config.get('exclude_holidays', False):
            holiday_mask = self._get_holiday_mask(filtered_df)
            filtered_df = filtered_df[~holiday_mask]
        
        return filtered_df
    
    def _get_holiday_mask(self, df: pd.DataFrame) -> pd.Series:
        """Get boolean mask for holiday dates."""
        # Extract years from the DataFrame to get holidays for the actual data period
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return pd.Series([False] * len(df), index=df.index)
        
        df.index = pd.to_datetime(df.index)
        data_years = sorted(df.index.year.unique().tolist())
        holiday_dates = self._get_holiday_dates(data_years)
        
        if not holiday_dates:
            return pd.Series([False] * len(df), index=df.index)
        
        mask = pd.Series([False] * len(df), index=df.index)
        
        for holiday_date in holiday_dates:
            if isinstance(holiday_date, str):
                try:
                    holiday_date = pd.to_datetime(holiday_date).date()
                except:
                    continue
            
            daily_mask = df.index.date == holiday_date
            mask |= daily_mask
        
        return mask
    
    def _get_holiday_dates(self, data_years: Optional[List[int]] = None) -> List[date]:
        """Get list of holiday dates for the specified years."""
        # Use data years if provided, otherwise use configured years or current year
        if data_years is not None:
            target_years = data_years
        elif self.years:
            target_years = self.years
        else:
            target_years = [datetime.now().year]
        
        # Create cache key from all years
        cache_key = "_".join(map(str, sorted(target_years)))
        
        if cache_key not in self.holiday_cache:
            holiday_dates = []
            
            # Get Danish holidays if available
            if holidays is not None:
                try:
                    dk_holidays = holidays.country_holidays(self.holidays_config.get('country', 'DK'), years=target_years)
                    holiday_dates.extend(list(dk_holidays.keys()))
                except:
                    pass
            
            # Add custom holidays from config
            custom_holidays = self.holidays_config.get('custom_holidays', [])
            for holiday in custom_holidays:
                try:
                    start_date = pd.to_datetime(holiday['start_date']).date()
                    end_date = holiday.get('end_date')
                    
                    if end_date:
                        end_date = pd.to_datetime(end_date).date()
                        current_date = start_date
                        while current_date <= end_date:
                            # Only include holidays that fall within target years
                            if current_date.year in target_years:
                                holiday_dates.append(current_date)
                            current_date += timedelta(days=1)
                    else:
                        # Only include holidays that fall within target years
                        if start_date.year in target_years:
                            holiday_dates.append(start_date)
                except:
                    continue
            
            self.holiday_cache[cache_key] = holiday_dates
        
        return self.holiday_cache[cache_key]
