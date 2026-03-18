import uuid

from .models import FileId
from .interfaces import BaseIdGenerator


__all__ = ['UUIDGenerator',]


class UUIDGenerator(BaseIdGenerator):
    async def generate_id(self) -> FileId:
        return FileId(uuid.uuid4())
