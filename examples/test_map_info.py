'''
Test script for War Thunder Map Info & Metric NED Coordinates
'''

import time
from pprint import pprint
from WarThunder import telemetry
from WarThunder import mapinfo


def main():
    print("------------------------------------------------------")
    print(" War Thunder Map Info & Metric NED Coordinate Test")
    print("------------------------------------------------------")
    
    telem = telemetry.TelemInterface()
    print("Waiting for War Thunder match / map data...")
    
    # Poll until map files are successfully downloaded and parsed from localhost:8111
    while not telem.map_info.download_files():
        time.sleep(1.0)
        
    mi = telem.map_info
    
    print("\n[SUCCESS] Map loaded successfully!\n")
    print("=== Map Metadata ===")
    print(f"  - Map Generation ID: {mi.grid_info.get('name')}")
    print(f"  - Calculated Size:   {mi.grid_info.get('size_km'):.2f} km")
    print(f"  - Map Min Bounds (m):{mi.grid_info.get('map_min')}")
    print(f"  - Map Max Bounds (m):{mi.grid_info.get('map_max')}")
    print(f"  - Grid Steps (m):    {mi.grid_info.get('grid_steps')}")
    print(f"  - Grid Zero (m):     {mi.grid_info.get('grid_zero')}")
    
    print("\n=== Airfields & Runways ===")
    airfields = mi.airfields()
    if airfields:
        for i, af in enumerate(airfields):
            side = "Friendly" if af.friendly else "Enemy"
            runway_len = mapinfo.hypotenuse(
                af.east_end_ned[0] - af.south_end_ned[0],
                af.east_end_ned[1] - af.south_end_ned[1]
            )
            print(f"  [{i+1}] {side} Airfield")
            print(f"      - South End NED:  North: {af.south_end_ned[0]:.1f} m, East: {af.south_end_ned[1]:.1f} m")
            print(f"      - East End NED:   North: {af.east_end_ned[0]:.1f} m, East: {af.east_end_ned[1]:.1f} m")
            print(f"      - Runway Heading: {af.runway_dir:.1f}°")
            print(f"      - Runway Length:  {runway_len:.1f} m")
    else:
        print("  None found.")
        
    print("\n=== Bombing & Objective Points ===")
    bomb_pts = mi.bombing_points() + mi.defend_points() + mi.capture_zones()
    if bomb_pts:
        for i, bp in enumerate(bomb_pts):
            side = "Friendly" if bp.friendly else "Enemy"
            print(f"  [{i+1}] {side} {bp.icon or bp.type} -> Northing: {bp.position_ned[0]:.1f} m, Easting: {bp.position_ned[1]:.1f} m")
    else:
        print("  None found.")

    print("\n=== Planes Detected ===")
    planes = mi.planes()
    if planes:
        for i, p in enumerate(planes):
            side = "Friendly" if p.friendly else "Enemy"
            print(f"  [{i+1}] {side} Plane ({p.icon}) -> NED: ({p.position_ned[0]:.1f} N, {p.position_ned[1]:.1f} E) | Hdg: {p.hdg:.1f}°")
    else:
        print("  None found.")

    print("\n=== Tanks & Ground Units Detected ===")
    tanks = mi.tanks()
    if tanks:
        for i, t in enumerate(tanks):
            side = "Friendly" if t.friendly else "Enemy"
            print(f"  [{i+1}] {side} Tank ({t.icon}) -> NED: ({t.position_ned[0]:.1f} N, {t.position_ned[1]:.1f} E) | Hdg: {t.hdg:.1f}°")
    else:
        print("  None found.")

    print("\n=== AAAs Detected ===")
    aaas = mi.AAAs()
    if aaas:
        print(f"  Total AAAs found: {len(aaas)}")
        for i, a in enumerate(aaas[:5]):  # Show first 5
            print(f"      - AAA [{i+1}] NED: ({a.position_ned[0]:.1f} N, {a.position_ned[1]:.1f} E)")
        if len(aaas) > 5:
            print(f"      ... and {len(aaas) - 5} more.")
    else:
        print("  None found.")

    print("\n------------------------------------------------------")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest script closed by user.")