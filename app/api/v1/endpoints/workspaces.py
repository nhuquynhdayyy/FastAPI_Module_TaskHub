from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from app.api.v1.params import PaginationDep
from app.api.v1.responses import FORBIDDEN, NOT_FOUND
from app.dependencies import CurrentUser, WorkspaceOwner, WorkspaceViewer
from app.schemas.common import Page
from app.schemas.workspace import (
    MemberAdd,
    MemberResponse,
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspace import WorkspaceService, get_workspace_service

router = APIRouter()

WorkspaceServiceDep = Annotated[WorkspaceService, Depends(get_workspace_service)]


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo workspace",
)
async def create_workspace(
    data: WorkspaceCreate, user: CurrentUser, service: WorkspaceServiceDep
) -> WorkspaceResponse:
    workspace = await service.create_workspace(data, user)
    return WorkspaceResponse.model_validate(workspace)


@router.get(
    "",
    response_model=Page[WorkspaceResponse],
    summary="Danh sách workspace của tôi",
)
async def list_my_workspaces(
    user: CurrentUser,
    service: WorkspaceServiceDep,
    pagination: PaginationDep,
) -> Page[WorkspaceResponse]:
    workspaces, total = await service.list_workspaces(user, pagination)
    return Page[WorkspaceResponse].build(
        [WorkspaceResponse.model_validate(w) for w in workspaces], total, pagination
    )


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Chi tiết workspace",
    responses={**NOT_FOUND},
)
async def get_workspace(access: WorkspaceViewer) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(access.workspace)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Cập nhật workspace (chỉ owner)",
    responses={**NOT_FOUND, **FORBIDDEN},
)
async def update_workspace(
    data: WorkspaceUpdate, access: WorkspaceOwner, service: WorkspaceServiceDep
) -> WorkspaceResponse:
    workspace = await service.update_workspace(access.workspace, data)
    return WorkspaceResponse.model_validate(workspace)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa workspace (chỉ owner)",
    responses={**NOT_FOUND, **FORBIDDEN},
)
async def delete_workspace(
    access: WorkspaceOwner, service: WorkspaceServiceDep
) -> None:
    await service.delete_workspace(access.workspace)


@router.get(
    "/{workspace_id}/members",
    response_model=list[MemberResponse],
    summary="Danh sách thành viên",
    responses={**NOT_FOUND},
)
async def list_members(
    access: WorkspaceViewer, service: WorkspaceServiceDep
) -> list[MemberResponse]:
    members = await service.list_members(access.workspace.id)
    return [MemberResponse.model_validate(m) for m in members]


@router.post(
    "/{workspace_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm thành viên (chỉ owner)",
    responses={**NOT_FOUND, **FORBIDDEN},
)
async def add_member(
    data: MemberAdd, access: WorkspaceOwner, service: WorkspaceServiceDep
) -> MemberResponse:
    member = await service.add_member(access.workspace.id, data)
    return MemberResponse.model_validate(member)


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa thành viên (chỉ owner)",
    responses={**NOT_FOUND, **FORBIDDEN},
)
async def remove_member(
    user_id: Annotated[int, Path(ge=1)],
    access: WorkspaceOwner,
    service: WorkspaceServiceDep,
) -> None:
    await service.remove_member(access.workspace, user_id)
