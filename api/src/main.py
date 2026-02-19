from fastapi import FastAPI
from .routers import rest_endpoints, websocket_server

app = FastAPI()

app.include_router(rest_endpoints.router, tags=["Rest"])
app.include_router(websocket_server.router, tags=["Websocket"])