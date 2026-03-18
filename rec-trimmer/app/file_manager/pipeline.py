from __future__ import annotations
from typing import Sequence, TYPE_CHECKING
from itertools import chain
import logging

from .models import (
    SearchPattern,
    PageRange,
    StorageFile,
    PipelineResult
)

if TYPE_CHECKING:
    from .interfaces import (
        FileParser,
        FileAnalyzer,
        MergeTool,
        PageRangeResolver,
        FileRepository,
        BaseIdGenerator,
    )


__all__ = ['TrimmerPipline',]


logger = logging.getLogger(__name__)


class TrimmerPipline:
    def __init__(
        self,
        id_generator: BaseIdGenerator,
        parser: FileParser,
        analyzer: FileAnalyzer,
        repository: FileRepository,
        page_resolver: PageRangeResolver,
        page_merge_tool: MergeTool,
    ) -> None:
        self._id_generator = id_generator
        self._parser = parser
        self._analyzer = analyzer
        self._repository = repository
        self._page_resolver = page_resolver
        self._page_merge_tool = page_merge_tool

    async def run(self, file: bytes,
                  patterns: Sequence[SearchPattern],
                  analysis_range: PageRange | None = None) -> PipelineResult:
        if analysis_range is None:
            analysis_range = PageRange(1, self._parser.get_total_pages(file))

        logger.warning("1. Извлечение оглавления...")
        toc_entries = self._parser.extract_toc(file)

        logger.warning("2. Получение результатов анализа оглавления...")
        toc_analysis_results = await self._analyzer.analyze_toc_by_patterns(
            toc_entries,
            patterns,
            analysis_range,
        )

        logger.warning("3. Извлечение страниц...")
        pages = self._parser.extract_pages(
            file,
            [analysis_range]
        )

        logger.warning("4. Получение результатов анализа страниц...")
        pages_analysis_results = await self._analyzer.analyze_pages_headings_by_patterns(
            pages,
            patterns,
            analysis_range,
        )

        logger.warning("5. Обработка полученных диапазонов страниц из оглавления и текста...")
        page_ranges = [
            page_range
            for analysis in chain(toc_analysis_results,
                                  pages_analysis_results)
            if analysis.page_ranges
            for page_range in analysis.page_ranges
        ]

        processed_page_ranges = self._page_resolver.resolve(page_ranges)

        logger.warning("6. Получение обрезанного файла...")
        processed_file = await self._page_merge_tool.merge(file, processed_page_ranges)

        file_metadata: StorageFile = StorageFile(
            file_id=await self._id_generator.generate_id(),
            extension='pdf'
        )

        logger.warning("7. Сохранение файла в хранилище...")
        await self._repository.save_file(processed_file, file_metadata)

        logger.warning("Файл успешно сохранен: %s", str(file_metadata.file_name))

        return PipelineResult(
            file_metadata=file_metadata,
            page_ranges=processed_page_ranges,
            toc_analysis_result=toc_analysis_results,
            pages_analysis_result=pages_analysis_results
        )
