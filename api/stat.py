from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal

router = APIRouter(prefix="/stats", tags=["stats"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{user_id}", response_model=schemas.UserStatOut)
def get_user_stat(user_id: int, db: Session = Depends(get_db)):
    stat = crud.get_user_stat(db, user_id)
    if not stat:
        raise HTTPException(status_code=404, detail="统计数据不存在")
    return stat
