import os
import json
import asyncio
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv


async def seed() -> None:
    load_dotenv()
    uri = os.getenv("MONGODB_URI") or os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB", "vehicle_diag")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]

    # Ensure indexes
    await db["obd_codes"].create_index("code", unique=True)

    seeds = [
        {
            "code": "P0300",
            "description": "Random/multiple cylinder misfire detected",
            "symptoms": "Rough idle, hesitation, reduced power",
            "common_causes": "Spark plugs, ignition coils, vacuum leak, fuel delivery",
            "generic_fixes": "Inspect plugs/coils, check vacuum leaks, test fuel pressure",
        },
        {
            "code": "P0171",
            "description": "System too lean (Bank 1)",
            "symptoms": "Rough idle, misfire, poor acceleration",
            "common_causes": "Vacuum leak, MAF sensor, fuel pressure, exhaust leak",
            "generic_fixes": "Check intake leaks, clean/replace MAF, test fuel pressure",
        },
        {
            "code": "P0420",
            "description": "Catalyst system efficiency below threshold (Bank 1)",
            "symptoms": "Check engine light, possible reduced performance",
            "common_causes": "Catalytic converter, O2 sensors, exhaust leak",
            "generic_fixes": "Check for exhaust leaks, evaluate O2 sensors, assess catalyst",
        },
        {
            "code": "P0128",
            "description": "Coolant thermostat (coolant temperature below thermostat regulating temperature)",
            "symptoms": "Check engine light, engine taking long to warm up, poor heater performance",
            "common_causes": "Stuck open thermostat, low coolant level, faulty ECT sensor",
            "generic_fixes": "Replace thermostat, check/top-up coolant, test/replace ECT sensor",
        },
        {
            "code": "P0100",
            "description": "Mass or Volume Air Flow (MAF) circuit malfunction",
            "symptoms": "Rough idle, hesitation, poor fuel economy, stalling",
            "common_causes": "Dirty/faulty MAF sensor, wiring/connector issue, intake air leak",
            "generic_fixes": "Inspect/clean/replace MAF sensor, check wiring/connectors, inspect intake for leaks",
        },
    ]

    for doc in seeds:
        await db["obd_codes"].update_one(
            {"code": doc["code"]},
            {"$setOnInsert": doc},
            upsert=True,
        )

    # Load starter dataset if present (app/data/obd_codes.json)
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "obd_codes.json")
    data_path = os.path.abspath(data_path)
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
        # dataset is a mapping from code -> structured fields
        for code_key, payload in dataset.items():
            code_up = str(code_key).upper().strip()
            description = payload.get("meaning") or ""
            symptoms = payload.get("symptoms") or ""
            causes_list = payload.get("generic_causes") or []
            checks_list = payload.get("generic_checks") or []
            doc = {
                "code": code_up,
                "description": description,
                "symptoms": symptoms,
                "common_causes": ", ".join([c for c in causes_list if c]),
                "generic_fixes": ", ".join([c for c in checks_list if c]),
            }
            # Preserve optional metadata if present
            if payload.get("system"):
                doc["system"] = payload["system"]
            if payload.get("severity"):
                doc["severity"] = payload["severity"]
            await db["obd_codes"].update_one(
                {"code": code_up},
                {"$setOnInsert": doc},
                upsert=True,
            )


if __name__ == "__main__":
    asyncio.run(seed())
