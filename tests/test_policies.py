import pytest

from app.core.enums import WorkspaceRole
from app.core.permissions import can_delete_comment

VIEWER, EDITOR, OWNER = WorkspaceRole.VIEWER, WorkspaceRole.EDITOR, WorkspaceRole.OWNER


@pytest.mark.parametrize(
    ("author_id", "user_id", "role", "expected"),
    [
        (1, 1, EDITOR, True),
        (1, 1, VIEWER, True),
        (1, 2, OWNER, True),
        (1, 2, EDITOR, False),
        (1, 2, VIEWER, False),
    ],
)
def test_can_delete_comment(author_id, user_id, role, expected):
    assert (
        can_delete_comment(author_id=author_id, user_id=user_id, role=role) is expected
    )
