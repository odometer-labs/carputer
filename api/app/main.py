from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import tracks, websocket
from .logging.handlers import logger

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    #front end development, npm run dev
        "http://localhost:4173"     #Production preview, npm run build + preview
        ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tracks.router)
app.include_router(websocket.router)

@app.get("/")
async def root():
    logger.info("GET Root")
    return "Welcome to the carputer API! Visit http://127.0.0.1:8000/docs for a Swaggerdocs of our endpoints!"