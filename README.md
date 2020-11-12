[![GitHub version](https://badge.fury.io/gh/PowerBroker2%2FWarThunder.svg)](https://badge.fury.io/gh/PowerBroker2%2FWarThunder) [![PyPI version](https://badge.fury.io/py/WarThunder.svg)](https://badge.fury.io/py/WarThunder)

# Overview
Python package to access vehicle telemetry and match data in real-time while in War Thunder air battles (NOT tanks). Here are some things you can access/do with this package:
- Get telemetry information on your vehicle and others identified on user's mini map
  - Data available for both user and other match player's vehicles:
    - Location in latitude/longitude (DD)
    - Heading angle
    - Airspeed
    - Pitch angle
  - Data avilable only for user's vehicle:
    - Roll angle
    - Flap state
    - Gear state
    - Altitude
- Data on other objects identified on user's mini map
  - Object's location in latitude/longitude (DD)
    - Airfields have 2 locations, one for each end of the runway
  - Object's faction (friendly or enemy)
  - Object's type (fighter, bomber, heavy tank, etc)
- Map name
- Chat comments (anything typed into chat)
- Match events (death, crash, etc)
- Log data in an [ACMI format](https://www.tacview.net/documentation/acmi/en/) compatible with [Tacview](https://www.tacview.net/)

# To Install
`pip install WarThunder`

# Example Python Script
```python
from pprint import pprint
from WarThunder import telemetry


if __name__ == '__main__':
    try:
        print('Starting')
        telem = telemetry.TelemInterface()
        
        while True:
            if telem.get_telemetry():
                pprint(telem.basic_telemetry)
    
    except KeyboardInterrupt:
        print('Closing')
```

This library makes use of War Thunder's localhost server pages (http://localhost:8111/indicators, http://localhost:8111/state, http://localhost:8111/map.img, http://localhost:8111/map_obj.json, and http://localhost:8111/map_info.json, and more!) that the game automatically serves when you launch a game match. If it is an air battle, these pages will include JSON formatted data with valid airplane telemetry. This telemetry is then converted and returned to the calling function/user.

The data can then be easily used for any custom application (i.e. telemetry datalogger and grapher).

# Example Use-Case:
https://github.com/PowerBroker2/Thunder_Viewer
