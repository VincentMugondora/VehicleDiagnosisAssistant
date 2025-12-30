import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ObdCode(Base):
    __tablename__ = "obd_codes"
    code = Column(String, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    symptoms = Column(Text)
    common_causes = Column(Text)
    generic_fixes = Column(Text)


class MessageLog(Base):
    __tablename__ = "message_logs"
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, index=True)
    request_text = Column(Text)
    response_text = Column(Text)
    code = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
