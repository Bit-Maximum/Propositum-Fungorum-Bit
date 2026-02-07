from __future__ import annotations
import hashlib
import re
from typing import Dict, List, Any, Tuple

ENTITY_KEYS = [
    "diagnosis",
    "fracture_classification",
    "surgical_method",
    "operation_type",
    "endoprosthesis_type",
    "fixation_type",
    "anatomical_location",
]

EDGE_TYPES = {
    ("diagnosis_category", "diagnosis"): "category_to_diagnosis",
    ("diagnosis", "surgical_model"): "diagnosis_to_model",
    ("surgical_model", "operation"): "model_to_operation",
}

TYPE_PRIORITY_FOR_PARAMS = [
    "operation_type",
    "surgical_method",
    "endoprosthesis_type",
    "fixation_type",
    "anatomical_location",
    "diagnosis",
    "fracture_classification",
]

CONDITION_CUES = [
    ("противопоказано", "forbid"),
    ("не рекомендуется", "forbid"),
    ("не показано", "forbid"),
    ("рекомендуется", "prefer"),
    ("предпочтительно", "prefer"),
    ("показано", "allow"),
    ("в случае", "unspecified"),
    ("если", "unspecified"),
    ("при ", "unspecified"),
]

def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:16]

def find_paragraph_id_by_source_text(paragraphs: List[Dict[str, Any]], source_text: str) -> str | None:
    if not source_text:
        return None
    for p in paragraphs:
        if source_text in p["text"]:
            return p["id"]
    return None

def extract_conditions(text: str) -> List[Tuple[str, str]]:
    spans = []
    for cue, _ in CONDITION_CUES:
        for m in re.finditer(re.escape(cue), text, flags=re.IGNORECASE):
            start = m.start()
            tail = text[start:]
            end_rel = re.search(r"[.;\n]", tail)
            end = start + (end_rel.start() if end_rel else len(tail))
            span = text[start:end].strip()
            spans.append((cue.lower(), span))
    uniq = {}
    for cue, t in spans:
        uniq[t] = cue
    return [(c, t) for t, c in uniq.items()]

def cue_to_effect(cue: str) -> str:
    for k, eff in CONDITION_CUES:
        if cue == k:
            return eff
    return "unspecified"

def index_entities_by_paragraph(paragraphs: List[Dict[str, Any]], step2: Dict[str, List[str]]) -> Dict[str, Dict[str, List[str]]]:
    idx = {p["id"]: {k: [] for k in ENTITY_KEYS} for p in paragraphs}
    for etype in ENTITY_KEYS:
        for val in step2.get(etype, []):
            for p in paragraphs:
                if val and val in p["text"]:
                    idx[p["id"]][etype].append(val)
    for pid in idx:
        for k in ENTITY_KEYS:
            idx[pid][k] = sorted(set(idx[pid][k]))
    return idx

def classify_params_against_entities(params: List[str], pid: str, ent_index: Dict[str, Dict[str, List[str]]]):
    typed = {k: [] for k in ENTITY_KEYS}
    untyped = []
    for prm in params:
        matched = None
        for t in TYPE_PRIORITY_FOR_PARAMS:
            for e in ent_index.get(pid, {}).get(t, []):
                if e == prm or e in prm or (prm and prm in e):
                    typed[t].append(e)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            untyped.append(prm)
    for k in typed:
        typed[k] = sorted(set(typed[k]))
    return typed, untyped

def build_step3_linking(paragraphs: List[Dict[str, Any]], step1: Dict[str, Any], step2: Dict[str, List[str]]) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    categories = step1.get("diagnosis_categories", []) or []

    node_params_map: Dict[str, Dict[str, List[str]]] = {}

    def add_node(node_type: str, name: str, source_text: str) -> str:
        pid = find_paragraph_id_by_source_text(paragraphs, source_text) or "unknown"
        uid = md5(f"{node_type}|{name}|{pid}")
        if not any(n["uid"] == uid for n in nodes):
            nodes.append({
                "uid": uid,
                "type": node_type,
                "name": name,
                "source_id": pid,
                "source_text": source_text
            })
        node_params_map.setdefault(uid, {"operation_parameters": [], "diagnosis_parameters": []})
        return uid

    for cat in categories:
        cat_uid = add_node("diagnosis_category", cat.get("name", ""), cat.get("source_text", ""))
        for dx in cat.get("diagnoses", []) or []:
            dx_uid = add_node("diagnosis", dx.get("name", ""), dx.get("source_text", ""))
            edges.append({"parent": cat_uid, "child": dx_uid, "type": EDGE_TYPES[("diagnosis_category", "diagnosis")]})
            for model in dx.get("surgical_models", []) or []:
                sm_uid = add_node("surgical_model", model.get("name", ""), model.get("source_text", ""))
                edges.append({"parent": dx_uid, "child": sm_uid, "type": EDGE_TYPES[("diagnosis", "surgical_model")]})
                for op in model.get("operations", []) or []:
                    op_uid = add_node("operation", op.get("name", ""), op.get("source_text", ""))
                    edges.append({"parent": sm_uid, "child": op_uid, "type": EDGE_TYPES[("surgical_model", "operation")]})
                    node_params_map[op_uid]["operation_parameters"].extend(op.get("operation_parameters", []) or [])
                    node_params_map[op_uid]["diagnosis_parameters"].extend(op.get("diagnosis_parameters", []) or [])

    ent_index = index_entities_by_paragraph(paragraphs, step2)
    annotations: List[Dict[str, Any]] = []
    for n in nodes:
        pid = n["source_id"]
        ents_here = ent_index.get(pid, {k: [] for k in ENTITY_KEYS})
        params = node_params_map.get(n["uid"], {"operation_parameters": [], "diagnosis_parameters": []})
        params_all = list(params.get("operation_parameters", [])) + list(params.get("diagnosis_parameters", []))
        typed_from_params, untyped = classify_params_against_entities(params_all, pid, ent_index)
        merged = {k: sorted(set((ents_here.get(k, []) or []) + (typed_from_params.get(k, []) or []))) for k in ENTITY_KEYS}
        annotations.append({
            "node_uid": n["uid"],
            "entities": merged,
            "untyped_parameters": untyped,
            "conditions": []
        })
    # Привязка условий к «самому нижнему» узлу в параграфе
    by_pid: Dict[str, List[Dict[str, Any]]] = {}
    for n in nodes:
        by_pid.setdefault(n["source_id"], []).append(n)
    order = {"operation": 4, "surgical_model": 3, "diagnosis": 2, "diagnosis_category": 1}
    for pid, ns in by_pid.items():
        ns.sort(key=lambda x: order[x["type"]], reverse=True)
        ptext = next((p["text"] for p in paragraphs if p["id"] == pid), "")
        conds = extract_conditions(ptext)
        if ns and conds:
            target_uid = ns[0]["uid"]
            ann = next(a for a in annotations if a["node_uid"] == target_uid)
            for cue, span in conds:
                ann["conditions"].append({
                    "text": span,
                    "source_id": pid,
                    "cue": cue,
                    "effect": cue_to_effect(cue)
                })

    return {
        "nodes": nodes,
        "hierarchy": edges,
        "annotations": annotations
    }