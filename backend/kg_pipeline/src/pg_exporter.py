import csv
import json

def export_property_graph_csv(jsonld_data: dict, nodes_file: str, edges_file: str):
    nodes_rows = []
    edges_rows = []

    for item in jsonld_data.get("@graph", []):
        if "http://example.org/ontology/source" in item:
            src = item["http://example.org/ontology/source"]["@id"]
            tgt = item["http://example.org/ontology/target"]["@id"]

            edges_rows.append({
                ":START_ID": src,
                ":END_ID": tgt,
                ":TYPE": "TRANSITION",
                "condition": item.get("http://example.org/ontology/condition"),
                "description": item.get("http://example.org/ontology/description")
            })
        else:

            label = "QuestionNode"
            nodes_rows.append({
                ":ID": item["@id"],
                ":LABEL": label,
                "title": item.get("http://example.org/ontology/title"),
                "question": item.get("http://example.org/ontology/question"),
                "question_type": item.get("http://example.org/ontology/question_type")
            })

    if nodes_rows:
        fieldnames = [":ID", ":LABEL", "title", "question", "question_type"]
        with open(nodes_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(nodes_rows)

    if edges_rows:
        fieldnames = [":START_ID", ":END_ID", ":TYPE", "condition", "description"]
        with open(edges_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(edges_rows)

    return len(nodes_rows), len(edges_rows)
