from __future__ import annotations

import uuid
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from core import (
    Portfolio,
    Building,
    Floor,
    Room,
    SensorDefinition,
    SensorSource,
    SensorSourceType,
    MetricType,
    SpatialEntityType,
    BuildingType,
    RoomType,
    EnergyCarrier,
)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class PortfolioStore:
    """
    Simple in-memory store backed by Streamlit session state.
    """

    def __init__(self) -> None:
        self.portfolio: Optional[Portfolio] = None
        self.buildings: Dict[str, Building] = {}
        self.floors: Dict[str, Floor] = {}
        self.rooms: Dict[str, Room] = {}

    # ------------------------------------------------------------------
    # Portfolio / Building / Floor / Room management
    # ------------------------------------------------------------------
    def create_portfolio(
        self,
        name: str,
        country: Optional[str] = None,
        region: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Portfolio:
        portfolio_id = _new_id("portfolio")
        portfolio = Portfolio(
            id=portfolio_id,
            name=name,
            type=SpatialEntityType.PORTFOLIO,
            country=country,
            region=region,
            metadata=metadata or {},
        )
        self.portfolio = portfolio
        return portfolio

    def add_building(
        self,
        name: str,
        building_type: BuildingType,
        area_m2: Optional[float] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        heating_carrier: Optional[EnergyCarrier] = None,
        cooling_carrier: Optional[EnergyCarrier] = None,
        dhw_carrier: Optional[EnergyCarrier] = None,
    ) -> Building:
        if self.portfolio is None:
            raise ValueError("Create a portfolio first.")

        building_id = _new_id("building")
        building = Building(
            id=building_id,
            name=name,
            parent_ids=[self.portfolio.id],
            building_type=building_type.value,
            area_m2=area_m2,
            city=city,
            country=country or self.portfolio.country,
            heating_energy_carrier=heating_carrier,
            cooling_energy_carrier=cooling_carrier,
            dhw_energy_carrier=dhw_carrier,
        )
        self.portfolio.add_building(building_id)
        self.buildings[building_id] = building
        return building

    def add_floor(
        self,
        building_id: str,
        name: str,
        floor_number: Optional[int] = None,
        area_m2: Optional[float] = None,
    ) -> Floor:
        building = self.buildings[building_id]
        floor_id = _new_id("floor")
        floor = Floor(
            id=floor_id,
            name=name,
            building_id=building_id,
            parent_ids=[building_id],
            floor_number=floor_number,
            area_m2=area_m2,
        )
        building.add_floor(floor_id)
        self.floors[floor_id] = floor
        return floor

    def add_room(
        self,
        building_id: str,
        floor_id: str,
        name: str,
        room_type: RoomType,
        area_m2: Optional[float] = None,
    ) -> Room:
        floor = self.floors[floor_id]
        room_id = _new_id("room")
        room = Room(
            id=room_id,
            name=name,
            floor_id=floor_id,
            building_id=building_id,
            parent_ids=[floor_id],
            room_type=room_type.value,
            area_m2=area_m2,
        )
        floor.add_room(room_id)
        building = self.buildings[building_id]
        building.add_room(room_id)
        self.rooms[room_id] = room
        return room

    # ------------------------------------------------------------------
    # Sensors and data
    # ------------------------------------------------------------------
    def add_sensor(
        self,
        entity_type: SpatialEntityType,
        entity_id: str,
        parameter: str,
        metric_type: MetricType,
        unit: str,
        source_type: SensorSourceType,
        weight: Optional[float] = None,
    ) -> SensorDefinition:
        entity = self.get_entity(entity_type, entity_id)
        if entity is None:
            raise ValueError("Invalid entity selection")

        sensor = SensorDefinition(
            id=_new_id("sensor"),
            spatial_entity_id=entity_id,
            parameter=parameter,
            metric=metric_type,
            unit=unit,
            sources=[
                SensorSource(
                    id=_new_id("source"),
                    type=source_type,
                    config={},
                )
            ],
            weight=weight,
        )
        entity.load_sensor(sensor)
        return sensor

    def load_room_timeseries(self, room_id: str, df: pd.DataFrame) -> None:
        room = self.rooms[room_id]
        dataset = df.copy()
        if "timestamp" in dataset.columns:
            dataset["timestamp"] = pd.to_datetime(dataset["timestamp"])
            dataset = dataset.set_index("timestamp")
        if dataset.index.dtype == "object":
            try:
                dataset.index = pd.to_datetime(dataset.index)
            except Exception:
                dataset.index = pd.RangeIndex(len(dataset))

        room.timestamps = [ts.isoformat() for ts in dataset.index]
        room.timeseries_data = {
            col: dataset[col].tolist() for col in dataset.columns
        }

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def get_entity(self, entity_type: SpatialEntityType, entity_id: str):
        if entity_type == SpatialEntityType.PORTFOLIO:
            return self.portfolio
        if entity_type == SpatialEntityType.BUILDING:
            return self.buildings.get(entity_id)
        if entity_type == SpatialEntityType.FLOOR:
            return self.floors.get(entity_id)
        if entity_type == SpatialEntityType.ROOM:
            return self.rooms.get(entity_id)
        return None

    def hierarchy_dict(self) -> Dict:
        if not self.portfolio:
            return {}

        def rooms_dict(floor: Floor) -> Dict:
            return {
                room_id: {
                    "name": self.rooms[room_id].name,
                    "room_type": self.rooms[room_id].room_type,
                    "area_m2": self.rooms[room_id].area_m2,
                }
                for room_id in floor.room_ids
                if room_id in self.rooms
            }

        def floors_dict(building: Building) -> Dict:
            data = {}
            for floor_id in building.floor_ids:
                floor = self.floors.get(floor_id)
                if floor:
                    data[floor_id] = {
                        "name": floor.name,
                        "number": floor.floor_number,
                        "rooms": rooms_dict(floor),
                    }
            return data

        buildings_data = {}
        for building_id, building in self.buildings.items():
            buildings_data[building_id] = {
                "name": building.name,
                "building_type": building.building_type,
                "area_m2": building.area_m2,
                "floors": floors_dict(building),
                "rooms": [
                    self.rooms[room_id].name
                    for room_id in building.room_ids
                    if room_id in self.rooms
                ],
            }

        return {
            "portfolio": {
                "id": self.portfolio.id,
                "name": self.portfolio.name,
                "country": self.portfolio.country,
                "buildings": buildings_data,
            }
        }


def get_portfolio_store() -> PortfolioStore:
    if "portfolio_store" not in st.session_state:
        st.session_state["portfolio_store"] = PortfolioStore()
    return st.session_state["portfolio_store"]
