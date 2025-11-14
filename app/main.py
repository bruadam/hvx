from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analysis_runner import run_en16798_for_rooms  # noqa: E402
from app.state import PortfolioStore, get_portfolio_store  # noqa: E402
from core import (
    SpatialEntityType,
    BuildingType,
    RoomType,
    MetricType,
    SensorSourceType,
    EnergyCarrier,
)


st.set_page_config(
    page_title="Digital Twin Portfolio Builder",
    layout="wide",
)


def _enum_format(enum_member) -> str:
    return enum_member.value.replace("_", " ").title()


def render_portfolio_section(store: PortfolioStore) -> None:
    st.header("1. Portfolio Setup")
    if store.portfolio is None:
        with st.form("create_portfolio_form"):
            name = st.text_input("Portfolio Name")
            country = st.text_input("Country Code (e.g. DK, FR)")
            region = st.text_input("Region / Climate Zone", value="")
            description = st.text_area("Description", value="")
            submitted = st.form_submit_button("Create Portfolio")
            if submitted:
                if not name:
                    st.warning("Portfolio name is required.")
                else:
                    store.create_portfolio(
                        name=name,
                        country=country or None,
                        region=region or None,
                        metadata={"description": description},
                    )
                    st.success(f"Portfolio '{name}' created.")
    else:
        portfolio = store.portfolio
        st.success(f"Active portfolio: {portfolio.name}")
        st.write(
            {
                "country": portfolio.country,
                "region": portfolio.region,
                "buildings": len(store.buildings),
            }
        )


def render_hierarchy(store: PortfolioStore) -> None:
    st.subheader("Hierarchy Overview")
    if not store.portfolio:
        st.info("Create a portfolio to start building the hierarchy.")
        return
    st.json(store.hierarchy_dict())


def render_building_forms(store: PortfolioStore) -> None:
    st.header("2. Spatial Hierarchy Builder")
    if not store.portfolio:
        st.info("Create a portfolio first.")
        return

    cols = st.columns(3)

    # Add Building
    with cols[0]:
        st.subheader("Add Building")
        with st.form("add_building_form"):
            name = st.text_input("Building Name")
            building_type = st.selectbox(
                "Building Type",
                options=list(BuildingType),
                format_func=_enum_format,
            )
            area = st.number_input("Area (m²)", min_value=0.0, value=1000.0, step=50.0)
            city = st.text_input("City", value="")
            heating_carrier = st.selectbox(
                "Heating Energy Carrier",
                options=list(EnergyCarrier),
                format_func=_enum_format,
                index=list(EnergyCarrier).index(EnergyCarrier.DISTRICT_HEATING),
            )
            cooling_carrier = st.selectbox(
                "Cooling Energy Carrier",
                options=list(EnergyCarrier),
                format_func=_enum_format,
                index=list(EnergyCarrier).index(EnergyCarrier.ELECTRICITY),
            )
            dhw_carrier = st.selectbox(
                "Hot Water Energy Carrier",
                options=list(EnergyCarrier),
                format_func=_enum_format,
                index=list(EnergyCarrier).index(EnergyCarrier.DISTRICT_HEATING),
            )
            submitted = st.form_submit_button("Add Building")
            if submitted:
                if not name:
                    st.warning("Building name is required.")
                else:
                    store.add_building(
                        name=name,
                        building_type=building_type,
                        area_m2=area,
                        city=city or None,
                        heating_carrier=heating_carrier,
                        cooling_carrier=cooling_carrier,
                        dhw_carrier=dhw_carrier,
                    )
                    st.success(f"Building '{name}' added.")

    building_options = list(store.buildings.values())

    # Add Floor
    with cols[1]:
        st.subheader("Add Floor")
        if not building_options:
            st.info("Add a building first.")
        else:
            building = st.selectbox(
                "Building",
                options=building_options,
                format_func=lambda b: b.name,
                key="floor_building_select",
            )
            with st.form("add_floor_form"):
                name = st.text_input("Floor Name", value=f"Floor {len(building.floor_ids)+1}")
                floor_number = st.number_input("Floor Number", value=len(building.floor_ids), step=1)
                area = st.number_input("Floor Area (m²)", min_value=0.0, value=building.area_m2 or 0.0)
                submitted = st.form_submit_button("Add Floor")
                if submitted:
                    floor = store.add_floor(
                        building_id=building.id,
                        name=name,
                        floor_number=int(floor_number),
                        area_m2=area,
                    )
                    st.success(f"Floor '{floor.name}' added to {building.name}.")

    # Add Room
    with cols[2]:
        st.subheader("Add Room")
        if not building_options:
            st.info("Add a building first.")
        else:
            building_for_room = st.selectbox(
                "Building",
                options=building_options,
                format_func=lambda b: b.name,
                key="room_building_select",
            )
            floors = [
                store.floors[floor_id]
                for floor_id in building_for_room.floor_ids
                if floor_id in store.floors
            ]
            if not floors:
                st.info("Create a floor before adding rooms.")
            else:
                floor = st.selectbox(
                    "Floor",
                    options=floors,
                    format_func=lambda f: f"{f.name} (#{f.floor_number})",
                )
                with st.form("add_room_form"):
                    name = st.text_input("Room Name", value=f"Room {len(floor.room_ids)+1}")
                    room_type = st.selectbox(
                        "Room Type",
                        options=list(RoomType),
                        format_func=_enum_format,
                    )
                    area = st.number_input("Room Area (m²)", min_value=0.0, value=50.0)
                    submitted = st.form_submit_button("Add Room")
                    if submitted:
                        room = store.add_room(
                            building_id=building_for_room.id,
                            floor_id=floor.id,
                            name=name,
                            room_type=room_type,
                            area_m2=area,
                        )
                        st.success(f"Room '{room.name}' added to {floor.name}.")

    render_hierarchy(store)


