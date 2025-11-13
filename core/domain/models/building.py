"""Building domain entity."""

from typing import Any

from pydantic import BaseModel, Field

from core.domain.enums.belgium_region import BelgiumRegion
from core.domain.enums.building_type import BuildingType
from core.domain.enums.countries import Country
from core.domain.enums.epc import EPCRating
from core.domain.enums.heating import HeatingType
from core.domain.enums.hvac import HVACType
from core.domain.enums.ventilation import VentilationType


class Building(BaseModel):
    """
    Building entity representing a physical building with hierarchical structure.

    Contains levels, which contain rooms.
    """

    # Identity
    id: str = Field(..., description="Unique building identifier")
    name: str = Field(..., description="Building name or address")

    # Classification
    building_type: BuildingType = Field(
        default=BuildingType.OFFICE, description="Type of building"
    )

    # Hierarchy
    level_ids: list[str] = Field(default_factory=list, description="IDs of levels in building")
    room_ids: list[str] = Field(
        default_factory=list,
        description="IDs of rooms in building (can be assigned directly without levels)"
    )

    # Physical properties
    total_area: float | None = Field(default=None, ge=0, description="Total building area in m²")
    year_built: int | None = Field(
        default=None, ge=1800, le=2100, description="Year of construction"
    )
    total_occupants: int | None = Field(
        default=None, ge=0, description="Total number of occupants"
    )

    # Location
    address: str | None = Field(default=None, description="Building address")
    city: str | None = Field(default=None, description="City")
    country: Country | None = Field(default=None, description="Country in Europe")
    belgium_region: BelgiumRegion | None = Field(
        default=None, description="Belgian region (Flanders, Wallonia, Brussels) - required for Belgium EPC"
    )
    latitude: float | None = Field(default=None, ge=-90, le=90, description="Latitude")
    longitude: float | None = Field(default=None, ge=-180, le=180, description="Longitude")

    # Building systems
    hvac_system: HVACType | None = Field(
        default=None, description="Type of HVAC system (e.g., VAV, CAV, radiant)"
    )
    ventilation_type: VentilationType | None = Field(
        default=VentilationType.NATURAL, description="Type of ventilation (e.g., natural, mechanical)"
    )
    heating_system: HeatingType | None = Field(
        default=None, description="Type of heating system (e.g., boiler, heat pump)"
    )

    # European Energy Performance Certificate (EPC) rating
    epc_rating: EPCRating | None = Field(
        default=None, description="EPC rating (e.g., A+, A, B, C, ... G)"
    )

    # Energy consumption tracking
    annual_heating_kwh: float | None = Field(
        default=None, ge=0, description="Annual heating energy consumption in kWh"
    )
    annual_cooling_kwh: float | None = Field(
        default=None, ge=0, description="Annual cooling energy consumption in kWh"
    )
    annual_electricity_kwh: float | None = Field(
        default=None, ge=0, description="Annual electricity consumption in kWh"
    )
    annual_hot_water_kwh: float | None = Field(
        default=None, ge=0, description="Annual hot water energy consumption in kWh"
    )
    annual_ventilation_kwh: float | None = Field(
        default=None, ge=0, description="Annual ventilation energy consumption in kWh"
    )

    # Water consumption
    annual_water_m3: float | None = Field(
        default=None, ge=0, description="Annual water consumption in m³"
    )

    # Renewable energy generation
    annual_solar_pv_kwh: float | None = Field(
        default=None, ge=0, description="Annual solar PV energy generation in kWh"
    )
    annual_renewable_kwh: float | None = Field(
        default=None, ge=0, description="Annual renewable energy generation in kWh (all sources)"
    )

    # Metadata
    attributes: dict[str, str] = Field(
        default_factory=dict,
        description="Custom attributes (e.g., HVAC type, insulation level)",
    )

    def add_level(self, level_id: str) -> None:
        """
        Add a level to this building.

        Args:
            level_id: Level identifier to add
        """
        if level_id not in self.level_ids:
            self.level_ids.append(level_id)

    def remove_level(self, level_id: str) -> bool:
        """
        Remove a level from this building.

        Args:
            level_id: Level identifier to remove

        Returns:
            True if level was removed, False if not found
        """
        if level_id in self.level_ids:
            self.level_ids.remove(level_id)
            return True
        return False

    def has_level(self, level_id: str) -> bool:
        """Check if building contains a specific level."""
        return level_id in self.level_ids

    def add_room(self, room_id: str) -> None:
        """
        Add a room directly to this building (without assigning to a level).

        Args:
            room_id: Room identifier to add
        """
        if room_id not in self.room_ids:
            self.room_ids.append(room_id)

    def add_rooms(self, room_ids: list[str]) -> None:
        """
        Add multiple rooms directly to this building.

        Args:
            room_ids: List of room identifiers to add
        """
        for room_id in room_ids:
            self.add_room(room_id)

    def remove_room(self, room_id: str) -> bool:
        """
        Remove a room from this building.

        Args:
            room_id: Room identifier to remove

        Returns:
            True if room was removed, False if not found
        """
        if room_id in self.room_ids:
            self.room_ids.remove(room_id)
            return True
        return False

    def has_room(self, room_id: str) -> bool:
        """Check if building contains a specific room."""
        return room_id in self.room_ids

    @property
    def level_count(self) -> int:
        """Get number of levels in building."""
        return len(self.level_ids)

    @property
    def room_count(self) -> int:
        """Get number of rooms directly assigned to building."""
        return len(self.room_ids)

    @property
    def total_rooms(self) -> int:
        """Get total number of rooms (direct rooms + rooms in levels)."""
        return len(self.room_ids)

    @property
    def typical_opening_hours(self) -> tuple[int, int]:
        """Get typical opening hours based on building type."""
        return self.building_type.typical_occupancy_hours

    def calculate_primary_energy_per_m2(self) -> float | None:
        """
        Calculate primary energy consumption per m² per year.

        Requires: country, total_area, and energy consumption data.

        Returns:
            Primary energy in kWh/m²/year, or None if required data is missing
        """
        if not self.country or not self.total_area or self.total_area <= 0:
            return None

        # Need at least some consumption data
        if all([
            self.annual_heating_kwh is None,
            self.annual_cooling_kwh is None,
            self.annual_electricity_kwh is None,
            self.annual_hot_water_kwh is None
        ]):
            return None

        return EPCRating.calculate_primary_energy(
            heating_kwh=self.annual_heating_kwh or 0.0,
            cooling_kwh=self.annual_cooling_kwh or 0.0,
            electricity_kwh=self.annual_electricity_kwh or 0.0,
            hot_water_kwh=self.annual_hot_water_kwh or 0.0,
            country=self.country,
            floor_area_m2=self.total_area,
            renewable_energy_kwh=(self.annual_renewable_kwh or self.annual_solar_pv_kwh or 0.0)
        )

    def calculate_epc_rating(self) -> EPCRating | None:
        """
        Calculate EPC rating based on building's energy consumption.

        Requires: country, total_area, and energy consumption data.
        For Belgium, also requires belgium_region.

        Returns:
            EPCRating, or None if required data is missing
        """
        primary_energy = self.calculate_primary_energy_per_m2()

        if primary_energy is None or not self.country:
            return None

        return EPCRating.calculate_from_energy_consumption(
            energy_kwh_per_m2=primary_energy,
            country=self.country,
            belgium_region=self.belgium_region
        )

    def update_epc_rating(self) -> bool:
        """
        Update the epc_rating field based on current consumption data.

        Returns:
            True if rating was updated, False if required data is missing
        """
        calculated_rating = self.calculate_epc_rating()

        if calculated_rating is not None:
            self.epc_rating = calculated_rating
            return True

        return False

    def get_energy_summary(self) -> dict[str, Any]:
        """Get summary of building energy consumption and performance."""
        summary = {
            "total_area_m2": self.total_area,
            "country": self.country.value if self.country else None,
            "belgium_region": self.belgium_region.value if self.belgium_region else None,
            "heating_system": self.heating_system.value if self.heating_system else None,
            "hvac_system": self.hvac_system.value if self.hvac_system else None,
            "ventilation_type": self.ventilation_type.value if self.ventilation_type else None,
        }

        # Annual consumption
        consumption = {}
        if self.annual_heating_kwh is not None:
            consumption["heating_kwh"] = self.annual_heating_kwh
            if self.total_area:
                consumption["heating_kwh_m2"] = self.annual_heating_kwh / self.total_area

        if self.annual_cooling_kwh is not None:
            consumption["cooling_kwh"] = self.annual_cooling_kwh
            if self.total_area:
                consumption["cooling_kwh_m2"] = self.annual_cooling_kwh / self.total_area

        if self.annual_electricity_kwh is not None:
            consumption["electricity_kwh"] = self.annual_electricity_kwh
            if self.total_area:
                consumption["electricity_kwh_m2"] = self.annual_electricity_kwh / self.total_area

        if self.annual_hot_water_kwh is not None:
            consumption["hot_water_kwh"] = self.annual_hot_water_kwh
            if self.total_area:
                consumption["hot_water_kwh_m2"] = self.annual_hot_water_kwh / self.total_area

        if self.annual_ventilation_kwh is not None:
            consumption["ventilation_kwh"] = self.annual_ventilation_kwh
            if self.total_area:
                consumption["ventilation_kwh_m2"] = self.annual_ventilation_kwh / self.total_area

        # Total consumption
        total_kwh = sum([
            self.annual_heating_kwh or 0.0,
            self.annual_cooling_kwh or 0.0,
            self.annual_electricity_kwh or 0.0,
            self.annual_hot_water_kwh or 0.0,
            self.annual_ventilation_kwh or 0.0
        ])
        consumption["total_kwh"] = total_kwh
        if self.total_area:
            consumption["total_kwh_m2"] = total_kwh / self.total_area

        summary["consumption"] = consumption

        # Renewable energy
        renewable = {}
        if self.annual_solar_pv_kwh is not None:
            renewable["solar_pv_kwh"] = self.annual_solar_pv_kwh
        if self.annual_renewable_kwh is not None:
            renewable["total_renewable_kwh"] = self.annual_renewable_kwh

        if renewable:
            summary["renewable_energy"] = renewable

        # Water consumption
        if self.annual_water_m3 is not None:
            summary["water_m3"] = self.annual_water_m3
            if self.total_area:
                summary["water_m3_per_m2"] = self.annual_water_m3 / self.total_area

        # EPC information
        primary_energy = self.calculate_primary_energy_per_m2()
        if primary_energy is not None:
            summary["primary_energy_kwh_m2"] = primary_energy

        calculated_rating = self.calculate_epc_rating()
        summary["epc_rating_calculated"] = calculated_rating.value if calculated_rating else None
        summary["epc_rating_current"] = self.epc_rating.value if self.epc_rating else None

        return summary

    def get_summary(self) -> dict[str, Any]:
        """Get summary information about this building."""
        return {
            "id": self.id,
            "name": self.name,
            "building_type": self.building_type.value,
            "level_count": self.level_count,
            "room_count": self.room_count,
            "total_rooms": self.total_rooms,
            "total_area_m2": self.total_area,
            "year_built": self.year_built,
            "location": {
                "address": self.address,
                "city": self.city,
                "country": self.country,
                "coordinates": (
                    {"lat": self.latitude, "lon": self.longitude}
                    if self.latitude and self.longitude
                    else None
                ),
            },
            "level_ids": self.level_ids,
            "room_ids": self.room_ids,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"Building(name={self.name}, type={self.building_type.value}, levels={self.level_count}, rooms={self.room_count})"

    def __repr__(self) -> str:
        """Repr representation."""
        return (
            f"Building(id={self.id!r}, name={self.name!r}, "
            f"type={self.building_type.value})"
        )
