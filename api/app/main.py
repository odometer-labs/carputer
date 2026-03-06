from fastapi import FastAPI
from .routers import rest_endpoints, websocket_server
from .logging.handlers import logger

app = FastAPI()

app.include_router(rest_endpoints.router, tags=["REST"])
app.include_router(websocket_server.router, tags=["Websocket"])

@app.get("/")
async def root():
    logger.info("GET Root")
    return "Welcome to the carputer API! Visit http://127.0.0.1:800/docs for a Swaggerdocs of our endpoints!"