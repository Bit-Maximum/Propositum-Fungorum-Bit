import re
from contextlib import contextmanager
from typing import Iterator, Sequence

import fitz

from .interfaces import FileParser
from .models import ParsedPage, TocEntry, PageRange


__all__ = ['PyMuPDFParser',]


class PyMuPDFParser(FileParser):
    _HEADING_FONT_SIZE_THRESHOLD = 14.0
    _HEADING_IS_BOLD_THRESHOLD = 5.0

    _TOC_SEARCH_LIMIT_PAGES = 5
    _TOC_MIN_SCORE = 3.0

    # _RE_HEADING_NUMBER = re.compile(r'^\d+(?:\.\d+)*\.?\s')
    _RE_HEADING_NUMBER = re.compile(
        r'^\d+(?:\.\d+)*\.?'  # номер раздела
        r'(?:\s(?=[А-ЯA-Z])'  # пробел + заглавная буква
        r'|'
        r'\.\s(?=[А-ЯA-Z])'   # точка + пробел + заглавная буква
        r')'
    )

    _RE_CLEAN_SPACES = re.compile(r'\s+')
    _RE_PUNCTUATION_SPACES = re.compile(r'\s+([,.:;!?])')

    # Строка с номером страницы в конце: "Заголовок .... 42"
    _RE_TOC_LINE_WITH_PAGE = re.compile(
        r'^'
        r'((?:[\d\.]+\s+)?.*?)'      # Группа 1: [номер раздела] + заголовок
        r'\s*[\.·\-–—]{2,}\s*'       # Разделитель: точки / тире
        r'(\d+)'                      # Группа 2: номер страницы
        r'\s*$'
    )

    # Строка вида "1.2.3 Заголовок 42" (без разделителя)
    _RE_TOC_LINE_NUM_TITLE_PAGE = re.compile(
        r'^'
        r'(\d+(?:\.\d+)*)'            # Группа 1: номер раздела
        r'\s+'
        r'([^0-9].+?)'                # Группа 2: заголовок (не начинается с цифры)
        r'\s+'
        r'(\d+)'                      # Группа 3: номер страницы
        r'\s*$'
    )

    # Строка — только продолжение заголовка (нет номера страницы в конце)
    _RE_CONTINUATION = re.compile(r'^[^\d].{3,}[^\d\s]$')

    _TOC_KEYWORDS = [
        "содержание", "оглавление",
    ]

    _UNNUMBERED_HEADINGS = frozenset({
        "введение",
        "заключение",
        "выводы",
        "список литературы",
        "список использованных источников",
        "приложение",
        "аннотация",
        "abstract",
        "содержание",
        "оглавление",
        "библиография",
    })

    def __init__(self) -> None:
        super().__init__()

    def extract_pages(
        self,
        file_bytes: bytes,
        page_ranges: Sequence[PageRange],
    ) -> Sequence[ParsedPage]:
        with self._open_doc(file_bytes) as doc:
            total_pages = len(doc)
            results: list[ParsedPage] = []

            pages_to_parse = set()
            for pr in page_ranges:
                start = max(1, pr.begin)
                end = min(total_pages, pr.end)
                if start <= end:
                    pages_to_parse.update(range(start, end + 1))

            for p_num in pages_to_parse:
                page_obj = doc[p_num - 1]
                results.append(self._process_page_object(page_obj, p_num))

            return results

    def extract_toc(self, file_bytes: bytes) -> Sequence[TocEntry]:
        with self._open_doc(file_bytes) as doc:
            # Попытка 1: встроенное оглавление
            toc_raw = doc.get_toc()
            if toc_raw:
                return [
                    TocEntry(level=item[0], title=item[1], page=item[2])
                    for item in toc_raw
                ]

            # Попытка 2: визуальное оглавление
            visual_entries = self._find_visual_toc(doc)
            if visual_entries:
                return [
                    TocEntry(level=self._detect_level(title),
                             title=title,
                             page=page)
                    for title, page in visual_entries
                ]

            return []

    def get_total_pages(self, file_bytes: bytes) -> int:
        with self._open_doc(file_bytes) as doc:
            return len(doc)

    @contextmanager
    def _open_doc(self, file_bytes: bytes) -> Iterator[fitz.Document]:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        try:
            yield doc
        finally:
            doc.close()

    def _detect_level(self, title: str) -> int:
        m = re.match(r'^(\d+(?:\.\d+)*)', title.strip())
        if not m:
            return 1
        return len(m.group(1).split('.'))

    def _process_page_object(self, page: fitz.Page,
                             page_number: int) -> ParsedPage:
        full_text = page.get_text("text")
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]
        headings = self._detect_headings(page)
        return ParsedPage(number=page_number, lines=lines, headings=headings)

    def _find_visual_toc(self, doc: fitz.Document) -> list[tuple[str, int]]:
        limit = min(len(doc), self._TOC_SEARCH_LIMIT_PAGES)
        toc_pages = []

        for p_num in range(limit):
            score = self._calculate_toc_score(doc[p_num])
            if score >= self._TOC_MIN_SCORE:
                toc_pages.append(p_num)

        if not toc_pages:
            return []

        return self._parse_visual_toc_pages(doc, toc_pages)

    def _calculate_toc_score(self, page: fitz.Page) -> float:
        score = 0.0
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        full_text_lower = page.get_text("text").lower()

        for keyword in self._TOC_KEYWORDS:
            if keyword in full_text_lower:
                score += 5.0
                break

        toc_lines_count = 0.0
        total_lines = 0

        for block in text_dict["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                line_text = "".join(span["text"] for span in line["spans"]).strip()
                if not line_text:
                    continue

                total_lines += 1

                if (self._RE_TOC_LINE_WITH_PAGE.match(line_text)
                   or self._RE_TOC_LINE_NUM_TITLE_PAGE.match(line_text)):
                    toc_lines_count += 1
                    score += 1.0
                elif (("..." in line_text or "---" in line_text)
                      and re.search(r'\d+\s*$', line_text)):
                    toc_lines_count += 0.5
                    score += 0.5

        if total_lines > 5:
            density = toc_lines_count / total_lines
            if density > 0.3:
                score += 3.0
            if density > 0.5:
                score += 5.0

        return score

    def _parse_visual_toc_pages(
        self,
        doc: fitz.Document,
        page_nums: list[int],
    ) -> list[tuple[str, int]]:
        entries: list[tuple[str, int]] = []
        pending_parts: list[str] = []  # многострочный заголовок переносится между страницами

        for page_num in page_nums:
            if page_num < 1 or page_num > len(doc):
                continue

            page = doc[page_num - 1]
            text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

            raw_lines: list[str] = []
            for block in text_dict["blocks"]:
                if block["type"] != 0:
                    continue
                for line in block["lines"]:
                    line_text = "".join(span["text"] for span in line["spans"]).strip()
                    if line_text:
                        raw_lines.append(line_text)

            for line_text in raw_lines:
                title, page_target = self._try_parse_toc_line(line_text)

                if title is not None and page_target is not None:
                    if pending_parts:
                        full_title = " ".join(pending_parts + [title])
                        pending_parts = []
                    else:
                        full_title = title

                    full_title = self._clean_heading_text(full_title)

                    if page_target > page_num and full_title:
                        entries.append((full_title, page_target))
                else:
                    stripped = line_text.strip()
                    if stripped and len(stripped) > 2:
                        pending_parts.append(stripped)
        return entries

    def _try_parse_toc_line(self, line_text: str) -> tuple[str, int] | tuple[None, None]:
        # Вариант 1: "Текст .... 42"
        m = self._RE_TOC_LINE_WITH_PAGE.match(line_text)
        if m:
            title = m.group(1).strip()
            try:
                return title, int(m.group(2))
            except ValueError:
                pass

        # Вариант 2: "1.2.3 Заголовок 42"
        m = self._RE_TOC_LINE_NUM_TITLE_PAGE.match(line_text)
        if m:
            section_num = m.group(1).strip()
            title_part = m.group(2).strip()
            title = f"{section_num} {title_part}"
            try:
                return title, int(m.group(3))
            except ValueError:
                pass

        return None, None

    def _detect_headings(self, page: fitz.Page) -> list[str]:
        headings: list[str] = []
        seen_headings: set[str] = set()

        try:
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

            for block in blocks:
                if block["type"] != 0:
                    continue

                for line in block.get("lines", []):
                    line_parts = []
                    
                    has_bold = False

                    for span in line.get("spans", []):
                        span_text = span["text"].strip()
                        if not span_text:
                            continue

                        line_parts.append(span_text)

                        flags = span["flags"]
                        font = span.get("font", "").lower()
                        if bool(flags & 2**4) or "bold" in font or "black" in font:
                            has_bold = True

                    if not line_parts:
                        continue

                    raw_line_text = "".join(line_parts)
                    raw_line_text = re.sub(r'^(\d+(?:\.\d+)*\.?)([^\s\d])', r'\1 \2', raw_line_text)

                    cleaned_text = self._clean_heading_text(raw_line_text)

                    if not cleaned_text or cleaned_text in seen_headings:
                        continue

                    starts_with_heading_number = bool(
                        self._RE_HEADING_NUMBER.match(cleaned_text)
                    )

                    is_numbered_heading = starts_with_heading_number and has_bold
                    is_unnumbered_heading = (
                        has_bold
                        and not starts_with_heading_number
                        and cleaned_text.lower() in self._UNNUMBERED_HEADINGS
                    )

                    if is_numbered_heading or is_unnumbered_heading:
                        headings.append(cleaned_text)
                        seen_headings.add(cleaned_text)
        except Exception:
            pass
        return headings

    def _clean_heading_text(self, text: str) -> str:
        cleaned = self._RE_CLEAN_SPACES.sub(' ', text)
        cleaned = self._RE_PUNCTUATION_SPACES.sub(r'\1', cleaned)
        # Убираем висячие разделители в конце (точки, тире)
        cleaned = re.sub(r'[\s\.·\-–—]+$', '', cleaned)
        return cleaned.strip()
