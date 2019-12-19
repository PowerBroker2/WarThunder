'''
Python3 module/script to query and access telemetry data during War Thunder "Air Battles" matches

NOTE: THIS DOES NOT WORK WITH TANK OR SHIP BATTLES

Example basic_telemetry dict:
    {'IAS': 2,
     'airframe': 'p-51d-5',
     'altitude': -475.12204,
     'clock_hour': 8.3,
     'clock_min': 18.0,
     'clock_sec': 47.0,
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


IP_ADDRESS     = socket.gethostbyname(socket.gethostname())
URL_INDICATORS = 'http://{}:8111/indicators'.format(IP_ADDRESS)
URL_STATE      = 'http://{}:8111/state'.format(IP_ADDRESS)


def combine_dicts(to_dict, from_dict):
    if (type(to_dict) == dict) and (type(from_dict) == dict):
        for key in from_dict.keys():
            to_dict[key] = from_dict[key]

        return to_dict
    else:
        return False


class TelemInterface(object):
    def __init__(self):
        self.connected = False
        self.full_telemetry = {}
        self.basic_telemetry = {}
        self.indicators = {}
        self.state = {}

    def get_telemetry(self):
        self.full_telemetry = {}
        self.basic_telemetry = {}

        try:
            # get indicator data
            indicator_response = requests.get(URL_INDICATORS)
            self.indicators = indicator_response.json()

            # get state data
            state_response = requests.get(URL_STATE)
            self.state = state_response.json()

            if self.indicators['valid'] and self.state['valid']:
                self.basic_telemetry['airframe']    = self.indicators['type']
                self.basic_telemetry['roll']        = self.indicators['aviahorizon_roll']
                self.basic_telemetry['pitch']       = self.indicators['aviahorizon_pitch']
                self.basic_telemetry['heading']     = self.indicators['compass']
                self.basic_telemetry['altitude']    = self.indicators['altitude_hour']
                self.basic_telemetry['clock_hour']  = self.indicators['clock_hour']
                self.basic_telemetry['clock_min']   = self.indicators['clock_min']
                self.basic_telemetry['clock_sec']    = self.indicators['clock_sec']

                self.basic_telemetry['IAS']         = self.state['TAS, km/h']
                self.basic_telemetry['flapState']   = self.state['flaps, %']
                self.basic_telemetry['gearState']   = self.state['gear, %']

                self.full_telemetry = combine_dicts(self.full_telemetry, self.indicators)
                self.full_telemetry = combine_dicts(self.full_telemetry, self.state)

                self.connected = True
                return True
            else:
                print("Mission not currently running...")
                self.connected = False
                return False

        except Exception as e:
            if "Failed to establish a new connection" in str(e):
                print("War Thunder not running...")
            else:
                import traceback
                traceback.print_exc()
            
            self.connected = False
            return False


if __name__ == "__main__":
    import pprint
    
    my_telem = TelemInterface()

    while True:
        my_telem.get_telemetry()
        pprint.pprint(my_telem.basic_telemetry)
