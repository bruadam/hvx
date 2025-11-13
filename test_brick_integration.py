"""Quick test to verify BrickSchema integration works."""

from datetime import datetime, timedelta

from core.domain.enums.building_type import BuildingType
from core.domain.enums.countries import Country
from core.domain.enums.hvac import HVACType
from core.domain.enums.ventilation import VentilationType
from core.domain.models.entities.building import Building
from core.domain.models.measurements.energy_consumption import EnergyConsumption
from core.domain.models.entities.room import Room
from core.infrastructure.brick.mapper import BrickMapper

print("Testing BrickSchema Integration...")
print("=" * 60)

# Test 1: Initialize mapper
print("\n[1] Initializing BrickMapper...")
mapper = BrickMapper()
print(f"✓ Mapper initialized")
print(f"  Graph size: {len(mapper.graph)} triples")

# Test 2: Create and map a building
print("\n[2] Creating and mapping building...")
building = Building(
    id="test_building",
    name="Test Office",
    building_type=BuildingType.OFFICE,
    total_area=1000.0,
    country=Country.BELGIUM,
    hvac_system=HVACType.VAV,
    ventilation_type=VentilationType.MECHANICAL,
)
building_uri = mapper.add_building(building)
print(f"✓ Building mapped: {building_uri}")

# Test 3: Create and map rooms
print("\n[3] Creating and mapping rooms...")
room = Room(
    id="test_room_101",
    name="Conference Room",
    building_id=building.id,
    area=50.0,
    volume=150.0,
)
room_uri = mapper.add_room(room, building_uri)
print(f"✓ Room mapped: {room_uri}")

# Test 4: Add energy consumption
print("\n[4] Adding energy consumption...")
energy = EnergyConsumption(
    measurement_start=datetime.now() - timedelta(days=365),
    measurement_end=datetime.now(),
    heating_kwh=50000.0,
    electricity_kwh=30000.0,
    cooling_kwh=20000.0,
)
meters = mapper.add_energy_consumption(building_uri, energy)
print(f"✓ Added {len(meters)} energy meters")

# Test 5: Query the graph
print("\n[5] Querying the graph...")
query = """
PREFIX brick: <https://brickschema.org/schema/Brick#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?entity ?type ?label WHERE {
    ?entity a ?type .
    OPTIONAL { ?entity rdfs:label ?label }
    FILTER(CONTAINS(STR(?entity), "test_"))
}
"""
results = mapper.query(query)
print(f"✓ Found {len(results)} entities")
for row in results[:5]:
    entity_type = str(row["type"]).split("#")[-1]
    label = row.get("label", "N/A")
    print(f"  - {label}: {entity_type}")

# Test 6: Get statistics
print("\n[6] Graph statistics...")
stats = mapper.get_stats()
for key, value in stats.items():
    print(f"  {key}: {value}")

# Test 7: Export to Turtle
print("\n[7] Exporting to Turtle format...")
output_file = "test_brick_model.ttl"
mapper.export_to_turtle(output_file)
print(f"✓ Exported to: {output_file}")

print("\n" + "=" * 60)
print("✓ All tests passed! BrickSchema integration is working.")
print("=" * 60)
