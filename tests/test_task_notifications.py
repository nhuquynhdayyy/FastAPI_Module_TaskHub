import pytest

from app.services import email as email_module
from app.services.email import send_task_assigned_email

API = "/api/v1"


@pytest.fixture
def sent(monkeypatch):
    calls = []

    async def fake_send(to, task_title, project_id):
        calls.append({"to": to, "title": task_title, "project_id": project_id})

    monkeypatch.setattr("app.services.task.send_task_assigned_email", fake_send)
    return calls


async def user_id(w, who):
    resp = await w["client"].get(f"{API}/users/me", headers=w[who])
    return resp.json()["id"]


async def make_task(w, **extra):
    resp = await w["client"].post(
        w["url"], json={"title": "Task 1", **extra}, headers=w["editor"]
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def patch_task(w, task_id, **body):
    return await w["client"].patch(
        f"{API}/tasks/{task_id}", json=body, headers=w["editor"]
    )


async def test_assigning_to_another_user_sends_email(world, sent):
    task = await make_task(world)
    viewer_id = await user_id(world, "viewer")
    resp = await patch_task(world, task["id"], assignee_id=viewer_id)
    assert resp.status_code == 200
    assert sent == [
        {
            "to": "t-viewer@example.com",
            "title": "Task 1",
            "project_id": world["project_id"],
        }
    ]


async def test_creating_task_with_assignee_sends_email(world, sent):
    viewer_id = await user_id(world, "viewer")
    await make_task(world, assignee_id=viewer_id)
    assert [c["to"] for c in sent] == ["t-viewer@example.com"]


async def test_same_assignee_again_does_not_send_again(world, sent):
    task = await make_task(world)
    viewer_id = await user_id(world, "viewer")
    await patch_task(world, task["id"], assignee_id=viewer_id)
    await patch_task(world, task["id"], assignee_id=viewer_id)
    assert len(sent) == 1


async def test_self_assignment_sends_nothing(world, sent):
    task = await make_task(world)
    editor_id = await user_id(world, "editor")
    resp = await patch_task(world, task["id"], assignee_id=editor_id)
    assert resp.status_code == 200
    assert sent == []


async def test_editing_title_only_sends_nothing(world, sent):
    viewer_id = await user_id(world, "viewer")
    task = await make_task(world, assignee_id=viewer_id)
    sent.clear()
    await patch_task(world, task["id"], title="Tiêu đề mới")
    assert sent == []


async def test_unassigning_sends_nothing(world, sent):
    viewer_id = await user_id(world, "viewer")
    task = await make_task(world, assignee_id=viewer_id)
    sent.clear()
    resp = await patch_task(world, task["id"], assignee_id=None)
    assert resp.status_code == 200
    assert sent == []


async def test_invalid_assignee_sends_nothing(world, sent):
    task = await make_task(world)
    outsider_id = await user_id(world, "outsider")
    resp = await patch_task(world, task["id"], assignee_id=outsider_id)
    assert resp.status_code == 404
    assert sent == []


async def test_email_content(monkeypatch):
    captured = {}

    async def fake_send_email(to, subject, body):
        captured.update(to=to, subject=subject, body=body)

    monkeypatch.setattr(email_module, "send_email", fake_send_email)
    await send_task_assigned_email("a@example.com", "Sửa lỗi đăng nhập", 7)
    assert captured["to"] == "a@example.com"
    assert "Sửa lỗi đăng nhập" in captured["subject"]
    assert "7" in captured["body"]


async def test_email_failure_is_swallowed_and_logged(monkeypatch, caplog):
    async def boom(*args, **kwargs):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(email_module, "send_email", boom)
    await send_task_assigned_email("a@example.com", "T", 1)
    assert "Gửi email giao việc thất bại" in caplog.text
