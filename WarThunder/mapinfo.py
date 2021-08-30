'''
Module to query and access map and non-player object/vehicle data during War Thunder matches
'''


import os
import socket
import imagehash
from time import sleep
from requests import get
from PIL import Image, ImageDraw
from json.decoder import JSONDecodeError
from simplejson.errors import JSONDecodeError as simpleJSONDecodeError
from urllib.error import URLError
from urllib.request import urlretrieve
from requests.exceptions import ReadTimeout, ConnectTimeout
from math import radians, degrees, sqrt, sin, asin, cos, atan2
from WarThunder.maps import maps


LOCAL_PATH   = os.path.dirname(os.path.realpath(__file__))
MAP_PATH     = os.path.join(LOCAL_PATH, 'map.jpg')
IP_ADDRESS   = socket.gethostbyname(socket.gethostname())
URL_MAP_IMG  = 'http://{}:8111/map.img'.format(IP_ADDRESS)
URL_MAP_OBJ  = 'http://{}:8111/map_obj.json'.format(IP_ADDRESS)
URL_MAP_INFO = 'http://{}:8111/map_info.json'.format(IP_ADDRESS)
ENEMY_HEX_COLORS = ['#f40C00', '#ff0D00', '#ff0000']
MAX_HAMMING_DIST = 3
EARTH_RADIUS_KM  = 6378.137
REQUEST_TIMEOUT  = 0.1


def hypotenuse(a: float, b: float) -> float:
    '''
    Find the length of the hypotenuse side of a right triangle
    
    Args:
        a:
            One side of the right triange
        b:
            Other side of the right triange
    
    Returns:
            Length of the hypotenuse
    '''
    
    return sqrt((a ** 2) + (b ** 2))

def coord_bearing(lat_1: float, lon_1: float, lat_2: float, lon_2: float) -> float:
    '''
    Find the bearing (in degrees) between two lat/lon coordinates (dd)
    
    Args:
        lat_1:
            First point's latitude (dd)
        lon_1:
            First point's longitude (dd)
        lat_2:
            Second point's latitude (dd)
        lon_2:
            Second point's longitude (dd)
    
    Returns:
            Bearing in degrees between point 1 and 2
    '''
    
    deltaLon_r = radians(lon_2 - lon_1)
    lat_1_r = radians(lat_1)
    lat_2_r = radians(lat_2)

    x = cos(lat_2_r) * sin(deltaLon_r)
    y = cos(lat_1_r) * sin(lat_2_r) - sin(lat_1_r) * cos(lat_2_r) * cos(deltaLon_r)

    return (degrees(atan2(x, y)) + 360) % 360

def coord_dist(lat_1: float, lon_1: float, lat_2: float, lon_2: float) -> float:
    '''
    Find the total distance (in km) between two lat/lon coordinates (dd)
    
    Args:
        lat_1:
            First point's latitude (dd)
        lon_1:
            First point's longitude (dd)
        lat_2:
            Second point's latitude (dd)
        lon_2:
            Second point's longitude (dd)
    
    Returns:
            Distance in km between point 1 and 2
    '''
    
    lat_1_rad = radians(lat_1)
    lon_1_rad = radians(lon_1)
    lat_2_rad = radians(lat_2)
    lon_2_rad = radians(lon_2)
    
    d_lat = lat_2_rad - lat_1_rad
    d_lon = lon_2_rad - lon_1_rad
    
    a = (sin(d_lat / 2) ** 2) + cos(lat_1_rad) * cos(lat_2_rad) * (sin(d_lon / 2) ** 2)
    
    return 2 * EARTH_RADIUS_KM * atan2(sqrt(a), sqrt(1 - a))

def coord_coord(lat: float, lon: float, dist: float, bearing: float) -> list:
    '''
    Finds the lat/lon coordinates "dist" km away from the given "lat" and "lon"
    coordinate along the given compass "bearing"
    
    Args:
        lat:
            First point's latitude (dd)
        lon:
            First point's longitude (dd)
        dist:
            Distance in km the second point should be from the first point
        bearing:
            Bearing in degrees from the first point to the second
    
    Returns:
            Latitude and longitude in DD of the second point
    '''
    
    brng  = radians(bearing)
    lat_1 = radians(lat)
    lon_1 = radians(lon)
    
    lat_2 = asin(sin(lat_1) * cos(dist / EARTH_RADIUS_KM) + cos(lat_1) * sin(dist / EARTH_RADIUS_KM) * cos(brng))
    lon_2 = lon_1 + atan2(sin(brng) * sin(dist / EARTH_RADIUS_KM) * cos(lat_1), cos(dist / EARTH_RADIUS_KM) - sin(lat_1) * sin(lat_2))
    
    return [degrees(lat_2), degrees(lon_2)]

