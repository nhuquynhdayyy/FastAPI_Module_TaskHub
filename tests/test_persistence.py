API = "/api/v1"
EMAIL = "quynh@gmail.com"
PASSWORD = "password123"


async def auth_headers(client):
    await client.post(
        f"{API}/auth/register",
        json={"email": EMAIL, "full_name": "Owner", "password": PASSWORD},
    )
    resp = await client.post(
        f"{API}/auth/login", data={"username": EMAIL, "password": PASSWORD}
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def create_workspace(client, headers, name="WS1"):
    resp = await client.post(f"{API}/workspaces", json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


async def create_project(client, headers, workspace_id, name="Project 1"):
    resp = await client.post(
        f"{API}/workspaces/{workspace_id}/projects",
        json={"name": name},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_create_workspace_persists(client):
    headers = await auth_headers(client)
    ws_id = await create_workspace(client, headers)

    resp = await client.get(f"{API}/workspaces/{ws_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "WS1"


async def test_update_workspace_persists(client):
    headers = await auth_headers(client)
    ws_id = await create_workspace(client, headers)

    resp = await client.patch(
        f"{API}/workspaces/{ws_id}", json={"name": "Renamed"}, headers=headers
    )
    assert resp.status_code == 200

    resp = await client.get(f"{API}/workspaces/{ws_id}", headers=headers)
    assert resp.json()["name"] == "Renamed"


async def test_delete_workspace_persists(client):
    headers = await auth_headers(client)
    ws_id = await create_workspace(client, headers)

    resp = await client.delete(f"{API}/workspaces/{ws_id}", headers=headers)
    assert resp.status_code == 204

    resp = await client.get(f"{API}/workspaces/{ws_id}", headers=headers)
    assert resp.status_code in (403, 404)


async def test_create_project_persists(client):
    headers = await auth_headers(client)
    ws_id = await create_workspace(client, headers)
    project_id = await create_project(client, headers, ws_id)

    resp = await client.get(
        f"{API}/workspaces/{ws_id}/projects/{project_id}", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Project 1"


async def test_update_project_persists(client):
    headers = await auth_headers(client)
    ws_id = await create_workspace(client, headers)
    project_id = await create_project(client, headers, ws_id)

    resp = await client.patch(
        f"{API}/workspaces/{ws_id}/projects/{project_id}",
        json={"name": "Renamed"},
        headers=headers,
    )
    assert resp.status_code == 200

    resp = await client.get(
        f"{API}/workspaces/{ws_id}/projects/{project_id}", headers=headers
    )
    assert resp.json()["name"] == "Renamed"


async def test_archive_project_persists(client):
    headers = await auth_headers(client)
    ws_id = await create_workspace(client, headers)
    project_id = await create_project(client, headers, ws_id)

    resp = await client.post(
        f"{API}/workspaces/{ws_id}/projects/{project_id}/archive", headers=headers
    )
    assert resp.status_code == 200

    resp = await client.get(
        f"{API}/workspaces/{ws_id}/projects/{project_id}", headers=headers
    )
    assert resp.json()["status"] == "ARCHIVED"


async def test_delete_project_persists(client):
    headers = await auth_headers(client)
    ws_id = await create_workspace(client, headers)
    project_id = await create_project(client, headers, ws_id)

    resp = await client.delete(
        f"{API}/workspaces/{ws_id}/projects/{project_id}", headers=headers
    )
    assert resp.status_code == 204

    resp = await client.get(
        f"{API}/workspaces/{ws_id}/projects/{project_id}", headers=headers
    )
    assert resp.status_code == 404


async def test_patch_project_name_null_returns_422(client):
    headers = await auth_headers(client)
    ws_id = await create_workspace(client, headers)
    project_id = await create_project(client, headers, ws_id)

    resp = await client.patch(
        f"{API}/workspaces/{ws_id}/projects/{project_id}",
        json={"name": None},
        headers=headers,
    )
    assert resp.status_code == 422, resp.text


async def test_patch_project_description_null_clears_it(client):
    headers = await auth_headers(client)
    ws_id = await create_workspace(client, headers)
    project_id = await create_project(client, headers, ws_id)
    url = f"{API}/workspaces/{ws_id}/projects/{project_id}"

    resp = await client.patch(url, json={"description": "Mô tả"}, headers=headers)
    assert resp.status_code == 200, resp.text

    resp = await client.patch(url, json={"description": None}, headers=headers)
    assert resp.status_code == 200, resp.text

    resp = await client.get(url, headers=headers)
    assert resp.json()["description"] is None
