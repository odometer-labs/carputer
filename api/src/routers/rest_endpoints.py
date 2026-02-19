from fastapi import APIRouter

router = APIRouter(prefix="/v1")

@router.get("/")
async def root():
    return {"Hello": "World"}