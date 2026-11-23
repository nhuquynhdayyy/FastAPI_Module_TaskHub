from fastapi import APIRouter, Depends
from app.api.v1.endpoints import (
    tasks,
    auth,
    users,
    workspaces,
    projects,
    labels,
    comments,
)
from app.dependencies import get_current_user
from app.api.v1.responses import UNAUTHORIZED

api_router = APIRouter()

api_router.include_router(
    tasks.project_router,
    prefix="/projects/{project_id}/tasks",
    tags=["Tasks"],
    responses=UNAUTHORIZED,
)
api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["Tasks"],
    responses=UNAUTHORIZED,
)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
    responses=UNAUTHORIZED,
)
api_router.include_router(
    workspaces.router,
    prefix="/workspaces",
    tags=["Workspaces"],
    responses=UNAUTHORIZED,
)
api_router.include_router(
    projects.router,
    prefix="/workspaces/{workspace_id}/projects",
    tags=["Projects"],
    responses=UNAUTHORIZED,
)
api_router.include_router(
    labels.project_router,
    prefix="/projects/{project_id}/labels",
    tags=["Labels"],
    responses=UNAUTHORIZED,
)
api_router.include_router(
    labels.task_router,
    prefix="/tasks/{task_id}/labels",
    tags=["Labels"],
    responses=UNAUTHORIZED,
)
api_router.include_router(
    comments.task_router,
    prefix="/tasks/{task_id}/comments",
    tags=["Comments"],
    responses=UNAUTHORIZED,
)
api_router.include_router(
    comments.router,
    prefix="/comments",
    tags=["Comments"],
    responses=UNAUTHORIZED,
)
