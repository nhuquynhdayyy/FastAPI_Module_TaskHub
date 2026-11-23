from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.params import PaginationDep
from app.api.v1.responses import forbidden, not_found
from app.core import messages
from app.dependencies import CommentViewer, TaskEditor, TaskViewer
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.common import Page
from app.services.comment import CommentService, get_comment_service

task_router = APIRouter()

router = APIRouter()

CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]

TASK_404 = "Task không tồn tại, hoặc người dùng không thuộc workspace"
COMMENT_404 = "Bình luận không tồn tại, hoặc người dùng không thuộc workspace"


@task_router.get(
    "",
    response_model=Page[CommentResponse],
    summary="Danh sách bình luận của task (phân trang, cũ nhất trước)",
    responses={**not_found(messages.TASK_NOT_FOUND, TASK_404)},
)
async def list_comments(
    access: TaskViewer, service: CommentServiceDep, pagination: PaginationDep
) -> Page[CommentResponse]:
    comments, total = await service.list_comments(access.task.id, pagination)
    return Page[CommentResponse].build(
        [CommentResponse.model_validate(c) for c in comments], total, pagination
    )


@task_router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm bình luận vào task",
    responses={
        **not_found(messages.TASK_NOT_FOUND, TASK_404),
        **forbidden(),
    },
)
async def add_comment(
    data: CommentCreate, access: TaskEditor, service: CommentServiceDep
) -> CommentResponse:
    comment = await service.add_comment(access, data)
    return CommentResponse.model_validate(comment)


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa bình luận (tác giả hoặc OWNER)",
    responses={
        **not_found(messages.COMMENT_NOT_FOUND, COMMENT_404),
        **forbidden(
            messages.COMMENT_DELETE_FORBIDDEN,
            "Không phải tác giả bình luận hoặc owner của workspace",
        ),
    },
)
async def delete_comment(access: CommentViewer, service: CommentServiceDep) -> None:
    await service.delete_comment(access)
