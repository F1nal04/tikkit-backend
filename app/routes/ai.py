from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from ..core import database
from ..core.security import get_current_active_user
from ..schemas import Role
from .. import models
from ..services import ai

router = APIRouter(prefix="", tags=["ai"])


@router.get("/ai_request/{ticket_id}")
async def get_ticket_solution(ticket_id: UUID, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == Role.admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not ai.is_ai_available():
        raise HTTPException(
            status_code=503,
            detail="AI service is not available. OpenAI API key is not configured."
        )

    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        return ai.get_response(ticket)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
