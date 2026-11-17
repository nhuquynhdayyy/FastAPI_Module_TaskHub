from app.core.enums import WorkspaceRole

ROLE_RANK: dict[WorkspaceRole, int] = {
    WorkspaceRole.VIEWER: 1,
    WorkspaceRole.EDITOR: 2,
    WorkspaceRole.OWNER: 3,
}


def has_at_least(role: WorkspaceRole, minimum: WorkspaceRole) -> bool:
    return ROLE_RANK[role] >= ROLE_RANK[minimum]


def can_delete_comment(*, author_id: int, user_id: int, role: WorkspaceRole) -> bool:
    return author_id == user_id or role == WorkspaceRole.OWNER
