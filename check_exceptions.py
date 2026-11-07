from fastapi.testclient import TestClient

from app.core.exceptions import (
    AppException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.main import app

KINDS: dict[str, type[AppException]] = {
    "notfound": NotFoundException,
    "forbidden": ForbiddenException,
    "conflict": ConflictException,
}


def boom(kind: str) -> None:
    raise KINDS[kind]("thông báo thử")


app.add_api_route("/_boom/{kind}", boom)
client = TestClient(app)

for kind in KINDS:
    response = client.get(f"/_boom/{kind}")
    print(kind, response.status_code, response.json())
