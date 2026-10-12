'''
Module to query and access map and non-player object/vehicle data during War Thunder matches
'''

import os
from time import sleep
from requests import get
from PIL import Image, ImageDraw
from json.decoder import JSONDecodeError
from simplejson.errors import JSONDecodeError as simpleJSONDecodeError
from urllib.error import URLError
from urllib.request import urlretrieve
from requests.exceptions import ReadTimeout, ConnectTimeout
from math import sqrt, atan2, degrees, radians, pi


LOCAL_PATH       = os.path.dirname(os.path.realpath(__file__))
MAP_PATH         = os.path.join(LOCAL_PATH, 'map.jpg')
IP_ADDRESS       = '127.0.0.1'
URL_MAP_IMG      = 'http://{}:8111/map.img'.format(IP_ADDRESS)
URL_MAP_OBJ      = 'http://{}:8111/map_obj.json'.format(IP_ADDRESS)
URL_MAP_INFO     = 'http://{}:8111/map_info.json'.format(IP_ADDRESS)
REQUEST_TIMEOUT  = 1.0

# WGS84 Earth Semi-Major Axis in meters
EARTH_RADIUS     = 6378137.0


def hypotenuse(a: float, b: float) -> float:
    '''
    Find the length of the hypotenuse side of a right triangle
    '''
    return sqrt((a ** 2) + (b ** 2))


def coord_dist(*args) -> float:
    '''
    Calculate the straight-line distance between two metric NED points in kilometers.
    Accepts either 4 arguments (n1, e1, n2, e2) or two point lists/tuples ([n1, e1], [n2, e2]).
    '''
    if len(args) == 4:
        n1, e1, n2, e2 = args
    elif len(args) == 2 and isinstance(args[0], (list, tuple)) and isinstance(args[1], (list, tuple)):
        n1, e1 = args[0]
        n2, e2 = args[1]
    else:
        return 0.0
    
    return sqrt((n2 - n1)**2 + (e2 - e1)**2) / 1000.0


def ned_to_lla(northing: float, easting: float, down: float, ref_lat: float = 37.0, ref_lon: float = -120.0, ref_alt: float = 0.0) -> tuple:
    '''
    Convert local NED (North-East-Down) coordinates in meters to WGS84 LLA 
    (Latitude, Longitude, Altitude) based on a reference origin.
    '''
    d_lat = (northing / EARTH_RADIUS) * (180.0 / pi)
    d_lon = (easting / (EARTH_RADIUS * cos_lat(ref_lat))) * (180.0 / pi) if abs(cos_lat(ref_lat)) > 1e-6 else 0.0
    
    lat = ref_lat + d_lat
    lon = ref_lon + d_lon
    alt = ref_alt - down
    
    return lat, lon, alt


def cos_lat(lat_deg: float) -> float:
    return sqrt(1.0 - (radians(lat_deg) * radians(lat_deg)) / 2.0) if abs(lat_deg) < 45 else __import__('math').cos(radians(lat_deg))


def lla_to_ned(lat: float, lon: float, alt: float, ref_lat: float = 37.0, ref_lon: float = -120.0, ref_alt: float = 0.0) -> tuple:
    '''
    Convert WGS84 LLA (Latitude, Longitude, Altitude) to local NED (North-East-Down) 
    in meters relative to a reference origin.
    '''
    d_lat = radians(lat - ref_lat)
    d_lon = radians(lon - ref_lon)
    
    northing = d_lat * EARTH_RADIUS
    easting = d_lon * EARTH_RADIUS * __import__('math').cos(radians(ref_lat))
    down = ref_alt - alt
    
    return northing, easting, down


