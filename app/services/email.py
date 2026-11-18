import asyncio
import logging

from app.core import messages

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str) -> None:
    await asyncio.sleep(0.5)
    logger.info("EMAIL to=%s | subject=%s | body=%s", to, subject, body)


async def send_task_assigned_email(to: str, task_title: str, project_id: int) -> None:
    try:
        await send_email(
            to,
            subject=messages.TASK_ASSIGNED_SUBJECT.format(title=task_title),
            body=messages.TASK_ASSIGNED_BODY.format(
                title=task_title, project_id=project_id
            ),
        )
    except Exception:
        logger.exception("Gửi email giao việc thất bại (to=%s)", to)
