'''
Python3 module/script to query and access telemetry data during War Thunder "Air Battles" matches

NOTE: THIS DOES NOT WORK WITH TANK OR SHIP BATTLES

Example basic_telemetry dict:
    {'IAS': 2,
     'airframe': 'p-51d-5',
     'altitude': -475.12204,
     'flapState': 0,
     'gearState': 0,
     'heading': 98.789597,
     'pitch': 81.356125,
     'roll': 27.817101}

Example full_telemetry dict:
    {'AoA, deg': 26.5,
     'AoS, deg': 38.8,
     'H, m': -59,
     'IAS, km/h': 2,
     'M': 0.0,
     'Mfuel, kg': 2,
     'Mfuel0, kg': 734,
     'Ny': 4.25,
     'RPM 1': 0,
     'RPM throttle 1, %': 0,
     'TAS, km/h': 1,
     'Vy, m/s': -0.3,
     'Wx, deg/s': 2,
     'aileron, %': 0,
     'altitude_10k': -193.246521,
     'altitude_hour': -193.246521,
     'altitude_min': -193.246521,
     'aviahorizon_pitch': 67.419807,
     'aviahorizon_roll': 9.448232,
     'bank': -8.0,
     'carb_temperature': 0.0,
     'clock_hour': 8.3,
     'clock_min': 18.0,
     'clock_sec': 47.0,
     'compass': 89.343414,
     'compass1': 89.343414,
     'efficiency 1, %': 0,
     'elevator, %': 0,
     'flaps': 0.0,
     'flaps, %': 0,
     'fuel1': 1.9,
     'fuel2': 0.0,
     'fuel_pressure': 0.0,
     'gear, %': 0,
     'gears': 0.0,
     'gears_lamp': 1.0,
     'magneto 1': 0,
     'manifold pressure 1, atm': 1.01,
     'manifold_pressure': 1.007005,
     'mixture': 0.833333,
     'oil temp 1, C': 66,
     'oil_pressure': 65.620697,
     'oil_temperature': 65.620697,
     'pedals1': 0.0,
     'pedals2': 0.0,
     'pedals3': 0.0,
     'pedals4': 0.0,
     'pitch 1, deg': 65.0,
     'power 1, hp': 0.0,
     'prop_pitch': 0.0,
     'radiator 1, %': 0,
     'rpm': 0.0,
     'rudder, %': 0,
     'speed': 0.309342,
     'stick_ailerons': 0.0,
     'stick_elevator': -1.0,
     'throttle': 0.0,
     'throttle 1, %': 0,
     'thrust 1, kgs': 0,
     'turn': 0.061294,
     'type': 'p-51d-5',
     'valid': True,
     'vario': -0.325393,
     'water temp 1, C': 92,
     'water_temperature': 92.17804,
     'weapon1': 0.0}
'''


import socket
import requests
from WarThunder import mapinfo


IP_ADDRESS     = socket.gethostbyname(socket.gethostname())
URL_INDICATORS = 'http://{}:8111/indicators'.format(IP_ADDRESS)
URL_STATE      = 'http://{}:8111/state'.format(IP_ADDRESS)
URL_COMMENTS   = 'http://{}:8111/gamechat?lastId=-1'.format(IP_ADDRESS)
URL_EVENTS     = 'http://{}:8111/hudmsg?lastEvt=0&lastDmg=0'.format(IP_ADDRESS)
FT_TO_M        = 0.3048


def combine_dicts(to_dict, from_dict):
    '''
    Description:
    ------------
    Merges all contents of "from_dict" into "to_dict"
    '''
    
    if (type(to_dict) == dict) and (type(from_dict) == dict):
        for key in from_dict.keys():
            to_dict[key] = from_dict[key]

        return to_dict
    else:
        return False


