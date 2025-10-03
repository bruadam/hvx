"""Analytics Service for running analysis and generating JSON output."""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.core.analysis.ieq import AnalysisEngine


class AnalyticsService:
    """Service for running analytics and managing JSON output."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize analytics service."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "tests.yaml"

        # Ensure config_path is a Path object
        if not isinstance(config_path, Path):
            config_path = Path(config_path)

        self.config_path = config_path
        self.output_dir = Path("output") / "analysis"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_analysis(
        self,
        data_path: Path,
        analysis_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run full analytics on a dataset and save to JSON."""
        # Load data
        df = self._load_data(data_path)

        # For demonstration purposes, create a simplified analysis result
        # In production, this would use the full UnifiedAnalyticsEngine
        results = self._run_simple_analysis(df, analysis_name)

        # Generate analysis name
        if analysis_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_name = f"analysis_{timestamp}"

        # Convert to JSON-serializable format
        json_output = self._convert_to_json(results, df, analysis_name)

        # Save to file
        output_path = self.output_dir / f"{analysis_name}.json"
        self._save_json(json_output, output_path)

        return {
            'analysis_name': analysis_name,
            'output_path': str(output_path),
            'results': json_output,
            'status': 'success'
        }

    def list_analyses(self) -> List[Dict[str, Any]]:
        """List all saved analysis results."""
        analyses = []

        if self.output_dir.exists():
            for json_file in self.output_dir.glob("*.json"):
                try:
                    data = self._load_json(json_file)
                    analyses.append({
                        'name': json_file.stem,
                        'path': str(json_file),
                        'timestamp': data.get('metadata', {}).get('timestamp', 'Unknown'),
                        'building': data.get('metadata', {}).get('building_name', 'Unknown')
                    })
                except Exception as e:
                    continue

        return sorted(analyses, key=lambda x: x['timestamp'], reverse=True)

    def get_analysis(self, analysis_name: str) -> Optional[Dict[str, Any]]:
        """Load a specific analysis result."""
        analysis_path = self.output_dir / f"{analysis_name}.json"

        if not analysis_path.exists():
            return None

        return self._load_json(analysis_path)

    def _run_simple_analysis(self, df: pd.DataFrame, analysis_name: Optional[str]) -> Dict[str, Any]:
        """Run simplified analysis for demonstration."""
        results = {
            'user_rules': []
        }

        # Analyze CO2 if available
        if 'co2' in df.columns:
            co2_data = df['co2'].dropna()
            if len(co2_data) > 0:
                threshold = 1000
                compliant = (co2_data <= threshold).sum()
                total = len(co2_data)

                results['user_rules'].append({
                    'parameter': 'co2',
                    'rule_name': 'CO2 All Year',
                    'compliance_rate': (compliant / total) * 100 if total > 0 else 0,
                    'total_points': total,
                    'compliant_points': compliant,
                    'statistics': {
                        'mean': float(co2_data.mean()),
                        'min': float(co2_data.min()),
                        'max': float(co2_data.max()),
                        'std': float(co2_data.std())
                    },
                    'recommendations': [
                        'Monitor CO2 levels during peak occupancy',
                        'Ensure adequate ventilation'
                    ]
                })

        # Analyze temperature if available
        if 'temperature' in df.columns:
            temp_data = df['temperature'].dropna()
            if len(temp_data) > 0:
                min_temp = 20
                max_temp = 24
                compliant = ((temp_data >= min_temp) & (temp_data <= max_temp)).sum()
                total = len(temp_data)

                results['user_rules'].append({
                    'parameter': 'temperature',
                    'rule_name': 'Temperature Comfort',
                    'compliance_rate': (compliant / total) * 100 if total > 0 else 0,
                    'total_points': total,
                    'compliant_points': compliant,
                    'statistics': {
                        'mean': float(temp_data.mean()),
                        'min': float(temp_data.min()),
                        'max': float(temp_data.max()),
                        'std': float(temp_data.std())
                    },
                    'recommendations': [
                        'Maintain temperature within comfort range',
                        'Check HVAC system performance'
                    ]
                })

        return results

    def _load_data(self, data_path: Path) -> pd.DataFrame:
        """Load data from CSV or parquet file."""
        if data_path.suffix == '.csv':
            df = pd.read_csv(data_path, parse_dates=['timestamp'])
        elif data_path.suffix == '.parquet':
            df = pd.read_parquet(data_path)
        else:
            raise ValueError(f"Unsupported file format: {data_path.suffix}")

        # Ensure timestamp column exists and is datetime
        if 'timestamp' not in df.columns:
            raise ValueError("Data must contain a 'timestamp' column")

        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Set timestamp as index for analytics engine
        df = df.set_index('timestamp')

        return df

    def _convert_to_json(
        self,
        results: Dict[str, Any],
        df: pd.DataFrame,
        analysis_name: str
    ) -> Dict[str, Any]:
        """Convert analysis results to JSON-serializable format."""
        json_output = {
            'metadata': {
                'analysis_name': analysis_name,
                'timestamp': datetime.now().isoformat(),
                'building_name': analysis_name,
                'data_points': len(df),
                'date_range': {
                    'start': df.index.min().isoformat(),
                    'end': df.index.max().isoformat()
                },
                'parameters': list(df.columns)
            },
            'summary': self._generate_summary(results, df),
            'detailed_results': self._format_results(results),
            'charts_data': self._generate_charts_data(results, df)
        }

        return json_output

    def _generate_summary(self, results: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Generate executive summary from results."""
        # Count total rules and compliance
        total_rules = len(results.get('user_rules', []))

        if total_rules > 0:
            compliance_rates = [r['compliance_rate'] for r in results.get('user_rules', [])]
            avg_compliance = sum(compliance_rates) / len(compliance_rates)
        else:
            avg_compliance = 0

        return {
            'overall_compliance': round(avg_compliance, 2),
            'total_rules_evaluated': total_rules,
            'data_quality_score': self._calculate_data_quality(df),
            'key_findings': self._generate_key_findings(results)
        }

    def _calculate_data_quality(self, df: pd.DataFrame) -> float:
        """Calculate overall data quality score."""
        # Simple data quality: percentage of non-null values
        total_cells = df.size
        non_null_cells = df.count().sum()

        return round((non_null_cells / total_cells) * 100, 2) if total_cells > 0 else 0

    def _generate_key_findings(self, results: Dict[str, Any]) -> List[str]:
        """Generate key findings from results."""
        findings = []

        user_rules = results.get('user_rules', [])
        if user_rules:
            # Find lowest compliance rule
            lowest = min(user_rules, key=lambda x: x['compliance_rate'])
            findings.append(
                f"Lowest compliance: {lowest['rule_name']} at {lowest['compliance_rate']:.1f}%"
            )

            # Find highest compliance rule
            highest = max(user_rules, key=lambda x: x['compliance_rate'])
            findings.append(
                f"Highest compliance: {highest['rule_name']} at {highest['compliance_rate']:.1f}%"
            )

        return findings

    def _format_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format detailed results for JSON output."""
        formatted = {}

        # Format user rules results
        if 'user_rules' in results:
            formatted['user_rules'] = [
                {
                    'parameter': r['parameter'],
                    'rule_name': r['rule_name'],
                    'compliance_rate': round(r['compliance_rate'], 2),
                    'total_points': r['total_points'],
                    'compliant_points': r['compliant_points'],
                    'statistics': {k: round(v, 2) for k, v in r['statistics'].items()},
                    'recommendations': r['recommendations']
                }
                for r in results['user_rules']
            ]

        return formatted

    def _generate_charts_data(self, results: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Generate data prepared for charts."""
        charts_data = {}

        # CO2 compliance data
        co2_rules = [r for r in results.get('user_rules', []) if 'co2' in r['parameter'].lower()]
        if co2_rules:
            charts_data['co2_compliance'] = {
                'periods': [r['rule_name'] for r in co2_rules[:5]],  # Max 5 periods
                'compliance_percentage': [r['compliance_rate'] for r in co2_rules[:5]]
            }

        # Temperature data (if available)
        if 'temperature' in df.columns:
            temp_data = df[['temperature']].dropna()
            if len(temp_data) > 0:
                # Sample to max 24 points
                if len(temp_data) > 24:
                    temp_data = temp_data.iloc[::len(temp_data)//24]

                charts_data['temperature_timeseries'] = {
                    'timestamps': temp_data.index.strftime('%Y-%m-%dT%H:%M:%S').tolist(),
                    'temperature': temp_data['temperature'].round(2).tolist()
                }

        return charts_data

    def _save_json(self, data: Dict[str, Any], output_path: Path):
        """Save data to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load data from JSON file."""
        with open(path, 'r') as f:
            return json.load(f)
