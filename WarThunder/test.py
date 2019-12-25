import pprint
import general, telemetry, acmi
from telemetry import combine_dicts
from getpass import getuser
import datetime as dt


TITLE_FORMAT = '{timestamp}_{user}.acmi'
ACMI_HEADER  = {'DataSource': '',
                'DataRecorder': '',
                'Author': '',
                'Title': '',
                'Comments': '',
                'ReferenceLongitude': 0,
                'ReferenceLatitude':  0}
ACMI_ENTRY   = {'T': '',
                'Throttle': 0,
                'RollControlInput': 0,
                'PitchControlInput': 0,
                'YawControlInput': 0,
                'IAS': 0,
                'TAS': 0,
                'FuelWeight': 0,
                'FuelVolume': 0,
                'Mach': 0,
                'AOA': 0,
                'LandingGear': 0,
                'Flaps': 0}
INITIAL_META = {'Slot': 0,
                'Importance': 1,
                'Parachute': 0,
                'DragChute': 0,
                'Disabled': 0,
                'Pilot': 0,
                'Name': '',
                'Type': '',
                'Color': None,
                'Callsign': None,
                'Coalition': None}


def format_header(grid_info, loc_time):
    '''
    Description:
    ------------
    Create a dictionary of formatted telemetry samples to be logged in the
    ACMI log
    
    :param grid_info: dict     - map location metadata
    :param loc_time:  datetime - local date/time at the time of ACMI log creation
    
    :return formatted_header: dict - all additional fields and values desired
                                     in the ACMI log header
    '''
    
    formatted_header = ACMI_HEADER
    
    formatted_header['DataSource']         = 'War Thunder v{}'.format(general.get_version())
    formatted_header['DataRecorder']       = 'Flight Viewer'
    formatted_header['Author']             = getuser()
    formatted_header['Title']              = grid_info['name']
    formatted_header['Comments']           = 'Local: {}'.format(loc_time.strftime('%Y-%m-%d %H:%M:%S'))
    formatted_header['ReferenceLatitude']  = grid_info['ULHC_lat']
    formatted_header['ReferenceLongitude'] = grid_info['ULHC_lon']
    
    return formatted_header

def format_entry(telem, initial_entry=False):
    '''
    Description:
    ------------
    Create a dictionary of formatted telemetry samples to be logged in the
    ACMI log
    
    :param telem: dict - full War Thunder vehicle telemetry data
    
    :return formatted_entry: dict - all fields and values necessary for a new
                                    entry in the ACMI log
    '''
    
    formatted_entry = ACMI_ENTRY
    
    formatted_entry['T'] = ('{lon:0.9f}|'
                            '{lat:0.9f}|'
                            '{alt}|'
                            '{roll:0.1f}|'
                            '{pitch:0.1f}|'
                            '{hdg:0.1f}').format(lon=telem['lon'],
                                                 lat=telem['lat'],
                                                 alt=int(telem['altitude_hour']),
                                                 roll=telem['aviahorizon_roll'],
                                                 pitch=telem['aviahorizon_pitch'],
                                                 hdg=telem['compass'])
                              
    formatted_entry['Throttle']          = telem['throttle 1, %'] / 100
    formatted_entry['RollControlInput']  = '{0:.6f}'.format(telem['stick_ailerons'])
    formatted_entry['PitchControlInput'] = '{0:.6f}'.format(telem['stick_elevator'])
    formatted_entry['YawControlInput']   = '{0:.6f}'.format(telem['pedals1'])
    formatted_entry['IAS']               = '{0:.6f}'.format(telem['IAS, km/h'])
    formatted_entry['TAS']               = telem['TAS, km/h']
    formatted_entry['FuelWeight']        = telem['Mfuel, kg']
    formatted_entry['FuelVolume']        = telem['Mfuel, kg'] / telem['Mfuel0, kg']
    formatted_entry['Mach']              = telem['M']
    formatted_entry['AOA']               = telem['AoA, deg']
    formatted_entry['LandingGear']       = telem['gear, %']  / 100
    formatted_entry['Flaps']             = telem['flaps, %'] / 100
    
    if initial_entry:
        formatted_entry = combine_dicts(formatted_entry,
                                        format_init_meta(telem))
    
    return formatted_entry

def format_init_meta(telem):
    '''
    Description:
    ------------
    Create a dictionary of formatted object metadata to be logged in the
    ACMI log (only needed once per object to be displayed)
    
    :param telem: dict - full War Thunder vehicle telemetry data
    
    :return formatted_meta: dict - all object metadata fields and values 
                                   necessary for it's initial entry in the ACMI log
    '''
    
    formatted_meta = INITIAL_META
    
    formatted_meta['Name'] = telem['type']
    formatted_meta['Type'] = 'Air+FixedWing'
    
    return formatted_meta


if __name__ == '__main__':
    try:
        telem_info = telemetry.TelemInterface() # class used to query War Thunder telemetry
        logger     = acmi.ACMI()                # class used to log match data
        
        loc_time = dt.datetime.now()
        title    = TITLE_FORMAT.format(timestamp=loc_time.strftime('%Y_%m_%d_%H_%M_%S'), user=getuser())
        
        logger.create(title)
        
        header_inserted = False
        meta_inserted   = False
        
        while True:
            if telem_info.get_telemetry():
                pprint.pprint(telem_info.basic_telemetry)
                print(' ')
                
                if not header_inserted and telem_info.map_info.map_valid:
                    header = format_header(telem_info.map_info.grid_info, loc_time)
                    logger.insert_user_header(header)
                    header_inserted = True
                
                if header_inserted:
                    if not meta_inserted:
                        entry = format_entry(telem_info.full_telemetry, True)
                        meta_inserted = True
                    else:
                        entry = format_entry(telem_info.full_telemetry)
                    logger.insert_entry(0, entry)
    except KeyboardInterrupt:
        pass

