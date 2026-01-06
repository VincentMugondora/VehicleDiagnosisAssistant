from sqlalchemy.orm import Session

from app.db.models import ObdCode, SessionLocal, init_db


def seed() -> None:
    init_db()
    db: Session = SessionLocal()
    try:
        seeds = [
            ObdCode(
                code="P0300",
                description="Random/multiple cylinder misfire detected",
                symptoms="Rough idle, hesitation, reduced power",
                common_causes="Spark plugs, ignition coils, vacuum leak, fuel delivery",
                generic_fixes="Inspect plugs/coils, check vacuum leaks, test fuel pressure",
            ),
            ObdCode(
                code="P0171",
                description="System too lean (Bank 1)",
                symptoms="Rough idle, misfire, poor acceleration",
                common_causes="Vacuum leak, MAF sensor, fuel pressure, exhaust leak",
                generic_fixes="Check intake leaks, clean/replace MAF, test fuel pressure",
            ),
            ObdCode(
                code="P0420",
                description="Catalyst system efficiency below threshold (Bank 1)",
                symptoms="Check engine light, possible reduced performance",
                common_causes="Catalytic converter, O2 sensors, exhaust leak",
                generic_fixes="Check for exhaust leaks, evaluate O2 sensors, assess catalyst",
            ),
            ObdCode(
                code="P0128",
                description="Coolant thermostat (coolant temperature below thermostat regulating temperature)",
                symptoms="Check engine light, engine taking long to warm up, poor heater performance",
                common_causes="Stuck open thermostat, low coolant level, faulty ECT sensor",
                generic_fixes="Replace thermostat, check/top-up coolant, test/replace ECT sensor",
            ),
            ObdCode(
                code="P0100",
                description="Mass or Volume Air Flow (MAF) circuit malfunction",
                symptoms="Rough idle, hesitation, poor fuel economy, stalling",
                common_causes="Dirty/faulty MAF sensor, wiring/connector issue, intake air leak",
                generic_fixes="Inspect/clean/replace MAF sensor, check wiring/connectors, inspect intake for leaks",
            ),
        ]
        existing = {r.code for r in db.query(ObdCode).all()}
        for s in seeds:
            if s.code not in existing:
                db.add(s)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
