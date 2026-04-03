from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models import Rule
from app.schemas.rules import RuleCreate, RuleRead, RuleUpdate

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("", response_model=list[RuleRead])
def list_rules(
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[RuleRead]:
    return db.query(Rule).order_by(Rule.priority.asc(), Rule.created_at.asc()).limit(limit).all()


@router.get("/{rule_id}", response_model=RuleRead)
def get_rule(
    rule_id: str,
    db: Session = Depends(get_db),
) -> RuleRead:
    rule = db.query(Rule).filter(Rule.id == rule_id).one_or_none()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found.")
    return rule


@router.post("", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(payload: RuleCreate, db: Session = Depends(get_db)) -> RuleRead:
    rule = Rule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=RuleRead)
def update_rule(
    rule_id: str,
    payload: RuleUpdate,
    db: Session = Depends(get_db),
) -> RuleRead:
    rule = db.query(Rule).filter(Rule.id == rule_id).one_or_none()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found.")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)

    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
