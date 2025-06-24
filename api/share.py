from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal
from typing import List

router = APIRouter(prefix="/share", tags=["share"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/tasks", response_model=List[schemas.ShareTaskOut])
def get_share_tasks(db: Session = Depends(get_db)):
    return crud.get_share_tasks(db)

@router.post("/{user_id}/complete/{task_id}", response_model=schemas.UserShareTaskOut)
def complete_task(user_id: int, task_id: int, db: Session = Depends(get_db)):
    return crud.complete_share_task(db, user_id, task_id)

@router.get("/{user_id}/user", response_model=List[schemas.UserShareTaskOut])
def get_user_share_tasks(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user_share_tasks(db, user_id)
