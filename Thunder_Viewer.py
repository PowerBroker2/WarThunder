import os
import sys
import arrow
import requests
import datetime as dt
import paho.mqtt.client as mqtt
from socketserver import TCPServer, BaseRequestHandler
from PyQt5.QtCore import QThread, QProcess
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from pySerialTransfer import pySerialTransfer as transfer
from WarThunder import general, telemetry, acmi
from WarThunder.telemetry import combine_dicts
from getpass import getuser
from gui import Ui_ThunderViewer


APP_DIR      = os.path.dirname(os.path.realpath(__file__))
STREAM_DIR   = os.path.join(APP_DIR, 'stream_log')
STREAM_FILE  = os.path.join(STREAM_DIR, 'stream.acmi')
LOGS_DIR     = os.path.join(APP_DIR, 'logs')
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


def format_header_dict(grid_info, loc_time):
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
    formatted_header['DataRecorder']       = 'Thunder Viewer'
    formatted_header['Author']             = getuser()
    formatted_header['Title']              = grid_info['name']
    formatted_header['Comments']           = 'Local: {}'.format(loc_time.strftime('%Y-%m-%d %H:%M:%S'))
    formatted_header['ReferenceLatitude']  = grid_info['ULHC_lat']
    formatted_header['ReferenceLongitude'] = grid_info['ULHC_lon']
    
    return formatted_header

def format_entry_dict(telem, initial_entry=False):
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
                                                 alt=telem['alt_m'],
                                                 roll=telem['aviahorizon_roll'],
                                                 pitch=telem['aviahorizon_pitch'],
                                                 hdg=telem['compass'])
                              
    formatted_entry['Throttle']          = telem['throttle 1, %'] / 100
    formatted_entry['RollControlInput']  = '{0:.6f}'.format(telem['stick_ailerons'])
    formatted_entry['PitchControlInput'] = '{0:.6f}'.format(telem['stick_elevator'])
    
    try:
        formatted_entry['YawControlInput'] = '{0:.6f}'.format(telem['pedals1'])
    except KeyError:
        formatted_entry['YawControlInput'] = 0
        
    formatted_entry['IAS']               = '{0:.6f}'.format(telem['IAS, km/h'])
    formatted_entry['TAS']               = telem['TAS, km/h']
    formatted_entry['FuelWeight']        = telem['Mfuel, kg']
    formatted_entry['FuelVolume']        = telem['Mfuel, kg'] / telem['Mfuel0, kg']
    formatted_entry['Mach']              = telem['M']
    
    try:
        formatted_entry['AOA'] = telem['AoA, deg']
    except KeyError:
        formatted_entry['AOA'] = 0
    
    try:
        formatted_entry['LandingGear'] = telem['gear, %'] / 100
    except KeyError:
        formatted_entry['LandingGear'] = 1
    
    try:
        formatted_entry['Flaps'] = telem['flaps, %'] / 100
    except KeyError:
        formatted_entry['Flaps'] = 0
    
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


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ThunderViewer()
        self.ui.setupUi(self)
        self.show()
        
        self.connect_signals()
        self.init_recording_status()
        self.update_port_list()
        
        self.ui.acmi_path.setText(LOGS_DIR)
        self.ui.usb_baud.setCurrentIndex(8) # default baud of 115200
    
    def connect_signals(self):
        self.ui.tacview_select.clicked.connect(self.get_tacview_install)
        self.ui.acmi_select.clicked.connect(self.get_acmi_dir)
        self.ui.launch_tacview_live.clicked.connect(self.launch_live)
        self.ui.record.clicked.connect(self.record_data)
        self.ui.stop.clicked.connect(self.stop_recording_data)
        self.ui.port_refresh.clicked.connect(self.update_port_list)
    
    def get_tacview_install(self):
        path = QFileDialog.getOpenFileName(self, filter='Tacview (Tacview.exe Tacview64.exe)')[0]
        if path:
            self.ui.tacview_path.setText(path)
    
    def get_acmi_dir(self):
        path = QFileDialog.getExistingDirectory(self, 'Select Directory', APP_DIR)
        if path:
            self.ui.acmi_path.setText(path)
    
    def launch_live(self):
        try:
            if not os.path.exists(self.ui.tacview_path.text()):
                raise FileNotFoundError
            self.process = QProcess()
            self.process.startDetached('"{}" {}'.format(self.ui.tacview_path.text(), '/ConnectRealTimeTelemetry'))
        except (FileNotFoundError, OSError):
            print('ERROR: Tacview.exe not found')
        
    def record_data(self):
        if not self.ui.recording.isChecked():
            self.disable_inputs()
            self.rec_th = RecordThread(self)
            self.rec_th.start()
            
            if self.ui.mqtt.isChecked():
                self.mqttc = mqtt.Client() # class used to connect to remote players via MQTT
            
            if self.ui.live_telem.isChecked():
                self.stream_th = StreamThread(self)
                self.stream_th.start()
            
            self.ui.recording.setChecked(True)
    
    def stop_recording_data(self):
        self.enable_inputs()
        try:
            if self.rec_th.isRunning():
                self.rec_th.terminate()
            if self.stream_th.isRunning():
                self.stream_th.terminate()
