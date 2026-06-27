"""BYOK settings routes: add/test, view (masked), and remove the AI key."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.settings import ApiKeyCreate, ApiKeyStatus
from app.services import key_manager

router = APIRouter(prefix="/settings", tags=["settings"])


def _status(record) -> ApiKeyStatus:
    if record is None:
        return ApiKeyStatus(configured=False)
    return ApiKeyStatus(
        configured=True,
        provider=record.provider,
        masked_key=record.masked_key,
        last_validated_at=record.last_validated_at,
    )


@router.get("/ai-key", response_model=ApiKeyStatus)
def get_ai_key(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiKeyStatus:
    return _status(key_manager.get_record(db, user))


@router.put("/ai-key", response_model=ApiKeyStatus)
def set_ai_key(
    body: ApiKeyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiKeyStatus:
    """Validate the key with a cheap provider call, then store it encrypted."""
    try:
        record = key_manager.set_key(db, user, body.provider, body.api_key)
    except key_manager.KeyValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return _status(record)


@router.delete("/ai-key", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_key(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    key_manager.remove_key(db, user)
