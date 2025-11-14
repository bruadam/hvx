"""
Simple test to verify portfolio loader structure detection.
"""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_structure_detection():
    """Test that we can detect different data structures."""
    from ingestion.csv.portfolio_loader import PortfolioLoader
    
    loader = PortfolioLoader()
    
    # Path to data samples
    data_path = Path(__file__).parent.parent.parent.parent / "data" / "samples"
    
    print("=" * 80)
    print("Testing Structure Detection")
    print("=" * 80)
    
    # Test hoeje-taastrup
    hoeje_path = data_path / "hoeje-taastrup"
    if hoeje_path.exists():
        structure = loader._detect_structure(hoeje_path)
        print(f"\nhoeje-taastrup: {structure}")
        assert structure == "hoeje-taastrup", f"Expected 'hoeje-taastrup', got '{structure}'"
        print("  ✓ Correctly detected")
        
        # List what we found
        building_dirs = list(hoeje_path.glob("building-*"))
        print(f"  Found {len(building_dirs)} buildings")
        
        for bd in building_dirs:
            sensors = list((bd / "sensors").glob("*.csv"))
            print(f"    - {bd.name}: {len(sensors)} sensor files")
    
    # Test dummy_data
    dummy_path = data_path / "dummy_data"
    if dummy_path.exists():
        structure = loader._detect_structure(dummy_path)
        print(f"\ndummy_data: {structure}")
        assert structure == "dummy_data", f"Expected 'dummy_data', got '{structure}'"
        print("  ✓ Correctly detected")
        
        # List what we found
        building_dirs = list(dummy_path.glob("building_*"))
        print(f"  Found {len(building_dirs)} buildings")
        
        for bd in building_dirs:
            if bd.is_dir():
                levels = list(bd.glob("level_*"))
                print(f"    - {bd.name}: {len(levels)} levels")
    
    # Test simple files
    structure = loader._detect_structure(data_path)
    print(f"\nsamples (top level): {structure}")
    assert structure == "simple", f"Expected 'simple', got '{structure}'"
    print("  ✓ Correctly detected")
    
    csv_files = list(data_path.glob("*.csv"))
    print(f"  Found {len(csv_files)} CSV files")
    for f in csv_files:
        print(f"    - {f.name}")
    
    print("\n" + "=" * 80)
    print("All structure detection tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    test_structure_detection()
