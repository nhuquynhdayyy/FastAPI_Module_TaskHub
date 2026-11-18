from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.responses import FORBIDDEN, NOT_FOUND
from app.dependencies import CommentViewer, TaskEditor
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.comment import CommentService, get_comment_service

task_router = APIRouter()

router = APIRouter()

CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]


@task_router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm bình luận vào task",
    responses={**NOT_FOUND, **FORBIDDEN},
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
    responses={**NOT_FOUND, **FORBIDDEN},
)
async def delete_comment(access: CommentViewer, service: CommentServiceDep) -> None:
    await service.delete_comment(access)
