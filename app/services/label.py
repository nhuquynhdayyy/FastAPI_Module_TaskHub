from typing import Annotated

from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import ConflictException, NotFoundException
from app.db.session import DBSession
from app.dependencies import TaskAccess
from app.models import Label, Task
from app.repositories.label import LabelRepository
from app.schemas.label import LabelCreate, LabelUpdate
from app.services.task import ensure_project_active
from app.services.cache_service import CacheService, get_cache_service
from app.core.pagination import Pagination


class LabelService:
    def __init__(
        self,
        session: AsyncSession,
        repository: LabelRepository,
        cache: CacheService,
    ) -> None:
        self.session = session
        self.repository = repository
        self.cache = cache

    async def list_labels(
        self, project_id: int, pagination: Pagination
    ) -> tuple[list[Label], int]:
        return await self.repository.list_by_project(project_id, pagination)

    async def get_label(self, project_id: int, label_id: int) -> Label:
        label = await self.repository.get_in_project(project_id, label_id)
        if label is None:
            raise NotFoundException(messages.LABEL_NOT_FOUND)
        return label

    async def create_label(self, project_id: int, data: LabelCreate) -> Label:
        try:
            label = await self.repository.create(
                project_id=project_id, **data.model_dump()
            )
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictException(messages.LABEL_NAME_EXISTS) from None
        return label

    async def update_label(
        self, project_id: int, label_id: int, data: LabelUpdate
    ) -> Label:
        label = await self.get_label(project_id, label_id)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return label
        try:
            label = await self.repository.update(label, changes)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictException(messages.LABEL_NAME_EXISTS) from None
        await self.cache.invalidate_project(project_id)
        return label

    async def delete_label(self, project_id: int, label_id: int) -> None:
        label = await self.get_label(project_id, label_id)
        await self.repository.delete(label)
        await self.session.commit()
        await self.cache.invalidate_project(project_id)

    async def assign_label(self, access: TaskAccess, label_id: int) -> Task:
        ensure_project_active(access.project)
        label = await self.get_label(access.project.id, label_id)
        task = access.task
        if label in task.labels:
            raise ConflictException(messages.LABEL_ALREADY_ASSIGNED)
        task.labels.append(label)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictException(messages.LABEL_ALREADY_ASSIGNED) from None
        await self.cache.invalidate_project(access.project.id)
        return task

    async def remove_label(self, access: TaskAccess, label_id: int) -> None:
        ensure_project_active(access.project)
        label = await self.get_label(access.project.id, label_id)
        task = access.task
        if label not in task.labels:
            raise NotFoundException(messages.LABEL_NOT_ASSIGNED)
        task.labels.remove(label)
        await self.session.commit()
        await self.cache.invalidate_project(access.project.id)


def get_label_service(
    session: DBSession,
    cache: Annotated[CacheService, Depends(get_cache_service)],
) -> LabelService:
    return LabelService(session, LabelRepository(session), cache)
