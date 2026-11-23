from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.responses import conflict, unauthorized
from app.core import messages
from app.schemas.auth import RefreshTokenRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import AuthService, get_auth_service

router = APIRouter()

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản",
    responses={**conflict(messages.EMAIL_ALREADY_REGISTERED, "Email đã được đăng ký")},
)
async def register(data: UserCreate, service: AuthServiceDep) -> UserResponse:
    user = await service.register(data)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập, nhận access token và refresh token",
    responses={**unauthorized(messages.INVALID_CREDENTIALS, "Sai email hoặc mật khẩu")},
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
) -> TokenResponse:
    return await service.login(form_data.username, form_data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Đổi refresh token lấy cặp token mới",
    responses={
        **unauthorized(
            messages.INVALID_REFRESH_TOKEN,
            "Refresh token không hợp lệ hoặc hết hạn; hoặc đã bị thu hồi "
            f"(`{messages.REFRESH_TOKEN_REVOKED}`); hoặc tài khoản không khả dụng "
            f"(`{messages.ACCOUNT_UNAVAILABLE}`)",
        )
    },
)
async def refresh(body: RefreshTokenRequest, service: AuthServiceDep) -> TokenResponse:
    return await service.refresh(body.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Đăng xuất (thu hồi refresh token)",
    description=(
        "Luôn trả 204, kể cả khi refresh token không hợp lệ hoặc đã bị thu hồi."
    ),
)
async def logout(body: RefreshTokenRequest, service: AuthServiceDep) -> None:
    await service.logout(body.refresh_token)
