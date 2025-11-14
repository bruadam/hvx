"""
Demo: Portfolio Loader

Shows how to use the portfolio loader with the data folder structure.
"""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestion.csv import load_portfolio, load_hoeje_taastrup, load_dummy_data


def demo_auto_detect():
    """Demo auto-detection of data structure."""
    print("=" * 80)
    print("Demo: Auto-Detect Portfolio Structure")
    print("=" * 80)
    
    # Point to your data/samples folder
    data_path = Path(__file__).parent.parent.parent.parent / "data" / "samples"
    
    print(f"\nData path: {data_path}")
    print(f"Exists: {data_path.exists()}")
    
    # Test with hoeje-taastrup
    hoeje_path = data_path / "hoeje-taastrup"
    if hoeje_path.exists():
        print(f"\n{'─' * 80}")
        print("Loading: hoeje-taastrup")
        print(f"{'─' * 80}")
        
        entities, points, ts = load_portfolio(hoeje_path)
        
        print(f"\nLoaded:")
        print(f"  - {len(entities)} spatial entities")
        print(f"  - {len(points)} metering points")
        print(f"  - {len(ts)} time series")
        
        print(f"\nSpatial Entities:")
        for eid, entity in list(entities.items())[:5]:
            print(f"  - {eid}: {entity.name} ({entity.type.value})")
        
        print(f"\nMetering Points (first 5):")
        for pid, point in list(points.items())[:5]:
            print(f"  - {pid}: {point.name} ({point.metric.value})")
        
        print(f"\nTime Series (first 5):")
        for tid, timeseries in list(ts.items())[:5]:
            metadata = timeseries.metadata
            data_points = metadata.get('data_points', 0)
            print(f"  - {tid}: {timeseries.metric.value} ({data_points} points)")
    
    # Test with dummy_data
    dummy_path = data_path / "dummy_data"
    if dummy_path.exists():
        print(f"\n{'─' * 80}")
        print("Loading: dummy_data")
        print(f"{'─' * 80}")
        
        entities, points, ts = load_portfolio(dummy_path)
        
        print(f"\nLoaded:")
        print(f"  - {len(entities)} spatial entities")
        print(f"  - {len(points)} metering points")
        print(f"  - {len(ts)} time series")
        
        print(f"\nSpatial Entities:")
        for eid, entity in list(entities.items())[:5]:
            print(f"  - {eid}: {entity.name} ({entity.type.value})")
        
        print(f"\nMetering Points (first 5):")
        for pid, point in list(points.items())[:5]:
            print(f"  - {pid}: {point.name} ({point.metric.value})")


def demo_specific_loader():
    """Demo using specific loaders."""
    print("\n" + "=" * 80)
    print("Demo: Specific Loaders")
    print("=" * 80)
    
    data_path = Path(__file__).parent.parent.parent.parent / "data" / "samples"
    
    # Load hoeje-taastrup specifically
    hoeje_path = data_path / "hoeje-taastrup"
    if hoeje_path.exists():
        print(f"\nLoading hoeje-taastrup with specific loader...")
        entities, points, ts = load_hoeje_taastrup(hoeje_path)
        
        # Show a sample room's data
        room_entities = {k: v for k, v in entities.items() if v.type.value == 'room'}
        if room_entities:
            sample_room_id = list(room_entities.keys())[0]
            sample_room = room_entities[sample_room_id]
            
            print(f"\nSample Room: {sample_room.name}")
            print(f"  ID: {sample_room_id}")
            
            # Find metering points for this room
            room_points = {
                k: v for k, v in points.items()
                if v.spatial_entity_id == sample_room_id
            }
            
            print(f"  Metrics: {len(room_points)}")
            for pid, point in room_points.items():
                # Get time series
                if point.timeseries_ids:
                    ts_id = point.timeseries_ids[0]
                    if ts_id in ts:
                        timeseries = ts[ts_id]
                        metadata = timeseries.metadata
                        data_points = metadata.get('data_points', 0)
                        print(f"    - {point.metric.value}: {data_points} measurements")


def demo_timeseries_data():
    """Demo accessing time series data."""
    print("\n" + "=" * 80)
    print("Demo: Accessing Time Series Data")
    print("=" * 80)
    
    data_path = Path(__file__).parent.parent.parent.parent / "data" / "samples"
    
    # Load simple building sample
    simple_file = data_path / "building_sample.csv"
    if simple_file.exists():
        print(f"\nLoading: building_sample.csv")
        
        from ingestion.csv import load_from_csv
        
        entities, points, ts = load_from_csv(
            simple_file,
            format="wide",
            spatial_entity_id="building_sample",
            spatial_entity_name="Sample Building",
        )
        
        print(f"\nLoaded:")
        print(f"  - {len(points)} metering points")
        print(f"  - {len(ts)} time series")
        
        # Show temperature data
        temp_points = {k: v for k, v in points.items() if 'temperature' in k.lower()}
        if temp_points:
            temp_point = list(temp_points.values())[0]
            print(f"\nTemperature Point: {temp_point.name}")
            
            if temp_point.timeseries_ids:
                ts_id = temp_point.timeseries_ids[0]
                if ts_id in ts:
                    timeseries = ts[ts_id]
                    metadata = timeseries.metadata
                    
                    timestamps = metadata.get('timestamps', [])
                    values = metadata.get('values', [])
                    
                    print(f"  Data points: {len(values)}")
                    print(f"  Start: {timeseries.start}")
                    print(f"  End: {timeseries.end}")
                    print(f"  Granularity: {timeseries.granularity_seconds}s")
                    
                    if values:
                        print(f"\n  Sample values (first 5):")
                        for i in range(min(5, len(values))):
                            print(f"    {timestamps[i]}: {values[i]:.2f} {timeseries.unit}")
                        
                        print(f"\n  Statistics:")
                        print(f"    Min: {min(values):.2f} {timeseries.unit}")
                        print(f"    Max: {max(values):.2f} {timeseries.unit}")
                        print(f"    Avg: {sum(values)/len(values):.2f} {timeseries.unit}")


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "PORTFOLIO LOADER DEMO" + " " * 37 + "║")
    print("╚" + "═" * 78 + "╝")
    
    demo_auto_detect()
    demo_specific_loader()
    demo_timeseries_data()
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
