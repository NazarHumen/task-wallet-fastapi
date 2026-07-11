from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user, require_role
from src.auth.models import Role, User
from src.db.database import get_db
from src.tags import service
from src.tags.schemas import TagCreate, TagList, TagRead

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(
    data: TagCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.MANAGER)),
):
    tag = service.create_tag(db, data)
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag with this name already exists",
        )
    return tag


@router.get("", response_model=TagList)
def list_tags(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    name: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = service.list_tags(db, name=name, limit=limit, offset=offset)
    return TagList(total=total, limit=limit, offset=offset, items=items)


@router.get("/{tag_id}", response_model=TagRead)
def get_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    tag = service.get_tag(db, tag_id)
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.MANAGER)),
):
    tag = service.get_tag(db, tag_id)
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    service.delete_tag(db, tag)