def render_sensor_section(store: PortfolioStore) -> None:
    st.header("3. Sensors & Data")
    if not store.portfolio:
        st.info("Create a portfolio first.")
        return

    entity_type = st.selectbox(
        "Select Entity Type",
        options=list(SpatialEntityType),
        format_func=_enum_format,
    )

    entity_map = {
        SpatialEntityType.PORTFOLIO: [store.portfolio] if store.portfolio else [],
        SpatialEntityType.BUILDING: list(store.buildings.values()),
        SpatialEntityType.FLOOR: list(store.floors.values()),
        SpatialEntityType.ROOM: list(store.rooms.values()),
    }
    entities = [e for e in entity_map[entity_type] if e is not None]
    selected_entity = None
    if entities:
        selected_entity = st.selectbox(
            "Select Entity",
            options=entities,
            format_func=lambda e: f"{e.name} ({e.id})",
        )
    else:
        st.info("No entities available.")

    if selected_entity:
        with st.form("add_sensor_form"):
            parameter = st.text_input("Parameter Name", value="temperature")
            metric_type = st.selectbox(
                "Metric Type",
                options=list(MetricType),
                format_func=_enum_format,
            )
            unit = st.text_input("Unit", value="°C")
            source_type = st.selectbox(
                "Source Type",
                options=list(SensorSourceType),
                format_func=_enum_format,
            )
            weight = st.number_input("Weight (optional)", min_value=0.0, value=1.0)
            submitted = st.form_submit_button("Add Sensor")
            if submitted:
                store.add_sensor(
                    entity_type=entity_type,
                    entity_id=selected_entity.id,
                    parameter=parameter,
                    metric_type=metric_type,
                    unit=unit,
                    source_type=source_type,
                    weight=weight,
                )
                st.success(f"Sensor '{parameter}' added to {selected_entity.name}.")

        if selected_entity.sensor_groups:
            st.subheader("Sensor Groups")
            sensor_summary = [
                {
                    "parameter": param,
                    "metric": group.metric.value,
                    "sensor_count": len(group.sensors),
                }
                for param, group in selected_entity.sensor_groups.items()
            ]
            st.table(pd.DataFrame(sensor_summary))

    st.subheader("Upload Room Measurements")
    rooms = list(store.rooms.values())
    if not rooms:
        st.info("Add rooms before uploading data.")
    else:
        room = st.selectbox(
            "Room",
            options=rooms,
            format_func=lambda r: f"{r.name} ({r.id})",
            key="upload_room_select",
        )
        uploaded = st.file_uploader(
            "Upload CSV with columns: timestamp, temperature, co2, humidity",
            type=["csv"],
        )
        if uploaded is not None:
            df = pd.read_csv(uploaded)
            store.load_room_timeseries(room.id, df)
            st.success(f"Loaded {len(df)} records for room {room.name}.")


def render_analysis_section(store: PortfolioStore) -> None:
    st.header("4. Run Analyses")
    rooms = list(store.rooms.values())
    if not rooms:
        st.info("Add rooms to run analyses.")
        return

    rooms_with_data = [room for room in rooms if room.timeseries_data]
    if not rooms_with_data:
        st.info("Upload time series data for at least one room.")
        return

    selected_rooms = st.multiselect(
        "Rooms to analyse (EN 16798)",
        options=rooms_with_data,
        default=rooms_with_data,
        format_func=lambda r: f"{r.name} ({r.id})",
    )
    season = st.selectbox("Season", options=["heating", "cooling"])
    if st.button("Run EN 16798 Analysis"):
        results = run_en16798_for_rooms(selected_rooms, season=season, buildings=store.buildings)
        if not results:
            st.warning("No results generated.")
        else:
            for room in selected_rooms:
                if room.id not in results:
                    st.info(f"No analysis output for {room.name}.")
                    continue
                st.subheader(f"Room: {room.name}")
                data = [
                    {
                        "Category": category,
                        "Compliance %": values["compliance_rate"],
                    }
                    for category, values in results[room.id].items()
                ]
                st.table(pd.DataFrame(data))


def main():
    store = get_portfolio_store()
    render_portfolio_section(store)
    st.divider()
    render_building_forms(store)
    st.divider()
    render_sensor_section(store)
    st.divider()
    render_analysis_section(store)


if __name__ == "__main__":
    main()
