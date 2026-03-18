from __future__ import annotations
from typing import Sequence

from .interfaces import PageRangeResolver
from .models import PageRange


__all__ = ['MergeResolver',]


class MergeResolver(PageRangeResolver):
    def resolve(
        self,
        page_ranges: Sequence[PageRange]
    ) -> Sequence[PageRange]:
        if len(page_ranges) <= 1:
            return page_ranges

        result: list[PageRange] = []

        sorted_page_ranges_by_borders = sorted(
            page_ranges,
            key=lambda x: (x.begin, x.end)
        )

        i: int = 0
        ranges_len: int = len(sorted_page_ranges_by_borders)

        while i < ranges_len:
            begin: int = sorted_page_ranges_by_borders[i].begin
            end: int = sorted_page_ranges_by_borders[i].end

            j: int = i + 1

            while (j < ranges_len) and (sorted_page_ranges_by_borders[j].begin <= end + 1):
                end = max(end, sorted_page_ranges_by_borders[j].end)
                j += 1

            result.append(PageRange(begin, end))
            i = j

        return result
