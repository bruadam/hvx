"""
Special analytics module.

Advanced analytics beyond standard compliance testing:
- Ventilation rate prediction from CO2 decay
- Thermal mass analysis
- Occupancy detection from CO2 patterns
- Energy efficiency indicators
"""

from .occupancy_detector import (
    OccupancyDetector,
    OccupancyPattern,
    detect_occupancy_from_co2,
)
from .ventilation_rate_predictor import (
    VentilationRatePredictor,
    VentilationRateResult,
    predict_ventilation_rate_from_co2_decay,
)

__all__ = [
    "VentilationRatePredictor",
    "VentilationRateResult",
    "predict_ventilation_rate_from_co2_decay",
    "OccupancyDetector",
    "OccupancyPattern",
    "detect_occupancy_from_co2",
]
