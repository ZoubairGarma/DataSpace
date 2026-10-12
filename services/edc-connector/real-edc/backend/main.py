"""Backend d'une usine : expose ses CSV (historical_data.csv / live_data.csv).
C'est l'URL cible (baseUrl) de l'asset EDC. Les données restent locales."""
import csv, os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

FACTORY = os.getenv("FACTORY", "usine_1")
DATA_DIR = os.getenv("DATA_DIR", "/data")
FILES = {"historical": "historical_data.csv", "live": "live_data.csv"}

app = FastAPI(title=f"Backend {FACTORY}")


def path_of(kind: str) -> str:
    if kind not in FILES:
        raise HTTPException(404, "dataset inconnu (historical | live)")
    p = os.path.join(DATA_DIR, FILES[kind])
    if not os.path.isfile(p):
        raise HTTPException(404, f"fichier absent : {FILES[kind]}")
    return p


@app.get("/health")
def health():
    return {"factory": FACTORY, "datasets": {k: os.path.isfile(os.path.join(DATA_DIR, v)) for k, v in FILES.items()}}


@app.get("/data/{kind}")
def get_data(kind: str, limit: int = Query(1000, ge=1, le=100000), offset: int = Query(0, ge=0)):
    """JSON paginé. kind = historical | live. Pour 'live', offset=-1 n'existe pas : utilisez /data/live/latest."""
    p = path_of(kind)
    with open(p, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {"factory": FACTORY, "dataset": kind, "total": len(rows), "offset": offset, "rows": rows[offset:offset + limit]}


@app.get("/data/{kind}/csv")
def get_csv(kind: str):
    """CSV brut (utile pour le Membre 3 : pandas.read_csv)."""
    return FileResponse(path_of(kind), media_type="text/csv", filename=FILES[kind])


@app.get("/data/live/latest")
def latest(n: int = Query(20, ge=1, le=1000)):
    p = path_of("live")
    with open(p, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {"factory": FACTORY, "rows": rows[-n:]}