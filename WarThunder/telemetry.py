'''
Module to query and access telemetry data during War Thunder matches
'''

import socket
import requests
from requests.exceptions import ConnectionError
from WarThunder import mapinfo


IP_ADDRESS     = '127.0.0.1'
URL_INDICATORS = 'http://{}:8111/indicators'.format(IP_ADDRESS)
URL_STATE      = 'http://{}:8111/state'.format(IP_ADDRESS)
URL_COMMENTS   = 'http://{}:8111/gamechat?lastId={}'
URL_EVENTS     = 'http://{}:8111/hudmsg?lastEvt=-1&lastDmg=-1'
FT_TO_M        = 0.3048
IN_FLIGHT      = 0
IN_MENU        = -1
NO_MISSION     = -2
WT_NOT_RUNNING = -3
OTHER_ERROR    = -4


def clean_text(text: str) -> str:
    '''
    Clean up bad unicode characters like non-breaking spaces (\xa0) from game strings
    '''
    if isinstance(text, str):
        return text.replace('\xa0', ' ').strip()
    return text


def combine_dicts(to_dict: dict, from_dict: dict) -> dict:
    '''
    Merges all contents of "from_dict" into "to_dict"
    
    Args:
        to_dict:
            One dictionary to be merged
        from_dict:
            Other dictionary to be merged
    
    Returns:
            Dictionary with the merged contents of the original to_dict and
            from_dict
    '''
    if isinstance(to_dict, dict) and isinstance(from_dict, dict):
        for key in from_dict.keys():
            to_dict[key] = from_dict[key]
        return to_dict
    else:
        return {}


