from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.post_repository import PostRepository
from app.schemas.post import PostListResponse, PostRead
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PostListResponse)
def list_posts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=9, ge=1, le=100),
    search: str | None = None,
    db: Session = Depends(get_db),
) -> PostListResponse:
    service = PostService(PostRepository(db))
    items, total = service.list_posts(page, page_size, search)
    return PostListResponse(page=page, page_size=page_size, total=total, items=items)


@router.get("/{slug}", response_model=PostRead)
def get_post(slug: str, db: Session = Depends(get_db)) -> PostRead:
    service = PostService(PostRepository(db))
    item = service.get_post_by_slug(slug)
    if not item:
        raise HTTPException(status_code=404, detail="Post not found")
    return item
