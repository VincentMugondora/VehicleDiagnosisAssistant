import os
import warnings
# Suppress Pydantic warning: built-in function `any` not a Python type during schema gen
warnings.filterwarnings("ignore", message=r".*ArbitraryTypeWarning.*")
# Also match the common message text and module that emits it
warnings.filterwarnings("ignore", message=r".*is not a Python type.*")
warnings.filterwarnings("ignore", module=r"pydantic\._internal\._generate_schema")
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from app.db.mongo import init_db
from app.api.webhook import router as webhook_router

app = FastAPI(title="Vehicle Diagnosis Assistant API")

app.include_router(webhook_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup():
    await init_db()
