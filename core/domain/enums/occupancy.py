"""Occupancy density and activity level enums for EN 16798-1."""

from enum import Enum


class ActivityLevel(str, Enum):
    """
    Metabolic activity levels according to EN 16798-1.

    Determines CO2 generation rate and sensible heat emission per person.
    """

    SEDENTARY = "sedentary"  # 1.0 met (seated, relaxed)
    LIGHT_ACTIVITY = "light_activity"  # 1.2 met (seated, light work)
    MEDIUM_ACTIVITY = "medium_activity"  # 1.6 met (standing, walking)
    HIGH_ACTIVITY = "high_activity"  # 3.0+ met (sports, manual labor)

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            self.SEDENTARY: "Sedentary (1.0 met)",
            self.LIGHT_ACTIVITY: "Light Activity (1.2 met)",
            self.MEDIUM_ACTIVITY: "Medium Activity (1.6 met)",
            self.HIGH_ACTIVITY: "High Activity (3.0+ met)",
        }
        return names.get(self, self.value.replace("_", " ").title())

    @property
    def metabolic_rate_met(self) -> float:
        """
        Get metabolic rate in met units.

        1 met = 58 W/m² of body surface area ≈ 100 W per person

        Returns:
            Metabolic rate in met
        """
        rates = {
            self.SEDENTARY: 1.0,
            self.LIGHT_ACTIVITY: 1.2,
            self.MEDIUM_ACTIVITY: 1.6,
            self.HIGH_ACTIVITY: 3.0,
        }
        return rates.get(self, 1.2)

    @property
    def co2_generation_rate_l_per_s_person(self) -> float:
        """
        Get CO2 generation rate per person in L/s.

        Based on typical adult at given activity level.

        Returns:
            CO2 generation in L/(s·person)
        """
        # Approximate values based on metabolic rate
        # Sedentary: ~0.005 L/s, increases with activity
        rates = {
            self.SEDENTARY: 0.005,
            self.LIGHT_ACTIVITY: 0.0054,
            self.MEDIUM_ACTIVITY: 0.0066,
            self.HIGH_ACTIVITY: 0.012,
        }
        return rates.get(self, 0.0054)

    @property
    def sensible_heat_emission_w_person(self) -> float:
        """
        Get sensible heat emission per person in W.

        At 24°C room temperature, typical values.

        Returns:
            Sensible heat in W/person
        """
        heat = {
            self.SEDENTARY: 70,
            self.LIGHT_ACTIVITY: 80,
            self.MEDIUM_ACTIVITY: 95,
            self.HIGH_ACTIVITY: 150,
        }
        return heat.get(self, 80)

    @classmethod
    def get_for_room_type(cls, room_type: str) -> "ActivityLevel":
        """
        Get typical activity level for room type.

        Args:
            room_type: Type of room

        Returns:
            Typical activity level
        """
        mappings = {
            "office": cls.LIGHT_ACTIVITY,
            "small_office": cls.LIGHT_ACTIVITY,
            "open_office": cls.LIGHT_ACTIVITY,
            "meeting_room": cls.SEDENTARY,
            "classroom": cls.SEDENTARY,
            "lecture_hall": cls.SEDENTARY,
            "library": cls.SEDENTARY,
            "hotel_room": cls.SEDENTARY,
            "restaurant": cls.SEDENTARY,
            "retail": cls.LIGHT_ACTIVITY,
            "laboratory": cls.MEDIUM_ACTIVITY,
            "workshop": cls.HIGH_ACTIVITY,
            "gym": cls.HIGH_ACTIVITY,
            "sports_hall": cls.HIGH_ACTIVITY,
        }
        return mappings.get(room_type.lower(), cls.LIGHT_ACTIVITY)


class OccupancyDensity(str, Enum):
    """
    Typical occupancy density levels for different space types.

    Used to estimate ventilation requirements based on floor area.
    """

    VERY_LOW = "very_low"  # < 0.05 person/m² (large spaces, warehouses)
    LOW = "low"  # 0.05-0.1 person/m² (offices, hotel rooms)
    MEDIUM = "medium"  # 0.1-0.3 person/m² (classrooms, meeting rooms)
    HIGH = "high"  # 0.3-0.5 person/m² (restaurants, lecture halls)
    VERY_HIGH = "very_high"  # > 0.5 person/m² (public transport, elevators)

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            self.VERY_LOW: "Very Low Density",
            self.LOW: "Low Density",
            self.MEDIUM: "Medium Density",
            self.HIGH: "High Density",
            self.VERY_HIGH: "Very High Density",
        }
        return names.get(self, self.value.replace("_", " ").title())

    @property
    def typical_occupancy_per_m2(self) -> float:
        """
        Get typical occupancy density in persons/m².

        Returns:
            Persons per square meter
        """
        densities = {
            self.VERY_LOW: 0.03,
            self.LOW: 0.07,
            self.MEDIUM: 0.20,
            self.HIGH: 0.40,
            self.VERY_HIGH: 0.70,
        }
        return densities.get(self, 0.10)

    @property
    def typical_floor_area_per_person(self) -> float:
        """
        Get typical floor area per person in m²/person.

        Returns:
            Square meters per person
        """
        return 1.0 / self.typical_occupancy_per_m2

    @classmethod
    def get_for_room_type(cls, room_type: str) -> "OccupancyDensity":
        """
        Get typical occupancy density for room type.

        Args:
            room_type: Type of room

        Returns:
            Typical occupancy density
        """
        mappings = {
            "warehouse": cls.VERY_LOW,
            "corridor": cls.VERY_LOW,
            "lobby": cls.VERY_LOW,
            "office": cls.LOW,
            "small_office": cls.LOW,
            "open_office": cls.LOW,
            "hotel_room": cls.LOW,
            "laboratory": cls.LOW,
            "classroom": cls.MEDIUM,
            "meeting_room": cls.MEDIUM,
            "library": cls.MEDIUM,
            "restaurant": cls.HIGH,
            "lecture_hall": cls.HIGH,
            "cafeteria": cls.HIGH,
            "retail": cls.MEDIUM,
            "gym": cls.MEDIUM,
        }
        return mappings.get(room_type.lower(), cls.MEDIUM)

    @classmethod
    def from_area_per_person(cls, area_per_person: float) -> "OccupancyDensity":
        """
        Determine density category from area per person.

        Args:
            area_per_person: Floor area per person in m²

        Returns:
            Occupancy density category
        """
        if area_per_person > 20:
            return cls.VERY_LOW
        elif area_per_person > 10:
            return cls.LOW
        elif area_per_person > 3:
            return cls.MEDIUM
        elif area_per_person > 2:
            return cls.HIGH
        else:
            return cls.VERY_HIGH
