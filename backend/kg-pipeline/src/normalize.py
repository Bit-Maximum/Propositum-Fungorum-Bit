import json
import hashlib
from typing import Dict, Any, List

NAMESPACE = "http://example.org/ontology/"


def generate_deterministic_id(value: str) -> str:
    """Generates a SHA-256 hash of the value to ensure idempotency."""
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def normalize_to_jsonld(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts generic ontology JSON to canonical JSON-LD.
    Assumes input has 'questionnaire_graph' -> 'nodes' structure based on your file.
    """
    nodes = input_data.get("questionnaire_graph", {}).get("nodes", [])

    jsonld_graph = []

    for node in nodes:
        # 1. Create Node URI
        node_id = node.get("id")
        node_uri = f"{NAMESPACE}node/{node_id}"

        # 2. Base Entity
        entity = {
            "@id": node_uri,
            "@type": [f"{NAMESPACE}QuestionNode"],
            f"{NAMESPACE}title": node.get("title"),
            f"{NAMESPACE}question": node.get("question"),
            f"{NAMESPACE}question_type": node.get("question_type")
        }
        jsonld_graph.append(entity)

        # 3. Handle Transitions (Edges)
        # We reify transitions to allow properties on edges (like 'condition')
        for trans in node.get("transitions", []):
            target_id = trans.get("target_node_id")
            if target_id:
                # Create a deterministic ID for the transition itself based on source+target
                trans_id_raw = f"{node_id}-{target_id}-{trans.get('condition', '')}"
                trans_uri = f"{NAMESPACE}transition/{generate_deterministic_id(trans_id_raw)}"

                transition_entity = {
                    "@id": trans_uri,
                    "@type": f"{NAMESPACE}Transition",
                    f"{NAMESPACE}source": {"@id": node_uri},
                    f"{NAMESPACE}target": {"@id": f"{NAMESPACE}node/{target_id}"},
                    f"{NAMESPACE}condition": trans.get("condition"),
                    f"{NAMESPACE}description": trans.get("description")
                }
                jsonld_graph.append(transition_entity)

    return {
        "@context": {
            "ex": NAMESPACE,
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
        },
        "@graph": jsonld_graph
    }