def get_grid_info(map_img: Image) -> dict:
    '''
    Compare map from browser interface to pre-calculated map hash to provide
    location info.
    
    Args:
        map_img:
            PIL.Image object of the current map's JPEG
    
    Returns:
            Dictionary with map metadata. Example - 
                {'name': 'Kursk',
                 'ULHC_lat': 51.16278580067218,
                 'ULHC_lon': 36.906235369488115,
                 'size_km' : 65},
    '''
    
    hash_ = str(imagehash.average_hash(map_img))
    hamming_dists = []
    
    for map_hash in maps.keys():
        hamming_dists.append((len([index for index in range(len(hash_)) if not hash_[index] == map_hash[index]]), map_hash))
        
        
    match = min(hamming_dists)
    
    if match[0] <= MAX_HAMMING_DIST:
        return maps[match[1]]
    
    return {'name': 'UNKNOWN',
            'ULHC_lat': 0.0,
            'ULHC_lon': 0.0,
            'size_km' : 65}

def find_obj_coords(x: float, y: float, map_size: float, ULHC_lat: float, ULHC_lon: float) -> list:
    '''
    Convert the provided object's x/y coordinate to lat/lon
    
    Args:
        x:
            The distance of the object from the upper left hand corner of the
            map in the horizontal direction. x=0 means the object is on the
            left border of the map and x=1 means the object is on the right
            border
        y:
            The distance of the object from the upper left hand corner of the
            map in the vertical direction. y=0 means the object is on the top
            border of the map and y=1 means the object is on the bottom border
        map_size:
            The length/width of the map in km (all maps are square)
        ULHC_lat:
            The true world estimated latidude of the map's upper left hand
            corner point
        ULHC_lon:
            The true world estimated longitude of the map's upper left hand
            corner point
    
    Returns:
            Estimated latitude and longitude of the object's position
    '''
    
    dist_x  = x * map_size
    dist_y  = y * map_size
    dist    = hypotenuse(dist_x, dist_y)
    bearing = degrees(atan2(y, x)) + 90
    
    if bearing < 0:
        bearing += 360
    
    return coord_coord(ULHC_lat, ULHC_lon, dist, bearing)