#            if self.mqtt_th.isRunning():
#                self.m1tt_th.terminate()
        except AttributeError:
            pass
        self.ui.recording.setChecked(False)
    
    def init_recording_status(self):
        self.ui.recording.setDisabled(True)
        self.ui.recording.setChecked(False)
    
    def update_port_list(self):
        ports = transfer.open_ports()
        self.ui.usb_ports.clear()
        self.ui.usb_ports.addItems(ports)
    
    def enable_inputs(self):
        self.change_inputs(True)
    
    def disable_inputs(self):
        self.change_inputs(False)
    
    def change_inputs(self, enable):
        self.ui.tacview_path.setEnabled(enable)
        self.ui.tacview_select.setEnabled(enable)
        self.ui.acmi_path.setEnabled(enable)
        self.ui.acmi_select.setEnabled(enable)
        self.ui.live_telem.setEnabled(enable)
        self.ui.live_telem_port.setEnabled(enable)
        self.ui.mqtt.setEnabled(enable)
        self.ui.mqtt_id.setEnabled(enable)
        self.ui.usb_ports.setEnabled(enable)
        self.ui.live_usb.setEnabled(enable)


class RecordThread(QThread):
    def __init__(self, parent=None):
        super(RecordThread, self).__init__(parent)
        
        self.telem   = telemetry.TelemInterface() # class used to query War Thunder telemetry
        self.logger  = acmi.ACMI()                # class used to log match data
        self.log_dir = parent.ui.acmi_path.text()
        self.mqtt_enable   = parent.ui.mqtt.isChecked()
        self.stream_enable = parent.ui.live_telem.isChecked()
        self.usb_enable    = parent.ui.live_usb.isChecked()
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        if self.usb_enable:
            self.usb_port = parent.ui.live_usb.text()
            self.usb_baud = parent.ui.usb_baud.text()
            if not self.usb_port:
                self.usb_enable = False
            else:
                self.transfer = transfer.SerialTransfer(self.usb_port, self.usb_baud)
    
    def process_player(self):
        if self.telem.get_telemetry():
            if not self.header_inserted and self.telem.map_info.map_valid:
                header = format_header_dict(self.telem.map_info.grid_info, self.loc_time)
                self.logger.insert_user_header(header)
                self.header_inserted = True
            
            if self.header_inserted:
                if not self.meta_inserted:
                    entry = format_entry_dict(self.telem.full_telemetry, True)
                    self.meta_inserted = True
                else:
                    entry = format_entry_dict(self.telem.full_telemetry)
                self.logger.insert_entry(0, entry)
            
            if self.mqtt_enable:
                #self.mqttc
                pass
            
            if self.stream_enable:
                log_line = self.logger.format_entry(0, entry)
                
                if not os.path.exists(STREAM_DIR):
                    os.makedirs(STREAM_DIR)
                if not os.path.exists(STREAM_FILE):
                    init_stream_log()
                else:
                    with open(STREAM_FILE, 'a') as log:
                        log.write(log_line)
            
            if self.usb_enable:
                # mulitply float values by a constant so as to preserve as much
                # of the value's precision as possible
                pitch = int(self.telem.basic_telemetry['pitch'] * 350)
                roll  = int(self.telem.basic_telemetry['roll']  * 350)
                hdg   = int(self.telem.basic_telemetry['heading'])
                alt   = int(self.telem.basic_telemetry['altitude'])
                lat   = int(self.telem.basic_telemetry['lat'] * 5000)
                lon   = int(self.telem.basic_telemetry['lon'] * 5000)
                
                self.transfer.txBuff[0]  = transfer.msb(pitch)
                self.transfer.txBuff[1]  = transfer.lsb(pitch)
                self.transfer.txBuff[2]  = transfer.msb(roll)
                self.transfer.txBuff[3]  = transfer.lsb(roll)
                self.transfer.txBuff[4]  = transfer.msb(hdg)
                self.transfer.txBuff[5]  = transfer.lsb(hdg)
                self.transfer.txBuff[6]  = transfer.msb(alt)
                self.transfer.txBuff[7]  = transfer.lsb(alt)
                self.transfer.txBuff[8]  = transfer.msb(lat)
                self.transfer.txBuff[9]  = transfer.byte_val(lat, 2)
                self.transfer.txBuff[10] = transfer.byte_val(lat, 1)
                self.transfer.txBuff[11] = transfer.lsb(lat)
                self.transfer.txBuff[12] = transfer.msb(lon)
                self.transfer.txBuff[13] = transfer.byte_val(lon, 2)
                self.transfer.txBuff[14] = transfer.byte_val(lon, 1)
                self.transfer.txBuff[15] = transfer.lsb(lon)
                
                self.transfer.send(16)
        
    def run(self):
        self.loc_time = dt.datetime.now()
        self.title = TITLE_FORMAT.format(timestamp=self.loc_time.strftime('%Y_%m_%d_%H_%M_%S'), user=getuser())
        self.title = os.path.join(self.log_dir, self.title)
        
        self.logger.create(self.title)
        self.header_inserted = False
        self.meta_inserted   = False
        
        while True:
            self.process_player()


