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

This library makes use of War Thunder's localhost server pages (http://localhost:8111/indicators, http://localhost:8111/state, http://localhost:8111/map.img, http://localhost:8111/map_obj.json, and http://localhost:8111/map_info.json, and more!) that the game automatically serves when you launch a game match. If it is an air battle, these pages will include JSON formatted data with valid airplane telemetry. This telemetry is then converted and returned to the calling function/user.

The data can then be easily used for any custom application (i.e. telemetry datalogger and grapher).

# Example Use-Case:
https://github.com/PowerBroker2/Thunder_Viewer

# To Install
`pip install WarThunder`

# Example Python Script
```python
from WarThunder import telemetry
from WarThunder import mapinfo
from pprint import pprint


def find_map_info():
    print('------------------------------------------------------')
    print('Map Info:')
    print('\tName:\t\t\t\t\t{}'.format(telem.map_info.grid_info['name']))
    print('\tUpper Left Hand Corner Coordinate:\t[{}, {}]'.format(telem.map_info.grid_info['ULHC_lat'], telem.map_info.grid_info['ULHC_lon']))
    print('\tSize:\t\t\t\t\t{}km x {}km'.format(telem.map_info.grid_info['size_km'], telem.map_info.grid_info['size_km']))
    print('')

def find_all_bomb_points():
    print('------------------------------------------------------')
    find_bomb_points(True)
    find_bomb_points(False)

def find_all_airfields():
    print('------------------------------------------------------')
    find_airfields(True)
    find_airfields(False)

def find_all_planes():
    print('------------------------------------------------------')
    find_planes(True)
    find_planes(False)

def find_all_tanks():
    print('------------------------------------------------------')
    find_tanks(True)
    find_tanks(False)

def find_all_AAAs():
    print('------------------------------------------------------')
    find_AAAs(True)
    find_AAAs(False)
    
def find_basic_telemetry():
    print('------------------------------------------------------')
    print('Basic Telemetry:')
    pprint(telem.basic_telemetry)
    print('')
    
def find_comments():
    print('------------------------------------------------------')
    print('Comments:')
    comments = telem.get_comments()
    
    if comments:
        pprint(comments)
    else:
        print('\tNone')
    print('')
    
def find_events():
    print('------------------------------------------------------')
    print('Events:')
    events = telem.get_events()
    
    if events:
        pprint(events)
    else:
        print('\tNone')
    print('')

def find_bomb_points(friendly=True):
    if friendly:
        print('Friendly Bomb Points:')
        bomb_points = [obj for obj in telem.map_info.bases() if obj.friendly]
    else:
        print('Enemy Bomb Points:')
        bomb_points = [obj for obj in telem.map_info.bases() if not obj.friendly]
    
    if bomb_points:
        for bomb_point in bomb_points:
            print('\tBombing Point: {}'.format(bomb_point.position_ll))
    else:
        print('\tNone')
    print(' ')

def find_airfields(friendly=True):
    if friendly:
        print('Friendly Airfields:')
        airfields = [obj for obj in telem.map_info.airfields() if obj.friendly]
    else:
        print('Enemy Airfields:')
        airfields = [obj for obj in telem.map_info.airfields() if not obj.friendly]
    
    if airfields:
        for airfield in airfields:
            print('\tEast Coordinate:\t{}'.format(airfield.east_end_ll))
            print('\tSouth Coordinate:\t{}'.format(airfield.south_end_ll))
            print('\tRunway Heading:\t\t{} °'.format(airfield.runway_dir))
            print('\tRunway Length:\t\t{} km'.format(mapinfo.coord_dist(*airfield.east_end_ll, *airfield.south_end_ll)))
            print('')
    else:
        print('\tNone')
    print('')

def find_planes(friendly=True):
    if friendly:
        print('Friendly Planes:')
        planes = [obj for obj in telem.map_info.planes() if obj.friendly]
    else:
        print('Enemy Planes:')
        planes = [obj for obj in telem.map_info.planes() if not obj.friendly]
    
    if planes:
        for plane in planes:
            print('\tPosition:\t{}'.format(plane.position_ll))
            print('\tHeading:\t{}'.format(plane.hdg))
            print('')
    else:
        print('\tNone')
    print('')
    

def find_tanks(friendly=True):
    if friendly:
        print('Friendly Tanks:')
        tanks = [obj for obj in telem.map_info.tanks() if obj.friendly]
    else:
        print('Enemy Tanks:')
        tanks = [obj for obj in telem.map_info.tanks() if not obj.friendly]
    
    if tanks:
        for tank in tanks:
            print('\tPosition:\t{}'.format(tank.position_ll))
            print('\tHeading:\t{}'.format(tank.hdg))
            print('')
    else:
        print('\tNone')
    print('')

def find_AAAs(friendly=True):
    if friendly:
        print('Friendly AAAs:')
        AAAs = [obj for obj in telem.map_info.aaas() if obj.friendly]
    else:
        print('Enemy AAAs:')
        AAAs = [obj for obj in telem.map_info.aaas() if not obj.friendly]
    
    if AAAs:
        for AAA in AAAs:
            print('\tPosition:\t{}'.format(AAA.position_ll))
    else:
        print('\tNone')
    print('')


if __name__ == '__main__':
    try:
        telem = telemetry.TelemInterface()
        
        while not telem.get_telemetry():
            pass
        
        find_map_info()
        find_all_airfields()
        find_all_planes()
        find_all_tanks()
        find_all_bomb_points()
        find_all_AAAs()
        find_basic_telemetry()
        find_comments()
        find_events()
        
    except KeyboardInterrupt:
        print('Closing')
```