class map_obj(object):
    def __init__(self, map_obj_entry: dict = {}, map_size: float = 65, ULHC_lat: float = 0, ULHC_lon: float = 0):
        '''
        Args:
            map_obj_entry:
                A single object/vehicle entry from the JSON scraped from
                http://localhost:8111/map_obj.json
            map_size:
                The length/width of the map in km (all maps are square)
            ULHC_lat:
                The true world estimated latidude of the map's upper left hand
                corner point
            ULHC_lon:
                The true world estimated longitude of the map's upper left hand
                corner point
        '''
        
        self.type      = ''
        self.icon      = ''
        self.hex_color = ''
        self.friendly  = True
        
        self.position       = [0, 0] # NOT for airfield
        self.position_delta = [0, 0] 
        self.south_end      = [0, 0] # ONLY for airfield
        self.east_end       = [0, 0] # ONLY for airfield
        
        self.position_ll   = [0, 0] # NOT for airfield
        self.south_end_ll  = [0, 0] # ONLY for airfield
        self.east_end_ll   = [0, 0] # ONLY for airfield
        self.runway_dir    = 0      # ONLY for airfield
        self.airfield      = False
        self.base          = False
        self.heavy_tank    = False
        self.medium_tank   = False
        self.light_tank    = False
        self.spg           = False
        self.spaa          = False
        self.wheeled       = False # AI only
        self.tracked       = False # AI only
        self.aaa           = False
        self.bomber        = False # Also helicopter (thanks Gayjin, very cool)
        self.heavy_fighter = False
        self.fighter       = False
        self.ship          = False
        self.torpedo_boat  = False
        self.tank_respawn  = False
        self.bomber_respawn  = False
        self.fighter_respawn = False
        self.capture_zone  = False
        self.defend_point  = False
        
        self.hdg = 0
        
        if map_obj_entry:
            self.update(map_obj_entry, map_size, ULHC_lat, ULHC_lon)
    
    def update(self, map_obj_entry: dict, map_size: float, ULHC_lat: float, ULHC_lon: float):
        '''
        Description:
        ------------
        Update object attributes based on the provided map context. Such attributes
        include:
            
            self.type
            self.icon
            self.hex_color
            self.position       (x-y coordinate)
            self.position_ll    (estimated latitude and longitude)
            self.position_delta (x-y difference)
            self.hdg
            self.south_end    (x-y coordinate)
            self.south_end_ll (estimated latitude and longitude)
            self.east_end     (x-y coordinate)
            self.east_end_ll  (estimated latitude and longitude)
            self.runway_dir
            
        plus other attributes that denote the object's vehicle type (i.e. ship
        or fighter)
        
        Args:
            map_obj_entry:
                A single object/vehicle entry from the JSON scraped from
                http://localhost:8111/map_obj.json
            map_size:
                The length/width of the map in km (all maps are square)
            ULHC_lat:
                The true world estimated latidude of the map's upper left hand
                corner point
            ULHC_lon:
                The true world estimated longitude of the map's upper left hand
                corner point
        '''
        
        self.type      = map_obj_entry['type']
        self.icon      = map_obj_entry['icon']
        self.hex_color = map_obj_entry['color']
        
        if (self.hex_color in ENEMY_HEX_COLORS) or map_obj_entry['blink']:
            self.friendly = False
        else:
            self.friendly = True
               
        if self.type.lower() == 'airfield':
            self.airfield = True
        else:
            self.airfield = False
            
        if self.icon.lower() == 'bombing_point':
            self.base = True
        else:
            self.base = False
        
        if self.icon.lower() == 'heavytank':
            self.heavy_tank = True
        else:
            self.heavy_tank = False
        
        if self.icon.lower() == 'mediumtank':
            self.medium_tank = True
        else:
            self.medium_tank = False
                
        if self.icon.lower() == 'lighttank':
            self.light_tank = True
        else:
            self.light_tank = False
        
        if self.icon.lower() == 'tankdestroyer':
            self.spg = True
        else:
            self.spg = False
        
        if self.icon.lower() == 'spaa':
            self.spaa = True
        else:
            self.spaa = False
        
        if self.icon.lower() == 'wheeled':
            self.wheeled = True
        else:
            self.wheeled = False
            
        if self.icon.lower() == 'tracked':
            self.tracked = True
        else:
            self.tracked = False
        
        if self.icon.lower() == 'airdefence':
            self.aaa = True
        else:
            self.aaa = False
        
        if self.icon.lower() == 'bomber':
            self.bomber = True
        else:
            self.bomber = False
        
        if self.icon.lower() == 'assault':
            self.heavy_fighter = True
        else:
            self.heavy_fighter = False
        
        if self.icon.lower() == 'fighter':
            self.fighter = True
        else:
            self.fighter = False
        
        if self.icon.lower() == 'ship':
            self.ship = True
        else:
            self.ship = False
        
        if self.icon.lower() == 'torpedoboat':
            self.torpedo_boat = True
        else:
            self.torpedo_boat = False
        
        if self.icon.lower() == 'respawn_base_tank':
            self.tank_respawn = True
        else:
            self.tank_respawn = False
        
        if self.icon.lower() == 'respawn_base_bomber':
            self.bomber_respawn = True
        else:
            self.bomber_respawn = False
        
        if self.icon.lower() == 'respawn_base_fighter':
            self.fighter_respawn = True
        else:
            self.fighter_respawn = False
        
        if self.icon.lower() == 'capture_zone':
            self.capture_zone = True
        else:
            self.capture_zone = False
        
        if self.icon.lower() == 'defending_point':
            self.defend_point = True
        else:
            self.defend_point = False
        
        try:
            self.position = [map_obj_entry['x'], map_obj_entry['y']]
        except KeyError:
            self.position = [0, 0]
        
        try:
            self.position_delta = [map_obj_entry['dx'], map_obj_entry['dy']]
            
            self.hdg = degrees(atan2(*self.position_delta)) + 90
                    
            if self.hdg < 0:
                self.hdg += 360
        except KeyError:
            self.position_delta = [0, 0]
            self.hdg = 0
        
        try:
            self.south_end = [map_obj_entry['sx'], map_obj_entry['sy']]
            self.east_end  = [map_obj_entry['ex'], map_obj_entry['ey']]
            
            self.south_end_ll = find_obj_coords(*self.south_end,
                                                map_size,
                                                ULHC_lat,
                                                ULHC_lon)
            self.east_end_ll = find_obj_coords(*self.east_end,
                                               map_size,
                                               ULHC_lat,
                                               ULHC_lon)
            self.runway_dir = coord_bearing(*self.south_end_ll,
                                            *self.east_end_ll)
        except KeyError:
            self.south_end = [0, 0]
            self.east_end  = [0, 0]
            
            self.south_end_ll = [0, 0]
            self.east_end_ll  = [0, 0]
            
            self.runway_dir = 0
        
        self.position_ll = find_obj_coords(*self.position,
                                           map_size,
                                           ULHC_lat,
                                           ULHC_lon)


