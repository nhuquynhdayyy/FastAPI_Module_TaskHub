import pytest

from app.core.enums import WorkspaceRole
from app.core.permissions import can_delete_comment


@pytest.mark.parametrize(
    ("author_id", "user_id", "role", "expected"),
    [
        (1, 1, WorkspaceRole.EDITOR, True),
        (1, 1, WorkspaceRole.VIEWER, True),
        (1, 2, WorkspaceRole.OWNER, True),
        (1, 2, WorkspaceRole.EDITOR, False),
        (1, 2, WorkspaceRole.VIEWER, False),
    ],
)
def test_can_delete_comment(author_id, user_id, role, expected):
    assert (
        can_delete_comment(author_id=author_id, user_id=user_id, role=role) is expected
    )
