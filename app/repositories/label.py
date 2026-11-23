from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination
from app.models import Label
from app.repositories.base import BaseRepository


class LabelRepository(BaseRepository[Label]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Label, session)

    async def list_by_project(
        self, project_id: int, pagination: Pagination
    ) -> tuple[list[Label], int]:
        stmt = (
            select(Label)
            .where(Label.project_id == project_id)
            .order_by(Label.name, Label.id)
        )
        return await self.paginate(stmt, pagination)

    async def get_in_project(self, project_id: int, label_id: int) -> Label | None:
        result = await self.session.scalars(
            select(Label).where(Label.id == label_id, Label.project_id == project_id)
        )
        return result.first()
