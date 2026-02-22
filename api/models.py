from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/uptime")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    websites = relationship("Website", back_populates="owner")


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    name = Column(String)
    check_interval = Column(Integer, default=5)  # minutes
    last_checked = Column(DateTime, nullable=True)
    last_status = Column(Boolean, default=True)  # True = UP, False = DOWN
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="websites")
    checks = relationship("CheckLog", back_populates="website")


class CheckLog(Base):
    __tablename__ = "check_logs"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"))
    status_code = Column(Integer)
    response_time = Column(Integer)  # milliseconds
    is_up = Column(Boolean)
    checked_at = Column(DateTime, default=datetime.utcnow)

    website = relationship("Website", back_populates="checks")


# Create tables
Base.metadata.create_all(bind=engine)