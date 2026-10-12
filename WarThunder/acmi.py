'''
Module to generate Tacview-compatible .acmi files and stream real-time 
telemetry over TCP/IP using the Tacview Real-Time Telemetry Public Protocol.
'''

import socket
import threading
from datetime import datetime
from WarThunder.mapinfo import ned_to_lla


class AcmiWriter(object):
    def __init__(self, filepath: str, ref_lat: float = 37.0, ref_lon: float = -120.0, ref_alt: float = 0.0):
        '''
        Initialize Tacview ACMI 2.2 file writer.
        '''
        self.filepath = filepath
        self.ref_lat = ref_lat
        self.ref_lon = ref_lon
        self.ref_alt = ref_alt
        self.file = None
        self.registered_objects = set()

    def open(self):
        '''Open file and write required Tacview 2.2 headers'''
        self.file = open(self.filepath, 'w', encoding='utf-8-sig')
        
        # Mandatory ACMI 2.2 Header
        self.file.write("FileType=text/acmi/tacview\n")
        self.file.write("FileVersion=2.2\n")
        
        # Global reference time & origin anchor (Object 0)
        timestamp_str = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        self.file.write(f"0,ReferenceTime={timestamp_str}\n")
        self.file.write(f"0,Author=WarThunderAutomationSuite\n")
        
    def add_object(self, obj_id: int, name: str, object_type: str, color: str = ""):
        '''
        Define or update a tactical object in the ACMI session.
        '''
        if not self.file:
            return
            
        hex_id = f"{obj_id:X}"
        props = [f"Name={name}", f"Type={object_type}"]
        if color:
            props.append(f"Color={color}")
            
        prop_string = ",".join(props)
        self.file.write(f"{hex_id},{prop_string}\n")
        self.registered_objects.add(obj_id)

    def write_frame(self, timestamp_sec: float, frame_data: list):
        '''
        Write a telemetry snapshot frame for all active objects at a given timestamp.
        '''
        if not self.file:
            return
            
        self.file.write(f"#{timestamp_sec:.2f}\n")
        
        for item in frame_data:
            obj_id = item.get('id')
            hex_id = f"{obj_id:X}"
            
            northing = item.get('northing', 0.0)
            easting = item.get('easting', 0.0)
            down = item.get('down', 0.0)
            
            lat, lon, alt = ned_to_lla(
                northing, easting, down, 
                self.ref_lat, self.ref_lon, self.ref_alt
            )
            
            roll = item.get('roll', 0.0)
            pitch = item.get('pitch', 0.0)
            yaw = item.get('yaw', 0.0)
            
            pos_str = f"T={lon:.7f}|{lat:.7f}|{alt:.2f}|{roll:.2f}|{pitch:.2f}|{yaw:.2f}"
            self.file.write(f"{hex_id},{pos_str}\n")

    def close(self):
        '''Safely close the ACMI file stream'''
        if self.file:
            self.file.close()
            self.file = None


