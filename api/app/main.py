from fastapi import FastAPI
from .routers import tracks, websocket
from .logging.handlers import logger

app = FastAPI()


app.include_router(tracks.router)
app.include_router(websocket.router)

@app.get("/")
async def root():
    logger.info("GET Root")
    return "Welcome to the carputer API! Visit http://127.0.0.1:8000/docs for a Swaggerdocs of our endpoints!"

@app.get("/health")
def health_check():
    return {"status": "healthy"}