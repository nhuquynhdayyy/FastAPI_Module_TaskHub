import pytest

API = "/api/v1"
PASSWORD = "password123"


async def login_as(client, email, full_name="User"):
    await client.post(
        f"{API}/auth/register",
        json={"email": email, "full_name": full_name, "password": PASSWORD},
    )
    resp = await client.post(
        f"{API}/auth/login", data={"username": email, "password": PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def world(client):
    owner = await login_as(client, "t-owner@example.com", "Owner")
    editor = await login_as(client, "t-editor@example.com", "Editor")
    viewer = await login_as(client, "t-viewer@example.com", "Viewer")
    outsider = await login_as(client, "t-out@example.com", "Outsider")

    resp = await client.post(f"{API}/workspaces", json={"name": "WS1"}, headers=owner)
    ws_id = resp.json()["id"]
    for email, role in (
        ("t-editor@example.com", "EDITOR"),
        ("t-viewer@example.com", "VIEWER"),
    ):
        r = await client.post(
            f"{API}/workspaces/{ws_id}/members",
            json={"email": email, "role": role},
            headers=owner,
        )
        assert r.status_code == 201, r.text

    resp = await client.post(
        f"{API}/workspaces/{ws_id}/projects", json={"name": "Project 1"}, headers=owner
    )
    project_id = resp.json()["id"]
    return {
        "client": client,
        "ws_id": ws_id,
        "project_id": project_id,
        "owner": owner,
        "editor": editor,
        "viewer": viewer,
        "outsider": outsider,
        "url": f"{API}/projects/{project_id}/tasks",
    }


async def make_task(w, headers=None, **extra):
    resp = await w["client"].post(
        w["url"], json={"title": "Task 1", **extra}, headers=headers or w["editor"]
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_editor_creates_task_and_it_persists(world):
    task = await make_task(world)
    resp = await world["client"].get(
        f"{API}/tasks/{task['id']}", headers=world["viewer"]
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Task 1"


async def test_created_by_is_the_logged_in_user(world):
    task = await make_task(world)
    me = await world["client"].get(f"{API}/users/me", headers=world["editor"])
    assert task["created_by"] == me.json()["id"]


async def test_viewer_cannot_create_task(world):
    resp = await world["client"].post(
        world["url"], json={"title": "Task 1"}, headers=world["viewer"]
    )
    assert resp.status_code == 403


async def test_outsider_and_missing_task_look_identical(world):
    task = await make_task(world)
    c = world["client"]
    r1 = await c.get(f"{API}/tasks/{task['id']}", headers=world["outsider"])
    r2 = await c.get(f"{API}/tasks/999999", headers=world["outsider"])
    assert r1.status_code == r2.status_code == 404
    assert r1.json() == r2.json()


async def test_update_task_persists(world):
    task = await make_task(world)
    c = world["client"]
    resp = await c.patch(
        f"{API}/tasks/{task['id']}",
        json={"status": "DONE", "priority": "HIGH"},
        headers=world["editor"],
    )
    assert resp.status_code == 200
    got = (await c.get(f"{API}/tasks/{task['id']}", headers=world["viewer"])).json()
    assert (got["status"], got["priority"]) == ("DONE", "HIGH")


async def test_patch_title_null_returns_422(world):
    task = await make_task(world)
    resp = await world["client"].patch(
        f"{API}/tasks/{task['id']}", json={"title": None}, headers=world["editor"]
    )
    assert resp.status_code == 422


async def test_patch_description_null_clears_it(world):
    task = await make_task(world, description="abc")
    c = world["client"]
    resp = await c.patch(
        f"{API}/tasks/{task['id']}", json={"description": None}, headers=world["editor"]
    )
    assert resp.status_code == 200
    got = (await c.get(f"{API}/tasks/{task['id']}", headers=world["viewer"])).json()
    assert got["description"] is None


async def test_assignee_must_be_workspace_member(world):
    c = world["client"]
    me = (await c.get(f"{API}/users/me", headers=world["outsider"])).json()
    resp = await c.post(
        world["url"],
        json={"title": "Task 1", "assignee_id": me["id"]},
        headers=world["editor"],
    )
    assert resp.status_code == 404


async def test_archived_project_blocks_create_and_update(world):
    task = await make_task(world)
    c = world["client"]
    r = await c.post(
        f"{API}/workspaces/{world['ws_id']}/projects/{world['project_id']}/archive",
        headers=world["owner"],
    )
    assert r.status_code == 200

    create = await c.post(
        world["url"], json={"title": "Task 2"}, headers=world["editor"]
    )
    update = await c.patch(
        f"{API}/tasks/{task['id']}", json={"title": "Doi ten"}, headers=world["editor"]
    )
    assert create.status_code == 409
    assert update.status_code == 409


async def test_delete_task_persists(world):
    task = await make_task(world)
    c = world["client"]
    resp = await c.delete(f"{API}/tasks/{task['id']}", headers=world["editor"])
    assert resp.status_code == 204
    resp = await c.get(f"{API}/tasks/{task['id']}", headers=world["editor"])
    assert resp.status_code == 404


async def test_list_filters_by_status(world):
    await make_task(world, title="Task A")
    done = await make_task(world, title="Task B")
    await world["client"].patch(
        f"{API}/tasks/{done['id']}", json={"status": "DONE"}, headers=world["editor"]
    )
    resp = await world["client"].get(
        world["url"], params={"status": "DONE"}, headers=world["viewer"]
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [t["title"] for t in body["items"]] == ["Task B"]
