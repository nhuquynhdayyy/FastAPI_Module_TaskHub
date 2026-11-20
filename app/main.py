import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.exceptions import register_exception_handlers
from app.db.session import engine
from app.core.redis import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("TaskHub starting up")
    yield
    await redis_client.aclose()
    await engine.dispose()
    logger.info("TaskHub shutting down")


tags_metadata = [
    {"name": "Auth", "description": "Đăng ký, đăng nhập, làm mới token."},
    {"name": "Users", "description": "Thông tin người dùng."},
    {"name": "Workspaces", "description": "Quản lý workspace và thành viên."},
    {"name": "Projects", "description": "Quản lý project trong workspace."},
    {"name": "Tasks", "description": "Task theo project: lọc, phân công, gắn label."},
    {"name": "Labels", "description": "Label của project và gắn label vào task."},
    {"name": "Comments", "description": "Bình luận trên task."},
    {"name": "System", "description": "Kiểm tra tình trạng dịch vụ."},
]

app = FastAPI(
    title="TaskHub API",
    summary="API quản lý công việc theo workspace và project.",
    description=(
        "TaskHub cho phép tạo workspace, project, task, label và bình luận.\n\n"
        "**Xác thực:** gọi endpoint đăng nhập trong nhóm Auth để lấy access token, "
        "rồi bấm **Authorize** ở góc phải trang này.\n\n"
        "**Phân quyền:** mỗi thao tác phụ thuộc vai trò (RBAC) trong workspace/project."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {"status": "OK"}
