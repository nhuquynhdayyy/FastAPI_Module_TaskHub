API = "/api/v1"


async def make_label(w, name="bug", headers=None, **extra):
    resp = await w["client"].post(
        f"{API}/projects/{w['project_id']}/labels",
        json={"name": name, **extra},
        headers=headers or w["editor"],
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def make_task(w, title="Task 1"):
    resp = await w["client"].post(w["url"], json={"title": title}, headers=w["editor"])
    assert resp.status_code == 201, resp.text
    return resp.json()


def labels_url(w):
    return f"{API}/projects/{w['project_id']}/labels"


async def task_labels(w, task_id):
    resp = await w["client"].get(f"{API}/tasks/{task_id}", headers=w["viewer"])
    return [lb["name"] for lb in resp.json()["labels"]]


async def test_editor_creates_label_viewer_lists_it(world):
    await make_label(world, color="#FF0000")
    resp = await world["client"].get(labels_url(world), headers=world["viewer"])
    assert resp.status_code == 200
    assert [(lb["name"], lb["color"]) for lb in resp.json()] == [("bug", "#FF0000")]


async def test_viewer_cannot_create_label(world):
    resp = await world["client"].post(
        labels_url(world), json={"name": "bug"}, headers=world["viewer"]
    )
    assert resp.status_code == 403


async def test_outsider_cannot_see_labels(world):
    resp = await world["client"].get(labels_url(world), headers=world["outsider"])
    assert resp.status_code == 404


async def test_duplicate_label_name_returns_409(world):
    await make_label(world)
    resp = await world["client"].post(
        labels_url(world), json={"name": "bug"}, headers=world["editor"]
    )
    assert resp.status_code == 409


async def test_invalid_color_returns_422(world):
    resp = await world["client"].post(
        labels_url(world),
        json={"name": "bug", "color": "red"},
        headers=world["editor"],
    )
    assert resp.status_code == 422


async def test_update_label_persists_and_rejects_null_name(world):
    label = await make_label(world)
    c, url = world["client"], f"{labels_url(world)}/{label['id']}"

    resp = await c.patch(url, json={"name": "defect"}, headers=world["editor"])
    assert resp.status_code == 200
    assert (await c.get(url, headers=world["viewer"])).json()["name"] == "defect"

    resp = await c.patch(url, json={"name": None}, headers=world["editor"])
    assert resp.status_code == 422


async def test_delete_label_persists(world):
    label = await make_label(world)
    c, url = world["client"], f"{labels_url(world)}/{label['id']}"
    assert (await c.delete(url, headers=world["editor"])).status_code == 204
    assert (await c.get(url, headers=world["editor"])).status_code == 404


async def test_assign_label_shows_on_task_and_persists(world):
    label, task = await make_label(world), await make_task(world)
    resp = await world["client"].post(
        f"{API}/tasks/{task['id']}/labels/{label['id']}", headers=world["editor"]
    )
    assert resp.status_code == 200
    assert [lb["name"] for lb in resp.json()["labels"]] == ["bug"]
    assert await task_labels(world, task["id"]) == ["bug"]


async def test_assign_same_label_twice_returns_409(world):
    label, task = await make_label(world), await make_task(world)
    url = f"{API}/tasks/{task['id']}/labels/{label['id']}"
    await world["client"].post(url, headers=world["editor"])
    resp = await world["client"].post(url, headers=world["editor"])
    assert resp.status_code == 409


async def test_viewer_cannot_assign_label(world):
    label, task = await make_label(world), await make_task(world)
    resp = await world["client"].post(
        f"{API}/tasks/{task['id']}/labels/{label['id']}", headers=world["viewer"]
    )
    assert resp.status_code == 403


async def test_cannot_assign_label_of_another_project(world):
    c = world["client"]
    other = await c.post(
        f"{API}/workspaces/{world['ws_id']}/projects",
        json={"name": "Project 2"},
        headers=world["owner"],
    )
    foreign = await c.post(
        f"{API}/projects/{other.json()['id']}/labels",
        json={"name": "foreign"},
        headers=world["owner"],
    )
    task = await make_task(world)
    resp = await c.post(
        f"{API}/tasks/{task['id']}/labels/{foreign.json()['id']}",
        headers=world["editor"],
    )
    assert resp.status_code == 404
    assert await task_labels(world, task["id"]) == []


async def test_remove_label_persists(world):
    label, task = await make_label(world), await make_task(world)
    url = f"{API}/tasks/{task['id']}/labels/{label['id']}"
    await world["client"].post(url, headers=world["editor"])
    assert (
        await world["client"].delete(url, headers=world["editor"])
    ).status_code == 204
    assert await task_labels(world, task["id"]) == []


async def test_remove_label_not_assigned_returns_404(world):
    label, task = await make_label(world), await make_task(world)
    resp = await world["client"].delete(
        f"{API}/tasks/{task['id']}/labels/{label['id']}", headers=world["editor"]
    )
    assert resp.status_code == 404


async def test_deleting_label_removes_it_from_tasks(world):
    label, task = await make_label(world), await make_task(world)
    c = world["client"]
    await c.post(
        f"{API}/tasks/{task['id']}/labels/{label['id']}", headers=world["editor"]
    )
    await c.delete(f"{labels_url(world)}/{label['id']}", headers=world["editor"])
    assert await task_labels(world, task["id"]) == []


async def test_archived_project_blocks_assign(world):
    label, task = await make_label(world), await make_task(world)
    c = world["client"]
    await c.post(
        f"{API}/workspaces/{world['ws_id']}/projects/{world['project_id']}/archive",
        headers=world["owner"],
    )
    resp = await c.post(
        f"{API}/tasks/{task['id']}/labels/{label['id']}", headers=world["editor"]
    )
    assert resp.status_code == 409
