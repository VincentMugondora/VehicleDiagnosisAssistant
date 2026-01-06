import os
from fastapi import FastAPI
from dotenv import load_dotenv

from app.db.mongo import init_db
from app.api.webhook import router as webhook_router

load_dotenv()

app = FastAPI(title="Vehicle Diagnosis Assistant API")

app.include_router(webhook_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup():
    await init_db()
