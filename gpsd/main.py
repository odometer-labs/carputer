from gpsdclient import GPSDClient
import time
import json
from websockets.sync.client import connect

WS_SERVER_URL = "ws://api:8000/ws/update-position"

def main():
    # Connect to fastapi's ws
    try:
        ws_client = connect(WS_SERVER_URL)
        print("Connected to ws server")
    except Exception as e:
        print(f"Failed to connect to ws server: {e}")
        exit()

    # Send gpsd data
    try:
        gpsd_client = GPSDClient()
        while True:
            for packet in gpsd_client.dict_stream(convert_datetime=True, filter=["TPV"]):
                ws_client.send(json.dumps(packet))
                time.sleep(0.1)
    except Exception as e:
        print(f"Failed to send data to wbsocket server: {e}")
    finally:
        ws_client.close()
        gpsd_client.close()
        print("Websocket closed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Closing gpsd service")