class map_obj(object):
    def __init__(self, map_obj_entry: dict = None, map_info_meta: dict = None):
        if map_obj_entry is None:
            map_obj_entry = {}
        if map_info_meta is None:
            map_info_meta = {}
            
        self.type       = ''
        self.icon       = ''
        self.hex_color  = ''
        self.friendly   = True
        
        self.position       = [0.0, 0.0]
        self.position_ned   = [0.0, 0.0]
        self.position_delta = [0.0, 0.0]
        
        self.south_end      = [0.0, 0.0]
        self.east_end       = [0.0, 0.0]
        self.south_end_ned  = [0.0, 0.0]
        self.east_end_ned   = [0.0, 0.0]
        self.runway_dir     = 0.0
        
        self.airfield       = False
        self.heavy_tank     = False
        self.medium_tank    = False
        self.light_tank     = False
        self.spg            = False
        self.spaa           = False
        self.wheeled        = False
        self.tracked        = False
        self.aaa            = False
        self.bomber         = False
        self.heavy_fighter  = False
        self.fighter        = False
        self.ship           = False
        self.torpedo_boat   = False
        self.tank_respawn   = False
        self.bomber_respawn = False
        self.fighter_respawn = False
        self.capture_zone   = False
        self.defend_point   = False
        self.bombing_point  = False
        
        self.hdg = 0.0
        
        if map_obj_entry:
            self.update(map_obj_entry, map_info_meta)
    
    def _convert_to_ned(self, x: float, y: float, meta: dict) -> list:
        try:
            map_min = meta.get('map_min', [-65536.0, -65536.0])
            map_max = meta.get('map_max', [65536.0, 65536.0])
            grid_zero = meta.get('grid_zero', [0.0, 0.0])
            grid_size = meta.get('grid_size', [1.0, 1.0])
            
            span_x = map_max[0] - map_min[0]
            span_y = map_max[1] - map_min[1]
            
            if grid_size[0] > 0 and grid_size[1] > 0:
                easting = map_min[0] + (x * span_x) + grid_zero[0]
                northing = map_max[1] - (y * span_y) + grid_zero[1]
            else:
                easting = map_min[0] + (x * span_x)
                northing = map_max[1] - (y * span_y)
            
            return [northing, easting]
        except Exception:
            return [0.0, 0.0]

    def update(self, map_obj_entry: dict, map_info_meta: dict):
        self.type       = map_obj_entry.get('type', '')
        self.icon       = map_obj_entry.get('icon', '')
        self.hex_color  = map_obj_entry.get('color', '')
        rgb_color       = map_obj_entry.get('color[]', [0, 0, 0])
        
        hex_lower = self.hex_color.lower()
        known_enemy_hexes = {'#fa0c00', '#f40c00', '#ff0d00', '#ff0000', '#f00c00', '#fa0800'}
        
        is_red_hex = hex_lower in known_enemy_hexes
        is_red_rgb = len(rgb_color) >= 3 and rgb_color[0] > rgb_color[2] and rgb_color[0] > 100
        
        if is_red_hex or is_red_rgb or map_obj_entry.get('blink', 0):
            self.friendly = False
        else:
            self.friendly = True
               
        type_lower = self.type.lower()
        icon_lower = self.icon.lower()
        
        self.airfield = (type_lower == 'airfield' or icon_lower == 'airfield')
        self.bombing_point = (type_lower == 'bombing_point' or icon_lower == 'bombing_point')
        if self.bombing_point:
            self.friendly = False
            
        self.heavy_tank = icon_lower in ('heavytank', 'heavy_tank')
        self.medium_tank = icon_lower in ('mediumtank', 'medium_tank', 'ifv', 'apc')
        self.light_tank = icon_lower in ('lighttank', 'light_tank')
        self.spg = icon_lower in ('tankdestroyer', 'spg', 'tank_destroyer')
        self.spaa = icon_lower in ('spaa', 'sam')
        self.wheeled = icon_lower == 'wheeled'
        self.tracked = icon_lower == 'tracked'
        self.aaa = icon_lower in ('airdefence', 'aaa', 'artillery')
        
        self.bomber = icon_lower in ('bomber', 'helicopter')
        self.heavy_fighter = icon_lower in ('assault', 'heavy_fighter', 'strike')
        self.fighter = icon_lower in ('fighter', 'player', 'aircraft')
        
        self.ship = icon_lower in ('ship', 'torpedoboat', 'boat', 'frigate', 'destroyer', 'cruiser', 'battleship', 'missiledestroyer', 'corvette')
        self.torpedo_boat = icon_lower in ('torpedoboat', 'boat')
        
        self.tank_respawn = icon_lower in ('respawn_base_tank', 'spawn_tank')
        self.bomber_respawn = icon_lower in ('respawn_base_bomber', 'spawn_bomber')
        self.fighter_respawn = icon_lower in ('respawn_base_fighter', 'spawn_fighter')
        
        self.capture_zone = type_lower in ('capture_zone', 'zone') or icon_lower == 'capture_zone'
        self.defend_point = type_lower == 'defending_point' or icon_lower == 'defending_point'
        if self.defend_point:
            self.friendly = True
        
        try:
            self.position = [map_obj_entry['x'], map_obj_entry['y']]
        except KeyError:
            self.position = [0.0, 0.0]
        
        try:
            self.position_delta = [map_obj_entry['dx'], map_obj_entry['dy']]
            self.hdg = degrees(atan2(*self.position_delta)) + 90
            if self.hdg < 0:
                self.hdg += 360
        except KeyError:
            self.position_delta = [0.0, 0.0]
            self.hdg = 0.0
        
        try:
            self.south_end = [map_obj_entry['sx'], map_obj_entry['sy']]
            self.east_end  = [map_obj_entry['ex'], map_obj_entry['ey']]
            
            self.south_end_ned = self._convert_to_ned(*self.south_end, map_info_meta)
            self.east_end_ned  = self._convert_to_ned(*self.east_end, map_info_meta)
            
            d_north = self.east_end_ned[0] - self.south_end_ned[0]
            d_east  = self.east_end_ned[1] - self.south_end_ned[1]
            self.runway_dir = (degrees(atan2(d_east, d_north)) + 360) % 360
        except KeyError:
            self.south_end = [0.0, 0.0]
            self.east_end  = [0.0, 0.0]
            self.south_end_ned = [0.0, 0.0]
            self.east_end_ned  = [0.0, 0.0]
            self.runway_dir = 0.0
        
        self.position_ned = self._convert_to_ned(*self.position, map_info_meta)
        
        self.position_ll = self.position_ned
        self.south_end_ll = self.south_end_ned
        self.east_end_ll = self.east_end_ned