class StreamThread(QThread):
    def __init__(self, parent=None):
        super(StreamThread, self).__init__(parent)
        self.port = parent.ui.live_telem_port.value()
        
    def run(self):
        if not os.path.exists(STREAM_DIR):
            os.makedirs(STREAM_DIR)
        init_stream_log()
        
        try:
            self.server = TCPServer(('localhost', self.port), StreamHandler)
            self.server.serve_forever()
        except OSError:
            print('ERROR: TCP port in use - please pick a different port')


class StreamHandler(BaseRequestHandler):
    def handle(self):
        self.request.sendall(b'XtraLib.Stream.0\nTacview.RealTimeTelemetry.0\nThunder_Viewer\n\x00')
        self.data = self.request.recv(1024).strip()
        self.read_index = 0
        
        while True:
            if not os.path.exists(STREAM_FILE):
                if not os.path.exists(STREAM_DIR):
                    os.makedirs(STREAM_DIR)
                self.read_index = 0
                init_stream_log()
            else:
                try:
                    with open(STREAM_FILE, 'r') as f:
                        log_line = f.readlines()[self.read_index]
                except (FileNotFoundError, IndexError):
                    log_line = ''
                
                if log_line:
                    payload = bytes(log_line, encoding='utf8')
                    print(payload)
                    self.request.sendall(payload)
                    self.read_index += 1


def main():
    app = QApplication(sys.argv)
    w = AppWindow()
    w.show()
    sys.exit(app.exec_())

def init_stream_log():
    with open(STREAM_FILE, 'w') as log:
        log.write(acmi.header_mandatory.format(filetype='text/acmi/tacview',
                                               acmiver='2.1',
                                               reftime=str(arrow.utcnow()).split('+')[0]))

def garbage_collection():
    if os.path.exists(STREAM_FILE):
        init_stream_log()


if __name__ == "__main__":
    try:
        main()
    except (SystemExit, KeyboardInterrupt, requests.exceptions.ConnectionError):
        garbage_collection()



