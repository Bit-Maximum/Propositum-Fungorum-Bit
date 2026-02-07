import re
from typing import List

ROMAN = ["I", "II", "III", "IV", "V"]


def expand_range(text: str) -> List[str]:
    """
    'Pipkin I-IV' -> ['Pipkin I', 'Pipkin II', 'Pipkin III', 'Pipkin IV']
    """
    match = re.search(r"(.*?)(I)\s*[-–]\s*(IV|III|II)", text)
    if not match:
        return [text.strip()]

    prefix = match.group(1).strip()
    start = match.group(2)
    end = match.group(3)

    start_i = ROMAN.index(start)
    end_i = ROMAN.index(end)

    return [f"{prefix} {r}" for r in ROMAN[start_i : end_i + 1]]