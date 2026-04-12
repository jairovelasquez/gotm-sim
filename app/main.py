from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers.web import router
from app.config import BASE_DIR

app = FastAPI(title="VibeFuel GTM Simulator")
app.mount("/static", StaticFiles(directory=BASE_DIR / "app/static"), name="static")
app.include_router(router)
