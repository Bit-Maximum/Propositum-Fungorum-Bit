import csv
import json


def export_property_graph_csv(jsonld_data: dict, nodes_file: str, edges_file: str):
    nodes_rows = []
    edges_rows = []

    # Simple logic: In normalized JSON-LD, items with "source" and "target" are Edges.
    # Everything else is a Node.

    for item in jsonld_data.get("@graph", []):
        if "http://example.org/ontology/source" in item:
            # It's an edge (Transition)
            # Edge format: :START_ID, :END_ID, :TYPE, property...
            src = item["http://example.org/ontology/source"]["@id"]
            tgt = item["http://example.org/ontology/target"]["@id"]

            # Extract plain ID from URI for cleaner CSVs (optional, here we keep URI for global uniqueness)
            edges_rows.append({
                ":START_ID": src,
                ":END_ID": tgt,
                ":TYPE": "TRANSITION",
                "condition": item.get("http://example.org/ontology/condition"),
                "description": item.get("http://example.org/ontology/description")
            })
        else:
            # It's a node
            # Node format: :ID, :LABEL, property...
            label = "QuestionNode"  # Simplified logic
            nodes_rows.append({
                ":ID": item["@id"],
                ":LABEL": label,
                "title": item.get("http://example.org/ontology/title"),
                "question": item.get("http://example.org/ontology/question"),
                "question_type": item.get("http://example.org/ontology/question_type")
            })

    # Write Nodes CSV
    if nodes_rows:
        fieldnames = [":ID", ":LABEL", "title", "question", "question_type"]
        with open(nodes_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(nodes_rows)

    # Write Edges CSV
    if edges_rows:
        fieldnames = [":START_ID", ":END_ID", ":TYPE", "condition", "description"]
        with open(edges_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(edges_rows)

    return len(nodes_rows), len(edges_rows)
