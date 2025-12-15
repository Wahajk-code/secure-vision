from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models_db import User
from auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_own_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(current_user)
    db.commit()
    return None
