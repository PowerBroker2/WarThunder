[![GitHub version](https://badge.fury.io/gh/PowerBroker2%2FWarThunder.svg)](https://badge.fury.io/gh/PowerBroker2%2FWarThunder) [![PyPI version](https://badge.fury.io/py/WarThunder.svg)](https://badge.fury.io/py/WarThunder)

# Overview
Python package to access vehicle telemetry, map objects, combat events, and real-time flight logs in War Thunder air battles (NOT tanks). With recent additions, this framework also supports **WGS84 spatial projections** and **Tacview ACMI 2.2 local logging & live TCP streaming**.

Here are the key capabilities and features accessible through this package:
- **Vehicle Telemetry**:
  - Available for both user and other match players: Location in latitude/longitude/altitude (via WGS84 NED-to-LLA conversions), heading angle, airspeed (IAS/TAS).
  - Available exclusively for user's vehicle: Pitch angle, roll angle, flap state, gear state, altitude, and airframe identifier.
- **Mini-Map & Battlefield Objects**:
  - Objects' locations in latitude/longitude (DD).
  - Airfields include dual coordinate entries for both ends of the runway plus runway heading and length calculations.
  - Faction identification (friendly or enemy) and specific entity classifications (fighter, bomber, heavy tank, artillery, AAA, etc.).
- **Match Events & Communication**:
  - Chat comments (anything typed into chat) with automatic text sanitization.
  - Robust match events and damage logs (crash, overheating, engine damage, kills) accumulated persistently without data loss.
- **Tacview ACMI 2.2 & Real-Time Streaming**:
  - `AcmiWriter`: Local `\.acmi` file generation compliant with Tacview 2.2 standards.
  - `AcmiTcpServer`: Real-Time Telemetry TCP server (default port `42674`) for live telemetry streaming directly into Tacview.

This library makes use of War Thunder's localhost server pages (`http://localhost:8111/indicators`, `http://localhost:8111/state`, `http://localhost:8111/map.img`, `http://localhost:8111/map_obj.json`, `http://localhost:8111/map_info.json`, `http://localhost:8111/hudmsg`, `http://localhost:8111/gamechat`) served automatically during an active match.

# Example Use-Case:
https://github.com/PowerBroker2/Thunder_Viewer

# To Install
`pip install WarThunder`

# Example Python Script (Telemetry & ACMI Bridge)
```python
import time
from WarThunder import telemetry
from WarThunder import mapinfo
from WarThunder import acmi
from pprint import pprint


def main():
    telem = telemetry.TelemInterface()
    
    # Initialize Tacview local writer and live TCP streamer
    writer = acmi.AcmiWriter("flight_recording.acmi", ref_lat=37.5, ref_lon=-120.0, ref_alt=0.0)
    server = acmi.AcmiTcpServer(host='127.0.0.1', port=42674, ref_lat=37.5, ref_lon=-120.0, ref_alt=0.0)
    
    writer.open()
    server.start()
    print("[STATUS] ACMI Local Logging & Live TCP Streamer Active.")

    try:
        while True:
            # Poll telemetry and match events (events=True keeps persistent event logs)
            in_flight = telem.get_telemetry(comments=True, events=True)
            
            if not in_flight:
                print("Waiting for active flight...", end="\r")
                time.sleep(1.0)
                continue
                
            print(f"Airframe: {telem.airframe} | Alt: {telem.altitude:.1f}m | IAS: {telem.ias} km/h")
            print(f"Events Logged: {len(telem.events.get('damage', []))}")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Closing...")
    finally:
        writer.close()
        server.stop()


if __name__ == '__main__':
    main()
```

# Example Output:

```
------------------------------------------------------
Map Info:
        Name:                                         Ruhr
        Size:                                         65km x 65km

------------------------------------------------------
Basic Telemetry:
{'IAS': 350.5,
 'airframe': 'Bf 109 F',
 'altitude': 592.21,
 'flapState': 0.0,
 'gearState': 0.0,
 'heading': 40.64,
 'lat': 51.428588,
 'lon': 6.919188,
 'pitch': 10.89,
 'roll': 0.01}

------------------------------------------------------
Events:
{'damage': [{'enemy': False,
             'id': 1,
             'mode': '',
             'msg': 'Bf 109 F has crashed.',
             'sender': '',
             'time': 1932}],
 'events': []}
```