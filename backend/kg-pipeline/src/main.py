import click
import json
import os
import boto3
import datetime
from .normalize import normalize_to_jsonld
from .rdf_converter import convert_jsonld_to_rdf
from .pg_exporter import export_property_graph_csv


@click.command()
@click.option('--input-file', required=True, help='Path to input JSON')
@click.option('--bucket', required=True, help='S3 Bucket Name')
@click.option('--neptune-endpoint', help='Neptune Cluster Endpoint (optional)')
def pipeline(input_file, bucket, neptune_endpoint):
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d_%H%M%S')
    local_out_dir = f"data/output/{timestamp}"
    os.makedirs(local_out_dir, exist_ok=True)

    # 1. Load Input
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # 2. Normalize
    print("Normalizing data...")
    jsonld = normalize_to_jsonld(raw_data)
    jsonld_path = f"{local_out_dir}/normalized.jsonld"
    with open(jsonld_path, 'w', encoding='utf-8') as f:
        json.dump(jsonld, f, indent=2)

    # 3. RDF Convert
    print("Converting to RDF...")
    ttl_path = f"{local_out_dir}/graph.ttl"
    nt_path = f"{local_out_dir}/graph.nt"
    triple_count = convert_jsonld_to_rdf(jsonld, ttl_path, nt_path)

    # 4. CSV Export
    print("Exporting CSVs...")
    nodes_path = f"{local_out_dir}/nodes.csv"
    edges_path = f"{local_out_dir}/edges.csv"
    node_count, edge_count = export_property_graph_csv(jsonld, nodes_path, edges_path)

    # 5. Upload to S3
    print(f"Uploading to S3 bucket {bucket}...")
    s3 = boto3.client('s3')
    prefix = f"kg_exports/{timestamp}"
    files = [jsonld_path, ttl_path, nt_path, nodes_path, edges_path]
    s3_map = {}

    for local_path in files:
        filename = os.path.basename(local_path)
        s3_key = f"{prefix}/{filename}"
        s3.upload_file(local_path, bucket, s3_key)
        s3_map[filename] = s3_key
        print(f"Uploaded {s3_key}")

    # 6. Manifest
    manifest = {
        "version": "1.0",
        "generated_at": timestamp,
        "counts": {"triples": triple_count, "nodes": node_count, "edges": edge_count},
        "s3_paths": s3_map,
        "source_file": os.path.basename(input_file)
    }
    with open(f"{local_out_dir}/manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    s3.upload_file(f"{local_out_dir}/manifest.json", bucket, f"{prefix}/manifest.json")

    print("Pipeline Complete. Manifest generated.")


if __name__ == "__main__":
    pipeline()
