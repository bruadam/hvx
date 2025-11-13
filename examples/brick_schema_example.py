"""
Example: Using BrickSchema with IEQ Analytics Domain Models

This example demonstrates how to:
1. Map domain models (Building, Room, EnergyConsumption) to Brick Schema
2. Create a semantic building model
3. Query the model using SPARQL
4. Export to various RDF formats
"""

from datetime import datetime, timedelta
from pathlib import Path

from core.domain.enums.building_type import BuildingType
from core.domain.enums.countries import Country
from core.domain.enums.hvac import HVACType
from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.ventilation import VentilationType
from core.domain.models.building import Building
from core.domain.models.energy_consumption import EnergyConsumption
from core.domain.models.room import Room
from core.infrastructure.brick.mapper import BrickMapper


def main():
    """Main example function."""
    print("=" * 80)
    print("BrickSchema Integration Example")
    print("=" * 80)

    # Initialize the Brick mapper
    print("\n[1] Initializing Brick mapper...")
    mapper = BrickMapper(base_namespace="https://ieq-analytics.example.org/")
    print("✓ Mapper initialized with Brick Schema ontology loaded")

    # Create a sample building
    print("\n[2] Creating sample building...")
    building = Building(
        id="office_building_001",
        name="Green Office Tower",
        building_type=BuildingType.OFFICE,
        address="123 Sustainable Street, Brussels",
        city="Brussels",
        country=Country.BELGIUM,
        total_area=5000.0,  # m²
        year_built=2015,
        total_occupants=250,
        hvac_system=HVACType.VAV,
        ventilation_type=VentilationType.MECHANICAL,
        latitude=50.8503,
        longitude=4.3517,
        annual_heating_kwh=150000.0,
        annual_cooling_kwh=80000.0,
        annual_electricity_kwh=200000.0,
        annual_hot_water_kwh=30000.0,
        annual_solar_pv_kwh=50000.0,
    )
    print(f"✓ Created building: {building}")

    # Add building to Brick graph
    print("\n[3] Mapping building to Brick Schema...")
    building_uri = mapper.add_building(building)
    print(f"✓ Building mapped to: {building_uri}")

    # Create sample rooms with sensors
    print("\n[4] Creating sample rooms with sensors...")
    rooms = [
        Room(
            id="room_101",
            name="Conference Room A",
            building_id=building.id,
            area=50.0,
            volume=150.0,
            occupancy=12,
            ventilation_type=VentilationType.MECHANICAL,
        ),
        Room(
            id="room_102",
            name="Open Office Space",
            building_id=building.id,
            area=200.0,
            volume=600.0,
            occupancy=50,
            ventilation_type=VentilationType.MECHANICAL,
        ),
        Room(
            id="room_103",
            name="Laboratory",
            building_id=building.id,
            area=80.0,
            volume=320.0,
            occupancy=8,
            ventilation_type=VentilationType.MIXED_MODE,
        ),
    ]

    # Simulate available parameters for each room
    for room in rooms:
        # Add to building
        building.add_room(room.id)

        # Simulate that rooms have sensors
        # In real usage, this would come from loaded data
        room_params = [
            ParameterType.TEMPERATURE,
            ParameterType.HUMIDITY,
            ParameterType.CO2,
        ]

        # For lab, add additional sensors
        if "Laboratory" in room.name:
            room_params.extend([ParameterType.PM25, ParameterType.VOC])

        # Mock the available parameters
        # (In real usage, this would be detected from time_series_data)
        # We'll manually track this for the example
        room._simulated_params = room_params

    # Map rooms to Brick
    for room in rooms:
        print(f"\n  Mapping {room.name}...")
        room_uri = mapper.add_room(room, building_uri)

        # Add sensors based on simulated parameters
        for param in room._simulated_params:
            sensor_type_map = {
                ParameterType.TEMPERATURE: "Temperature_Sensor",
                ParameterType.HUMIDITY: "Humidity_Sensor",
                ParameterType.CO2: "CO2_Level_Sensor",
                ParameterType.PM25: "PM2_dot_5_Sensor",
                ParameterType.VOC: "TVOC_Sensor",
            }
            sensor_type = sensor_type_map.get(param)
            if sensor_type:
                print(f"    ✓ Added {sensor_type}")

        print(f"  ✓ Room mapped to: {room_uri}")

    # Add energy consumption data
    print("\n[5] Adding energy consumption data...")
    energy = EnergyConsumption(
        measurement_start=datetime.now() - timedelta(days=365),
        measurement_end=datetime.now(),
        heating_kwh=150000.0,
        cooling_kwh=80000.0,
        electricity_kwh=200000.0,
        hot_water_kwh=30000.0,
        ventilation_kwh=20000.0,
        solar_pv_kwh=50000.0,
    )

    meters = mapper.add_energy_consumption(building_uri, energy)
    print(f"✓ Added {len(meters)} energy meters:")
    for meter_type, meter_uri in meters.items():
        print(f"  - {meter_type}: {meter_uri}")

    # Get graph statistics
    print("\n[6] Graph statistics:")
    stats = mapper.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Query the graph using SPARQL
    print("\n[7] Querying the Brick graph...")

    # Query 1: Find all rooms
    print("\n  Query 1: Find all rooms")
    query1 = """
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?room ?label ?area WHERE {
        ?room a brick:Room .
        ?room rdfs:label ?label .
        OPTIONAL { ?room brick:area ?area }
    }
    ORDER BY ?label
    """
    results = mapper.query(query1)
    for row in results:
        area = f"{row.get('area', 'N/A')} m²" if row.get("area") else "N/A"
        print(f"    - {row['label']}: {area}")

    # Query 2: Find all sensors
    print("\n  Query 2: Find all sensors")
    query2 = """
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?sensor ?type ?label WHERE {
        ?sensor a ?type .
        ?sensor rdfs:label ?label .
        FILTER(CONTAINS(STR(?type), "Sensor"))
    }
    ORDER BY ?label
    """
    results = mapper.query(query2)
    for row in results:
        sensor_type = str(row["type"]).split("#")[-1]
        print(f"    - {row['label']}: {sensor_type}")

    # Query 3: Find all energy meters
    print("\n  Query 3: Find all energy meters")
    query3 = """
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?meter ?type ?label WHERE {
        ?meter a ?type .
        ?meter rdfs:label ?label .
        FILTER(CONTAINS(STR(?type), "Meter"))
    }
    ORDER BY ?label
    """
    results = mapper.query(query3)
    for row in results:
        meter_type = str(row["type"]).split("#")[-1]
        print(f"    - {row['label']}: {meter_type}")

    # Get building hierarchy
    print("\n[8] Building hierarchy:")
    hierarchy = mapper.get_building_hierarchy(building.id)
    print(f"  Building: {hierarchy['building_id']}")
    print(f"  Total components: {len(hierarchy['parts'])}")

    # Group by type
    type_counts = {}
    for part in hierarchy["parts"]:
        part_type = part["type"].split("#")[-1]
        type_counts[part_type] = type_counts.get(part_type, 0) + 1

    print("\n  Component breakdown:")
    for comp_type, count in sorted(type_counts.items()):
        print(f"    - {comp_type}: {count}")

    # Export to different formats
    print("\n[9] Exporting to RDF formats...")
    output_dir = Path("output/brick")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export to Turtle
    turtle_file = output_dir / "building_model.ttl"
    mapper.export_to_turtle(turtle_file)
    print(f"  ✓ Exported to Turtle: {turtle_file}")

    # Export to RDF/XML
    rdf_file = output_dir / "building_model.rdf"
    mapper.export_to_rdf(rdf_file)
    print(f"  ✓ Exported to RDF/XML: {rdf_file}")

    # Export to JSON-LD
    jsonld_file = output_dir / "building_model.jsonld"
    mapper.export_to_json_ld(jsonld_file)
    print(f"  ✓ Exported to JSON-LD: {jsonld_file}")

    # Validate graph
    print("\n[10] Validating Brick graph...")
    is_valid, errors = mapper.validate_graph()
    if is_valid:
        print("  ✓ Graph is valid!")
    else:
        print("  ✗ Graph validation errors:")
        for error in errors:
            print(f"    - {error}")

    print("\n" + "=" * 80)
    print("Example completed successfully!")
    print("=" * 80)

    # Print summary
    print("\n📊 Summary:")
    print(f"  • Mapped 1 building with {building.total_area} m²")
    print(f"  • Mapped {len(rooms)} rooms with various sensors")
    print(f"  • Added {len(meters)} energy meters")
    print(f"  • Total RDF triples: {stats['total_triples']}")
    print(f"  • Exported to 3 different RDF formats")

    print("\n💡 Next steps:")
    print("  • Load actual sensor data into rooms")
    print("  • Query for specific sensor readings")
    print("  • Integrate with other building systems")
    print("  • Use SPARQL to analyze building performance")
    print("  • Visualize the building topology")

    return mapper, building, rooms


if __name__ == "__main__":
    mapper, building, rooms = main()
