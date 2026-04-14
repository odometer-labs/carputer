from gpsdclient import GPSDClient
import os
import time
import json
from websockets.sync.client import connect

WS_SERVER_URL = os.getenv("WS_SERVER_URL", "ws://api:8000/ws/update-position")
GPSD_HOST = os.getenv("GPSD_HOST", "host-gateway")
GPSD_PORT = int(os.getenv("GPSD_PORT", "2947"))

def main():
    # Connect to fastapi's ws
    try:
        ws_client = connect(WS_SERVER_URL)
        print(f"Connected to ws server at {WS_SERVER_URL}")
    except Exception:
        print(f"Failed to connect to ws server at {WS_SERVER_URL}")
        exit()

    # Send gpsd data
    try:
        gpsd_client = GPSDClient(host=GPSD_HOST, port=GPSD_PORT)
        print(f"Connected to gpsd at {GPSD_HOST}:{GPSD_PORT}")
        while True:
            for packet in gpsd_client.dict_stream(convert_datetime=True, filter=["TPV"]):
                # Skip TPV packets without a position fix
                if "lat" not in packet or "lon" not in packet:
                    continue
                ws_client.send(json.dumps(packet))
                time.sleep(0.1)
    except Exception as e:
        print(f"Failed to send data to websocket server: {e}")
    finally:
        ws_client.close()
        gpsd_client.close()
        print("Websocket closed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Closing gpsd service")