class TelemInterface(object):
    def __init__(self):
        self.connected       = False
        self.full_telemetry  = {}
        self.basic_telemetry = {}
        self.indicators      = {}
        self.state           = {}
        self.map_info        = mapinfo.MapInfo()
        self.last_event_ID   = -1
        self.last_comment_ID = -1
        self.comments        = []
        self.events          = {'damage': [], 'events': []}
        self.status          = WT_NOT_RUNNING
        
        # High-level processed telemetry properties
        self.airframe  = ''
        self.altitude  = 0.0
        self.ias       = 0.0
        self.tas       = 0.0
        self.heading   = 0.0
        self.pitch     = 0.0
        self.roll      = 0.0
        self.lat       = 0.0
        self.lon       = 0.0
        self.flaps_pct = 0.0
        self.gear_pct  = 0.0
    
    def get_comments(self) -> list:
        '''
        Query http://localhost:8111/gamechat?lastId=-1 to get a list of all
        comments (in JSON format) made in the current match
        
        Returns:
                List of comments
        '''
        try:
            comments_response = requests.get(
                URL_COMMENTS.format(IP_ADDRESS, self.last_comment_ID),
                timeout=mapinfo.REQUEST_TIMEOUT
            )
            new_comments = comments_response.json()
            for comment in new_comments:
                if isinstance(comment, dict):
                    for k, v in comment.items():
                        if isinstance(v, str):
                            comment[k] = clean_text(v)
            self.comments.extend(new_comments)
            if self.comments:
                self.last_comment_ID = max([comment['id'] for comment in self.comments if isinstance(comment, dict) and 'id' in comment], default=self.last_comment_ID)
        except Exception:
            pass
        return self.comments
    
    def get_events(self) -> dict:
        '''
        Query http://localhost:8111/hudmsg?lastEvt=-1&lastDmg=-1 to get
        information on all events (i.e. when someone is damaged or destroyed)
        in the current match and accumulate them safely without overwriting.
        
        Returns:
                Events log dictionary containing accumulated damage and event lists
        '''
        try:
            events_response = requests.get(
                URL_EVENTS.format(IP_ADDRESS),
                timeout=mapinfo.REQUEST_TIMEOUT
            )
            data = events_response.json()
            
            if isinstance(data, dict):
                if not self.events:
                    self.events = {'damage': [], 'events': []}
                
                # Merge damage messages without duplicates and clean strings
                existing_damage_ids = {item.get('id') for item in self.events.get('damage', []) if isinstance(item, dict)}
                for item in data.get('damage', []):
                    if isinstance(item, dict):
                        for k, v in item.items():
                            if isinstance(v, str):
                                item[k] = clean_text(v)
                        if item.get('id') not in existing_damage_ids:
                            self.events.setdefault('damage', []).append(item)
                
                # Merge general HUD event messages without duplicates and clean strings
                existing_event_ids = {item.get('id') for item in self.events.get('events', []) if isinstance(item, dict)}
                for item in data.get('events', []):
                    if isinstance(item, dict):
                        for k, v in item.items():
                            if isinstance(v, str):
                                item[k] = clean_text(v)
                        if item.get('id') not in existing_event_ids:
                            self.events.setdefault('events', []).append(item)
                        
        except Exception:
            pass
            
        return self.events
    
    def find_altitude(self) -> float:
        '''
        Finds and standardizes reported altitude to meters from state data,
        falling back to indicator fields if state altitude is unavailable.
        
        Returns:
                Altitude in meters
        '''
        if 'H, m' in self.state:
            return float(self.state['H, m'])
        
        for alt_key in ('altitude_hour', 'altitude_min', 'altitude_10k'):
            if alt_key in self.indicators:
                return float(self.indicators[alt_key])
                
        return 0.0

    def get_telemetry(self, comments: bool = False, events: bool = False) -> bool:
        '''
        Ping http://localhost:8111/indicators and http://localhost:8111/state
        to sample telemetry data.
        
        Args:
            comments:
                Whether or not to query for match comment data
            events:
                Whether or not to query for match event data
        
        Returns:
                Whether or not player is in a match
        '''
        self.connected       = False
        self.full_telemetry  = {}
        self.basic_telemetry = {}

        try:
            self.map_info.download_files()
            self.map_info.parse_meta()
            
            indicator_response = requests.get(URL_INDICATORS, timeout=mapinfo.REQUEST_TIMEOUT)
            self.indicators    = indicator_response.json()

            state_response = requests.get(URL_STATE, timeout=mapinfo.REQUEST_TIMEOUT)
            self.state     = state_response.json()
            
            if comments:
                self.get_comments()
            else:
                self.comments = []
            
            if events:
                self.get_events()
            else:
                self.events = {'damage': [], 'events': []}

            if self.indicators.get('valid') and self.state.get('valid'):
                try:
                    self.airframe = clean_text(self.indicators.get('type', ''))
                    self.altitude = self.find_altitude()
                    
                    self.ias = float(self.state.get('IAS, km/h', 0.0))
                    self.tas = float(self.state.get('TAS, km/h', 0.0))
                    
                    self.pitch = float(-self.indicators.get('aviahorizon_pitch', 0.0))
                    self.roll  = float(-self.indicators.get('aviahorizon_roll', 0.0))
                    self.heading = float(
                        self.indicators.get('compass1',
                        self.indicators.get('compass', 0.0))
                    )
                    
                    self.lat = getattr(self.map_info, 'player_lat', 0.0)
                    self.lon = getattr(self.map_info, 'player_lon', 0.0)
                    
                    self.flaps_pct = float(self.state.get('flaps, %', 0.0))
                    self.gear_pct  = float(self.state.get('gear, %', 0.0))
                    
                    self.basic_telemetry = {
                        'airframe':  self.airframe,
                        'altitude':  self.altitude,
                        'IAS':       self.ias,
                        'TAS':       self.tas,
                        'heading':   self.heading,
                        'pitch':     self.pitch,
                        'roll':      self.roll,
                        'lat':       self.lat,
                        'lon':       self.lon,
                        'flapState': self.flaps_pct,
                        'gearState': self.gear_pct
                    }
                    
                    self.full_telemetry = combine_dicts({}, self.indicators)
                    self.full_telemetry = combine_dicts(self.full_telemetry, self.state)
                    self.full_telemetry['lat'] = self.lat
                    self.full_telemetry['lon'] = self.lon
                    self.full_telemetry['alt_m'] = self.altitude
                    
                    self.connected = True
                    self.status    = IN_FLIGHT
                    
                except (KeyError, AttributeError, ValueError):
                    self.status = IN_MENU
            else:
                self.status = NO_MISSION

        except ConnectionError:
            self.status = WT_NOT_RUNNING
        except Exception as e:
            if isinstance(e, (socket.error, requests.exceptions.Timeout)):
                self.status = WT_NOT_RUNNING
            else:
                import traceback
                traceback.print_exc()
                self.status = OTHER_ERROR
        
        return self.connected