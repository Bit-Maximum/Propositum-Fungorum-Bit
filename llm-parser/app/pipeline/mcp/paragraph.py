from dataclasses import dataclass


@dataclass
class Paragraph:
    id: str
    text: str
    index: int