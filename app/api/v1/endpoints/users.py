from typing import Annotated
from fastapi import APIRouter, Depends, status
from app.dependencies import CurrentUser
from app.schemas.user import ChangePassword, UserResponse, UserUpdate
from app.services.user import UserService, get_user_service

router = APIRouter()

UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.get("/me", response_model=UserResponse)
async def read_me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate, user: CurrentUser, service: UserServiceDep
) -> UserResponse:
    updated = await service.update_profile(user, data)
    return UserResponse.model_validate(updated)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePassword, user: CurrentUser, service: UserServiceDep
) -> None:
    await service.change_password(user, data)
