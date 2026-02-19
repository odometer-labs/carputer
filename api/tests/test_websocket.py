import asyncio
import websockets
import pytest


@pytest.mark.asyncio
async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws/hello"

    async with websockets.connect(uri) as ws:
        await ws.send("knock knock")
        greeting = await ws.recv()