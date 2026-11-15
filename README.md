# TaskHub API

## Tech stack

FastAPI | SQLAlchemy 2.x (async) | Alembic | Pydantic v2 | PostgreSQL 16 | Redis 7 | pytest

## Cấu trúc project

```
app/
├── api/v1/endpoints/   # Tầng API: nhận request, trả response
├── services/           # Business logic (gồm cache_service.py, email.py)
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

### 3. Chạy Redis bằng Docker

```bash
docker run --name taskhub-redis -p 6379:6379 -d redis:7
docker exec -it taskhub-redis redis-cli ping
```

### 4. Cấu hình biến môi trường

Sao chép `.env.example` thành `.env` rồi chỉnh giá trị. Các biến liên quan Redis:

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `REDIS_URL` | (bắt buộc) | Địa chỉ Redis, ví dụ `redis://localhost:6379/0`. Thiếu thì app báo lỗi ngay khi khởi động |
| `CACHE_TTL_SECONDS` | `60` | Thời gian sống của cache, phải lớn hơn 0 |

### 5. Tạo bảng (migration)

```bash
alembic upgrade head
```

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
| GET | `/api/v1/projects/{project_id}/tasks` | Danh sách task (lọc `status`, `priority`, `assignee_id`; phân trang `page`, `limit`). Có cache Redis, xem mục Caching | VIEWER+ |
| GET | `/api/v1/tasks/{task_id}` | Chi tiết task | VIEWER+ |
| PATCH | `/api/v1/tasks/{task_id}` | Sửa task, giao việc, đổi status, priority, due_date. Giao việc cho người khác thì gửi email nền | EDITOR+ |
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

## Caching (Redis)

`GET /api/v1/projects/{project_id}/tasks` được cache trong Redis, mỗi tổ hợp bộ lọc và trang là một khóa riêng.

| Vấn đề | Quyết định | Lý do |
|---|---|---|
| Phân quyền và cache | Dependency kiểm tra quyền luôn chạy trước khi đọc cache | Cache không được lách RBAC: user bị xóa khỏi workspace vẫn nhận 404 dù cache còn dữ liệu |
| Khóa cache | `tasks:{project_id}:v{version}:{status}:{priority}:{assignee}:{page}:{limit}` | Mỗi bộ lọc một khóa |
| Invalidate | Mỗi project có bộ đếm `tasks:ver:{project_id}`; có thay đổi thì `INCR` | Khóa cũ bị bỏ rơi và tự hết hạn theo TTL. Không cần `SCAN` để xóa hàng loạt, `INCR` là nguyên tử |
| Thời điểm invalidate | Sau khi `commit()` thành công | Tránh việc request đọc xen vào lưu dữ liệu cũ dưới khóa mới |
| TTL | 60 giây (`CACHE_TTL_SECONDS`) | Lưới an toàn: lỡ quên invalidate thì dữ liệu sai tối đa 60 giây |
| Redis lỗi | Fail-open: ghi log cảnh báo, đọc thẳng từ DB | Cache chỉ là tối ưu, không được làm hỏng chức năng chính |

Các thao tác làm cache của project mất hiệu lực: tạo, sửa, xóa task; gán, bỏ label khỏi task; sửa, xóa label. Thao tác thất bại (403, 404, 409) không làm mất hiệu lực. Tạo label mới không ảnh hưởng vì label chưa gắn vào task nào.

## Email nền khi giao việc

Khi giao task cho người khác (lúc tạo hoặc sửa), người được giao nhận một email, gửi bằng `BackgroundTasks` của FastAPI nên response trả về ngay.

- Chỉ gửi khi `assignee_id` thật sự đổi, người được giao khác người đang thao tác, và đã commit thành công.
- Hàm nền chỉ nhận giá trị thuần (email, tiêu đề, id), không nhận object ORM, vì session DB đã đóng khi tác vụ chạy.
- Email hiện là email giả: hàm `send_email` trong `app/services/email.py` chỉ ghi log. Thay bằng SMTP sau này chỉ cần sửa trong hàm này.
- Lỗi khi gửi chỉ được ghi log, không ảnh hưởng response.

## Test

```bash
pytest -q
```

## Migration

```bash
alembic upgrade head
```