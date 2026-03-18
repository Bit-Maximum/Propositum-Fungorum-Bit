import io
from typing import Sequence

import fitz

from .interfaces import MergeTool
from .models import PageRange


__all__ = ['PyMuPDFMergeTool',]


class PyMuPDFMergeTool(MergeTool):
    async def merge(
        self,
        file_bytes: bytes,
        page_ranges: Sequence[PageRange]
    ) -> bytes:
        if not page_ranges:
            return file_bytes

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        new_doc = fitz.open()

        try:
            for p_range in page_ranges:
                start_idx = p_range.begin - 1
                end_idx = p_range.end - 1

                if start_idx < 0:
                    start_idx = 0
                if end_idx > len(doc) - 1:
                    end_idx = len(doc) - 1

                if start_idx >= end_idx:
                    continue

                new_doc.insert_pdf(
                    doc,
                    from_page=start_idx,
                    to_page=end_idx
                )

            buffer = io.BytesIO()
            new_doc.save(buffer, garbage=3, deflate=True)
            return buffer.getvalue()
        finally:
            doc.close()
            new_doc.close()
