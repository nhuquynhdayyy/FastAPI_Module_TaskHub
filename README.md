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

### Test trên Swagger

1. `POST /api/v1/auth/register` để tạo tài khoản.
2. Bấm **Authorize** (góc trên bên phải), nhập email vào ô `username` và mật khẩu.
3. Gọi các endpoint cần đăng nhập, ví dụ `GET /api/v1/users/me`.

## API hiện có

| Method | Endpoint | Mô tả | Cần đăng nhập |
|---|---|---|---|
| GET | `/health` | Kiểm tra trạng thái ứng dụng | Không |
| POST | `/api/v1/auth/register` | Đăng ký tài khoản | Không |
| POST | `/api/v1/auth/login` | Đăng nhập (form-data) | Không |
| POST | `/api/v1/auth/refresh` | Cấp cặp token mới | Không (gửi refresh token) |
| POST | `/api/v1/auth/logout` | Thu hồi refresh token | Không (gửi refresh token) |
| GET | `/api/v1/users/me` | Xem hồ sơ | Có |
| PATCH | `/api/v1/users/me` | Sửa hồ sơ | Có |
| POST | `/api/v1/users/me/change-password` | Đổi mật khẩu | Có |
| POST | `/api/v1/tasks/` | Tạo task | Có |
| GET | `/api/v1/tasks/?page=1&limit=20` | Danh sách task, có phân trang | Có |
| GET | `/api/v1/tasks/{task_id}` | Chi tiết task | Có |
| PATCH | `/api/v1/tasks/{task_id}` | Cập nhật một phần | Có |
| DELETE | `/api/v1/tasks/{task_id}` | Xóa task | Có |