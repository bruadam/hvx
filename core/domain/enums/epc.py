"""European Energy Performance Certificate (EPC) rating enumeration.

Data source: European DataWarehouse GmbH, 2024
Based on official European EPBD country implementations.
"""

from enum import Enum
from typing import Optional

from .belgium_region import BelgiumRegion
from .countries import Country


class EPCRating(str, Enum):
    """EPC rating categories for European countries."""

    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"

    @property
    def description(self) -> str:
        """Get description of EPC rating."""
        descriptions = {
            self.A_PLUS: "Excellent energy performance",
            self.A: "Very good energy performance",
            self.B: "Good energy performance",
            self.C: "Average energy performance",
            self.D: "Below average energy performance",
            self.E: "Poor energy performance",
            self.F: "Very poor energy performance",
            self.G: "Extremely poor energy performance",
        }
        return descriptions.get(self, "Unknown rating")

    @property
    def numeric_score(self) -> int:
        """Get numeric score for rating (higher is better)."""
        scores = {
            self.A_PLUS: 8,
            self.A: 7,
            self.B: 6,
            self.C: 5,
            self.D: 4,
            self.E: 3,
            self.F: 2,
            self.G: 1,
        }
        return scores.get(self, 0)

    @staticmethod
    def get_country_thresholds(country: Country) -> dict[str, tuple[float, float]]:
        """
        Get EPC rating thresholds for a specific country.

        Returns ranges as (min, max) in kWh/m²/year based on official European data.
        Data source: European DataWarehouse GmbH, 2024

        Args:
            country: The country for which to get thresholds

        Returns:
            Dictionary mapping rating to (min, max) energy consumption tuple (kWh/m²/year)
            max value of float('inf') indicates no upper limit
        """

        # Official EPC thresholds by country (kWh/m²/year)
        # Format: "Rating": (min, max)

        thresholds = {
            Country.CROATIA: {
                "A+": (0, 20),
                "A": (20, 25),
                "B": (25, 50),
                "C": (50, 105),
                "D": (105, 150),
                "E": (150, 200),
                "F": (200, 250),
                "G": (250, float('inf')),
            },

            Country.ITALY: {  # Old scale - Primary Energy
                "A+": (0, 29.5),
                "A": (29.5, 42.7),
                "B": (42.7, 59),
                "C": (59, 72.2),
                "D": (72.2, 95.7),
                "E": (95.7, 132.5),
                "F": (132.5, 170.7),
                "G": (170.7, float('inf')),
            },

            Country.SPAIN: {  # Primary Energy
                "A+": (0, 34.1),
                "A": (34.1, 41),
                "B": (41, 55.5),
                "C": (55.5, 85.4),
                "D": (85.4, 111),
                "E": (111, 136.6),
                "F": (136.6, 170.7),
                "G": (170.7, float('inf')),
            },

            Country.LUXEMBOURG: {  # Flats - Primary Energy
                "A+": (0, 16),
                "A": (16, 41),
                "B": (41, 71),
                "C": (71, 84),
                "D": (84, 98),
                "E": (98, 154),
                "F": (154, 225),
                "G": (225, float('inf')),
            },

            Country.BELGIUM: {  # Flanders - Primary Energy
                "A+": (0, 22),
                "A": (22, 90),
                "B": (90, 123),
                "C": (123, 142),
                "D": (142, 208),
                "E": (208, 295),
                "F": (295, 395),
                "G": (395, float('inf')),
            },

            Country.DENMARK: {  # Final Energy
                "A": (0, 30),
                "B": (30, 50),
                "C": (50, 75),
                "D": (75, 110),
                "E": (110, 150),
                "F": (150, 190),
                "G": (190, float('inf')),
            },

            Country.GERMANY: {  # Final Energy (Endenergie)
                "A+": (0, 30),
                "A": (30, 50),
                "B": (50, 75),
                "C": (75, 100),
                "D": (100, 130),
                "E": (130, 160),
                "F": (160, 200),
                "G": (200, float('inf')),
            },

            Country.FRANCE: {  # Primary Energy + CO2
                "A": (0, 70),
                "B": (70, 110),
                "C": (110, 180),
                "D": (180, 250),
                "E": (250, 330),
                "F": (330, 420),
                "G": (420, float('inf')),
            },

            Country.IRELAND: {  # Primary Energy
                "A": (0, 25),
                "B": (25, 50),
                "C": (50, 90),
                "D": (90, 150),
                "E": (150, 225),
                "F": (225, 340),
                "G": (340, float('inf')),
            },

            Country.FINLAND: {  # Primary Energy
                "A": (0, 50),
                "B": (50, 80),
                "C": (80, 115),
                "D": (115, 155),
                "E": (155, 200),
                "F": (200, 250),
                "G": (250, float('inf')),
            },

            Country.AUSTRIA: {  # Primary Energy
                "A+": (0, 15),
                "A": (15, 30),
                "B": (30, 50),
                "C": (50, 70),
                "D": (70, 90),
                "E": (90, 120),
                "F": (120, 160),
                "G": (160, float('inf')),
            },

            Country.NORWAY: {  # Energy Delivered
                "A+": (0, 85),
                "A": (85, 100),
                "B": (100, 125),
                "C": (125, 155),
                "D": (155, 190),
                "E": (190, 240),
                "F": (240, 290),
                "G": (290, float('inf')),
            },

            Country.BULGARIA: {  # Primary Energy
                "A+": (0, 55),
                "A": (55, 80),
                "B": (80, 105),
                "C": (105, 140),
                "D": (140, 175),
                "E": (175, 220),
                "F": (220, 280),
                "G": (280, float('inf')),
            },

            Country.NETHERLANDS: {  # Primary Energy
                "A+": (0, 50),
                "A": (50, 75),
                "B": (75, 105),
                "C": (105, 145),
                "D": (145, 195),
                "E": (195, 245),
                "F": (245, 300),
                "G": (300, float('inf')),
            },

            Country.ROMANIA: {  # Primary Energy
                "A+": (0, 55),
                "A": (55, 80),
                "B": (80, 105),
                "C": (105, 165),
                "D": (165, 205),
                "E": (205, 255),
                "F": (255, 345),
                "G": (345, float('inf')),
            },

            Country.SLOVAKIA: {  # Primary Energy
                "A+": (0, 55),
                "A": (55, 80),
                "B": (80, 105),
                "C": (105, 160),
                "D": (160, 200),
                "E": (200, 250),
                "F": (250, 350),
                "G": (350, float('inf')),
            },

            Country.PORTUGAL: {
                "A+": (0, 30),
                "A": (30, 55),
                "B": (55, 80),
                "C": (80, 105),
                "D": (105, 155),
                "E": (155, 205),
                "F": (205, 255),
                "G": (255, float('inf')),
            },

            Country.CZECH_REPUBLIC: {
                "A": (0, 55),
                "B": (55, 80),
                "C": (80, 105),
                "D": (105, 155),
                "E": (155, 205),
                "F": (205, 255),
                "G": (255, float('inf')),
            },

            Country.POLAND: {  # Primary Energy
                "A+": (0, 60),
                "A": (60, 90),
                "B": (90, 120),
                "C": (120, 160),
                "D": (160, 210),
                "E": (210, 270),
                "F": (270, 350),
                "G": (350, float('inf')),
            },

            Country.HUNGARY: {  # Primary Energy (estimated based on EU standards)
                "A+": (0, 50),
                "A": (50, 75),
                "B": (75, 110),
                "C": (110, 155),
                "D": (155, 205),
                "E": (205, 260),
                "F": (260, 330),
                "G": (330, float('inf')),
            },

            Country.GREECE: {  # Primary Energy (estimated based on EU standards)
                "A+": (0, 40),
                "A": (40, 65),
                "B": (65, 100),
                "C": (100, 145),
                "D": (145, 195),
                "E": (195, 250),
                "F": (250, 320),
                "G": (320, float('inf')),
            },
        }

        return thresholds.get(country, {})

    @staticmethod
    def get_belgium_region_thresholds(region: BelgiumRegion) -> dict[str, tuple[float, float]]:
        """
        Get EPC rating thresholds for a specific Belgian region.

        Belgium has different EPC regulations for each region (Flanders, Wallonia, Brussels).

        Args:
            region: The Belgian region

        Returns:
            Dictionary mapping rating to (min, max) energy consumption tuple (kWh/m²/year)
            max value of float('inf') indicates no upper limit
        """
        thresholds = {
            BelgiumRegion.FLANDERS: {  # Vlaanderen - Primary Energy
                "A+": (0, 22),
                "A": (22, 90),
                "B": (90, 123),
                "C": (123, 142),
                "D": (142, 208),
                "E": (208, 295),
                "F": (295, 395),
                "G": (395, float('inf')),
            },

            BelgiumRegion.WALLONIA: {  # Wallonie - Primary Energy
                "A+": (0, 45),
                "A": (45, 85),
                "B": (85, 170),
                "C": (170, 255),
                "D": (255, 340),
                "E": (340, 425),
                "F": (425, 510),
                "G": (510, float('inf')),
            },

            BelgiumRegion.BRUSSELS: {  # Bruxelles - Primary Energy
                "A+": (0, 45),
                "A": (45, 95),
                "B": (95, 150),
                "C": (150, 210),
                "D": (210, 275),
                "E": (275, 345),
                "F": (345, 425),
                "G": (425, float('inf')),
            },
        }

        return thresholds.get(region, {})

    @staticmethod
    def get_energy_type(country: Country) -> str:
        """
        Get the type of energy measurement used for EPC in a country.

        Args:
            country: The country

        Returns:
            Energy measurement type: "primary" (Primary Energy),
            "final" (Final/Delivered Energy), or "primary+co2" (Primary Energy + CO2)
        """
        energy_types = {
            Country.CROATIA: "primary",
            Country.ITALY: "primary",
            Country.SPAIN: "primary",
            Country.LUXEMBOURG: "primary",
            Country.BELGIUM: "primary",
            Country.DENMARK: "final",
            Country.GERMANY: "final",
            Country.FRANCE: "primary+co2",
            Country.IRELAND: "primary",
            Country.FINLAND: "primary",
            Country.AUSTRIA: "primary",
            Country.NORWAY: "delivered",
            Country.BULGARIA: "primary",
            Country.NETHERLANDS: "primary",
            Country.ROMANIA: "primary",
            Country.SLOVAKIA: "primary",
            Country.PORTUGAL: "primary",
            Country.CZECH_REPUBLIC: "primary",
            Country.POLAND: "primary",
            Country.HUNGARY: "primary",
            Country.GREECE: "primary",
        }
        return energy_types.get(country, "primary")

    @staticmethod
    def calculate_from_energy_consumption(
        energy_kwh_per_m2: float,
        country: Country,
        belgium_region: BelgiumRegion | None = None
    ) -> Optional["EPCRating"]:
        """
        Calculate EPC rating from energy consumption.

        Args:
            energy_kwh_per_m2: Energy consumption in kWh/m²/year
                              (type depends on country - see get_energy_type())
            country: Country for which to calculate the rating
            belgium_region: Belgian region (required if country is Belgium)

        Returns:
            EPCRating corresponding to the energy consumption, or None if
            country thresholds not available
        """
        # Special handling for Belgium with regions
        if country == Country.BELGIUM and belgium_region is not None:
            thresholds = EPCRating.get_belgium_region_thresholds(belgium_region)
        else:
            thresholds = EPCRating.get_country_thresholds(country)

        if not thresholds:
            return None

        # Find the rating that matches the energy consumption
        for rating, (min_val, max_val) in thresholds.items():
            if min_val <= energy_kwh_per_m2 < max_val:
                return EPCRating(rating)

        # If no match found, return worst rating
        return EPCRating.G

    @staticmethod
    def calculate_primary_energy(
        heating_kwh: float,
        cooling_kwh: float,
        electricity_kwh: float,
        hot_water_kwh: float,
        country: Country,
        floor_area_m2: float,
        renewable_energy_kwh: float = 0.0
    ) -> float:
        """
        Calculate primary energy consumption with country-specific conversion factors.

        Primary energy accounts for the energy used to generate, transmit, and distribute
        the energy used in the building.

        Args:
            heating_kwh: Annual heating energy consumption (final energy)
            cooling_kwh: Annual cooling energy consumption (final energy)
            electricity_kwh: Annual electricity consumption (final energy)
            hot_water_kwh: Annual hot water energy consumption (final energy)
            country: Country for conversion factors
            floor_area_m2: Building floor area in m²
            renewable_energy_kwh: Annual renewable energy generation (reduces primary energy)

        Returns:
            Primary energy consumption in kWh/m²/year
        """
        # Country-specific primary energy factors (final energy -> primary energy)
        # Based on grid efficiency, fuel mix, transmission losses, etc.
        electricity_factors = {
            Country.DENMARK: 1.9,
            Country.GERMANY: 1.8,
            Country.FRANCE: 2.3,
            Country.NETHERLANDS: 2.0,
            Country.SWEDEN: 1.6,
            Country.FINLAND: 1.7,
            Country.SPAIN: 1.9,
            Country.ITALY: 2.0,
            Country.BELGIUM: 2.0,
            Country.AUSTRIA: 1.9,
            Country.PORTUGAL: 2.5,
            Country.IRELAND: 2.1,
            Country.POLAND: 3.0,
            Country.CZECH_REPUBLIC: 2.5,
            Country.CROATIA: 2.0,
            Country.LUXEMBOURG: 2.0,
            Country.BULGARIA: 2.5,
            Country.ROMANIA: 2.5,
            Country.SLOVAKIA: 2.5,
            Country.HUNGARY: 2.3,
            Country.GREECE: 2.2,
            Country.NORWAY: 1.5,
            Country.SWEDEN: 1.6,
        }

        # District heating/natural gas factors
        heating_factors = {
            Country.DENMARK: 1.0,
            Country.GERMANY: 1.1,
            Country.FRANCE: 1.0,
            Country.NETHERLANDS: 1.1,
            Country.SWEDEN: 1.0,
            Country.FINLAND: 1.0,
            Country.SPAIN: 1.1,
            Country.ITALY: 1.05,
            Country.BELGIUM: 1.1,
            Country.AUSTRIA: 1.05,
            Country.PORTUGAL: 1.0,
            Country.IRELAND: 1.1,
            Country.POLAND: 1.2,
            Country.CZECH_REPUBLIC: 1.2,
            Country.CROATIA: 1.1,
            Country.LUXEMBOURG: 1.1,
            Country.BULGARIA: 1.2,
            Country.ROMANIA: 1.2,
            Country.SLOVAKIA: 1.2,
            Country.HUNGARY: 1.15,
            Country.GREECE: 1.1,
            Country.NORWAY: 1.0,
        }

        electricity_factor = electricity_factors.get(country, 2.0)
        heating_factor = heating_factors.get(country, 1.1)

        # Calculate primary energy
        primary_energy = (
            (heating_kwh * heating_factor) +
            (cooling_kwh * electricity_factor) +
            (electricity_kwh * electricity_factor) +
            (hot_water_kwh * heating_factor) -
            (renewable_energy_kwh * electricity_factor)
        )

        # Convert to per square meter
        primary_energy_per_m2 = primary_energy / floor_area_m2 if floor_area_m2 > 0 else 0

        return max(0, primary_energy_per_m2)

    def get_threshold_range(self, country: Country) -> dict[str, float | str | None] | None:
        """
        Get the energy consumption range for this rating in a specific country.

        Args:
            country: Country for which to get the range

        Returns:
            Dictionary with 'min' and 'max' energy consumption values (kWh/m²/year),
            'energy_type' as string, or None if country not supported
        """
        thresholds = self.get_country_thresholds(country)

        if not thresholds:
            return None

        range_tuple = thresholds.get(self.value)

        if not range_tuple:
            return None

        min_val, max_val = range_tuple

        return {
            "min": min_val,
            "max": max_val if max_val != float('inf') else None,
            "energy_type": self.get_energy_type(country)
        }

    @staticmethod
    def get_rating_info(country: Country) -> dict[str, str]:
        """
        Get information about how EPC ratings are calculated in a specific country.

        Args:
            country: The country

        Returns:
            Dictionary with rating methodology information
        """
        info = {
            Country.CROATIA: {
                "base": "kWh/m²/year",
                "energy_type": "Primary Energy",
            },
            Country.ITALY: {
                "base": "kWh/m²/year",
                "energy_type": "Primary Energy (old scale)",
                "note": "New multi-factor calculation system available"
            },
            Country.SPAIN: {
                "base": "kWh/m²/year",
                "energy_type": "Primary Energy",
            },
            Country.LUXEMBOURG: {
                "base": "kWh/m²/year",
                "energy_type": "Primary Energy",
                "note": "Different thresholds for flats vs houses"
            },
            Country.BELGIUM: {
                "base": "kWh/m²/year",
                "energy_type": "Primary Energy",
                "note": "Regional variations (Flanders, Wallonia, Brussels)"
            },
            Country.DENMARK: {
                "base": "kWh/m²/year",
                "energy_type": "Final Energy",
            },
            Country.GERMANY: {
                "base": "kWh/m²/year",
                "energy_type": "Final Energy (Endenergie)",
            },
            Country.FRANCE: {
                "base": "kWh/m²/year AND kg CO2/m²/year",
                "energy_type": "Primary Energy + CO2 Emissions",
            },
            Country.IRELAND: {
                "base": "kWh/m²/year",
                "energy_type": "Primary Energy",
            },
            Country.FINLAND: {
                "base": "kWh/m²/year",
                "energy_type": "Primary Energy",
            },
            Country.AUSTRIA: {
                "base": "kWh/m²/year",
                "energy_type": "Primary Energy",
            },
            Country.NORWAY: {
                "base": "kWh/m²/year",
                "energy_type": "Energy Delivered",
                "note": "Color scale also based on heating type"
            },
            Country.NETHERLANDS: {
                "base": "kWh/m²/year",
                "energy_type": "Primary Energy",
            },
            Country.PORTUGAL: {
                "base": "% of reference",
                "energy_type": "Primary Energy",
                "note": "Also uses percentage scale"
            },
            Country.CZECH_REPUBLIC: {
                "base": "% of reference",
                "energy_type": "Primary Energy",
                "note": "Also uses percentage scale"
            },
        }

        return info.get(country, {
            "base": "kWh/m²/year",
            "energy_type": "Primary Energy",
        })
