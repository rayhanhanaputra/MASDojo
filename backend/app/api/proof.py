"""Public Proof-of-Pwn verification — no auth, so anyone can check a certificate."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.proof import verify_certificate
from app.schemas.proof import VerifyRequest, VerifyResponse

router = APIRouter(tags=["proof"])


@router.post("/verify", response_model=VerifyResponse)
def verify(body: VerifyRequest) -> VerifyResponse:
    """Verify a Proof-of-Pwn token was genuinely issued by this server."""
    payload = verify_certificate(body.token)
    return VerifyResponse(valid=payload is not None, payload=payload)
