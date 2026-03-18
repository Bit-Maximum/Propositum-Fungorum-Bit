from dataclasses import dataclass, field
from typing import TypeAlias
from enum import StrEnum

from app.core import settings


__all__ = [
    'FileId',
    'PageRange',
    'ParsedPage',
    'TocEntry',
    'StorageFile',
    'SearchPattern',
    'AnalysisResult',
    'PipelineResult',
]


FileId: TypeAlias = str


@dataclass(frozen=True, slots=True)
class PageRange:
    begin: int
    end: int

    def __post_init__(self) -> None:
        if self.begin < 1:
            raise ValueError("Начало диапазона страниц begin - натуральное число")
        if self.end < 1:
            raise ValueError("Конец диапазона страниц end - натуральное число")
        if self.end < self.begin:
            raise ValueError("Конец диапазона страниц end должен быть больше начала begin")


@dataclass(frozen=True, slots=True)
class ParsedPage:
    number: int
    lines: list[str] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("Номер страницы должен быть >= 1, "
                             f"получено {self.number}")


@dataclass(frozen=True, slots=True)
class TocEntry:
    title: str
    page: int
    level: int = 1


@dataclass(frozen=True, slots=True)
class StorageFile:
    file_id: FileId
    extension: str

    def __post_init__(self) -> None:
        clean_extension = (self.extension[1:]
                           if self.extension.startswith('.')
                           else self.extension)

        object.__setattr__(self, 'extension', clean_extension)

        if not self.file_id:
            raise ValueError("file_id не может быть пустым")
        if not clean_extension:
            raise ValueError("extension не может быть пустым")
        if clean_extension not in settings.STORAGE.ALLOWED_EXTENSIONS:
            raise ValueError(f"Недопустимое расширение файла: {clean_extension}")

    @property
    def file_name(self) -> str:
        return f"{self.file_id}.{self.extension}"

    def __str__(self) -> str:
        return f"{self.file_id}.{self.extension}"


@dataclass(frozen=True, slots=True)
class SearchPattern:
    text: str
    case_sensitive: bool = False
    priority: int = 0  # Для сортировки паттернов

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Текст не может быть пустым или состоять из пробелов")
        if self.priority < 0:
            raise ValueError("Некорректный приоритет: "
                             f"priority={self.priority} < 0")


class AnalysisStrategy(StrEnum):
    TOC = "toc"  # По оглавлению
    FILE_TEXT = "file_text"  # По тексту


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    strategy: AnalysisStrategy
    pattern: SearchPattern
    page_ranges: list[PageRange] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PipelineResult:
    file_name: str
    page_ranges: list[PageRange] = field(default_factory=list)
    toc_analysis_result: list[AnalysisResult] = field(default_factory=list)
    pages_analysis_result: list[AnalysisResult] = field(default_factory=list)
