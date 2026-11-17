"""Tenant scoping helpers. Tenant identity is always taken from the authenticated user."""
from typing import Optional

DEFAULT_INSTITUTION_ID = "INST-DEFAULT"


def institution_id_for(user: dict) -> str:
    return str(user.get("institution_id") or DEFAULT_INSTITUTION_ID)


def scoped_filter(user: dict, query: Optional[dict] = None) -> dict:
    base = {"institution_id": institution_id_for(user)}
    if not query:
        return base
    return {"$and": [base, query]}


def tenant_document(user: dict, document: dict) -> dict:
    return {**document, "institution_id": institution_id_for(user)}
