# TaskHub API

## Tech stack

FastAPI | SQLAlchemy 2.x (async) | Alembic | Pydantic v2 | PostgreSQL 16 | pytest

## Cấu trúc project

```
app/
├── api/v1/endpoints/   # Tầng API: nhận request, trả response
├── services/           # Business logic
├── repositories/       # Truy cập DB (BaseRepository[T] + CRUD async)
├── models/             # SQLAlchemy models
├── schemas/            # Pydantic schemas
├── core/               # Cấu hình, enums, constants, messages
├── db/                 # Engine, session
└── dependencies.py     # Xác thực + phân quyền (workspace, project, task, comment)
migrations/             # Alembic migrations
tests/                  # pytest
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

### 5. Chạy ứng dụng

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
| Xem task, label, danh sách task (lọc, phân trang) | ✅ | ✅ | ✅ |
| Tạo, sửa, archive project | ❌ | ✅ | ✅ |
| Tạo, sửa, xóa task; giao việc; đổi status | ❌ | ✅ | ✅ |
| Tạo, sửa, xóa label; gán, bỏ label cho task | ❌ | ✅ | ✅ |
| Thêm bình luận | ❌ | ✅ | ✅ |
| Xóa bình luận của chính mình | ❌ | ✅ | ✅ |
| Xóa bình luận của người khác | ❌ | ❌ | ✅ |
| Xóa project | ❌ | ❌ | ✅ |
| Sửa, xóa workspace | ❌ | ❌ | ✅ |
| Mời, xóa thành viên | ❌ | ❌ | ✅ |

- ADMIN toàn hệ thống vượt qua mọi kiểm tra trong workspace (tính như OWNER).
- Người không phải thành viên nhận 404; thành viên thiếu quyền nhận 403.
- Không thể xóa chủ sở hữu khỏi workspace.
- Project luôn được truy vấn kèm workspace_id.

### Phân quyền cho Task, Label, Comment

Các route `/projects/{id}/...`, `/tasks/{id}` và `/comments/{id}` không có `workspace_id` trên URL, nên quyền được suy ngược theo chuỗi:

```
comment → task → project → workspace → role
```

Toàn bộ dùng chung một hàm `resolve_workspace_access` trong `app/dependencies.py`, qua các dependency `require_workspace_role`, `require_project_role`, `require_task_role`, `require_comment_role`.

Quy tắc trả lỗi:

| Tình huống | Status | Thông báo |
|---|---|---|
| Chưa đăng nhập | 401 | |
| Không phải thành viên workspace | 404 | Đúng thông báo của tài nguyên được hỏi (`Project không tồn tại`, `Task không tồn tại`, `Không tìm thấy bình luận`) |
| Tài nguyên không tồn tại | 404 | Giống hệt trường hợp ở dòng trên, nên không lộ ID có thật |
| Thành viên thiếu quyền | 403 | |
| Project ARCHIVED, tạo hoặc sửa task | 409 | |
| Dữ liệu sai (status không hợp lệ, `limit=0`, bình luận rỗng) | 422 | |

Các quy tắc nghiệp vụ:

- Assignee phải là thành viên workspace của project.
- Label chỉ được gán cho task cùng project.
- Project ARCHIVED không cho tạo, sửa task. Bình luận và xóa vẫn được.
- Xóa task kèm xóa các bình luận của task.

### Test trên Swagger

1. `POST /api/v1/auth/register` để tạo tài khoản.
2. Bấm Authorize, nhập email và mật khẩu.
3. Tạo workspace, rồi project trong workspace đó.
4. Gọi các endpoint task, label, comment.

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
| POST | `/api/v1/projects/{project_id}/tasks` | Tạo task (`created_by` là user đăng nhập) | EDITOR+ |
| GET | `/api/v1/projects/{project_id}/tasks` | Danh sách task (lọc `status`, `priority`, `assignee_id`; phân trang `page`, `limit`) | VIEWER+ |
| GET | `/api/v1/tasks/{task_id}` | Chi tiết task | VIEWER+ |
| PATCH | `/api/v1/tasks/{task_id}` | Sửa task, giao việc, đổi status, priority, due_date | EDITOR+ |
| DELETE | `/api/v1/tasks/{task_id}` | Xóa task (kèm bình luận) | EDITOR+ |
| GET | `/api/v1/projects/{project_id}/labels` | Danh sách label của project | VIEWER+ |
| POST | `/api/v1/projects/{project_id}/labels` | Tạo label | EDITOR+ |
| PATCH | `/api/v1/projects/{project_id}/labels/{label_id}` | Sửa label | EDITOR+ |
| DELETE | `/api/v1/projects/{project_id}/labels/{label_id}` | Xóa label | EDITOR+ |
| POST | `/api/v1/tasks/{task_id}/labels/{label_id}` | Gán label cho task (cùng project) | EDITOR+ |
| DELETE | `/api/v1/tasks/{task_id}/labels/{label_id}` | Bỏ label khỏi task | EDITOR+ |
| POST | `/api/v1/tasks/{task_id}/comments` | Thêm bình luận | EDITOR+ |
| DELETE | `/api/v1/comments/{comment_id}` | Xóa bình luận | Tác giả hoặc OWNER |
| GET | `/health` | Kiểm tra trạng thái | Công khai |

### Ví dụ lọc và phân trang

```
GET /api/v1/projects/1/tasks?status=IN_PROGRESS&priority=HIGH&assignee_id=3&page=1&limit=10
```

## Test

```bash
pytest -q
```

| File | Nội dung |
|---|---|
| `tests/test_tasks_api.py` | Task: quyền, lọc, phân trang, project ARCHIVED, assignee |
| `tests/test_labels_api.py` | Label: quyền, gán label khác project |
| `tests/test_comments_api.py` | Comment: thêm, xóa theo tác giả hoặc OWNER, 404 không lộ tài nguyên |

## Migration

```bash
alembic upgrade head
```