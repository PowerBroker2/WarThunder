import time
from WarThunder import telemetry

def main():
    print("------------------------------------------------------")
    print("War Thunder Telemetry Test Script")
    print("------------------------------------------------------")
    print("Initializing TelemInterface...")
    
    telem = telemetry.TelemInterface()

    print("Waiting for War Thunder match to start (Press Ctrl+C to exit)...")
    
    try:
        while True:
            in_match = telem.get_telemetry(comments=True, events=True)
            
            if in_match:
                print("\n[IN FLIGHT] Active telemetry detected:")
                print(f"  - Airframe:   {telem.airframe}")
                print(f"  - Altitude:   {telem.altitude:.2f} m")
                print(f"  - IAS / TAS:  {telem.ias:.1f} km/h / {telem.tas:.1f} km/h")
                print(f"  - Heading:    {telem.heading:.2f}°")
                print(f"  - Position:   ({telem.lat:.6f}, {telem.lon:.6f})")
                print(f"  - Roll/Pitch:  {telem.roll:.2f}° / {telem.pitch:.2f}°")
                print(f"  - Raw Keys:   {len(telem.indicators.keys())} keys in raw indicators dict")
            else:
                status_messages = {
                    telemetry.IN_MENU: "In menu or hangar.",
                    telemetry.NO_MISSION: "No mission loaded.",
                    telemetry.WT_NOT_RUNNING: "War Thunder is not running or HTTP server is down.",
                    telemetry.OTHER_ERROR: "An unexpected error occurred."
                }
                msg = status_messages.get(telem.status, "Waiting...")
                print(f"[STATUS] {msg} (Status Code: {telem.status})", end='\r')
            
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\n\nTest script closed by user.")

if __name__ == '__main__':
    main()