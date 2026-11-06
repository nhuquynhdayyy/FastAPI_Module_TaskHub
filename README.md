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

## API hiện có (Task)

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/v1/tasks/` | Tạo task |
| GET | `/api/v1/tasks/?page=1&limit=20` | Danh sách, có phân trang |
| GET | `/api/v1/tasks/{task_id}` | Chi tiết task |
| PATCH | `/api/v1/tasks/{task_id}` | Cập nhật một phần |
| DELETE | `/api/v1/tasks/{task_id}` | Xóa task |