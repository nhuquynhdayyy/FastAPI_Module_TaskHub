"""set ondelete restrict for user foreign keys

Revision ID: 712f49c42b07
Revises: facd6149c586
Create Date: 2026-11-10 19:24:12.290838

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "712f49c42b07"
down_revision: Union[str, Sequence[str], None] = "facd6149c586"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("comments_author_id_fkey", "comments", type_="foreignkey")
    op.create_foreign_key(
        "comments_author_id_fkey",
        "comments",
        "users",
        ["author_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("tasks_created_by_fkey", "tasks", type_="foreignkey")
    op.create_foreign_key(
        "tasks_created_by_fkey",
        "tasks",
        "users",
        ["created_by"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("workspaces_owner_id_fkey", "workspaces", type_="foreignkey")
    op.create_foreign_key(
        "workspaces_owner_id_fkey",
        "workspaces",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("workspaces_owner_id_fkey", "workspaces", type_="foreignkey")
    op.create_foreign_key(
        "workspaces_owner_id_fkey",
        "workspaces",
        "users",
        ["owner_id"],
        ["id"],
    )

    op.drop_constraint("tasks_created_by_fkey", "tasks", type_="foreignkey")
    op.create_foreign_key(
        "tasks_created_by_fkey",
        "tasks",
        "users",
        ["created_by"],
        ["id"],
    )

    op.drop_constraint("comments_author_id_fkey", "comments", type_="foreignkey")
    op.create_foreign_key(
        "comments_author_id_fkey",
        "comments",
        "users",
        ["author_id"],
        ["id"],
    )
