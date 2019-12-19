import os
import arrow
from random import randint


MAX_NUM_OBJS     = 1000
header_mandatory = ('FileType={filetype}\n' 
                    'FileVersion={acmiver}\n'
                    '0,ReferenceTime={reftime}Z\n')


class ACMI(object):
    def __init__(self, num_objs):
        '''
        '''
        
        self.entry_vals = []
        
        if num_objs > MAX_NUM_OBJS:
            raise Exception('Too many objects specified - cannot be more than {}'.format(MAX_NUM_OBJS))
        
        for x in range(num_objs):
            self.entry_vals.append({'id': hex(randint(1, MAX_NUM_OBJS + 2))[2:]})
        
    def create(self, file_name, reference_time, file_type='text/acmi/tacview', acmi_ver='2.1'):
        '''
        Example reference_time:
        -----------------------
        '2019-12-19T00:23:17.705626'
        '''
        
        self.file_name = file_name
        
        if not self.file_name.endswith('.acmi'):
            self.file_name += '.acmi'
        
        dir_name = os.path.dirname(file_name)
        
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
        
        with open(self.file_name, 'w') as log:
            log.write(header_mandatory.format(filetype=file_type,
                                              acmiver=acmi_ver,
                                              reference_time))

    def insert_user_header(self, header_content: dict):
        '''
        TODO
        '''
        
        if not type(x) == dict:
            raise TypeError('"header_content" must be of type dict, not {}'.format(type(x)))
        
        header_list = ['0,{}={}'.format(key, header_content[key]) for key in header_content.keys()]
        header = '\n'.join(header_list) + '\n'
        
        try:
            with open(self.file_name, 'a') as log:
                log.write(header)
            return True
        
        except FileNotFoundError:
            print('ERROR - ACMI file not found')
            return False
    
    def insert_sample(timestamp, data):
        '''
        TODO
        '''
        
        entry = '#{:0.2f}\n'.format(timestamp)
        entry += '|'.join(data)
        entry += '\n'
        

    sortie_telemetry = (
        "#{:0.2f}\n{},T={:0.9f}|{:0.9f}|{}|{:0.1f}|{:0.1f}|{:0.1f},".format(
            time_adjusted_tick, state.PLAYERS_OID, x, y, z, r, p, h
        )
        + "Throttle={}".format(s_throttle1)
        + "RollControlInput={},".format(stick_ailerons)
        + "PitchControlInput={},".format(stick_elevator)
        + "YawControlInput={},".format(pedals)
        + "IAS={:0.6f},".format(ias)
        + "TAS={:0.6f},".format(tas)
        + "FuelWeight={},".format(fuel_kg)
        + "Mach={},".format(m)
        + "AOA={},".format(aoa)
        + "FuelVolume={},".format(fuel_vol)
        + "LandingGear={},".format(gear)
        + "Flaps={},".format(flaps)
    )

    sortie_subheader = (
          "Slot={},".format("0")
        + "Importance={},".format("1")
        + "Parachute={},".format("0")
        + "DragChute={},".format("0")
        + "Disabled={},".format("0")
        + "Pilot={},".format("0")
        + "Name={},".format(unit)
        + "ShortName={},".format(sname)
        + "LongName={},".format(lname)
        + "FullName={},".format(fname)
        + "Type={},".format("Air+FixedWing")
        + "Color={},".format("None")
        + "Callsign={},".format("None")
        + "Coalition={},".format("None")
    )

    with open("{}.acmi".format(filename), "a", newline="") as g:
        if insert_sortie_subheader:
            g.write(sortie_telemetry + sortie_subheader + "\n")
            insert_sortie_subheader = False
        else:
            g.write(sortie_telemetry + "\n")
    
    
    
    