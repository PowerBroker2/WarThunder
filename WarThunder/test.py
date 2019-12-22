import pprint
import telemetry


if __name__ == '__main__':
    try:
        telem_info = telemetry.TelemInterface()
        
        while True:
            if telem_info.get_telemetry(comments=True, events=True):
                pprint.pprint(telem_info.comments)
                print(' ')
                pprint.pprint(telem_info.events)
                print(' ')
                pprint.pprint(telem_info.basic_telemetry)
                print(' ')
                print(' ')
    except KeyboardInterrupt:
        pass

