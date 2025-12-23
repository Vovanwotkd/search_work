from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.schemas.auth import AuthStatus
from app.services.hh_client import HHClient

router = APIRouter()


@router.get("/status", response_model=AuthStatus)
async def get_auth_status(
    user: User = Depends(get_current_user),
):
    """Get current authentication status."""
    return AuthStatus(
        is_authenticated=True,
        hh_connected=bool(user.hh_access_token),
        hh_user_id=user.hh_user_id,
    )


@router.get("/hh/login")
async def hh_login():
    """Redirect to HH.ru OAuth."""
    client = HHClient()
    auth_url = client.get_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/hh/callback")
async def hh_callback(
    code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Handle HH.ru OAuth callback."""
    try:
        client = HHClient()
        tokens = await client.exchange_code(code)

        # Get user info from HH
        client_with_token = HHClient(access_token=tokens["access_token"])
        hh_user = await client_with_token.get_me()

        # Update user
        user.hh_user_id = str(hh_user.get("id"))
        user.hh_access_token = tokens["access_token"]
        user.hh_refresh_token = tokens["refresh_token"]
        user.hh_token_expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
        user.updated_at = datetime.utcnow()

        db.commit()

        # Redirect to frontend
        return RedirectResponse(url="http://localhost:5173/?hh_connected=true")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with HH.ru: {str(e)}",
        )


@router.post("/logout")
async def logout(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Logout from HH.ru (clear tokens)."""
    user.hh_access_token = None
    user.hh_refresh_token = None
    user.hh_token_expires_at = None
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Logged out from HH.ru"}
