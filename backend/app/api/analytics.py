from datetime import datetime, timezone
from typing import Dict, Any, List
from collections import defaultdict
from fastapi import APIRouter, Depends
from app.core.database import get_database
from app.core.security import require_roles
from app.services.sla_service import check_ticket_sla

router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])

@router.get("/dashboard")
async def get_dashboard_analytics(current_user: dict = Depends(require_roles("admin"))):
    db = get_database()
    # Iterate the full collection: fixed-size to_list() silently under-reports once
    # the campus exceeds the old 2,000-ticket ceiling.
    total_tickets = 0

    status_counts = defaultdict(int)
    priority_counts = defaultdict(int)
    category_counts = defaultdict(int)
    building_counts = defaultdict(int)
    department_counts = defaultdict(int)
    monthly_trends = defaultdict(lambda: {"total": 0, "resolved": 0})
    staff_stats = defaultdict(lambda: {"assigned": 0, "resolved": 0, "resolution_hours_sum": 0.0, "resolution_count": 0})

    overdue_count = 0
    total_resolution_hours = 0.0
    resolution_duration_count = 0
    resolved_count = 0
    sla_assessed_count = 0
    sla_met_count = 0

    async for t in db.tickets.find({}):
        total_tickets += 1
        st = t.get("status", "open")
        pr = t.get("priority", "medium")
        cat = t.get("category", "Other")
        bld = t.get("building", "Main Campus")
        dep = t.get("department") or "General"

        status_counts[st] += 1
        priority_counts[pr] += 1
        category_counts[cat] += 1
        building_counts[bld] += 1
        department_counts[dep] += 1

        # Monthly trend
        created_at = t.get("created_at", "")
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        if created_at:
            month_key = str(created_at)[:7]  # YYYY-MM
            monthly_trends[month_key]["total"] += 1
            if st in ["resolved", "closed"]:
                monthly_trends[month_key]["resolved"] += 1

        # Check overdue & SLA
        is_overdue, _ = check_ticket_sla(t)
        if is_overdue and st in ["open", "assigned", "in_progress", "on_hold", "reopened"]:
            overdue_count += 1

        # Resolution calculation
        if st in ["resolved", "closed"] and t.get("resolved_at"):
            resolved_count += 1
            if t.get("sla_deadline"):
                sla_assessed_count += 1
                if not is_overdue:
                    sla_met_count += 1

            try:
                t_start = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
                t_end = datetime.fromisoformat(t["resolved_at"].replace("Z", "+00:00"))
                diff_hours = (t_end - t_start).total_seconds() / 3600.0
                total_resolution_hours += diff_hours
                resolution_duration_count += 1

                # Staff tracking
                assigned_to = t.get("assigned_to")
                if assigned_to:
                    s_name = assigned_to.get("name", "Unassigned")
                    staff_stats[s_name]["resolution_hours_sum"] += diff_hours
                    staff_stats[s_name]["resolution_count"] += 1
            except Exception:
                pass

        # Staff assignment count
        assigned_to = t.get("assigned_to")
        if assigned_to:
            s_name = assigned_to.get("name", "Unassigned")
            staff_stats[s_name]["assigned"] += 1
            if st in ["resolved", "closed"]:
                staff_stats[s_name]["resolved"] += 1

    avg_resolution_hours = round(total_resolution_hours / resolution_duration_count, 1) if resolution_duration_count > 0 else 0.0
    sla_compliance_rate = round((sla_met_count / sla_assessed_count) * 100, 1) if sla_assessed_count > 0 else 100.0

    # Format trends for Recharts
    trend_data = [
        {"month": k, "submitted": v["total"], "resolved": v["resolved"]}
        for k, v in sorted(monthly_trends.items())
    ]
    if not trend_data:
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        trend_data = [{"month": current_month, "submitted": 0, "resolved": 0}]

    category_data = [{"name": k, "count": v} for k, v in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)]
    priority_data = [{"name": k.title(), "count": v} for k, v in priority_counts.items()]
    building_data = [{"name": k, "count": v} for k, v in sorted(building_counts.items(), key=lambda x: x[1], reverse=True)]
    department_data = [{"name": k, "count": v} for k, v in sorted(department_counts.items(), key=lambda x: x[1], reverse=True)[:6]]

    staff_performance_data = []
    for s_name, data in staff_stats.items():
        avg_res = round(data["resolution_hours_sum"] / data["resolution_count"], 1) if data["resolution_count"] else 0.0
        staff_performance_data.append({
            "name": s_name,
            "assigned": data["assigned"],
            "resolved": data["resolved"],
            "avg_hours": avg_res
        })

    # Feedback ratings
    feedback_pipeline = [
        {"$group": {"_id": None, "average_rating": {"$avg": "$rating"}}}
    ]
    feedback_summary = await db.feedback.aggregate(feedback_pipeline).to_list(1)
    avg_rating = round(float(feedback_summary[0]["average_rating"]), 2) if feedback_summary and feedback_summary[0].get("average_rating") is not None else 0.0

    return {
        "kpis": {
            "total_tickets": total_tickets,
            "open_tickets": status_counts["open"],
            "assigned_tickets": status_counts["assigned"],
            "in_progress_tickets": status_counts["in_progress"],
            "on_hold_tickets": status_counts["on_hold"],
            "resolved_tickets": status_counts["resolved"],
            "closed_tickets": status_counts["closed"],
            "critical_tickets": priority_counts["critical"],
            "overdue_tickets": overdue_count,
            "avg_resolution_hours": avg_resolution_hours,
            "sla_compliance_rate": sla_compliance_rate,
            "average_rating": avg_rating
        },
        "charts": {
            "monthly_trends": trend_data,
            "category_distribution": category_data,
            "priority_distribution": priority_data,
            "building_distribution": building_data,
            "department_distribution": department_data,
            "staff_performance": staff_performance_data,
            "status_distribution": [{"name": k.replace('_', ' ').title(), "count": v} for k, v in status_counts.items()]
        }
    }
