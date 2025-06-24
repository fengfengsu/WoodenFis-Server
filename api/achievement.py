from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal
from typing import List

router = APIRouter(prefix="/achievements", tags=["achievements"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.AchievementOut])
def get_achievements(db: Session = Depends(get_db)):
    return crud.get_achievements(db)

@router.post("/{user_id}/unlock/{achievement_id}", response_model=schemas.UserAchievementOut)
def unlock_achievement(user_id: int, achievement_id: int, db: Session = Depends(get_db)):
    return crud.unlock_achievement(db, user_id, achievement_id)

@router.get("/{user_id}/user", response_model=List[schemas.UserAchievementOut])
def get_user_achievements(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user_achievements(db, user_id)
