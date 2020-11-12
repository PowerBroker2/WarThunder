import os
import socket
import imagehash
from requests import get
from PIL import Image, ImageDraw
from json.decoder import JSONDecodeError
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


def hypotenuse(a, b):
    return sqrt((a ** 2) + (b ** 2))

def coord_bearing(lat_1, lon_1, lat_2, lon_2):
    '''
    Description:
    ------------
    Find the bearing (in degrees) between two lat/lon coordinates (dd)
    '''
    
    deltaLon_r = radians(lon_2 - lon_1)
    lat_1_r = radians(lat_1)
    lat_2_r = radians(lat_2)

    x = cos(lat_2_r) * sin(deltaLon_r)
    y = cos(lat_1_r) * sin(lat_2_r) - sin(lat_1_r) * cos(lat_2_r) * cos(deltaLon_r)

    return (degrees(atan2(x, y)) + 360) % 360

def coord_dist(lat_1, lon_1, lat_2, lon_2):
    '''
    Description:
    ------------
    Find the total distance (in km) between two lat/lon coordinates (dd)
    '''
    
    lat_1_rad = radians(lat_1)
    lon_1_rad = radians(lon_1)
    lat_2_rad = radians(lat_2)
    lon_2_rad = radians(lon_2)
    
    d_lat = lat_2_rad - lat_1_rad
    d_lon = lon_2_rad - lon_1_rad
    
    a = (sin(d_lat / 2) ** 2) + cos(lat_1_rad) * cos(lat_2_rad) * (sin(d_lon / 2) ** 2)
    
    return 2 * EARTH_RADIUS_KM * atan2(sqrt(a), sqrt(1 - a))

def coord_coord(lat, lon, dist, bearing):
    '''
    Description:
    ------------
    Finds the lat/lon coordinates "dist" km away from the given "lat" and "lon"
    coordinate along the given compass "bearing"
    '''
    
    brng  = radians(bearing)
    lat_1 = radians(lat)
    lon_1 = radians(lon)
    
    lat_2 = asin(sin(lat_1) * cos(dist / EARTH_RADIUS_KM) + cos(lat_1) * sin(dist / EARTH_RADIUS_KM) * cos(brng))
    lon_2 = lon_1 + atan2(sin(brng) * sin(dist / EARTH_RADIUS_KM) * cos(lat_1), cos(dist / EARTH_RADIUS_KM) - sin(lat_1) * sin(lat_2))
    
    return [degrees(lat_2), degrees(lon_2)]

def get_grid_info(map_img):
    '''
    Description:
    ------------
    Compare map from browser interface to pre-calculated map hash to provide
    location info: Note that map_img must be a PIL.Image object
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

def find_obj_coords(x, y, map_size, ULHC_lat, ULHC_lon):
    '''
    Description:
    ------------
    Convert the provided x/y coordinate to lat/lon
    '''
    
    dist_x  = x * map_size
    dist_y  = y * map_size
    dist    = hypotenuse(dist_x, dist_y)
    bearing = degrees(atan2(y, x)) + 90
    
    if bearing < 0:
        bearing += 360
    
    return coord_coord(ULHC_lat, ULHC_lon, dist, bearing)


class map_obj(object):
    def __init__(self, map_obj_entry=None, map_size=None, ULHC_lat=None, ULHC_lon=None):
        self.type      = ''
        self.icon      = ''
        self.hex_color = ''
        self.friendly  = True
        
        self.position       = [0, 0] # NOT for airfield
        self.position_delta = [0, 0] # ONLY for planes (maybe ground vehicles while on the move?)
        self.south_end      = [0, 0] # ONLY for airfield
        self.east_end       = [0, 0] # ONLY for airfield
        
        self.position_ll  = [0, 0] # NOT for airfield
        self.south_end_ll = [0, 0] # ONLY for airfield
        self.east_end_ll  = [0, 0] # ONLY for airfield
        self.runway_dir   = 0 # ONLY for airfield
        
        self.hdg = 0 # ONLY for planes (maybe ground vehicles while on the move?)
        
        if map_obj_entry:
            self.update(map_obj_entry, map_size, ULHC_lat, ULHC_lon)
    
    def update(self, map_obj_entry, map_size, ULHC_lat, ULHC_lon):
        '''
        Description:
        ------------
        Update object attributes based on the provided context
        '''
        
        self.type = map_obj_entry['type']
        self.icon = map_obj_entry['icon']
        self.hex_color = map_obj_entry['color']
        
        if self.hex_color in ENEMY_HEX_COLORS:
            self.friendly = False
        else:
            self.friendly = True
        
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
        self.map_objs = []
    
    def download_files(self):
        '''
        Description:
        ------------
        Sample information about the map and the "seen" objects in the match
        from the localhost
        
        Example self.info:
        ------------------
        {'grid_steps': [8192.0, 8192.0],
         'grid_zero': [-28672.0, 28672.0],
         'map_generation': 12,
         'map_max': [32768.0, 32768.0],
         'map_min': [-32768.0, -32768.0]}
        
        Example self.obj:
        -----------------
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
        '''
        
        self.map_valid = False
        
        try:
            urlretrieve(URL_MAP_IMG, MAP_PATH)
            self.info = get(URL_MAP_INFO, timeout=REQUEST_TIMEOUT).json()
            self.obj  = get(URL_MAP_OBJ,  timeout=REQUEST_TIMEOUT).json()
            
            self.map_img  = Image.open(MAP_PATH)
            self.map_draw = ImageDraw.Draw(self.map_img)
            
            self.grid_info = get_grid_info(self.map_img)
            
            self.map_valid = True
    
        except URLError:
            print('ERROR: could not download map.jpg')
    
        except (OSError, JSONDecodeError):
            print('Waiting to join a match')
            
        except ReadTimeout:
            print('ERROR: ReadTimeout')
            
        except ConnectTimeout:
            print('ERROR: ConnectTimeout')
            
        return self.map_valid
    
    def parse_meta(self):
        '''
        Description:
        ------------
        Calculate values that might be useful for extra processing
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
    
    

