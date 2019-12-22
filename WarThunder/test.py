import pprint
import general, telemetry, acmi
from getpass import getuser
import datetime as dt
import paho.mqtt.client as mqtt


TITLE_FORMAT = '{timestamp}_{user}.acmi'
ACMI_HEADER  = {'DataSource':    '',
                'DataRecorder':  '',
                'Author':        '',
                'Title':         '',
                'Comments':      '',
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
                'Flaps': 0,
                'Name': ''}


def format_header(grid_info, loc_time):
    '''
    TODO
    '''
    
    formatted_header = ACMI_HEADER
    
    formatted_header['DataSource']   = 'War Thunder v{}'.format(general.get_version())
    formatted_header['DataRecorder'] = 'Flight Viewer'
    formatted_header['Author']       = getuser()
    formatted_header['Title']        = grid_info['name']
    formatted_header['Comments']     = 'Local: {}'.format(loc_time)
    formatted_header['ReferenceLatitude']  = grid_info['ULHC_lat']
    formatted_header['ReferenceLongitude'] = grid_info['ULHC_lon']
    
    return formatted_header

def format_entry(telem):
    '''
    TODO
    '''
    
    formatted_entry = ACMI_ENTRY
    
    formatted_entry['T'] = '{lon}|{lat}|{alt}|{roll}|{pitch}|{hdg}|{H_m}'.format(lon=telem['lon'],
                                                                                 lat=telem['lat'],
                                                                                 alt=telem['altitude_hour'],
                                                                                 roll=telem['aviahorizon_roll'],
                                                                                 pitch=telem['aviahorizon_pitch'],
                                                                                 hdg=telem['compass'],
                                                                                 H_m=telem['H, m'])
    formatted_entry['Throttle'] = telem['throttle 1, %']
    formatted_entry['RollControlInput']  = telem['stick_ailerons']
    formatted_entry['PitchControlInput'] = telem['stick_elevator']
    formatted_entry['YawControlInput']   = telem['pedals1']
    formatted_entry['IAS'] = telem['IAS, km/h']
    formatted_entry['TAS'] = telem['TAS, km/h']
    formatted_entry['FuelWeight'] = telem['Mfuel, kg']
    formatted_entry['FuelVolume'] = telem['Mfuel, kg'] / telem['Mfuel0, kg']
    formatted_entry['Mach'] = telem['M']
    formatted_entry['AOA']  = telem['AoA, deg']
    formatted_entry['LandingGear'] = telem['gear, %']  / 100
    formatted_entry['Flaps']       = telem['flaps, %'] / 100
    formatted_entry['Name'] = telem['type']
    
    return formatted_entry


if __name__ == '__main__':
    try:
        telem_info = telemetry.TelemInterface()
        logger     = acmi.ACMI()
        
        loc_time = dt.datetime.now()
        title    = TITLE_FORMAT.format(timestamp=loc_time.strftime('%Y_%m_%d_%H_%M_%S'), user=getuser())
        
        logger.create(title)
        
        header_inserted = False
        
        while True:
            if telem_info.get_telemetry():
                pprint.pprint(telem_info.basic_telemetry)
                print(' ')
                
                if not header_inserted and telem_info.map_info.map_valid:
                    header = format_header(telem_info.map_info.grid_info, loc_time)
                    logger.insert_user_header(header)
                    header_inserted = True
                
                if header_inserted:
                    entry = format_entry(telem_info.full_telemetry)
                    logger.insert_entry(0, entry)
    except KeyboardInterrupt:
        pass

