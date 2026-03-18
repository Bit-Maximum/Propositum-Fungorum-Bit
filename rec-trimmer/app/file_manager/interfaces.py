from __future__ import annotations
from typing import TYPE_CHECKING, Sequence
from abc import ABC, abstractmethod


if TYPE_CHECKING:
    from .models import (
        SearchPattern,
        AnalysisResult,
        StorageFile,
        ParsedPage,
        PageRange,
        TocEntry,
        FileId
    )


__all__ = [
    'BaseIdGenerator',
    'FileRepository',
    'FileParser',
    'SimmilarityCalculator',
    'FileAnalyzer',
    'PageRangeResolver',
    'MergeTool',
]


class BaseIdGenerator(ABC):
    """Базовый класс для генераторов ID"""

    @abstractmethod
    async def generate_id(self) -> FileId:
        pass


class FileRepository(ABC):
    """Базовый класс для файловых хранилиш"""

    @abstractmethod
    async def save_file(
        self,
        file_bytes: bytes,
        metadata: StorageFile,
    ) -> None:
        pass

    @abstractmethod
    async def load_file(self, metadata: StorageFile) -> bytes:
        pass

    @abstractmethod
    async def delete_file(self, metadata: StorageFile) -> None:
        pass

    @abstractmethod
    async def file_exists(self, metadata: StorageFile) -> bool:
        pass


class FileParser(ABC):
    """Базовый класс для парсеров файлов"""

    @abstractmethod
    def extract_pages(self, file_bytes: bytes,
                      page_ranges: Sequence[PageRange]) -> Sequence[ParsedPage]:
        pass

    @abstractmethod
    def extract_toc(self, file_bytes: bytes) -> Sequence[TocEntry]:
        pass

    @abstractmethod
    def get_total_pages(self, file_bytes: bytes) -> int:
        pass


class SimmilarityCalculator(ABC):
    @abstractmethod
    def is_similar(
        self,
        first: str,
        second: str,
        similarity_threshold: float = 0.5
    ) -> bool:
        pass


class FileAnalyzer(ABC):
    """Базовый класс для анализаторов файлов"""

    def __init__(self, simm_calc: SimmilarityCalculator,
                 simm_threshold: float = 0.5) -> None:
        self._simm_calc: SimmilarityCalculator = simm_calc
        self._simm_threshold: float = simm_threshold

    @abstractmethod
    async def analyze_pages_headings_by_patterns(
        self,
        pages: Sequence[ParsedPage],
        text_patterns: Sequence[SearchPattern],
        analysis_range: PageRange,
    ) -> Sequence[AnalysisResult]:
        """
        Функция для анализа текста файла
        на предмет наличия заголовков, соответствующих паттернам
        """
        pass

    @abstractmethod
    async def analyze_toc_by_patterns(
        self,
        toc_entries: Sequence[TocEntry],
        text_patterns: Sequence[SearchPattern],
        analysis_range: PageRange,
    ) -> Sequence[AnalysisResult]:
        """
        Функция для анализа оглавления
        на предмет наличия искомых паттернов
        """
        pass


class PageRangeResolver(ABC):
    @abstractmethod
    def resolve(
        self,
        page_ranges: Sequence[PageRange]
    ) -> Sequence[PageRange]:
        pass


class MergeTool(ABC):
    @abstractmethod
    async def merge(
        self,
        file_bytes: bytes,
        page_ranges: Sequence[PageRange]
    ) -> bytes:
        pass
