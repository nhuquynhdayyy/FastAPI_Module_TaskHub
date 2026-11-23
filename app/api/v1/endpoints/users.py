from typing import Annotated
from fastapi import APIRouter, Depends, status
from app.api.v1.responses import bad_request
from app.core import messages
from app.dependencies import CurrentUser
from app.schemas.user import ChangePassword, UserResponse, UserUpdate
from app.services.user import UserService, get_user_service

router = APIRouter()

UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.get("/me", response_model=UserResponse, summary="Thông tin của tôi")
async def read_me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse, summary="Cập nhật thông tin của tôi")
async def update_me(
    data: UserUpdate, user: CurrentUser, service: UserServiceDep
) -> UserResponse:
    updated = await service.update_profile(user, data)
    return UserResponse.model_validate(updated)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Đổi mật khẩu",
    responses={
        **bad_request(
            messages.CURRENT_PASSWORD_INCORRECT,
            "Mật khẩu hiện tại không đúng, hoặc mật khẩu mới trùng mật khẩu hiện tại "
            f"(`{messages.NEW_PASSWORD_SAME_AS_CURRENT}`)",
        )
    },
)
async def change_password(
    data: ChangePassword, user: CurrentUser, service: UserServiceDep
) -> None:
    await service.change_password(user, data)
