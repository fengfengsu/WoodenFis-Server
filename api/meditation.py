from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal
from typing import List

router = APIRouter(prefix="/meditation", tags=["meditation"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{user_id}/sessions", response_model=schemas.MeditationSessionOut)
def create_session(user_id: int, session: schemas.MeditationSessionCreate, db: Session = Depends(get_db)):
    return crud.create_meditation_session(db, user_id, session)

@router.get("/{user_id}/sessions", response_model=List[schemas.MeditationSessionOut])
def get_sessions(user_id: int, db: Session = Depends(get_db)):
    return crud.get_meditation_sessions(db, user_id)