class AcmiTcpServer(object):
    def __init__(self, host: str = '127.0.0.1', port: int = 42674, ref_lat: float = 37.0, ref_lon: float = -120.0, ref_alt: float = 0.0):
        '''
        Initialize Tacview Real-Time Telemetry TCP Server.
        
        Args:
            host: Local IP to bind to (default: 127.0.0.1)
            port: TCP port for Tacview connection (default: 42674)
            ref_lat, ref_lon, ref_alt: Geographic reference origin for coordinate projection
        '''
        self.host = host
        self.port = port
        self.ref_lat = ref_lat
        self.ref_lon = ref_lon
        self.ref_alt = ref_alt
        
        self.server_socket = None
        self.clients = []
        self.clients_lock = threading.Lock()
        self.is_running = False
        self.server_thread = None
        
        self.session_header = []
        self.active_objects = {}  # obj_id -> prop_string

    def start(self):
        '''Start the TCP background server listening for Tacview connections'''
        if self.is_running:
            return
            
        self.is_running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        timestamp_str = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        self.session_header = [
            "FileType=text/acmi/tacview\n",
            "FileVersion=2.2\n",
            f"0,ReferenceTime={timestamp_str}\n",
            "0,Author=WarThunderAutomationSuite\n"
        ]
        
        self.server_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.server_thread.start()
        print(f"[ACMI TCP] Real-time telemetry server active on {self.host}:{self.port}")

    def _accept_loop(self):
        while self.is_running:
            try:
                self.server_socket.settimeout(1.0)
                client_sock, addr = self.server_socket.accept()
                
                client_thread = threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True)
                client_thread.start()
            except socket.timeout:
                continue
            except Exception:
                if not self.is_running:
                    break

    def _handle_client(self, sock: socket.socket):
        try:
            sock.settimeout(5.0)
            # 1. Send Host Handshake per Tacview Real-Time Telemetry Protocol
            host_handshake = b"XtraLib.Stream.0\nTacview.RealTimeTelemetry.0\nWarThunderHost\n\0"
            sock.sendall(host_handshake)
            
            # 2. Read Client Handshake until terminating null byte '\0'
            data = bytearray()
            while b'\0' not in data:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                data.extend(chunk)
                
            sock.settimeout(None)  # Remove timeout for active streaming
            
            # 3. Transmit session headers and existing objects to the newly connected client
            with self.clients_lock:
                for line in self.session_header:
                    sock.sendall(line.encode('utf-8'))
                for prop_str in self.active_objects.values():
                    sock.sendall((prop_str + "\n").encode('utf-8'))
                
                self.clients.append(sock)
                print(f"[ACMI TCP] Tacview client handshake complete and streaming active.")
                
        except Exception as e:
            print(f"[ACMI TCP] Handshake failed: {e}")
            try:
                sock.close()
            except:
                pass

    def add_object(self, obj_id: int, name: str, object_type: str, color: str = ""):
        '''Register or update an object and broadcast it to connected Tacview clients'''
        hex_id = f"{obj_id:X}"
        props = [f"Name={name}", f"Type={object_type}"]
        if color:
            props.append(f"Color={color}")
        prop_string = f"{hex_id}," + ",".join(props)
        
        with self.clients_lock:
            self.active_objects[obj_id] = prop_string
            line = (prop_string + "\n").encode('utf-8')
            
            active_clients = []
            for sock in self.clients:
                try:
                    sock.sendall(line)
                    active_clients.append(sock)
                except Exception:
                    sock.close()
            self.clients = active_clients

    def broadcast_frame(self, timestamp_sec: float, frame_data: list):
        '''Broadcast real-time telemetry frame to all connected Tacview clients'''
        if not self.clients:
            return
            
        payload_lines = [f"#{timestamp_sec:.2f}\n"]
        for item in frame_data:
            obj_id = item.get('id')
            hex_id = f"{obj_id:X}"
            
            northing = item.get('northing', 0.0)
            easting = item.get('easting', 0.0)
            down = item.get('down', 0.0)
            
            lat, lon, alt = ned_to_lla(
                northing, easting, down, 
                self.ref_lat, self.ref_lon, self.ref_alt
            )
            
            roll = item.get('roll', 0.0)
            pitch = item.get('pitch', 0.0)
            yaw = item.get('yaw', 0.0)
            
            pos_str = f"T={lon:.7f}|{lat:.7f}|{alt:.2f}|{roll:.2f}|{pitch:.2f}|{yaw:.2f}"
            payload_lines.append(f"{hex_id},{pos_str}\n")
            
        payload = "".join(payload_lines).encode('utf-8')
        
        with self.clients_lock:
            active_clients = []
            for sock in self.clients:
                try:
                    sock.sendall(payload)
                    active_clients.append(sock)
                except Exception:
                    try:
                        sock.close()
                    except:
                        pass
            self.clients = active_clients

    def stop(self):
        '''Stop the TCP server and disconnect all clients'''
        self.is_running = False
        with self.clients_lock:
            for sock in self.clients:
                try:
                    sock.close()
                except:
                    pass
            self.clients = []
            
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("[ACMI TCP] Server shut down.")