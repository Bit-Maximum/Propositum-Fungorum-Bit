from __future__ import annotations
import re
from typing import List
from .paragraph import Paragraph

SURGERY_KEYWORDS = [
    "хирургическ", "операци", "эндопротез", "остеосинтез",
    "фиксац", "остеотом", "репозиц", "пластик", "доступ"
]

def normalize_text(t: str) -> str:
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()

def segment_text(t: str) -> List[str]:
    parts = re.split(r"\n\s*\n", t)
    parts = [p.strip() for p in parts if p and p.strip()]
    return parts

def filter_paragraphs(paragraphs: List[Paragraph], *, scope: str) -> List[Paragraph]:
    if scope == "surgery_only":
        return [p for p in paragraphs if any(k in p.text.lower() for k in SURGERY_KEYWORDS)]
    if scope == "broad":
        return paragraphs
    return paragraphs