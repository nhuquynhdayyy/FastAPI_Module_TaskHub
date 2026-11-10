# TaskHub API

## Tech stack

FastAPI | SQLAlchemy 2.x (async) | Alembic | Pydantic v2 | PostgreSQL 16

## Cấu trúc project

```
app/
├── api/v1/endpoints/   # Tầng API: nhận request, trả response
├── services/           # Business logic
├── repositories/       # Truy cập DB (BaseRepository[T] + CRUD async)
├── models/             # SQLAlchemy models
├── schemas/            # Pydantic schemas
├── core/               # Cấu hình, enums
└── db/                 # Engine, session
migrations/             # Alembic migrations
```

## Cài đặt

### 1. Môi trường Python

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Chạy PostgreSQL bằng Docker

```bash
docker run --name taskhub-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=taskhub -p 5434:5432 -d postgres:16
```

### 3. Cấu hình biến môi trường

Sao chép `.env.example` thành `.env` rồi chỉnh giá trị


### 4. Tạo bảng (migration)

```bash
alembic upgrade head
```

### 5. Tạo dữ liệu mẫu (user, workspace, project)

```bash
python -m scripts.seed
```

Ghi hai số in ra (`DEFAULT_USER_ID`, `DEFAULT_PROJECT_ID`) vào file `.env`.

### 6. Chạy ứng dụng

```bash
uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Authentication

Dùng JWT với hai loại token:

| Token | Thời hạn | Dùng để |
|---|---|---|
| Access token | Ngắn (30 phút) | Gọi các API cần đăng nhập |
| Refresh token | Dài (7 ngày) | Xin cặp token mới; lưu `jti` trong DB để thu hồi được khi logout |

Mật khẩu được băm bằng bcrypt, không lưu dạng thô.

## Phân quyền (RBAC)

Có hai tầng role:

| Tầng | Lưu ở | Giá trị |
|---|---|---|
| Toàn hệ thống | `users.role` | `ADMIN`, `MEMBER` |
| Trong workspace | `workspace_members.role` | `OWNER`, `EDITOR`, `VIEWER` |

| Hành động | VIEWER | EDITOR | OWNER |
|---|:---:|:---:|:---:|
| Xem workspace, project, thành viên | ✅ | ✅ | ✅ |
| Tạo, sửa, archive project | ❌ | ✅ | ✅ |
| Xóa project | ❌ | ❌ | ✅ |
| Sửa, xóa workspace | ❌ | ❌ | ✅ |
| Mời, xóa thành viên | ❌ | ❌ | ✅ |

- ADMIN toàn hệ thống vượt qua mọi kiểm tra trong workspace.
- Người không phải thành viên nhận 404; thành viên thiếu quyền nhận 403.
- Không thể xóa chủ sở hữu khỏi workspace.
- Project luôn được truy vấn kèm workspace_id.

### Test trên Swagger

1. `POST /api/v1/auth/register` để tạo tài khoản.
2. Bấm Authorize, nhập email và mật khẩu.
3. Gọi các endpoint cần đăng nhập.

## API hiện có

| Method | Endpoint | Mô tả | Quyền |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Đăng ký | Công khai |
| POST | `/api/v1/auth/login` | Đăng nhập (form-data) | Công khai |
| POST | `/api/v1/auth/refresh` | Cấp cặp token mới | Công khai (gửi refresh token) |
| POST | `/api/v1/auth/logout` | Thu hồi refresh token | Công khai (gửi refresh token) |
| GET | `/api/v1/users/me` | Xem hồ sơ | Đăng nhập |
| PATCH | `/api/v1/users/me` | Sửa hồ sơ | Đăng nhập |
| POST | `/api/v1/users/me/change-password` | Đổi mật khẩu | Đăng nhập |
| POST | `/api/v1/workspaces` | Tạo workspace (người tạo thành OWNER) | Đăng nhập |
| GET | `/api/v1/workspaces` | Danh sách workspace của tôi | Đăng nhập |
| GET | `/api/v1/workspaces/{workspace_id}` | Chi tiết workspace | VIEWER+ |
| PATCH | `/api/v1/workspaces/{workspace_id}` | Sửa workspace | OWNER |
| DELETE | `/api/v1/workspaces/{workspace_id}` | Xóa workspace | OWNER |
| GET | `/api/v1/workspaces/{workspace_id}/members` | Danh sách thành viên | VIEWER+ |
| POST | `/api/v1/workspaces/{workspace_id}/members` | Mời thành viên bằng email | OWNER |
| DELETE | `/api/v1/workspaces/{workspace_id}/members/{user_id}` | Xóa thành viên | OWNER |
| POST | `/api/v1/workspaces/{workspace_id}/projects` | Tạo project | EDITOR+ |
| GET | `/api/v1/workspaces/{workspace_id}/projects` | Danh sách project (lọc `status`, phân trang) | VIEWER+ |
| GET | `/api/v1/workspaces/{workspace_id}/projects/{project_id}` | Chi tiết project | VIEWER+ |
| PATCH | `/api/v1/workspaces/{workspace_id}/projects/{project_id}` | Sửa project | EDITOR+ |
| POST | `/api/v1/workspaces/{workspace_id}/projects/{project_id}/archive` | Lưu trữ project | EDITOR+ |
| DELETE | `/api/v1/workspaces/{workspace_id}/projects/{project_id}` | Xóa project | OWNER |
| POST/GET/PATCH/DELETE | `/api/v1/tasks/...` | CRUD task (tạm thời, sẽ chuyển theo project) | Đăng nhập |
| GET | `/health` | Kiểm tra trạng thái | Công khai |
