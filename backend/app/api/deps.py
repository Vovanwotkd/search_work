from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Get current user. For single-user mode, get or create default user."""
    user = db.query(User).first()

    if not user:
        # Create default user for single-user mode
        user = User()
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


def get_current_user_with_hh(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    """Get current user and require HH connection."""
    if not user.hh_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="HH.ru not connected. Please authorize first.",
        )
    return user
