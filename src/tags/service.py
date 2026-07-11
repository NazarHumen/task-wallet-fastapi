from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.tags.models import Tag
from src.tags.schemas import TagCreate


def get_tag(db: Session, tag_id: int) -> Tag | None:
    return db.get(Tag, tag_id)


def create_tag(db: Session, data: TagCreate) -> Tag | None:
    # Returns None when the name is taken, so the router can answer 409.
    if db.scalar(select(Tag).where(Tag.name == data.name)) is not None:
        return None
    tag = Tag(name=data.name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def delete_tag(db: Session, tag: Tag) -> None:
    db.delete(tag)
    db.commit()


def list_tags(
    db: Session,
    *,
    name: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Tag], int]:
    conditions = []
    if name is not None:
        conditions.append(Tag.name.contains(name.lower()))

    total = db.scalar(select(func.count()).select_from(Tag).where(*conditions))
    items = db.scalars(
        select(Tag)
        .where(*conditions)
        .order_by(Tag.name)
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), total or 0


def resolve_tags(
    db: Session, tag_ids: list[int]
) -> tuple[list[Tag], list[int]]:
    unique_ids = set(tag_ids)
    if not unique_ids:
        return [], []
    tags = db.scalars(select(Tag).where(Tag.id.in_(unique_ids))).all()
    missing = sorted(unique_ids - {tag.id for tag in tags})
    return list(tags), missing
