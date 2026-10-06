from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User, Block
from app.schemas.schemas import BlockRequest, BlockResponse, UserResponse
from app.repositories import repo

router = APIRouter(prefix="/blocks", tags=["Blocks"])

@router.get("", response_model=List[BlockResponse])
def list_blocks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    blocks = db.query(Block).filter(Block.blocker_id == current_user.id).all()
    results = []
    for b in blocks:
        blocked_user = repo.get_user_by_id(db, b.blocked_id)
        if blocked_user:
            results.append(BlockResponse(
                id=b.id,
                blocker_id=b.blocker_id,
                blocked_id=b.blocked_id,
                blocked_user=UserResponse.model_validate(blocked_user),
                created_at=b.created_at
            ))
    return results

@router.post("", response_model=BlockResponse)
def block_user(
    payload: BlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.blocked_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot block yourself")

    target = repo.get_user_by_id(db, payload.blocked_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    block = repo.block_user(db, blocker_id=current_user.id, blocked_id=target.id)
    return BlockResponse(
        id=block.id,
        blocker_id=block.blocker_id,
        blocked_id=block.blocked_id,
        blocked_user=UserResponse.model_validate(target),
        created_at=block.created_at
    )

@router.delete("/{user_id}")
def unblock_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = repo.unblock_user(db, blocker_id=current_user.id, blocked_id=user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block entry not found")
    return {"success": True, "message": "User unblocked"}
