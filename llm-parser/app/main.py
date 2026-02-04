import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, Body
import uvicorn
from typing import Dict
from metrics import (
    extract_entities,
    compute_metrics,
    compute_metrics_per_label,
)
from api.parse import PDFParser
from pipeline.pipeline import Pipeline

app = FastAPI(title="LLM Clinical Guideline Parser")

BASE_DIR = Path(__file__).parents[1]
PROMPTS_DIR = BASE_DIR / "app" / "pipeline" / "prompts"

pipeline = Pipeline(PROMPTS_DIR)


@app.post("/")
async def parse_pdf(file: UploadFile):
    tmp_path = Path("/tmp") / file.filename
    tmp_path.write_bytes(file.file.read())

    text = __parse_document(file, tmp_path)

    return await pipeline.run(text)


def __parse_document(file: UploadFile, tmp_path: Path):
    if file.content_type == "application/pdf":
        parser = PDFParser()
        return parser.parse(str(tmp_path))

    elif file.content_type == "application/json":
        try:
            with open(tmp_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            return json.dumps(json_data, ensure_ascii=False, indent=2)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error reading JSON file: {str(e)}")

    else:
        raise ValueError(f"Unsupported file type: {file.content_type}")

@app.post("/metrics")
async def metrics(gold: dict, pred: dict):
    gold_entities = extract_entities(gold)
    pred_entities = extract_entities(pred)

    return {
        "ner": compute_metrics(gold_entities, pred_entities),
        "per_label": compute_metrics_per_label(gold_entities, pred_entities),
        "total_gold": len(gold_entities),
        "total_pred": len(pred_entities),
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)