from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal
from typing import List

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{period}", response_model=List[schemas.LeaderboardOut])
def get_leaderboard(period: str, db: Session = Depends(get_db)):
    return crud.get_leaderboard(db, period)
