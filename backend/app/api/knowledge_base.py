import re
import uuid
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.database import get_database
from app.core.security import get_current_user, require_roles
from app.core.audit import record_audit_log
from app.models.knowledge_base import KBArticleResponse, KBArticleCreate, KBArticleUpdate
from app.models.vote import ArticleVote

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base & FAQ"])

@router.get("", response_model=List[KBArticleResponse])
async def list_articles(
    category: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    query = {"is_published": True}
    if category:
        query["category"] = category
    if tag:
        query["tags"] = tag
    if search:
        query["$or"] = [
            {"title": {"$regex": re.escape(search[:100]), "$options": "i"}},
            {"content": {"$regex": re.escape(search[:100]), "$options": "i"}},
            {"tags": {"$in": [search[:100]]}}
        ]

    docs = await db.knowledge_base.find(query).sort("views", -1).to_list(50)
    if current_user.get("role") in ("staff", "admin"):
        drafts = await db.knowledge_base.find({**{k: v for k, v in query.items() if k != "is_published"}, "is_published": False}).sort("updated_at", -1).to_list(50)
        docs.extend(drafts)
        docs = list({str(d["_id"]): d for d in docs}.values())[:100]

    return [
        KBArticleResponse(
            id=str(d["_id"]),
            title=d["title"],
            category=d["category"],
            content=d["content"],
            tags=d.get("tags", []),
            is_published=d.get("is_published", True),
            views=d.get("views", 0),
            helpful_count=d.get("helpful_count", 0),
            not_helpful_count=d.get("not_helpful_count", 0),
            author_name=d.get("author_name", "IT Support"),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", "")
        )
        for d in docs
    ]

@router.get("/suggested")
async def get_suggested_articles(
    category: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    docs = await db.knowledge_base.find({
        "category": category,
        "is_published": True
    }).sort("helpful_count", -1).limit(4).to_list(4)

    return [
        {
            "id": str(d["_id"]),
            "title": d["title"],
            "summary": d["content"][:150] + "...",
            "helpful_count": d.get("helpful_count", 0)
        }
        for d in docs
    ]

@router.get("/{article_id}", response_model=KBArticleResponse)
async def get_article_detail(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    article = await db.knowledge_base.find_one({"_id": article_id})
    if not article or (not article.get("is_published", True) and current_user.get("role") not in ("staff", "admin")):
        raise HTTPException(status_code=404, detail="Article not found")

    # Increment view count
    await db.knowledge_base.update_one({"_id": article_id}, {"$inc": {"views": 1}})
    article["views"] = article.get("views", 0) + 1

    return KBArticleResponse(
        id=str(article["_id"]),
        title=article["title"],
        category=article["category"],
        content=article["content"],
        tags=article.get("tags", []),
        is_published=article.get("is_published", True),
        views=article.get("views", 0),
        helpful_count=article.get("helpful_count", 0),
        not_helpful_count=article.get("not_helpful_count", 0),
        author_name=article.get("author_name", "IT Support"),
        created_at=article.get("created_at", ""),
        updated_at=article.get("updated_at", "")
    )

@router.post("/{article_id}/vote")
async def vote_article(
    article_id: str,
    vote_in: Optional[ArticleVote] = None,
    helpful: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    article = await db.knowledge_base.find_one({"_id": article_id, "is_published": True})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    is_helpful = vote_in.helpful if vote_in is not None else (helpful if helpful is not None else True)
    vote_doc = {
        "article_id": article_id,
        "user_id": current_user["id"],
        "helpful": is_helpful,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await db.knowledge_base_votes.insert_one(vote_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="You have already voted on this article.") from None

    field = "helpful_count" if is_helpful else "not_helpful_count"
    await db.knowledge_base.update_one({"_id": article_id}, {"$inc": {field: 1}})
    updated = await db.knowledge_base.find_one({"_id": article_id})
    return {
        "message": "Thank you for your feedback!",
        "helpful_count": updated.get("helpful_count", 0),
        "not_helpful_count": updated.get("not_helpful_count", 0)
    }

@router.post("", response_model=KBArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    article_in: KBArticleCreate,
    current_user: dict = Depends(require_roles("admin", "staff"))
):
    db = get_database()
    now_iso = datetime.now(timezone.utc).isoformat()
    article_id = f"KB-{uuid.uuid4().hex[:8].upper()}"

    doc = {
        "_id": article_id,
        "title": article_in.title,
        "category": article_in.category,
        "content": article_in.content,
        "tags": article_in.tags,
        "is_published": article_in.is_published,
        "views": 0,
        "helpful_count": 0,
        "not_helpful_count": 0,
        "author_name": current_user["name"],
        "created_at": now_iso,
        "updated_at": now_iso
    }

    await db.knowledge_base.insert_one(doc)

    await record_audit_log(
        action="KB_ARTICLE_CREATED",
        resource_type="knowledge_base",
        resource_id=article_id,
        actor=current_user,
        details={"title": article_in.title, "category": article_in.category}
    )

    return KBArticleResponse(id=article_id, **doc)

@router.put("/{article_id}", response_model=KBArticleResponse)
async def update_article(
    article_id: str,
    update_in: KBArticleUpdate,
    current_user: dict = Depends(require_roles("admin", "staff"))
):
    db = get_database()
    article = await db.knowledge_base.find_one({"_id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    update_data = {k: v for k, v in update_in.model_dump().items() if v is not None}
    update_data["updated_at"] = now_iso

    await db.knowledge_base.update_one({"_id": article_id}, {"$set": update_data})
    updated = await db.knowledge_base.find_one({"_id": article_id})
    await record_audit_log(
        action="KB_ARTICLE_UPDATED",
        resource_type="knowledge_base",
        resource_id=article_id,
        actor=current_user,
        details={"changed_fields": sorted(update_data.keys())}
    )

    return KBArticleResponse(
        id=str(updated["_id"]),
        title=updated["title"],
        category=updated["category"],
        content=updated["content"],
        tags=updated.get("tags", []),
        is_published=updated.get("is_published", True),
        views=updated.get("views", 0),
        helpful_count=updated.get("helpful_count", 0),
        not_helpful_count=updated.get("not_helpful_count", 0),
        author_name=updated.get("author_name", "IT Support"),
        created_at=updated.get("created_at", ""),
        updated_at=updated.get("updated_at", "")
    )

@router.delete("/{article_id}")
async def delete_article(
    article_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    article = await db.knowledge_base.find_one({"_id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    await db.knowledge_base.delete_one({"_id": article_id})
    await db.knowledge_base_votes.delete_many({"article_id": article_id})
    await record_audit_log(
        action="KB_ARTICLE_DELETED",
        resource_type="knowledge_base",
        resource_id=article_id,
        actor=current_user,
        details={"article_id": article_id}
    )
    return {"message": "Article deleted successfully"}
