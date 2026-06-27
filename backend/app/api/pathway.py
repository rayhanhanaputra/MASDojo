"""Pathway routes: the skill map and the next-task recommendation."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.progress import Progress
from app.models.user import User
from app.schemas.task import SkillMap, SkillNode
from app.services.pathway import PathwayEngine

router = APIRouter(prefix="/pathway", tags=["pathway"])

_engine = PathwayEngine()


@router.get("/skill-map", response_model=SkillMap)
def skill_map(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SkillMap:
    nodes, recommended = _engine.skill_map(db, user.id)

    progress = {
        p.task_id: p
        for p in db.scalars(select(Progress).where(Progress.user_id == user.id)).all()
    }

    skill_nodes = [
        SkillNode(
            id=t.id,
            title=t.title,
            module=t.module,
            domain=t.domain,
            difficulty=t.difficulty,
            prereqs=t.prereqs,
            success_type=t.success_type,
            masvs=t.masvs,
            is_reference=t.is_reference,
            state=state,
            best_score=progress[t.id].best_score if t.id in progress else 0,
            attempts=progress[t.id].attempts if t.id in progress else 0,
        )
        for t, state in nodes
    ]
    return SkillMap(
        nodes=skill_nodes,
        recommended_task_id=recommended.id if recommended else None,
    )
