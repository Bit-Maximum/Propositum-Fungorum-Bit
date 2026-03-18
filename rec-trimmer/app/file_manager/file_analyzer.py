from __future__ import annotations
import re
from typing import Sequence, TYPE_CHECKING
import logging

from .interfaces import FileAnalyzer, SimmilarityCalculator
from .models import AnalysisResult, AnalysisStrategy, PageRange

if TYPE_CHECKING:
    from .models import (
        SearchPattern,
        ParsedPage,
        TocEntry
    )


__all__ = ['BasicFileAnalyzer',]


logger = logging.getLogger(__name__)


class BasicFileAnalyzer(FileAnalyzer):
    _RE_HEADING_LEVEL = re.compile(r'^(\d+(?:\.\d+)*)')

    def __init__(
        self,
        simm_calc: SimmilarityCalculator,
        simm_threshold: float = 0.50
    ) -> None:
        super().__init__(simm_calc, simm_threshold)

    async def analyze_toc_by_patterns(
        self,
        toc_entries: Sequence[TocEntry],
        text_patterns: Sequence[SearchPattern],
        analysis_range: PageRange,
    ) -> Sequence[AnalysisResult]:
        filtered_toc_entries: list[TocEntry] = [
            entry
            for entry in toc_entries
            if analysis_range.begin <= entry.page <= analysis_range.end
        ]

        if not filtered_toc_entries:
            return []

        sorted_patterns_by_priority: Sequence[SearchPattern] = sorted(
            text_patterns,
            key=lambda x: x.priority,
            reverse=True
        )

        analysis_results: list[SearchPattern] = []

        for pattern in sorted_patterns_by_priority:
            page_ranges: list[PageRange] = []

            for idx, toc_entry in enumerate(filtered_toc_entries):
                if not pattern.case_sensitive:
                    pattern_text, toc_entry_title = (pattern.text.lower(),
                                                     toc_entry.title.lower())
                else:
                    pattern_text, toc_entry_title = (pattern.text,
                                                     toc_entry.title)

                logger.info("[] Сравниваем паттерн и заголовок: %s | %s", pattern_text, toc_entry_title)

                if self._simm_calc.is_similar(
                    pattern_text,
                    toc_entry_title,
                    self._simm_threshold
                ):
                    logger.info("[X] Паттерн и заголовок совпали: %s | %s", pattern_text, toc_entry_title)

                    logger.info("[] Ищем следующий заголовок в оглавлении для %s", toc_entry.title)

                    next_idx: int = self._find_next_toc_entry_idx(
                        filtered_toc_entries,
                        idx,
                        toc_entry.level
                    )

                    logger.info("[X] Следующий заголовок для %s найден: %s",
                                toc_entry.title, filtered_toc_entries[next_idx].title)

                    start_page_num: int = filtered_toc_entries[idx].page
                    end_page_num: int = filtered_toc_entries[next_idx].page

                    page_ranges.append(
                        PageRange(
                            start_page_num,
                            end_page_num,
                        )
                    )

            analysis_results.append(
                AnalysisResult(AnalysisStrategy.TOC, pattern, page_ranges)
            )

        return analysis_results

    async def analyze_pages_headings_by_patterns(
        self,
        pages: Sequence[ParsedPage],
        text_patterns: Sequence[SearchPattern],
        analysis_range: PageRange,
    ) -> Sequence[AnalysisResult]:
        filtered_pages: list[ParsedPage] = [
            page
            for page in pages
            if analysis_range.begin <= page.number <= analysis_range.end
        ]

        if not filtered_pages:
            return []

        sorted_patterns_by_priority: list[SearchPattern] = sorted(
            text_patterns,
            key=lambda x: x.priority,
            reverse=True
        )

        analysis_results: list[AnalysisResult] = []

        for pattern in sorted_patterns_by_priority:
            page_ranges: list[PageRange] = []

            for idx, page in enumerate(filtered_pages):
                matched_heading_level: int = None

                for heading in page.headings:
                    if not pattern.case_sensitive:
                        heading_text, pattern_text = heading.lower(), pattern.text.lower()
                    else:
                        heading_text, pattern_text = heading, pattern.text

                    logger.info("[] Сравниваем паттерн и заголовок: %s | %s", pattern_text, heading_text)

                    if self._simm_calc.is_similar(
                        heading_text,
                        pattern_text,
                        self._simm_threshold
                    ):
                        logger.info("[X] Паттерн и заголовок совпали: %s | %s", pattern_text, heading_text)
                        matched_heading_level = self._get_heading_level(heading)
                        break

                if matched_heading_level is not None:
                    logger.info("[] Ищем конец для %s, начало на %i стр.", heading, page.number)

                    next_idx = self._find_next_page_idx_with_same_level(
                        filtered_pages,
                        idx,
                        matched_heading_level,
                        heading
                    )

                    logger.info("[X] Найден конец для %s: %i", heading, filtered_pages[next_idx].number)

                    start_page_num = filtered_pages[idx].number
                    end_page_num = filtered_pages[next_idx].number

                    page_ranges.append(PageRange(start_page_num, end_page_num))

            analysis_results.append(
                AnalysisResult(AnalysisStrategy.FILE_TEXT, pattern, page_ranges)
            )

        return analysis_results

    def _find_next_page_idx_with_same_level(
        self,
        pages: Sequence[ParsedPage],
        current_page_idx: int,
        current_level: int,
        matched_heading: str,
    ) -> int:
        for i in range(current_page_idx, len(pages)):
            page = pages[i]

            for heading in (
                heading
                for heading in page.headings
                if heading != matched_heading
            ):
                h_level = self._get_heading_level(heading)

                if h_level <= current_level:
                    return i
        return len(pages) - 1

    def _get_heading_level(self, heading: str) -> int:
        match = self._RE_HEADING_LEVEL.match(heading.strip())

        if not match:
            return 1

        return len(match.group(1).split('.'))

    def _find_next_toc_entry_idx(
            self,
            toc_entries: Sequence[TocEntry],
            current_entry_idx: int,
            current_level: int,
    ) -> int:
        for i in range(current_entry_idx + 1, len(toc_entries)):
            if toc_entries[i].level <= current_level:
                return i
        return len(toc_entries) - 1
