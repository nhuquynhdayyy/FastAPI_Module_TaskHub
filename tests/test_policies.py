import pytest

from app.core.enums import WorkspaceRole
from app.core.permissions import can_delete_comment

V, E, O = WorkspaceRole.VIEWER, WorkspaceRole.EDITOR, WorkspaceRole.OWNER


@pytest.mark.parametrize(
    ("author_id", "user_id", "role", "expected"),
    [
        (1, 1, E, True),
        (1, 1, V, True),
        (1, 2, O, True),
        (1, 2, E, False),
        (1, 2, V, False),
    ],
)
def test_can_delete_comment(author_id, user_id, role, expected):
    assert (
        can_delete_comment(author_id=author_id, user_id=user_id, role=role) is expected
    )
