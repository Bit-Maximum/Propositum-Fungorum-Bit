import aiofiles
import aiofiles.os
from pathlib import Path

from .interfaces import FileRepository
from app.core import settings
from .models import StorageFile


__all__ = ['LocalFileRepository',]


class LocalFileRepository(FileRepository):
    def __init__(self, upload_dir: Path = None):
        self._upload_dir: Path = (upload_dir
                                  or settings.STORAGE.LOCAL_UPLOAD_DIR)
        self._ensure_directory_exists(self._upload_dir)

    async def save_file(
        self,
        file_bytes: bytes,
        metadata: StorageFile,
    ) -> None:
        file_path: Path = self._get_file_path(metadata)

        try:
            async with aiofiles.open(file_path, mode='wb') as f:
                await f.write(file_bytes)
                await f.flush()
            if not await self.file_exists(metadata):
                raise IOError(f"Не удалось записать файл: {file_path}")
        except Exception as e:
            await self.delete_file(metadata)
            raise IOError(f"Файл удален. Не удалось полностью сохранить: {str(e)}") from e

    def _get_file_path(self, metadata: StorageFile) -> Path:
        return self._upload_dir / metadata.file_name

    def _ensure_directory_exists(self, dir_path: Path) -> None:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    async def load_file(self, metadata: StorageFile) -> bytes:
        if not await self.file_exists(metadata):
            raise FileNotFoundError(f"Файл {str(metadata)} уже существует")

        file_path: Path = self._get_file_path(metadata)

        try:
            async with aiofiles.open(file_path, mode='rb') as f:
                data = await f.read()
            return data
        except Exception as e:
            raise IOError(f"Неудалось загрузить файл: {e}") from e

    async def delete_file(self, metadata: StorageFile) -> None:
        file_path: Path = self._get_file_path(metadata)

        try:
            await aiofiles.os.remove(file_path)
        except Exception as e:
            raise IOError(f"Не удалось удалить файл: {e}") from e

    async def file_exists(self, metadata: StorageFile) -> bool:
        try:
            file_path: Path = self._get_file_path(metadata)
            return await aiofiles.os.path.exists(file_path)
        except Exception:
            return False
