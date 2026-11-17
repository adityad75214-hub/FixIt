import io
import csv
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from app.core.database import get_database
from app.core.security import require_roles
from app.core.audit import record_audit_log
from app.core.tenancy import institution_id_for

router = APIRouter(prefix="/reports", tags=["Reports & Export"])


def safe_csv_cell(value):
    text = "" if value is None else str(value)
    # Spreadsheet applications may ignore leading whitespace before formula markers.
    if text.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + text
    return text

@router.get("/export/csv")
async def export_tickets_csv(
    status: Optional[str] = Query(default=None, max_length=30),
    priority: Optional[str] = Query(default=None, max_length=20),
    category: Optional[str] = Query(default=None, max_length=80),
    building: Optional[str] = Query(default=None, max_length=100),
    current_user: dict = Depends(require_roles("admin", "staff"))
):
    db = get_database()
    query = {"institution_id": institution_id_for(current_user)}
    if current_user["role"] == "staff":
        query["$or"] = [
            {"assigned_to.id": current_user["id"]},
            {"assigned_to": None},
            {"assigned_to": {"$exists": False}},
        ]
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if category:
        query["category"] = category
    if building:
        query["building"] = building

    filename = f"fixit_tickets_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"

    async def csv_rows():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Ticket ID", "Title", "Category", "Priority", "Status", "Building", "Room",
            "Department", "Reported By", "Reporter Role", "Assigned Staff", "Created At",
            "SLA Deadline", "Resolved At"
        ])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        record_count = 0
        cursor = db.tickets.find(query).sort("created_at", -1)
        async for ticket in cursor:
            assigned_to = ticket.get("assigned_to") or {}
            created_by = ticket.get("created_by") or {}
            writer.writerow([safe_csv_cell(value) for value in [
                ticket.get("ticket_id", ""),
                ticket.get("title", ""),
                ticket.get("category", ""),
                str(ticket.get("priority", "")).upper(),
                str(ticket.get("status", "")).replace("_", " ").title(),
                ticket.get("building", ""),
                ticket.get("room", ""),
                ticket.get("department", ""),
                created_by.get("name", ""),
                created_by.get("role", ""),
                assigned_to.get("name", "Unassigned"),
                ticket.get("created_at", ""),
                ticket.get("sla_deadline", ""),
                ticket.get("resolved_at", ""),
            ]])
            record_count += 1
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

        await record_audit_log(
            action="REPORT_EXPORT_CSV",
            resource_type="report",
            resource_id="tickets_csv",
            actor=current_user,
            details={"record_count": record_count},
        )

    return StreamingResponse(
        csv_rows(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