class MapInfo(object):
    def __init__(self):
        self.map_valid = False
        self.map_objs  = []
    
    def download_files(self) -> bool:
        '''
        Sample information about the map and the "seen" objects in the match
        from the localhost
        
        Example self.info - 
        {'grid_steps': [8192.0, 8192.0],
         'grid_zero': [-28672.0, 28672.0],
         'map_generation': 12,
         'map_max': [32768.0, 32768.0],
         'map_min': [-32768.0, -32768.0]}
        
        Example self.obj - 
        [{'type': 'airfield',
          'color': '#185AFF',
          'color[]': [24, 90, 255],
          'blink': 0,
          'icon': 'none',
          'icon_bg': 'none',
          'sx': 0.338597,
          'sy': 0.720108,
          'ex': 0.357913,
          'ey': 0.692523},
         {'type': 'aircraft',
          'color': '#fa3200',
          'color[]': [250, 50, 0],
          'blink': 0,
          'icon': 'Fighter',
          'icon_bg': 'none',
          'x': 0.48744,
          'y': 0.542793,
          'dx': -0.640827,
          'dy': 0.767686},
         ...]
        
        Returns:
                Whether or not the map data was successfully retrieved
        '''
        
        self.map_valid = False
        
        try:
            urlretrieve(URL_MAP_IMG, MAP_PATH)
            self.info = get(URL_MAP_INFO, timeout=REQUEST_TIMEOUT).json()
            self.obj  = get(URL_MAP_OBJ,  timeout=REQUEST_TIMEOUT).json()
            self.parse_meta()
            
            self.map_img  = Image.open(MAP_PATH)
            self.map_draw = ImageDraw.Draw(self.map_img)
            
            self.grid_info = get_grid_info(self.map_img)
            
            self.map_valid = True
                
        except URLError:
            print('ERROR: could not download map.jpg')
    
        except (OSError, JSONDecodeError, simpleJSONDecodeError):
            print('Waiting to join a match')
            sleep(1)
            
        except ReadTimeout:
            print('ERROR: ReadTimeout')
            
        except ConnectTimeout:
            print('ERROR: ConnectTimeout')
            
        return self.map_valid
    
    def parse_meta(self):
        '''
        Calculate values that might be useful for extra processing. Also build
        a list of War Thunder objects (self.map_objs) present in the match to
        keep track of
        '''
        
        self.map_objs = []
        self.player_found = False
        
        if self.map_valid:
            for obj in self.obj:
                self.map_objs.append(map_obj(obj,
                                             self.grid_info['size_km'],
                                             self.grid_info['ULHC_lat'],
                                             self.grid_info['ULHC_lon']))
                
                if obj['icon'] == 'Player':
                    self.player_found = True
                    
                    self.player_lat = self.map_objs[-1].position_ll[0]
                    self.player_lon = self.map_objs[-1].position_ll[1]
    
    def airfields(self) -> list:
        '''
        Return a list of map_objs that includes all airfields currently in the match
        
        Returns:
                List of map_objs of found airfields
        '''
        
        return [obj for obj in self.map_objs if obj.airfield]
    
    def bases(self) -> list:
        '''
        Return a list of map_objs that includes all bases (bomb points) currently in the match
        
        Returns:
                List of map_objs of found bases 
        '''
        
        return [obj for obj in self.map_objs if obj.base]
    
    def heavy_tanks(self) -> list:
        '''
        Return a list of map_objs that includes all heavy tanks currently in the match
        
        Returns:
                List of map_objs of found heavy tanks
        '''
        
        return [obj for obj in self.map_objs if obj.heavy_tank]
    
    def medium_tanks(self) -> list:
        '''
        Return a list of map_objs that includes all medium tanks currently in the match
        
        Returns:
                List of map_objs of found medium tanks
        '''
        
        return [obj for obj in self.map_objs if obj.medium_tank]
    
    def light_tanks(self) -> list:
        '''
        Return a list of map_objs that includes all light tanks currently in the match
        
        Returns:
                List of map_objs of found light tanks
        '''
        
        return [obj for obj in self.map_objs if obj.light_tank]
    
    def SPGs(self) -> list:
        '''
        Return a list of map_objs that includes all spgs currently in the match
        
        Returns:
                List of map_objs of found spgs
        '''
        
        return [obj for obj in self.map_objs if obj.spg]
    
    def SPAAs(self) -> list:
        '''
        Return a list of map_objs that includes all spaas currently in the match
        
        Returns:
                List of map_objs of found spaas
        '''
        
        return [obj for obj in self.map_objs if obj.spaa]
    
    def tanks(self) -> list:
        '''
        Return a list of map_objs that includes all tanks currently in the match
        
        Returns:
                List of map_objs of found tanks
        '''
        
        output = []
        
        output.extend(self.heavy_tanks())
        output.extend(self.medium_tanks())
        output.extend(self.light_tanks())
        output.extend(self.SPGs())
        output.extend(self.SPAAs())
        
        return output
    
    def wheeled_AIs(self) -> list:
        '''
        Return a list of map_objs that includes all wheeled AIs currently in the match
        
        Returns:
                List of map_objs of found wheeled AIs
        '''
        
        return [obj for obj in self.map_objs if obj.wheeled]
    
    def tracked_AIs(self) -> list:
        '''
        Return a list of map_objs that includes all tracked AIs currently in the match
        
        Returns:
                List of map_objs of found tracked AIs
        '''
        
        return [obj for obj in self.map_objs if obj.tracked]
    
    def AAAs(self) -> list:
        '''
        Return a list of map_objs that includes all AAAs currently in the match
        
        Returns:
                List of map_objs of found AAAs
        '''
        
        return [obj for obj in self.map_objs if obj.aaa]
    
    def bombers(self) -> list:
        '''
        Return a list of map_objs that includes all bombers (and helicopters) currently in the match
        
        Returns:
                List of map_objs of found bombers/helicopters
        '''
        
        return [obj for obj in self.map_objs if obj.bomber]
    
    def heavy_fighters(self) -> list:
        '''
        Return a list of map_objs that includes all heavy fighters currently in the match
        
        Returns:
                List of map_objs of found heavy fighters
        '''
        
        return [obj for obj in self.map_objs if obj.heavy_fighter]
    
    def fighters(self) -> list:
        '''
        Return a list of map_objs that includes all fighters currently in the match
        
        Returns:
                List of map_objs of found fighters
        '''
        
        return [obj for obj in self.map_objs if obj.fighter]
    
    def ships(self) -> list:
        '''
        Return a list of map_objs that includes all shis currently in the match
        
        Returns:
                List of map_objs of found ships
        '''
        
        return [obj for obj in self.map_objs if obj.ship or obj.torpedo_boat]
    
    def planes(self) -> list:
        '''
        Return a list of map_objs that includes all planes currently in the match
        
        Returns:
                List of map_objs of found planes
        '''
        
        output = []
        
        output.extend(self.bombers())
        output.extend(self.heavy_fighters())
        output.extend(self.fighters())
        
        return output
    
    def tank_respawns(self) -> list:
        '''
        Return a list of map_objs that includes all tank respawns currently in the match
        
        Returns:
                List of map_objs of found tank respawns
        '''
        
        return [obj for obj in self.map_objs if obj.tank_respawn]
    
    def bomber_respawns(self) -> list:
        '''
        Return a list of map_objs that includes all bomber respawns currently in the match
        
        Returns:
                List of map_objs of found bomber respawns
        '''
        
        return [obj for obj in self.map_objs if obj.bomber_respawn]
    
    def fighter_respawns(self) -> list:
        '''
        Return a list of map_objs that includes all fighter respawns currently in the match
        
        Returns:
                List of map_objs of found fighter respawns
        '''
        
        return [obj for obj in self.map_objs if obj.fighter_respawn]
    
    def plane_respawns(self) -> list:
        '''
        Return a list of map_objs that includes all plane respawns currently in the match
        
        Returns:
                List of map_objs of found plane respawns
        '''
        
        output = []
        
        output.extend(self.bomber_respawns())
        output.extend(self.fighter_respawns())
        
        return output
    
    def capture_zones(self) -> list:
        '''
        Return a list of map_objs that includes all capture zones currently in the match
        
        Returns:
                List of map_objs of found capture zones
        '''
        
        return [obj for obj in self.map_objs if obj.capture_zone]
    
    def defend_points(self) -> list:
        '''
        Return a list of map_objs that includes all defend points currently in the match
        
        Returns:
                List of map_objs of found defend points
        '''
        
        return [obj for obj in self.map_objs if obj.defend_point]
    
    

