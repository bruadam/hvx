"""EN 16798-1 indoor environment category enumeration."""

from enum import Enum


class EN16798Category(str, Enum):
    """
    EN 16798-1 indoor environment categories.

    The standard defines four categories of indoor environment quality:
    - Category I: High level of expectation (sensitive/fragile occupants)
    - Category II: Normal level of expectation (new buildings, renovations)
    - Category III: Moderate level of expectation (existing buildings)
    - Category IV: Values outside criteria for categories I-III (acceptable for limited periods)
    """

    CATEGORY_I = "cat_i"
    CATEGORY_II = "cat_ii"
    CATEGORY_III = "cat_iii"
    CATEGORY_IV = "cat_iv"

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            self.CATEGORY_I: "Category I - High Expectation",
            self.CATEGORY_II: "Category II - Normal Expectation",
            self.CATEGORY_III: "Category III - Moderate Expectation",
            self.CATEGORY_IV: "Category IV - Outside Standard",
        }
        return names.get(self, self.value.title())

    @property
    def description(self) -> str:
        """Get detailed description of the category."""
        descriptions = {
            self.CATEGORY_I: (
                "High level of expectation. Recommended for spaces with "
                "very sensitive and fragile occupants (children, elderly, disabled)"
            ),
            self.CATEGORY_II: (
                "Normal level of expectation. Recommended for new buildings "
                "and renovations. Default category for most applications."
            ),
            self.CATEGORY_III: (
                "Moderate level of expectation. Acceptable for existing "
                "buildings where renovation is not economically feasible."
            ),
            self.CATEGORY_IV: (
                "Values outside the criteria for categories I-III. Should only "
                "be accepted for limited periods of the year."
            ),
        }
        return descriptions.get(self, "")

    @property
    def performance_level(self) -> int:
        """
        Get performance hierarchy level (higher = better).

        Returns:
            Performance level: I=4, II=3, III=2, IV=1
        """
        levels = {
            self.CATEGORY_I: 4,
            self.CATEGORY_II: 3,
            self.CATEGORY_III: 2,
            self.CATEGORY_IV: 1,
        }
        return levels.get(self, 0)

    @property
    def compliance_percentage(self) -> float:
        """
        Get typical compliance percentage for this category.

        Returns:
            Compliance target (0-100%)
        """
        percentages = {
            self.CATEGORY_I: 100.0,
            self.CATEGORY_II: 95.0,
            self.CATEGORY_III: 90.0,
            self.CATEGORY_IV: 0.0,
        }
        return percentages.get(self, 0.0)

    @classmethod
    def get_recommended_for_building_type(cls, building_type: str) -> "EN16798Category":
        """
        Get recommended category for a building type.

        Args:
            building_type: Type of building

        Returns:
            Recommended category
        """
        recommendations = {
            "school": cls.CATEGORY_I,  # Children
            "kindergarten": cls.CATEGORY_I,  # Young children
            "hospital": cls.CATEGORY_I,  # Vulnerable occupants
            "nursing_home": cls.CATEGORY_I,  # Elderly
            "office": cls.CATEGORY_II,  # Normal office workers
            "hotel": cls.CATEGORY_II,  # Guests
            "residential": cls.CATEGORY_II,  # Residents
            "retail": cls.CATEGORY_III,  # Short-term occupancy
            "warehouse": cls.CATEGORY_III,  # Industrial
        }
        return recommendations.get(building_type.lower(), cls.CATEGORY_II)

    @classmethod
    def from_performance_level(cls, level: int) -> "EN16798Category":
        """
        Get category from performance level.

        Args:
            level: Performance level (1-4)

        Returns:
            Corresponding category
        """
        for category in cls:
            if category.performance_level == level:
                return category
        return cls.CATEGORY_IV
