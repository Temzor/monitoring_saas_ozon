from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.schemas.website import WebsiteCreate, WebsiteResponse
from app.services import website_service
from app.core.dependencies import get_db, get_current_user
from app.models.user import User

router = APIRouter(prefix="/websites", tags=["websites"])

@router.get("/", response_model=List[WebsiteResponse])
async def get_websites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all websites for current user"""
    return website_service.get_user_websites(db, current_user.id)

@router.post("/", response_model=WebsiteResponse)
async def create_website(
    website: WebsiteCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new website to monitor"""
    return website_service.create_website(
        db, website, current_user.id, background_tasks
    )

@router.get("/{website_id}/logs")
async def get_website_logs(
    website_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get check logs for a website"""
    return website_service.get_website_logs(db, website_id, current_user.id, limit)