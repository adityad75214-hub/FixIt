from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from app.core.database import get_database
from app.core.security import require_roles

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_audit_logs(
    action: Optional[str] = Query(default=None, max_length=100),
    resource_type: Optional[str] = Query(default=None, max_length=80),
    actor_id: Optional[str] = Query(default=None, max_length=100),
    skip: int = Query(0, ge=0, le=100000),
    limit: int = Query(100, ge=1, le=200),
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    query = {}
    if action:
        query["action"] = action
    if resource_type:
        query["resource_type"] = resource_type
    if actor_id:
        query["actor.user_id"] = actor_id

    logs = await db.audit_logs.find(query).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    return logs
