from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
import unicodedata
import re


LATIN_TO_CYR_LOOKALIKES = {
    "a": "а", "e": "е", "o": "о", "p": "р", "c": "с", "x": "х",
    "y": "у", "k": "к", "m": "м", "t": "т", "b": "в", "h": "н"
}
DASHES = r"\u2010\u2011\u2012\u2013\u2014\u2212"

def _to_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    if isinstance(x, (int, float, bool)):
        return str(x)
    return ""

def _has_cyrillic(s: str) -> bool:
    return bool(re.search(r"[а-яё]", s, flags=re.I))

def _fix_mixed_alphabet(s: str) -> str:
    if _has_cyrillic(s) and re.search(r"[A-Za-z]", s):
        out = []
        for ch in s:
            low = ch.lower()
            out.append(LATIN_TO_CYR_LOOKALIKES.get(low, ch))
        return "".join(out)
    return s

def _norm_for_display(x: Any) -> str:
    s = _to_str(x)
    s = unicodedata.normalize("NFKC", s)
    s = _fix_mixed_alphabet(s)
    s = re.sub(f"[{DASHES}]", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def _soft_name_key(x: Any) -> str:
    s = _norm_for_display(x).lower()
    s = re.sub(f"[{DASHES}]", "-", s)
    s = re.sub(r"[^\w\-]+", "", s, flags=re.U)
    s = s.replace("-", "")
    return s


def _uniq_str_list(items: List[Any]) -> List[str]:
    seen = set()
    out: List[str] = []
    for it in items or []:
        v = _norm_for_display(it)
        if not v or v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out

def _merge_params(a: Optional[List[Any]], b: Optional[List[Any]]) -> List[str]:
    return _uniq_str_list((a or []) + (b or []))


def _merge_operations(a_ops: List[Any], b_ops: List[Any]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for raw in (a_ops or []) + (b_ops or []):
        if not isinstance(raw, dict):
            continue
        name = _norm_for_display(raw.get("name", ""))
        if not name:
            continue
        soft = _soft_name_key(name)
        src = _norm_for_display(raw.get("source_text", ""))
        op_params = _merge_params(raw.get("operation_parameters"), [])
        dx_params = _merge_params(raw.get("diagnosis_parameters"), [])
        if soft not in merged:
            merged[soft] = {
                "name": name,
                "source_text": src,
                "operation_parameters": op_params,
                "diagnosis_parameters": dx_params,
            }
        else:
            merged[soft]["operation_parameters"] = _merge_params(merged[soft].get("operation_parameters"), op_params)
            merged[soft]["diagnosis_parameters"] = _merge_params(merged[soft].get("diagnosis_parameters"), dx_params)
    return list(merged.values())

def _collapse_model_op_duplicate(model: Dict[str, Any]) -> None:
    ops = model.get("operations") or []
    if len(ops) != 1:
        return
    m_name_soft = _soft_name_key(model.get("name", ""))
    op = ops[0] if isinstance(ops[0], dict) else {}
    if _soft_name_key(op.get("name", "")) == m_name_soft:
        op_params = op.get("operation_parameters") or []
        dx_params = op.get("diagnosis_parameters") or []
        if not (op_params or dx_params):
            model["operations"] = []

def _merge_models(a_models: List[Any], b_models: List[Any]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for raw in (a_models or []) + (b_models or []):
        if not isinstance(raw, dict):
            continue
        name = _norm_for_display(raw.get("name", ""))
        if not name:
            continue
        soft = _soft_name_key(name)
        src = _norm_for_display(raw.get("source_text", ""))
        ops = _merge_operations(raw.get("operations", []) or [], [])

        if soft not in merged:
            merged[soft] = {
                "name": name,
                "source_text": src,
                "operations": ops
            }
        else:
            merged[soft]["operations"] = _merge_operations(merged[soft].get("operations", []), ops)

    for mdl in merged.values():
        _collapse_model_op_duplicate(mdl)

    return list(merged.values())

def _merge_diagnoses(a_dx: List[Any], b_dx: List[Any]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for raw in (a_dx or []) + (b_dx or []):
        if not isinstance(raw, dict):
            continue
        name = _norm_for_display(raw.get("name", ""))
        if not name:
            continue
        soft = _soft_name_key(name)
        src = _norm_for_display(raw.get("source_text", ""))
        models = _merge_models(raw.get("surgical_models", []) or [], [])

        if soft not in merged:
            merged[soft] = {
                "name": name,
                "source_text": src,
                "surgical_models": models
            }
        else:
            merged[soft]["surgical_models"] = _merge_models(merged[soft].get("surgical_models", []), models)
    return list(merged.values())

def dedupe_step1_structure(step1: Dict[str, Any]) -> Dict[str, Any]:
    step1 = dict(step1 or {})
    cats_in = step1.get("diagnosis_categories", []) or []

    norm_cats: List[Dict[str, Any]] = []
    for c in cats_in:
        if not isinstance(c, dict):
            continue
        c_name = _norm_for_display(c.get("name", "") or "Без категории")
        c_src = _norm_for_display(c.get("source_text", ""))
        diagnoses = _merge_diagnoses(c.get("diagnoses", []) or [], [])
        for dx in diagnoses:
            for m in dx.get("surgical_models", []) or []:
                m["operations"] = _merge_operations(m.get("operations", []) or [], [])
                _collapse_model_op_duplicate(m)
        norm_cats.append({
            "name": c_name,
            "source_text": c_src,
            "diagnoses": diagnoses
        })

    by_soft_name: Dict[str, Dict[str, Any]] = {}
    for c in norm_cats:
        soft = _soft_name_key(c.get("name", ""))
        if soft not in by_soft_name:
            by_soft_name[soft] = c
        else:
            by_soft_name[soft]["diagnoses"] = _merge_diagnoses(by_soft_name[soft].get("diagnoses", []), c.get("diagnoses", []))

    step1["diagnosis_categories"] = list(by_soft_name.values())
    return step1