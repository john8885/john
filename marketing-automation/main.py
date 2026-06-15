"""메인 진입점 — FastAPI CRM + 백그라운드 스케줄러"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from crm.database import init_db
from crm.api import router as crm_router
from scheduler import create_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

scheduler = create_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start()
    logging.getLogger(__name__).info("Scheduler started")
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="마케팅 자동화 CRM", lifespan=lifespan)
app.include_router(crm_router)
