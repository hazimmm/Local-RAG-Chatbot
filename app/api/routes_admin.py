from fastapi import APIRouter, Depends

from app.auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/ping")
def ping():
    return {"admin": True}
