from sqlalchemy.orm import Session
from fastapi import HTTPException, BackgroundTasks
from typing import List
import json

from app.models.website import Website
from app.models.check_log import CheckLog
from app.schemas.website import WebsiteCreate
from app.utils.redis_client import redis_client


def get_user_websites(db: Session, user_id: int) -> List[Website]:
    return db.query(Website).filter(Website.owner_id == user_id).all()


def create_website(
        db: Session,
        website: WebsiteCreate,
        user_id: int,
        background_tasks: BackgroundTasks
) -> Website:
    # Check if URL already exists for user
    existing = db.query(Website).filter(
        Website.owner_id == user_id,
        Website.url == website.url
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Website already being monitored")

    # Create website
    db_website = Website(
        url=website.url,
        name=website.name,
        check_interval=website.check_interval,
        owner_id=user_id
    )
    db.add(db_website)
    db.commit()
    db.refresh(db_website)

    # Add to check queue
    background_tasks.add_task(
        add_to_check_queue,
        website_id=db_website.id,
        url=db_website.url,
        interval=db_website.check_interval
    )

    return db_website


def add_to_check_queue(website_id: int, url: str, interval: int):
    """Add website to Redis queue for checking"""
    task = {
        "website_id": website_id,
        "url": url,
        "interval": interval
    }
    redis_client.rpush("check_queue", json.dumps(task))


def get_website_logs(db: Session, website_id: int, user_id: int, limit: int):
    # Verify ownership
    website = db.query(Website).filter(
        Website.id == website_id,
        Website.owner_id == user_id
    ).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    return db.query(CheckLog) \
        .filter(CheckLog.website_id == website_id) \
        .order_by(CheckLog.checked_at.desc()) \
        .limit(limit) \
        .all()