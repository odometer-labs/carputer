from gpsdclient import GPSDClient
import asyncio
import json
from websockets.asyncio.client import connect

WS_SERVER_URL = "ws://api:8000/ws/update-position"

async def main():
    # Connect to fastapi's ws
    try:
        ws_client = await connect(WS_SERVER_URL)
        print("Connected to ws server")
    except Exception:
        print("Failed to connect to ws server")
        exit()

    # Send gpsd data
    try:
        gpsd_client = GPSDClient()
        while True:
            for packet in gpsd_client.dict_stream(convert_datetime=True, filter=["TPV"]):
                latest = packet
                ws_client.send(json.dumps(latest))
                await asyncio.sleep(0.1)
    finally:
        await ws_client.close()
        gpsd_client.close()
        print("Websocket closed")
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Closing gpsd service")