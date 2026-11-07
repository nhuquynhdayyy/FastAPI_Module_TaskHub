from fastapi import APIRouter, Depends
from app.api.v1.endpoints import tasks, auth, users, workspaces, projects
from app.dependencies import get_current_user
from app.api.v1.params import PROTECTED_RESPONSES

api_router = APIRouter()

api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["Tasks"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(
    workspaces.router,
    prefix="/workspaces",
    tags=["Workspaces"],
    responses=PROTECTED_RESPONSES,
)
api_router.include_router(
    projects.router,
    prefix="/workspaces/{workspace_id}/projects",
    tags=["Projects"],
    responses=PROTECTED_RESPONSES,
)
