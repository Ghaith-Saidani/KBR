import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User, UserRole


router = APIRouter(
    prefix="/dev",
    tags=["development"],
)


@router.post(
    "/make-admin/{user_id}",
)
def make_user_admin(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> dict:
    """
    Development-only endpoint.

    Promotes an existing user to administrator.
    This endpoint MUST NOT be exposed in production.
    """

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user.role = UserRole.ADMIN

    db.commit()
    db.refresh(user)

    return {
        "message": "User promoted to admin.",
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "is_email_verified": user.is_email_verified,
    }