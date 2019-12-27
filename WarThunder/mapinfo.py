import os
import json
import imagehash
import socket
import urllib.request
from PIL import Image, ImageDraw
from requests import get
from requests.exceptions import ReadTimeout, ConnectTimeout
from math import radians, degrees, sqrt, sin, asin, cos, atan2
from WarThunder.maps import maps


DEBUG = False

IP_ADDRESS   = socket.gethostbyname(socket.gethostname())
URL_MAP_IMG  = 'http://{}:8111/map.img'.format(IP_ADDRESS)
URL_MAP_OBJ  = 'http://{}:8111/map_obj.json'.format(IP_ADDRESS)
URL_MAP_INFO = 'http://{}:8111/map_info.json'.format(IP_ADDRESS)

AIR_DIMENSION_KM = 65 # all air maps are 65kmx65km
TEXTURES_PATH    = os.environ['APPDATA'] + r'\Tacview\Data\Terrain\Textures'
EARTH_RADIUS_KM  = 6378.137
REQUEST_TIMEOUT  = 0.1


def hypotenuse(a, b):
    return sqrt((a ** 2) + (b ** 2))

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
    
    return (degrees(lat_2), degrees(lon_2))

def get_grid_info(map_img):
    '''
    Description:
    ------------
    Compare map from browser interface to pre-calculated map hash to provide
    location info: Note that map_img must be a PIL.Image object
    '''
    
    hash_ = str(imagehash.average_hash(map_img))
    
    if hash_ in maps.keys():
        return maps[hash_]
    
    return {'name': 'UNKNOWN',
            'ULHC_lat': 0.0,
            'ULHC_lon': 0.0}


class MapInfo(object):
    def __init__(self):
        self.map_valid = False
    
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
            urllib.request.urlretrieve(URL_MAP_IMG, 'map.jpg')
            self.info = get(URL_MAP_INFO, timeout=REQUEST_TIMEOUT).json()
            self.obj  = get(URL_MAP_OBJ,  timeout=REQUEST_TIMEOUT).json()
            
            self.map_img  = Image.open('map.jpg')
            self.map_draw = ImageDraw.Draw(self.map_img)
            
            self.grid_info = get_grid_info(self.map_img)
            
            self.map_valid = True
    
        except urllib.error.URLError:
            print('ERROR: could not download map.jpg')
    
        except json.decoder.JSONDecodeError:
            print('Waiting to join a match')
            
        except ReadTimeout:
            print('ERROR: ReadTimeout')
            
        except ConnectTimeout:
            print('ERROR: ConnectTimeout')
        
        except FileNotFoundError:
            print('ERROR: map.jpg not found')
            
        return self.map_valid
    
    def parse_meta(self):
        '''
        Description:
        ------------
        Calculate values that might be useful for extra processing
        '''
        
        self.player_found = False
        
        if self.map_valid:
            for obj in self.obj:
                if obj['icon'] == 'Player':
                    self.player_found = True
                    
                    self.player_x = obj['x']
                    self.player_y = obj['y']
                    
                    try:
                        self.player_dx = obj['dx']
                        self.player_dy = obj['dy']
                    except KeyError:
                        self.player_dx = 0
                        self.player_dy = 0
                    
                    self.player_hdg = degrees(atan2(self.player_dy,
                                                    self.player_dx)) + 90
                    if self.player_hdg < 0:
                        self.player_hdg += 360
                    
                    if self.grid_info:
                        dist_x  = self.player_x * AIR_DIMENSION_KM
                        dist_y  = self.player_y * AIR_DIMENSION_KM
                        dist    = hypotenuse(dist_x, dist_y)
                        bearing = degrees(atan2(self.player_y,
                                                self.player_x)) + 90
                        if bearing < 0:
                            bearing += 360
                        
                        (self.player_lat, self.player_lon) = coord_coord(self.grid_info['ULHC_lat'],
                                                                         self.grid_info['ULHC_lon'],
                                                                         dist,
                                                                         bearing)
                        
    
    

