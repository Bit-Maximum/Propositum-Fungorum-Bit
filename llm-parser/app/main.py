from fastapi import FastAPI
from .api import parse, health

app = FastAPI(
    title="LLM Clinical Guideline Parser",
    version="0.1.0"
)

app.include_router(parse.router, prefix="/api")
app.include_router(health.router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok"}
