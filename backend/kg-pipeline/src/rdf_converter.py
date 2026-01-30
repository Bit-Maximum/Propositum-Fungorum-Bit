import json
from rdflib import Graph


def convert_jsonld_to_rdf(jsonld_data: dict, output_ttl: str, output_nt: str):
    g = Graph()
    # Parse the normalized JSON-LD dictionary
    g.parse(data=json.dumps(jsonld_data), format='json-ld')

    # Serialize to Turtle (human readable)
    g.serialize(destination=output_ttl, format='turtle')

    # Serialize to N-Triples (bulk loader friendly)
    g.serialize(destination=output_nt, format='nt')

    return len(g)
