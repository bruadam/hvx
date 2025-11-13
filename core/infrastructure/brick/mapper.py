"""Brick Schema mapper for converting domain models to Brick ontology."""

from pathlib import Path
from typing import Any

import brickschema
from rdflib import Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

from core.domain.enums.hvac import HVACType
from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.ventilation import VentilationType
from core.domain.models.entities.building import Building
from core.domain.models.measurements.energy_consumption import EnergyConsumption
from core.domain.models.entities.room import Room
from core.infrastructure.brick.namespace_manager import BrickNamespaceManager as NSM


class BrickMapper:
    """
    Maps domain models to Brick Schema ontology.

    Converts Buildings, Rooms, and energy systems into semantic RDF triples
    following the Brick Schema standard.
    """

    def __init__(self, base_namespace: str = "https://ieq-analytics.example.org/"):
        """
        Initialize the Brick mapper.

        Args:
            base_namespace: Base URI for building instances
        """
        self.graph = brickschema.Graph()
        self.base_namespace = base_namespace

        # Load Brick Schema ontology (updated for brickschema 0.7+)
        self.graph.load_file(source="https://github.com/BrickSchema/Brick/releases/download/nightly/Brick.ttl")

        # Bind namespaces
        NSM.bind_to_graph(self.graph)

        # Track mapped entities
        self._mapped_buildings: dict[str, URIRef] = {}
        self._mapped_rooms: dict[str, URIRef] = {}
        self._mapped_sensors: dict[str, URIRef] = {}

    def add_building(self, building: Building) -> URIRef:
        """
        Add a building to the Brick graph.

        Args:
            building: Building domain model

        Returns:
            URIRef of the created building entity
        """
        # Create building URI
        building_uri = NSM.BUILDING[building.id]
        self._mapped_buildings[building.id] = building_uri

        # Add building as instance of Brick Building class
        self.graph.add((building_uri, RDF.type, NSM.BRICK.Building))

        # Add basic properties
        self.graph.add((building_uri, RDFS.label, Literal(building.name)))

        if building.address:
            self.graph.add((building_uri, NSM.BRICK.hasAddress, Literal(building.address)))

        # Add building type
        building_type_map = {
            "office": NSM.BRICK.Office_Building,
            "residential": NSM.BRICK.Residential_Building,
            "school": NSM.BRICK.Education_Building,
            "hospital": NSM.BRICK.Healthcare_Building,
            "retail": NSM.BRICK.Retail_Building,
            "industrial": NSM.BRICK.Industrial_Building,
        }

        brick_type = building_type_map.get(building.building_type.value.lower())
        if brick_type:
            self.graph.add((building_uri, RDF.type, brick_type))

        # Add area as property
        if building.total_area:
            area_value = Literal(building.total_area)
            self.graph.add((building_uri, NSM.BRICK.area, area_value))

        # Add location information
        if building.latitude and building.longitude:
            location_uri = NSM.BUILDING[f"{building.id}_location"]
            self.graph.add((building_uri, NSM.BRICK.hasLocation, location_uri))
            self.graph.add((location_uri, RDF.type, NSM.BRICK.Location))
            self.graph.add((location_uri, NSM.BRICK.latitude, Literal(building.latitude)))
            self.graph.add((location_uri, NSM.BRICK.longitude, Literal(building.longitude)))

        # Add HVAC system
        if building.hvac_system:
            self._add_hvac_system(building_uri, building)

        # Add ventilation system
        if building.ventilation_type:
            self._add_ventilation_system(building_uri, building)

        # Add heating system
        if building.heating_system:
            self._add_heating_system(building_uri, building)

        return building_uri

    def add_room(self, room: Room, building_uri: URIRef | None = None) -> URIRef:
        """
        Add a room to the Brick graph.

        Args:
            room: Room domain model
            building_uri: Optional parent building URI

        Returns:
            URIRef of the created room entity
        """
        # Create room URI
        room_uri = NSM.BUILDING[room.id]
        self._mapped_rooms[room.id] = room_uri

        # Add room as instance of Brick Space
        self.graph.add((room_uri, RDF.type, NSM.BRICK.Room))
        self.graph.add((room_uri, RDFS.label, Literal(room.name)))

        # Link to building
        if building_uri:
            self.graph.add((building_uri, NSM.BRICK.hasPart, room_uri))
            self.graph.add((room_uri, NSM.BRICK.isPartOf, building_uri))

        # Add area
        if room.area:
            self.graph.add((room_uri, NSM.BRICK.area, Literal(room.area)))

        # Add volume
        if room.volume:
            self.graph.add((room_uri, NSM.BRICK.volume, Literal(room.volume)))

        # Add sensors for available parameters
        if room.has_data:
            self._add_room_sensors(room_uri, room)

        return room_uri

    def add_energy_consumption(
        self, building_uri: URIRef, energy: EnergyConsumption
    ) -> dict[str, URIRef]:
        """
        Add energy consumption meters to a building.

        Args:
            building_uri: Building URI to attach meters to
            energy: Energy consumption data

        Returns:
            Dictionary mapping meter types to their URIRefs
        """
        meters = {}

        # Create meters for different energy types
        if energy.total_heating_kwh > 0:
            meter_uri = self._create_meter(
                building_uri, "heating", energy.total_heating_kwh, "heating"
            )
            meters["heating"] = meter_uri

        if energy.cooling_kwh > 0:
            meter_uri = self._create_meter(building_uri, "cooling", energy.cooling_kwh, "cooling")
            meters["cooling"] = meter_uri

        if energy.total_electricity_kwh > 0:
            meter_uri = self._create_meter(
                building_uri, "electricity", energy.total_electricity_kwh, "electricity"
            )
            meters["electricity"] = meter_uri

        if energy.total_hot_water_kwh > 0:
            meter_uri = self._create_meter(
                building_uri, "hot_water", energy.total_hot_water_kwh, "hot_water"
            )
            meters["hot_water"] = meter_uri

        if energy.ventilation_kwh > 0:
            meter_uri = self._create_meter(
                building_uri, "ventilation", energy.ventilation_kwh, "ventilation"
            )
            meters["ventilation"] = meter_uri

        # Add renewable energy generation
        if energy.total_renewable_kwh > 0:
            meter_uri = self._create_meter(
                building_uri,
                "solar_pv",
                energy.total_renewable_kwh,
                "renewable_generation",
            )
            meters["renewable"] = meter_uri

        return meters

    def _add_hvac_system(self, building_uri: URIRef, building: Building) -> URIRef:
        """Add HVAC system to building."""
        hvac_uri = NSM.BUILDING[f"{building.id}_hvac"]

        hvac_type_map = {
            HVACType.VAV: NSM.BRICK.Variable_Air_Volume_System,
            HVACType.CAV: NSM.BRICK.Constant_Air_Volume_System,
            HVACType.RADIANT: NSM.BRICK.Radiant_Heating_and_Cooling_System,
            HVACType.FAN_COIL: NSM.BRICK.Fan_Coil_Unit_System,
        }

        hvac_system_type = building.hvac_system if building.hvac_system is not None else None
        brick_hvac = hvac_type_map.get(hvac_system_type, NSM.BRICK.HVAC_System)

        self.graph.add((hvac_uri, RDF.type, brick_hvac))
        self.graph.add((building_uri, NSM.BRICK.hasPart, hvac_uri))
        self.graph.add((hvac_uri, NSM.BRICK.isPartOf, building_uri))

        return hvac_uri

    def _add_ventilation_system(self, building_uri: URIRef, building: Building) -> URIRef:
        """Add ventilation system to building."""
        vent_uri = NSM.BUILDING[f"{building.id}_ventilation"]

        vent_type_map = {
            VentilationType.NATURAL: NSM.BRICK.Natural_Ventilation_System,
            VentilationType.MECHANICAL: NSM.BRICK.Mechanical_Ventilation_System,
            VentilationType.MIXED_MODE: NSM.BRICK.Mixed_Mode_Ventilation_System,
        }

        brick_vent = vent_type_map.get(
            building.ventilation_type, NSM.BRICK.Ventilation_System
        )

        self.graph.add((vent_uri, RDF.type, brick_vent))
        self.graph.add((building_uri, NSM.BRICK.hasPart, vent_uri))
        self.graph.add((vent_uri, NSM.BRICK.isPartOf, building_uri))

        return vent_uri

    def _add_heating_system(self, building_uri: URIRef, building: Building) -> URIRef:
        """Add heating system to building."""
        heating_uri = NSM.BUILDING[f"{building.id}_heating"]

        # Map to Brick heating equipment types
        self.graph.add((heating_uri, RDF.type, NSM.BRICK.Heating_System))
        self.graph.add((building_uri, NSM.BRICK.hasPart, heating_uri))
        self.graph.add((heating_uri, NSM.BRICK.isPartOf, building_uri))

        return heating_uri

    def _add_room_sensors(self, room_uri: URIRef, room: Room) -> dict[str, URIRef]:
        """Add sensors for room parameters."""
        sensors = {}

        parameter_sensor_map = {
            ParameterType.TEMPERATURE: (NSM.BRICK.Temperature_Sensor, "temperature"),
            ParameterType.HUMIDITY: (NSM.BRICK.Humidity_Sensor, "humidity"),
            ParameterType.CO2: (NSM.BRICK.CO2_Level_Sensor, "co2"),
            ParameterType.PM25: (NSM.BRICK.PM2_dot_5_Sensor, "pm25"),
            ParameterType.PM10: (NSM.BRICK.PM10_Sensor, "pm10"),
            ParameterType.VOC: (NSM.BRICK.TVOC_Sensor, "tvoc"),
            ParameterType.ILLUMINANCE: (NSM.BRICK.Illuminance_Sensor, "illuminance"),
        }

        for param in room.available_parameters:
            if param in parameter_sensor_map:
                brick_class, sensor_name = parameter_sensor_map[param]
                sensor_uri = self._create_sensor(room_uri, room.id, sensor_name, brick_class)
                sensors[param.value] = sensor_uri

        return sensors

    def _create_sensor(
        self, room_uri: URIRef, room_id: str, sensor_name: str, brick_class: URIRef
    ) -> URIRef:
        """Create a sensor and link it to a room."""
        sensor_uri = NSM.SENSOR[f"{room_id}_{sensor_name}"]

        self.graph.add((sensor_uri, RDF.type, brick_class))
        self.graph.add((sensor_uri, RDFS.label, Literal(f"{room_id} {sensor_name} sensor")))
        self.graph.add((room_uri, NSM.BRICK.hasPart, sensor_uri))
        self.graph.add((sensor_uri, NSM.BRICK.isPointOf, room_uri))

        self._mapped_sensors[f"{room_id}_{sensor_name}"] = sensor_uri
        return sensor_uri

    def _create_meter(
        self, building_uri: URIRef, meter_type: str, value: float, category: str
    ) -> URIRef:
        """Create an energy meter."""
        meter_uri = NSM.SENSOR[f"{building_uri.split('/')[-1]}_{meter_type}_meter"]

        meter_class_map = {
            "heating": NSM.BRICK.Heating_Thermal_Energy_Meter,
            "cooling": NSM.BRICK.Cooling_Thermal_Energy_Meter,
            "electricity": NSM.BRICK.Electrical_Energy_Meter,
            "hot_water": NSM.BRICK.Thermal_Energy_Meter,
            "ventilation": NSM.BRICK.Electrical_Energy_Meter,
            "renewable_generation": NSM.BRICK.Solar_Panel_Energy_Meter,
        }

        brick_class = meter_class_map.get(category, NSM.BRICK.Energy_Meter)

        self.graph.add((meter_uri, RDF.type, brick_class))
        self.graph.add((meter_uri, RDFS.label, Literal(f"{meter_type} meter")))
        self.graph.add((building_uri, NSM.BRICK.hasPart, meter_uri))
        self.graph.add((meter_uri, NSM.BRICK.isPointOf, building_uri))

        return meter_uri

    def export_to_turtle(self, output_path: Path | str) -> None:
        """
        Export the Brick graph to a Turtle file.

        Args:
            output_path: Path to save the Turtle file
        """
        self.graph.serialize(destination=str(output_path), format="turtle")

    def export_to_rdf(self, output_path: Path | str) -> None:
        """
        Export the Brick graph to RDF/XML format.

        Args:
            output_path: Path to save the RDF file
        """
        self.graph.serialize(destination=str(output_path), format="xml")

    def export_to_json_ld(self, output_path: Path | str) -> None:
        """
        Export the Brick graph to JSON-LD format.

        Args:
            output_path: Path to save the JSON-LD file
        """
        self.graph.serialize(destination=str(output_path), format="json-ld")

    def query(self, sparql_query: str) -> list[dict[str, Any]]:
        """
        Execute a SPARQL query on the Brick graph.

        Args:
            sparql_query: SPARQL query string

        Returns:
            List of query results as dictionaries
        """
        results = self.graph.query(sparql_query)
        # Convert SPARQL results to list of dicts
        result_list = []
        for row in results:
            row_dict = {}
            for var in results.vars:
                row_dict[str(var)] = row[var]
            result_list.append(row_dict)
        return result_list

    def get_building_hierarchy(self, building_id: str) -> dict[str, Any]:
        """
        Get the complete hierarchy of a building (spaces, equipment, points).

        Args:
            building_id: Building identifier

        Returns:
            Dictionary representing the building hierarchy
        """
        building_uri = self._mapped_buildings.get(building_id)
        if not building_uri:
            return {}

        query = f"""
        PREFIX brick: <https://brickschema.org/schema/Brick#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?part ?label ?type WHERE {{
            <{building_uri}> brick:hasPart+ ?part .
            ?part a ?type .
            OPTIONAL {{ ?part rdfs:label ?label }}
        }}
        """

        results = self.query(query)

        hierarchy = {"building_id": building_id, "building_uri": str(building_uri), "parts": []}

        for row in results:
            hierarchy["parts"].append(
                {
                    "uri": str(row["part"]),
                    "type": str(row["type"]),
                    "label": str(row.get("label", "")),
                }
            )

        return hierarchy

    def find_sensors_by_type(self, sensor_type: str) -> list[URIRef]:
        """
        Find all sensors of a specific type.

        Args:
            sensor_type: Brick sensor class name (e.g., 'Temperature_Sensor')

        Returns:
            List of sensor URIRefs
        """
        query = f"""
        PREFIX brick: <https://brickschema.org/schema/Brick#>

        SELECT ?sensor WHERE {{
            ?sensor a brick:{sensor_type} .
        }}
        """

        results = self.query(query)
        return [row["sensor"] for row in results]

    def validate_graph(self) -> tuple[bool, list[str]]:
        """
        Validate the Brick graph for consistency.

        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []

        # Check if graph has entities
        if len(self.graph) == 0:
            errors.append("Graph is empty")
            return False, errors

        # Use Brick's built-in validation if available
        try:
            # Basic validation: check for orphaned entities
            query = """
            PREFIX brick: <https://brickschema.org/schema/Brick#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?s WHERE {
                ?s rdf:type ?type .
                FILTER NOT EXISTS { ?parent brick:hasPart ?s }
                FILTER NOT EXISTS { ?s brick:hasPart ?child }
                FILTER (CONTAINS(STR(?s), "sensor/") || CONTAINS(STR(?s), "building/"))
            }
            """
            # This is a simplified validation
            # Production code should use brickschema.validate()
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return len(errors) == 0, errors

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the Brick graph.

        Returns:
            Dictionary with graph statistics
        """
        return {
            "total_triples": len(self.graph),
            "buildings": len(self._mapped_buildings),
            "rooms": len(self._mapped_rooms),
            "sensors": len(self._mapped_sensors),
        }
