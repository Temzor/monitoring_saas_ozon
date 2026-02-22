import sys
import os
from pathlib import Path

# Добавляем корневую папку в путь
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import redis
import json
import os

# Теперь используем абсолютные импорты
from api import models, auth
from api.database import SessionLocal, engine
from pydantic import BaseModel

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=6379,
    decode_responses=True,
    socket_connect_timeout=5  # Добавляем таймаут
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str


class WebsiteCreate(BaseModel):
    url: str
    name: str
    check_interval: int = 5


class WebsiteResponse(BaseModel):
    id: int
    url: str
    name: str
    last_status: bool
    last_checked: datetime | None = None  # Обновленный синтаксис для Python 3.10+

    class Config:
        from_attributes = True


# Routes
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/token")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = auth.authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/websites", response_model=List[WebsiteResponse])
def get_websites(
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    websites = db.query(models.Website).filter(
        models.Website.owner_id == current_user.id
    ).all()
    return websites


@app.post("/websites")
def create_website(
        website: WebsiteCreate,
        background_tasks: BackgroundTasks,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    # Проверяем, не существует ли уже такой URL
    existing = db.query(models.Website).filter(
        models.Website.owner_id == current_user.id,
        models.Website.url == website.url
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Website already being monitored")

    db_website = models.Website(
        url=website.url,
        name=website.name,
        check_interval=website.check_interval,
        owner_id=current_user.id
    )
    db.add(db_website)
    db.commit()
    db.refresh(db_website)

    # Add to Redis queue for Go checker
    try:
        check_task = {
            "website_id": db_website.id,
            "url": db_website.url,
            "interval": db_website.check_interval
        }
        redis_client.rpush("check_queue", json.dumps(check_task))
    except redis.ConnectionError:
        print("Warning: Redis not available, check queue not updated")
        # В продакшене здесь нужно добавить повторные попытки или очередь в БД

    return {"message": "Website added", "id": db_website.id}


@app.get("/websites/{website_id}/logs")
def get_website_logs(
        website_id: int,
        limit: int = 10,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    website = db.query(models.Website).filter(
        models.Website.id == website_id,
        models.Website.owner_id == current_user.id
    ).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    logs = db.query(models.CheckLog).filter(
        models.CheckLog.website_id == website_id
    ).order_by(models.CheckLog.checked_at.desc()).limit(limit).all()

    return logs


if __name__ == "__main__":
    import uvicorn

    print("Starting Uptime Monitor API...")
    print("🚀 Server will run on http://localhost:8000")
    print("📚 API docs available at http://localhost:8000/docs")
    uvicorn.run(
        "api.main:app",  # Изменено на абсолютный путь
        host="0.0.0.0",
        port=8000,
        reload=True
    )