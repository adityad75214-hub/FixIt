"""Explainable ticket insights: category suggestions, staff ranking and volume forecast.

These are decision-support endpoints, not autonomous decisions. The classifier is a
transparent keyword baseline (not a trained ML model); forecasts are withheld when
there is not enough tenant-local history to support them.
"""
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.database import get_database
from app.core.security import require_roles
from app.core.tenancy import institution_id_for

router = APIRouter(prefix="/advanced-insights", tags=["Advanced Insights"])

ACTIVE_STATUSES = ["open", "assigned", "in_progress", "on_hold", "reopened"]
RESOLVED_STATUSES = ["resolved", "closed"]

# Intentionally conservative keyword groups. Suggestions never overwrite user input.
CATEGORY_KEYWORDS = {
    "Network and Wi-Fi": {"wifi", "wi-fi", "internet", "network", "router", "ethernet", "connectivity", "lan"},
    "Computer and Hardware": {"computer", "laptop", "desktop", "keyboard", "mouse", "monitor", "hardware", "printer"},
    "Software and Applications": {"software", "application", "app", "install", "crash", "login", "password", "license"},
    "Electrical": {"electricity", "power", "socket", "switch", "wiring", "fan", "light", "voltage"},
    "Plumbing": {"water", "tap", "pipe", "leak", "plumbing", "drain", "washroom"},
    "Cleaning and Housekeeping": {"clean", "cleaning", "garbage", "waste", "dust", "hygiene"},
    "Furniture": {"chair", "desk", "table", "bench", "furniture", "door", "window"},
}


class ClassificationRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=5, max_length=5000)


class StaffRecommendationRequest(BaseModel):
    category: str = Field(..., min_length=2, max_length=80)
    limit: int = Field(default=5, ge=1, le=20)


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (value or "").casefold()))


@router.post("/classify")
async def classify_ticket(
    payload: ClassificationRequest,
    current_user: dict = Depends(require_roles("student", "faculty", "staff", "admin")),
):
    """Return ranked category suggestions with matched terms and confidence."""
    db = get_database()
    tenant = institution_id_for(current_user)
    text = f"{payload.title} {payload.description}".casefold()
    words = _tokens(text)
    scored = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        matched = sorted(term for term in keywords if term in text or (term.isalnum() and term in words))
        if matched:
            scored.append((len(matched), category, matched))
    scored.sort(key=lambda item: (-item[0], item[1]))

    # Prefer categories configured by this institution; don't suggest global categories.
    configured = await db.categories.find({"institution_id": tenant, "is_active": True}).to_list(None)
    configured_names = [str(item.get("name", "")).strip() for item in configured if item.get("name")]
    suggestions = []
    for count, canonical_category, matched in scored:
        aliases = _tokens(canonical_category)
        # Resolve the keyword family to an actual category configured by this tenant.
        configured_match = next(
            (name for name in configured_names
             if aliases.intersection(_tokens(name))
             or _tokens(name).intersection(set(matched))),
            None,
        )
        if configured_names and not configured_match:
            continue
        suggestions.append({
            "category": configured_match or canonical_category,
            "matched_terms": matched,
            "confidence": round(min(0.95, 0.45 + 0.15 * count), 2),
        })
    suggestions = suggestions[:3]
    return {
        "suggestions": suggestions,
        "method": "explainable_keyword_baseline",
        "is_trained_model": False,
        "message": "Suggestions are advisory. Confirm the category before submitting."
        if suggestions else "No reliable keyword match. Please choose a category manually.",
    }


@router.post("/staff-recommendations")
async def recommend_staff(
    payload: StaffRecommendationRequest,
    current_user: dict = Depends(require_roles("admin")),
):
    """Rank active, category-qualified staff using tenant-local workload and history."""
    db = get_database()
    tenant = institution_id_for(current_user)
    staff = await db.users.find({
        "institution_id": tenant, "role": "staff", "is_active": True
    }).to_list(None)
    normalized = re.sub(r"[^a-z0-9]", "", payload.category.casefold())
    ranked = []
    for person in staff:
        specs = person.get("specialization") or []
        eligible = any(
            re.sub(r"[^a-z0-9]", "", str(spec).casefold()) == normalized
            for spec in specs if isinstance(spec, str)
        )
        if not eligible:
            continue
        staff_id = str(person.get("_id"))
        ticket_filter = {"institution_id": tenant, "assigned_to.id": staff_id}
        active = await db.tickets.count_documents({
            **ticket_filter, "status": {"$in": ACTIVE_STATUSES}
        })
        resolved = await db.tickets.count_documents({
            **ticket_filter, "status": {"$in": RESOLVED_STATUSES}
        })
        total = active + resolved
        resolution_rate = round(resolved / total * 100, 1) if total else None
        # Category match is a hard eligibility gate; history is a modest tie-breaker.
        history_score = resolution_rate if resolution_rate is not None else 50.0
        workload_score = max(0.0, 100.0 - active * 12.5)
        score = round(0.65 * workload_score + 0.35 * history_score, 1)
        ranked.append({
            "staff_id": staff_id, "name": person.get("name", "Staff"),
            "specialization": specs, "active_tickets": active,
            "resolved_tickets": resolved, "resolution_rate": resolution_rate,
            "score": score,
            "reason": "Category-qualified; ranked by current workload and historical resolution rate."
        })
    ranked.sort(key=lambda item: (-item["score"], item["active_tickets"], item["name"].casefold()))
    return {
        "category": payload.category, "recommendations": ranked[:payload.limit],
        "method": "category_gate_workload_and_resolution_history",
        "message": "No active staff member is configured for this category." if not ranked else None,
    }


@router.get("/ticket-forecast")
async def forecast_ticket_volume(
    current_user: dict = Depends(require_roles("admin")),
):
    """Simple linear trend forecast from the last six complete/partial tenant months."""
    db = get_database()
    tenant = institution_id_for(current_user)
    monthly = Counter()
    async for ticket in db.tickets.find({"institution_id": tenant}):
        value = ticket.get("created_at")
        if isinstance(value, datetime):
            month = value.strftime("%Y-%m")
        else:
            try:
                month = datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%Y-%m")
            except (TypeError, ValueError):
                continue
        monthly[month] += 1

    observed = sorted(monthly.items())[-6:]
    if len(observed) < 3:
        return {
            "available": False, "forecast": None, "observations": observed,
            "required_months": 3,
            "message": "At least three months of tenant-local ticket history are required.",
        }

    # Least-squares line over sequential observed months; no external or cross-tenant data.
    values = [count for _, count in observed]
    n = len(values)
    mean_x = (n - 1) / 2
    mean_y = sum(values) / n
    denominator = sum((x - mean_x) ** 2 for x in range(n))
    slope = sum((x - mean_x) * (value - mean_y) for x, value in enumerate(values)) / denominator
    estimate = max(0, round(mean_y + slope * n))
    residuals = [value - (mean_y + slope * x) for x, value in enumerate(values)]
    mae = round(sum(abs(value) for value in residuals) / n, 2)
    return {
        "available": True,
        "forecast": {"period": "next_observed_month", "estimated_tickets": estimate, "mean_absolute_error": mae},
        "observations": [{"month": month, "tickets": count} for month, count in observed],
        "method": "six_month_linear_trend",
        "message": "Directional estimate only; accuracy depends on historical volume stability.",
    }
