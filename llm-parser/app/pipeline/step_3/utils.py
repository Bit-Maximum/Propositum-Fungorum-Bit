import uuid
import re
from typing import List


def uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def expand_range(text: str) -> List[str]:
    """
    Pipkin I-IV -> [Pipkin I, Pipkin II, Pipkin III, Pipkin IV]
    Garden I-II -> [Garden I, Garden II]
    """
    match = re.match(r"(.*?)([IVX]+)\s*-\s*([IVX]+)", text)
    if not match:
        return [text]

    prefix, start, end = match.groups()
    roman = ["I", "II", "III", "IV", "V"]
    return [f"{prefix.strip()} {r}" for r in roman[roman.index(start): roman.index(end) + 1]]