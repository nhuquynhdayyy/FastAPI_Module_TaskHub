from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import messages
from app.core.enums import Environment
from app.main import app, docs_config

HTTP_METHODS = ("get", "post", "put", "patch", "delete")
API_PREFIX = "/api/v1"
MEMBERS_PATH = f"{API_PREFIX}/workspaces/{{workspace_id}}/members"
MEMBER_PATH = f"{API_PREFIX}/workspaces/{{workspace_id}}/members/{{user_id}}"


@pytest.fixture(scope="module")
def paths() -> dict[str, Any]:
    return app.openapi()["paths"]


def _codes(paths: dict[str, Any], path: str, method: str) -> set[str]:
    return set(paths[path][method]["responses"])


def test_add_member_declares_already_member_conflict(paths: dict[str, Any]) -> None:
    responses = paths[MEMBERS_PATH]["post"]["responses"]
    assert "409" in responses
    example = responses["409"]["content"]["application/json"]["example"]
    assert example == {"detail": messages.ALREADY_MEMBER}


def test_list_my_workspaces_has_no_parent_errors(paths: dict[str, Any]) -> None:
    codes = _codes(paths, f"{API_PREFIX}/workspaces", "get")
    assert "401" in codes
    assert "403" not in codes
    assert "404" not in codes


def test_users_me_has_no_parent_errors(paths: dict[str, Any]) -> None:
    codes = _codes(paths, f"{API_PREFIX}/users/me", "get")
    assert {"403", "404"}.isdisjoint(codes)


def test_remove_member_explains_both_forbidden_cases(paths: dict[str, Any]) -> None:
    description = paths[MEMBER_PATH]["delete"]["description"]
    assert messages.CANNOT_REMOVE_OWNER in description
    assert messages.INSUFFICIENT_PERMISSION in description


def test_logout_documents_always_204(paths: dict[str, Any]) -> None:
    operation = paths[f"{API_PREFIX}/auth/logout"]["post"]
    assert "204" in operation["description"]
    assert "401" not in operation["responses"]


def test_protected_routes_declare_401_with_error_model(paths: dict[str, Any]) -> None:
    missing = []
    for path, item in paths.items():
        if not path.startswith(API_PREFIX) or path.startswith(f"{API_PREFIX}/auth"):
            continue
        for method in HTTP_METHODS:
            operation = item.get(method)
            if operation is None:
                continue
            response = operation["responses"].get("401")
            if response is None or "ErrorResponse" not in str(response):
                missing.append(f"{method.upper()} {path}")
    assert missing == []


@pytest.mark.parametrize("url", ["/docs", "/redoc", "/openapi.json"])
@pytest.mark.parametrize(
    ("environment", "expected_status"),
    [
        (Environment.DEV, 200),
        (Environment.TEST, 200),
        (Environment.PROD, 404),
    ],
)
def test_docs_are_hidden_only_in_production(
    environment: Environment, expected_status: int, url: str
) -> None:
    client = TestClient(FastAPI(**docs_config(environment)))
    assert client.get(url).status_code == expected_status