class MapInfo(object):
    def __init__(self):
        self.map_valid = False
        self.map_objs  = []
        self.info      = {}
        self.obj       = []
        self.grid_info = {}
        
        self.player_ned_n = 0.0
        self.player_ned_e = 0.0
        self.player_lat   = 0.0
        self.player_lon   = 0.0
    
    def download_files(self) -> bool:
        self.map_valid = False
        
        try:
            urlretrieve(URL_MAP_IMG, MAP_PATH)
            self.info = get(URL_MAP_INFO, timeout=REQUEST_TIMEOUT).json()
            self.obj  = get(URL_MAP_OBJ,  timeout=REQUEST_TIMEOUT).json()
            
            self.grid_info = {
                'name': self.info.get('map_generation', 'DynamicMap'),
                'map_min': self.info.get('map_min'),
                'map_max': self.info.get('map_max'),
                'grid_size': self.info.get('grid_size'),
                'grid_steps': self.info.get('grid_steps'),
                'grid_zero': self.info.get('grid_zero'),
                'size_km': (self.info.get('map_max', [65536, 65536])[0] - self.info.get('map_min', [-65536, -65536])[0]) / 1000.0
            }
            
            self.map_valid = True
            self.parse_meta()
            
            with Image.open(MAP_PATH) as img:
                self.map_img = img.copy()
            self.map_draw = ImageDraw.Draw(self.map_img)
                
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
        self.map_objs = []
        self.player_found = False
        
        if self.map_valid and self.obj:
            for obj in self.obj:
                self.map_objs.append(map_obj(obj, self.info))
                
                if obj.get('icon') == 'Player':
                    self.player_found = True
                    self.player_ned_n = self.map_objs[-1].position_ned[0]
                    self.player_ned_e = self.map_objs[-1].position_ned[1]
                    self.player_lat   = self.player_ned_n
                    self.player_lon   = self.player_ned_e
    
    def airfields(self) -> list:
        return [obj for obj in self.map_objs if obj.airfield]
    
    def bombing_points(self) -> list:
        return [obj for obj in self.map_objs if obj.bombing_point]
    
    def heavy_tanks(self) -> list:
        return [obj for obj in self.map_objs if obj.heavy_tank]
    
    def medium_tanks(self) -> list:
        return [obj for obj in self.map_objs if obj.medium_tank]
    
    def light_tanks(self) -> list:
        return [obj for obj in self.map_objs if obj.light_tank]
    
    def SPGs(self) -> list:
        return [obj for obj in self.map_objs if obj.spg]
    
    def SPAAs(self) -> list:
        return [obj for obj in self.map_objs if obj.spaa]
    
    def tanks(self) -> list:
        output = []
        output.extend(self.heavy_tanks())
        output.extend(self.medium_tanks())
        output.extend(self.light_tanks())
        output.extend(self.SPGs())
        output.extend(self.SPAAs())
        return output
    
    def wheeled_AIs(self) -> list:
        return [obj for obj in self.map_objs if obj.wheeled]
    
    def tracked_AIs(self) -> list:
        return [obj for obj in self.map_objs if obj.tracked]
    
    def AAAs(self) -> list:
        return [obj for obj in self.map_objs if obj.aaa]
    
    def bombers(self) -> list:
        return [obj for obj in self.map_objs if obj.bomber]
    
    def heavy_fighters(self) -> list:
        return [obj for obj in self.map_objs if obj.heavy_fighter]
    
    def fighters(self) -> list:
        return [obj for obj in self.map_objs if obj.fighter]
    
    def ships(self) -> list:
        return [obj for obj in self.map_objs if obj.ship or obj.torpedo_boat]
    
    def planes(self) -> list:
        output = []
        output.extend(self.bombers())
        output.extend(self.heavy_fighters())
        output.extend(self.fighters())
        return output
    
    def tank_respawns(self) -> list:
        return [obj for obj in self.map_objs if obj.tank_respawn]
    
    def bomber_respawns(self) -> list:
        return [obj for obj in self.map_objs if obj.bomber_respawn]
    
    def fighter_respawns(self) -> list:
        return [obj for obj in self.map_objs if obj.fighter_respawn]
    
    def plane_respawns(self) -> list:
        output = []
        output.extend(self.bomber_respawns())
        output.extend(self.fighter_respawns())
        return output
    
    def capture_zones(self) -> list:
        return [obj for obj in self.map_objs if obj.capture_zone]
    
    def defend_points(self) -> list:
        return [obj for obj in self.map_objs if obj.defend_point]