class TelemInterface(object):
    def __init__(self):
        self.connected       = False
        self.full_telemetry  = {}
        self.basic_telemetry = {}
        self.indicators      = {}
        self.state           = {}
        self.map_info        = mapinfo.MapInfo()
    
    def get_comments(self):
        '''
        Description:
        ------------
        Query http://localhost:8111/gamechat?lastId=-1 to get a JSON of all
        comments made in the current match
        '''
        
        comments_response = requests.get(URL_COMMENTS)
        self.comments     = comments_response.json()
        return self.comments
    
    def get_events(self):
        '''
        Description:
        ------------
        Query http://localhost:8111/gamechat?lastId=-1 to get a JSON of all
        events (i.e. when someone is damaged or destroyed) in the current match
        '''
        
        events_response = requests.get(URL_EVENTS)
        self.events     = events_response.json()
        return self.events
    
    def find_altitude(self):
        '''
        Description:
        ------------
        Finds and standardizes reported alittude to meters for all planes
        '''
        
        name = self.indicators['type']
        
        # account for freedom units in US planes
        if name.startswith('p-') or name.startswith('f-') or \
           name.startswith('f2') or name.startswith('f3') or \
           name.startswith('f4') or name.startswith('f6') or \
           name.startswith('f7') or name.startswith('f8') or \
           name.startswith('f9') or name.startswith('os') or \
           name.startswith('sb') or name.startswith('tb') or \
           name.startswith('a-') or name.startswith('pb') or \
           name.startswith('am') or name.startswith('ad') or \
           name.startswith('fj') or name.startswith('b-') or \
           name.startswith('xp') or name.startswith('bt') or \
           name.startswith('xa') or name.startswith('xf'):
            if 'altitude_10k' in self.indicators.keys():
                return self.indicators['altitude_10k'] * FT_TO_M
            elif 'altitude_hour' in self.indicators.keys():
                return self.indicators['altitude_hour'] * FT_TO_M
            elif 'altitude_min' in self.indicators.keys():
                return self.indicators['altitude_min'] * FT_TO_M
            else:
                return 0
        else:
            if 'altitude_10k' in self.indicators.keys():
                return self.indicators['altitude_10k']
            elif 'altitude_hour' in self.indicators.keys():
                return self.indicators['altitude_hour']
            elif 'altitude_min' in self.indicators.keys():
                return self.indicators['altitude_min']
            else:
                return 0

    def get_telemetry(self, comments=False, events=False):
        '''
        Description:
        ------------
        Ping http://localhost:8111/indicators and http://localhost:8111/state
        to sample telemetry data. Each one of the URL requests returns a
        respective JSON string. These two JSON strings are converted into
        dictionaries (self.indicators and self.state). From these dictionaries,
        two more dictionaries are created: self.full_telemetry and
        self.basic_telemetry.
        
        Dictionary self.full_telemetry holds a combination of all telemetry
        values returned from http://localhost:8111/indicators and
        http://localhost:8111/state. Dictionary self.basic_telemetry holds
        the minimal amount of telmetry needed for navigation and control (see
        file docstring for more info)
        
        :param comments: bool - whether or not to query for match comment data
        :param events:   bool - whether or not to query for match event data
        
        :return self.connected: bool - whehter or not player is in a match and
                                       flying
        '''
        
        self.connected       = False
        self.full_telemetry  = {}
        self.basic_telemetry = {}

        try:
            self.map_info.download_files()
            self.map_info.parse_meta()
            
            indicator_response = requests.get(URL_INDICATORS)
            self.indicators    = indicator_response.json()

            state_response = requests.get(URL_STATE)
            self.state     = state_response.json()
            
            if comments:
                self.get_comments()
            else:
                self.comments = None
            
            if events:
                self.get_events()
            else:
                self.events = None

            if self.indicators['valid'] and self.state['valid']:
                try:
                    # fix odd WT sign conventions
                    try:
                        self.indicators['aviahorizon_pitch'] = -self.indicators['aviahorizon_pitch']
                    except KeyError:
                        self.indicators['aviahorizon_pitch'] = 0
                    
                    try:
                        self.indicators['aviahorizon_roll']  = -self.indicators['aviahorizon_roll']
                    except KeyError:
                        self.indicators['aviahorizon_roll']  = 0
                    
                    self.indicators['alt_m'] = self.find_altitude()
                    
                    self.full_telemetry = combine_dicts(self.full_telemetry, self.indicators)
                    self.full_telemetry = combine_dicts(self.full_telemetry, self.state)
                    
                    self.basic_telemetry['airframe'] = self.indicators['type']
                    self.basic_telemetry['roll']     = self.indicators['aviahorizon_roll']
                    self.basic_telemetry['pitch']    = self.indicators['aviahorizon_pitch']
                    self.basic_telemetry['heading']  = self.indicators['compass']
                    self.basic_telemetry['altitude'] = self.indicators['alt_m']
                
                    try:
                        self.basic_telemetry['lat'] = self.map_info.player_lat
                        self.full_telemetry['lat']  = self.map_info.player_lat
                        self.basic_telemetry['lon'] = self.map_info.player_lon
                        self.full_telemetry['lon']  = self.map_info.player_lon
                    except AttributeError:
                        self.basic_telemetry['lat'] = None
                        self.full_telemetry['lat']  = None
                        self.basic_telemetry['lon'] = None
                        self.full_telemetry['lon']  = None
                    
                    try: 
                        self.basic_telemetry['IAS'] = self.state['TAS, km/h']
                    except KeyError:
                        self.basic_telemetry['IAS'] = None
                    
                    try: 
                        self.basic_telemetry['flapState'] = self.state['flaps, %']
                    except KeyError:
                        self.basic_telemetry['flapState'] = None
                    
                    try: 
                        self.basic_telemetry['gearState'] = self.state['gear, %']
                    except KeyError:
                        self.basic_telemetry['gearState'] = None
                    
                    self.connected = True
                    
                except KeyError:
                    print('In mission menu...')
            else:
                print('Mission not currently running...')

        except Exception as e:
            if 'Failed to establish a new connection' in str(e):
                print('War Thunder not running...')
            else:
                import traceback
                traceback.print_exc()
        
        return self.connected



