'''
Example script demonstrating simultaneous local ACMI file saving 
and live TCP streaming to Tacview using the War Thunder telemetry suite.
'''

import time
from WarThunder import telemetry
from WarThunder import acmi


def main():
    print("------------------------------------------------------")
    print(" War Thunder: Dual ACMI Logger & Tacview Streamer")
    print("------------------------------------------------------")
    
    # 1. Initialize Telemetry Interface
    telem = telemetry.TelemInterface()
    
    # Define a default reference origin (e.g., standard map center or test coordinates)
    # In a full run, you can pull reference lat/lon dynamically from map_info metadata.
    REF_LAT = 37.5
    REF_LON = -120.0
    REF_ALT = 0.0
    
    # 2. Initialize Local File Writer and TCP Server
    local_log_path = "flight_recording.acmi"
    writer = acmi.AcmiWriter(local_log_path, ref_lat=REF_LAT, ref_lon=REF_LON, ref_alt=REF_ALT)
    server = acmi.AcmiTcpServer(host='127.0.0.1', port=42674, ref_lat=REF_LAT, ref_lon=REF_LON, ref_alt=REF_ALT)
    
    # Start local file and TCP broadcast server
    writer.open()
    server.start()
    print(f"[STATUS] Local recording started: {local_log_path}")
    print(f"[STATUS] Tacview real-time stream listening on localhost:42674")
    
    # Track registered objects to avoid re-sending definition headers every tick
    registered_objects = set()
    
    print("\nWaiting for active flight telemetry... (Press Ctrl+C to stop)")
    try:
        start_time = time.time()
        
        while True:
            # Poll telemetry and map objects (enabling events for combat tracking)
            in_flight = telem.get_telemetry(events=True)
            
            if not in_flight:
                print("[STATUS] Waiting to spawn into mission...", end="\r")
                time.sleep(1.0)
                continue
                
            elapsed_sec = time.time() - start_time
            
            # Prepare frame data collection
            frame_items = []
            
            # --- 1. Register and track the Player Aircraft ---
            player_id = 10001
            if player_id not in registered_objects:
                player_name = telem.airframe or "Player_Aircraft"
                writer.add_object(player_id, player_name, "Air+FixedWing", color="Blue")
                server.add_object(player_id, player_name, "Air+FixedWing", color="Blue")
                registered_objects.add(player_id)
                
            # Convert player position (Assuming map_info parsed NED coordinates)
            # In your main loop, use telem.map_info player coordinates or fallback values
            player_n = getattr(telem.map_info, 'player_ned_n', 0.0)
            player_e = getattr(telem.map_info, 'player_ned_e', 0.0)
            player_d = -telem.altitude  # Altitude up converted to down (negative altitude)
            
            frame_items.append({
                'id': player_id,
                'northing': player_n,
                'easting': player_e,
                'down': player_d,
                'roll': telem.roll,
                'pitch': telem.pitch,
                'yaw': telem.heading
            })
            
            # --- 2. Register and track dynamic map entities (tanks, enemies, etc.) ---
            for idx, obj in enumerate(telem.map_info.map_objs):
                obj_id = 20000 + idx
                
                if obj_id not in registered_objects:
                    obj_name = obj.icon or "Entity"
                    obj_type = "Ground+Armor" if obj.tank else "Ground+Vehicle"
                    obj_color = "Blue" if obj.friendly else "Red"
                    
                    writer.add_object(obj_id, obj_name, obj_type, color=obj_color)
                    server.add_object(obj_id, obj_name, obj_type, color=obj_color)
                    registered_objects.add(obj_id)
                
                # Get entity NED coordinates
                pos_n, pos_e = obj.position_ned
                frame_items.append({
                    'id': obj_id,
                    'northing': pos_n,
                    'easting': pos_e,
                    'down': 0.0,
                    'roll': 0.0,
                    'pitch': 0.0,
                    'yaw': obj.hdg
                })
                
            # --- 3. Write locally and broadcast live over TCP ---
            if frame_items:
                writer.write_frame(elapsed_sec, frame_items)
                server.broadcast_frame(elapsed_sec, frame_items)
                
            print(f"[STREAMING] Time: {elapsed_sec:.1f}s | Tracked Entities: {len(frame_items)}", end="\r")
            time.sleep(0.1)  # 10 Hz telemetry logging rate
            
    except KeyboardInterrupt:
        print("\n\nShutting down ACMI bridge...")
    finally:
        writer.close()
        server.stop()
        print("[SUCCESS] ACMI file saved locally and server closed.")


if __name__ == '__main__':
    main()