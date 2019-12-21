# WarThunder_Telemetry
Python and C++ libraries to query and access vehicle telemetry data while in War Thunder air battles (NOT tanks)

This script makes use of two localhost servers ('http://localhost:8111/indicators' and 'http://localhost:8111/state') that War Thunder automatically runs when you launch a game match. If it is an air battle, these pages will include JSON formatted data with valid airplane telemetry. This telemetry is then converted and returned to the calling function/user.

The data can then be easily used for any custom application (i.e. telemetry datalogger and grapher).

# Example Python Script
```python
from pprint import pprint
from WarThunder import telemetry


if __name__ == '__main__':
    try:
        print('Starting')
        telem    = telemetry.TelemInterface()
        
        while True:
            if telem.get_telemetry():
                pprint(telem.basic_telemetry)
    
    except KeyboardInterrupt:
        print('Closing')
'''
