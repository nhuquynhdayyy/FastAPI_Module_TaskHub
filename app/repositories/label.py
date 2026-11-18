from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Label
from app.repositories.base import BaseRepository


class LabelRepository(BaseRepository[Label]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Label, session)

    async def list_by_project(self, project_id: int) -> list[Label]:
        result = await self.session.scalars(
            select(Label)
            .where(Label.project_id == project_id)
            .order_by(Label.name, Label.id)
        )
        return list(result.all())

    async def get_in_project(self, project_id: int, label_id: int) -> Label | None:
        result = await self.session.scalars(
            select(Label).where(Label.id == label_id, Label.project_id == project_id)
        )
        return result.first()
