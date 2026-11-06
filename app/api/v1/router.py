from fastapi import APIRouter, Depends
from app.api.v1.endpoints import tasks, auth, users
from app.dependencies import get_current_user

api_router = APIRouter()

api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["Tasks"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