# Example Output:

```
------------------------------------------------------
Map Info:
        Name:                                   Ruhr
        Upper Left Hand Corner Coordinate:      [51.73829303094487, 6.437537416826182]
        Size:                                   65km x 65km

------------------------------------------------------
Friendly Airfields:
        East Coordinate:        [51.43642186048186, 6.930164507472621]
        South Coordinate:       [51.42827500146132, 6.9187980201946795]
        Runway Heading:         41.012963528358455 °
        Runway Length:          1.2019773371283782 km


Enemy Airfields:
        None

------------------------------------------------------
Friendly Planes:
        Position:       [51.44442707177771, 6.9048435542278]
        Heading:        191.7501316630443

        Position:       [51.444117867741056, 6.904189278772745]
        Heading:        191.7327479963323

        Position:       [51.44454697658904, 6.904059699788993]
        Heading:        191.73257970022075

        Position:       [51.44424583467913, 6.903432678896212]
        Heading:        191.73146722121177


Enemy Planes:
        None

------------------------------------------------------
Friendly Tanks:
        None

Enemy Tanks:
        Position:       [51.448172861547235, 6.883101199222394]
        Heading:        0


------------------------------------------------------
Friendly Bomb Points:
        None
 
Enemy Bomb Points:
        None
 
------------------------------------------------------
Friendly AAAs:
        Position:       [51.43844836391245, 6.925201117152168]
        Position:       [51.43829338882834, 6.9249774559908275]
        Position:       [51.438609103385076, 6.925442639430436]
        Position:       [51.4276199323936, 6.924573106340005]
        Position:       [51.42778836500274, 6.924790301773768]
        Position:       [51.427463714376124, 6.924367280891929]
        Position:       [51.438792600079246, 6.9392408728402595]

Enemy AAAs:
        None

------------------------------------------------------
Basic Telemetry:
{'IAS': 0,
 'airframe': 'bf_110g_4',
 'altitude': 59.221455,
 'flapState': 0,
 'gearState': 100,
 'heading': 40.639851,
 'lat': 51.428588129131136,
 'lon': 6.919188108689251,
 'pitch': 10.894329,
 'roll': 0.010828}

------------------------------------------------------
Comments:
        None

------------------------------------------------------
Events:
{'events': [], 'damage': [{'id': 1, 'msg': 'yn1/error/82220002', 'sender': '', 'enemy': False, 'mode': ''}]}
{'damage': [{'enemy': False,
             'id': 1,
             'mode': '',
             'msg': 'yn1/error/82220002',
             'sender': ''}],
 'events': []}
 ```
