"""TAIL (Thermal, Acoustic, Indoor Air Quality, Luminous) rating calculator.

Reference: https://github.com/asitkm76/TAILRatingScheme
TAIL Rating Scheme developed by the ALDREN project.
https://www.sciencedirect.com/science/article/pii/S0378778821003133
"""

from typing import Any


class TAILRatingCalculator:
    """
    Calculator for TAIL rating scheme.

    TAIL provides a comprehensive assessment of indoor environmental quality across:
    - T: Thermal comfort (temperature, humidity)
    - A: Acoustic comfort (noise levels)
    - I: Indoor Air Quality (CO2, PM2.5, VOCs, etc.)
    - L: Luminous comfort (illuminance, daylight)

    Rating Scale:
    - I (1): Green - Best quality (≥95% compliant)
    - II (2): Yellow - Good quality (70-95% compliant)
    - III (3): Orange - Fair quality (50-70% compliant)
    - IV (4): Red - Poor quality (<50% compliant)
    """

    # Rating thresholds based on compliance percentage
    RATING_THRESHOLDS = {
        1: 95.0,  # I - Green (Excellent)
        2: 70.0,  # II - Yellow (Good)
        3: 50.0,  # III - Orange (Fair)
        4: 0.0,   # IV - Red (Poor)
    }

    # Parameter mapping to TAIL categories
    THERMAL_PARAMETERS = {"temperature", "temp", "humidity", "humid", "rh", "relative_humidity"}
    ACOUSTIC_PARAMETERS = {"noise", "sound", "acoustic", "sound_level", "noise_level"}
    IAQ_PARAMETERS = {"co2", "pm25", "pm2.5", "pm10", "voc", "tvoc", "formaldehyde", "radon", "ventilation", "air_quality"}
    LUMINOUS_PARAMETERS = {"illuminance", "light", "daylight", "lux", "daylight_factor", "luminance"}

    @classmethod
    def compliance_to_rating(cls, compliance_rate: float) -> int:
        """
        Convert compliance percentage to TAIL rating (1-4).

        Args:
            compliance_rate: Compliance percentage (0-100)

        Returns:
            Rating from 1 (best/green) to 4 (worst/red)
        """
        if compliance_rate >= cls.RATING_THRESHOLDS[1]:
            return 1  # Green - Excellent
        elif compliance_rate >= cls.RATING_THRESHOLDS[2]:
            return 2  # Yellow - Good
        elif compliance_rate >= cls.RATING_THRESHOLDS[3]:
            return 3  # Orange - Fair
        else:
            return 4  # Red - Poor

    @classmethod
    def rating_to_label(cls, rating: int | None) -> str:
        """
        Convert rating number to label.

        Args:
            rating: Rating (1-4) or None

        Returns:
            Roman numeral label or "N/A"
        """
        if rating is None:
            return "N/A"
        labels = {1: "I", 2: "II", 3: "III", 4: "IV"}
        return labels.get(rating, "N/A")

    @classmethod
    def get_parameter_category(cls, parameter: str) -> str | None:
        """
        Determine which TAIL category a parameter belongs to.

        Args:
            parameter: Parameter name

        Returns:
            Category name ('thermal', 'acoustic', 'iaq', 'luminous') or None
        """
        param_lower = parameter.lower()

        if param_lower in cls.THERMAL_PARAMETERS:
            return "thermal"
        elif param_lower in cls.ACOUSTIC_PARAMETERS:
            return "acoustic"
        elif param_lower in cls.IAQ_PARAMETERS:
            return "iaq"
        elif param_lower in cls.LUMINOUS_PARAMETERS:
            return "luminous"
        return None

    @classmethod
    def calculate_from_measured_values(
        cls,
        measured_values: dict[str, float],
        thresholds: dict[str, dict[str, float]] | None = None,
    ) -> dict[str, Any]:
        """
        Calculate TAIL rating from measured values and thresholds.

        Args:
            measured_values: Dict of parameter -> measured value
            thresholds: Optional dict of parameter -> {lower, upper} thresholds

        Returns:
            Dictionary with TAIL ratings and details
        """
        # Calculate compliance for each parameter
        parameter_ratings = {}
        category_ratings = {"thermal": [], "acoustic": [], "iaq": [], "luminous": []}

        for param, value in measured_values.items():
            if thresholds and param in thresholds:
                threshold = thresholds[param]
                lower = threshold.get("lower", float("-inf"))
                upper = threshold.get("upper", float("inf"))

                # Simple compliance check
                is_compliant = lower <= value <= upper
                compliance_rate = 100.0 if is_compliant else 0.0
            else:
                # If no threshold, assume 100% compliance
                compliance_rate = 100.0

            rating = cls.compliance_to_rating(compliance_rate)
            parameter_ratings[param] = {
                "value": value,
                "compliance_rate": compliance_rate,
                "rating": rating,
                "rating_label": cls.rating_to_label(rating),
            }

            # Add to category
            category = cls.get_parameter_category(param)
            if category:
                category_ratings[category].append(rating)

        # Calculate category ratings (worst parameter in category)
        tail_categories = {}
        for category, ratings in category_ratings.items():
            if ratings:
                tail_categories[category] = {
                    "rating": max(ratings),  # Worst rating (highest number)
                    "rating_label": cls.rating_to_label(max(ratings)),
                    "parameter_count": len(ratings),
                }
            else:
                tail_categories[category] = {
                    "rating": None,
                    "rating_label": "N/A",
                    "parameter_count": 0,
                }

        # Overall rating (worst category)
        measured_categories = [
            cat["rating"] for cat in tail_categories.values() if cat["rating"] is not None
        ]
        overall_rating = max(measured_categories) if measured_categories else None

        return {
            "overall_rating": overall_rating,
            "overall_rating_label": cls.rating_to_label(overall_rating),
            "categories": tail_categories,
            "parameters": parameter_ratings,
        }

    @classmethod
    def aggregate_ratings(
        cls,
        child_ratings: list[dict[str, Any]],
        aggregation_method: str = "worst",
    ) -> dict[str, Any]:
        """
        Aggregate TAIL ratings from multiple child entities (rooms/buildings).

        Args:
            child_ratings: List of TAIL rating dictionaries
            aggregation_method: 'worst', 'average', or 'weighted_average'

        Returns:
            Aggregated TAIL rating dictionary
        """
        if not child_ratings:
            return {
                "overall_rating": None,
                "overall_rating_label": "N/A",
                "categories": {
                    "thermal": {"rating": None, "rating_label": "N/A"},
                    "acoustic": {"rating": None, "rating_label": "N/A"},
                    "iaq": {"rating": None, "rating_label": "N/A"},
                    "luminous": {"rating": None, "rating_label": "N/A"},
                },
            }

        # Aggregate overall ratings
        overall_ratings = [r["overall_rating"] for r in child_ratings if r.get("overall_rating")]

        if aggregation_method == "worst":
            overall = max(overall_ratings) if overall_ratings else None
        elif aggregation_method == "average":
            overall = round(sum(overall_ratings) / len(overall_ratings)) if overall_ratings else None
        else:  # weighted_average would need weights
            overall = max(overall_ratings) if overall_ratings else None

        # Aggregate categories
        aggregated_categories = {}
        for category in ["thermal", "acoustic", "iaq", "luminous"]:
            category_ratings = [
                r["categories"][category]["rating"]
                for r in child_ratings
                if r.get("categories", {}).get(category, {}).get("rating") is not None
            ]

            if aggregation_method == "worst":
                cat_rating = max(category_ratings) if category_ratings else None
            elif aggregation_method == "average":
                cat_rating = (
                    round(sum(category_ratings) / len(category_ratings))
                    if category_ratings
                    else None
                )
            else:
                cat_rating = max(category_ratings) if category_ratings else None

            aggregated_categories[category] = {
                "rating": cat_rating,
                "rating_label": cls.rating_to_label(cat_rating),
                "sample_count": len(category_ratings),
            }

        return {
            "overall_rating": overall,
            "overall_rating_label": cls.rating_to_label(overall),
            "categories": aggregated_categories,
            "aggregation_method": aggregation_method,
            "child_count": len(child_ratings),
        }
