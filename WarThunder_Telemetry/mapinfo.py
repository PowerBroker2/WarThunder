import os
import json
import imagehash
import socket
import urllib.request
from PIL import Image, ImageDraw
from requests import get
from requests.exceptions import ReadTimeout, ConnectTimeout
from math import radians, sqrt, sin, cos, atan2
from maphash import maps


DEBUG = False

IP_ADDRESS   = socket.gethostbyname(socket.gethostname())
URL_MAP_IMG  = 'http://{}:8111/map.img'.format(IP_ADDRESS)
URL_MAP_OBJ  = 'http://{}:8111/map_obj.json'.format(IP_ADDRESS)
URL_MAP_INFO = 'http://{}:8111/map_info.json'.format(IP_ADDRESS)

TEXTURES_PATH   = os.environ['APPDATA'] + r'\Tacview\Data\Terrain\Textures'
EARTH_RADIUS    = 6378137 # meters
REQUEST_TIMEOUT = 0.1


def hypotenuse(a, b):
    return sqrt((a ** 2) + (b ** 2))

def distance(x1, y1, x2, y2):
    '''
    Description:
    ------------
    Find the distance between two points on a cartesian plane
    '''
    
    return sqrt(((y2 - y1) ** 2) + ((x2 - x1) ** 2))

def coord_dist(lat_1, lon_1, lat_2, lon_2):
    '''
    Description:
    ------------
    Find the total distance (in meters) between two lat/lon coordinates (dd)
    '''
    
    lat_1_rad = radians(lat_1)
    lon_1_rad = radians(lon_1)
    lat_2_rad = radians(lat_2)
    lon_2_rad = radians(lon_2)
    
    d_lat = lat_2_rad - lat_1_rad
    d_lon = lon_2_rad - lon_1_rad
    
    a = (sin(d_lat / 2) ** 2) + cos(lat_1_rad) * cos(lat_2_rad) * (sin(d_lon / 2) ** 2)
    
    return 2 * EARTH_RADIUS * atan2(sqrt(a), sqrt(1 - a))

def map_name(map_img):
    '''
    Description:
    ------------
    Compare map from browser interface to pre-calculated map hash to provide
    location info: Note that map_img must be a PIL.Image object
    '''
    
    hash_ = str(imagehash.average_hash(map_img))
    
    if hash_ in maps.keys():
        return maps[hash_]
    
    print('ERROR: No map found with hash {}'.format(hash_))
    return None

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
            self.map_name = map_name(self.map_img)
            
            self.map_valid = True
    
        except json.decoder.JSONDecodeError:
            print('ERROR; Waiting to join a match')
            
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
        
        self.map_total   = self.info['map_max'][0] - self.info['map_min'][0]
        self.map_total_x = self.info['map_max'][0] - self.info['map_min'][0]
        self.map_total_y = self.info['map_max'][1] - self.info['map_min'][1]
        
        self.step_qnty   = self.map_total / self.info['grid_steps'][0]
        self.step_size   = self.map_img.width / self.step_qnty
        self.step_offset = self.info['map_min'][0] - self.info['grid_zero'][0]
        
        if self.step_size == self.info['map_max'][0]:
            # TODO: document this, it was a hack fix for the odd maps that cause scale problems
            '''assuming duel map until found to be other'''
            self.step_offset = 0
            self.step_size   = 256
    
    

