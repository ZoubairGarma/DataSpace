"""Module 2 - Connecteur Data Space d'une usine (contrat d'integration Module 4).

Lance par `python main.py`, ecoute sur le port 8000, en continu.
Variables d'environnement : USINE_ID (usine_1...), DATA_DIR (/data).
Optionnelles : EDC_MANAGEMENT_URL (ex: http://localhost:19193/management/v3), PEERS, SIM_DATA_URL, LOG_FILE.

Deux modes :
  - EDC_MANAGEMENT_URL defini  -> facade : /catalog /contracts /policies /logs sont lus depuis un
                                  vrai connecteur Eclipse EDC (Management API v3).
  - sinon (defaut cluster)     -> mini-connecteur Data Space integre, qui reprend les memes concepts :
                                  asset, politique, contract definition, negociation, accord,
                                  transfert avec token, journal d'echange.
"""
import csv, io, json, os, secrets, time, datetime
import requests, uvicorn
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import PlainTextResponse

USINE_ID = os.getenv("USINE_ID", "usine_1")
N = USINE_ID.split("_")[-1]
DATA_DIR = os.getenv("DATA_DIR", "/data")
EDC_MGMT = os.getenv("EDC_MANAGEMENT_URL", "").rstrip("/")
LOG_FILE = os.getenv("LOG_FILE", "/tmp/exchange_log.jsonl")
SIM_URL = os.getenv("SIM_DATA_URL", f"http://sim-data-usine-{N}:8001/{USINE_ID}/live_data.csv")
HIST_FILE = os.path.join(DATA_DIR, USINE_ID, "historical_data.csv")
PARTICIPANT = USINE_ID.replace("_", "-")          # identifiant Data Space : usine-1

def peer_url(pid: str) -> str:
    """pid = 'usine_2'. PEERS='usine_2=http://localhost:8002,usine_3=...' pour les tests locaux."""
    for item in filter(None, os.getenv("PEERS", "").split(",")):
        k, v = item.split("=", 1)
        if k.strip() == pid:
            return v.strip().rstrip("/")
    return f"http://edc-connector-usine-{pid.split('_')[-1]}:8000"

app = FastAPI(title=f"Connecteur Data Space {USINE_ID}")

# ------------------------------------------------------------------ etat (en memoire)
ASSETS = {
    f"iot-usine-{N}-historical": {"name": f"Historique capteurs {USINE_ID}", "contenttype": "text/csv",
                                  "source": {"file": HIST_FILE}},
    f"iot-usine-{N}-live": {"name": f"Flux temps reel {USINE_ID}", "contenttype": "text/csv",
                            "source": {"url": SIM_URL}},
    f"iot-usine-{N}-expired": {"name": "Jeu a politique expiree (test de refus)", "contenttype": "text/csv",
                               "source": {"file": HIST_FILE}},
    f"iot-usine-{N}-hidden": {"name": "Asset non publie (test invisibilite)", "contenttype": "text/csv",
                              "source": {"file": HIST_FILE}},
}
POLICIES = {
    "policy-ok": {"description": "Acces libre pour tout participant du Data Space", "permission": ["use"],
                  "constraints": []},
    "policy-expired": {"description": "Acces valable jusqu'au 2020-01-01 (expire)", "permission": ["use"],
                       "constraints": [{"inForceDate": {"lteq": "2020-01-01T00:00:00Z"}}]},
}
CONTRACT_DEFS = {f"cd-iot-usine-{N}-historical": {"asset": f"iot-usine-{N}-historical", "policy": "policy-ok"},
                 f"cd-iot-usine-{N}-live": {"asset": f"iot-usine-{N}-live", "policy": "policy-ok"},
                 f"cd-iot-usine-{N}-expired": {"asset": f"iot-usine-{N}-expired", "policy": "policy-expired"}}
AGREEMENTS = {}      # cote provider : accords signes
NEGOTIATIONS = []    # cote consumer : negociations lancees
LOGS = []

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

def log(event, **kw):
    rec = {"ts": now(), "event": event, "participant": PARTICIPANT, **kw}
    LOGS.append(rec)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass

def policy_allows(pid: str) -> tuple[bool, str]:
    for c in POLICIES[pid]["constraints"]:
        if "inForceDate" in c:
            end = c["inForceDate"].get("lteq")
            if end and datetime.datetime.now(datetime.timezone.utc) > datetime.datetime.fromisoformat(end.replace("Z", "+00:00")):
                return False, f"politique {pid} expiree le {end}"
    return True, "ok"

def read_source(asset_id: str) -> bytes:
    src = ASSETS[asset_id]["source"]
    if "file" in src:
        if not os.path.isfile(src["file"]): raise HTTPException(404, "fichier de donnees absent")
        return open(src["file"], "rb").read()
    r = requests.get(src["url"], timeout=15)
    r.raise_for_status()
    return r.content

# ------------------------------------------------------------------ endpoints du contrat Module 4
def mgmt(path, kind=""):
    body = {"@context": {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"}, "@type": "QuerySpec", "limit": 200}
    r = requests.post(f"{EDC_MGMT}/{path}/request", json=body, timeout=15)
    r.raise_for_status()
    return r.json()

@app.get("/healthz")
def healthz():
    return {"status": "ok", "usine": USINE_ID, "mode": "edc-facade" if EDC_MGMT else "builtin"}

@app.get("/catalog")
def catalog(peer: str | None = None):
    """Jeux de donnees publies. ?peer=usine_2 : decouverte du catalogue d'une autre usine."""
    if peer:
        r = requests.get(f"{peer_url(peer)}/dsp/catalog", params={"consumer": USINE_ID}, timeout=15)
        log("catalog_request", provider=peer.replace("_", "-"), status=r.status_code)
        return r.json()
    if EDC_MGMT:
        return mgmt("assets", "asset")
    published = {cd["asset"] for cd in CONTRACT_DEFS.values()}
    return {"participant": PARTICIPANT, "datasets": [
        {"asset": a, **{k: v for k, v in ASSETS[a].items() if k != "source"}, "offered": a in published}
        for a in ASSETS if a in published]}

@app.get("/contracts")
def contracts():
    if EDC_MGMT:
        return {"negotiations": mgmt("contractnegotiations", "neg"),
                "transfers": mgmt("transferprocesses", "tp")}
    return {"as_consumer": NEGOTIATIONS, "as_provider": list(AGREEMENTS.values())}

@app.get("/policies")
def policies():
    if EDC_MGMT:
        return mgmt("policydefinitions", "policy")
    return {"policies": POLICIES, "contract_definitions": CONTRACT_DEFS}

@app.get("/logs")
def logs(limit: int = 200):
    return {"participant": PARTICIPANT, "count": len(LOGS), "events": LOGS[-limit:]}

# ------------------------------------------------------------------ protocole entre connecteurs (cote provider)
@app.get("/dsp/catalog")
def dsp_catalog(consumer: str = ""):
    log("catalog_served", consumer=consumer)
    return catalog()

@app.post("/dsp/negotiate")
def dsp_negotiate(req: dict):
    consumer, asset = req.get("consumer", "?"), req.get("asset", "")
    cd = next((c for c in CONTRACT_DEFS.values() if c["asset"] == asset), None)
    if not cd:
        log("negotiation_terminated", consumer=consumer, asset=asset, reason="asset non offert")
        return {"state": "TERMINATED", "reason": "asset non offert"}
    ok, why = policy_allows(cd["policy"])
    if not ok:
        log("negotiation_terminated", consumer=consumer, asset=asset, reason=why)
        return {"state": "TERMINATED", "reason": why}
    ag = {"agreement_id": "ag-" + secrets.token_hex(6), "asset": asset, "consumer": consumer,
          "policy": cd["policy"], "token": secrets.token_urlsafe(24), "signed_at": now(),
          "expires_at": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).isoformat()}
    AGREEMENTS[ag["agreement_id"]] = ag
    log("negotiation_finalized", consumer=consumer, asset=asset, agreement=ag["agreement_id"])
    return {"state": "FINALIZED", **ag}

@app.get("/dsp/data/{agreement_id}")
def dsp_data(agreement_id: str, authorization: str = Header(default="")):
    ag = AGREEMENTS.get(agreement_id)
    if not ag or authorization != ag["token"]:
        log("transfer_denied", agreement=agreement_id, reason="accord ou token invalide")
        raise HTTPException(403, "accord ou token invalide")
    if datetime.datetime.fromisoformat(ag["expires_at"]) < datetime.datetime.now(datetime.timezone.utc):
        log("transfer_denied", agreement=agreement_id, reason="accord expire")
        raise HTTPException(403, "accord expire")
    data = read_source(ag["asset"])
    log("transfer_completed", consumer=ag["consumer"], asset=ag["asset"], agreement=agreement_id, bytes=len(data))
    return PlainTextResponse(data.decode("utf-8", "replace"), media_type="text/csv")

# ------------------------------------------------------------------ cote consumer
@app.post("/negotiate")
def negotiate(req: dict):
    """{"provider": "usine_2", "asset": "iot-usine-2-historical"}"""
    prov, asset = req["provider"], req["asset"]
    cat = requests.get(f"{peer_url(prov)}/dsp/catalog", params={"consumer": USINE_ID}, timeout=15).json()
    offered = {d["asset"] for d in cat.get("datasets", [])}
    rec = {"negotiation_id": "neg-" + secrets.token_hex(4), "provider": prov, "asset": asset, "started_at": now()}
    if asset not in offered:
        rec.update(state="TERMINATED", reason="asset non visible dans le catalogue")
    else:
        r = requests.post(f"{peer_url(prov)}/dsp/negotiate", json={"consumer": USINE_ID, "asset": asset}, timeout=15).json()
        rec.update(state=r["state"], agreement_id=r.get("agreement_id"), token=r.get("token"), reason=r.get("reason"))
    NEGOTIATIONS.append(rec)
    log("negotiation_" + rec["state"].lower(), provider=prov.replace("_", "-"), asset=asset,
        agreement=rec.get("agreement_id"), reason=rec.get("reason"))
    return {k: v for k, v in rec.items() if k != "token"}

@app.post("/transfer")
def transfer(req: dict):
    """{"negotiation_id": "neg-..."} -> telecharge via le token de l'accord. Renvoie un resume, pas les lignes."""
    rec = next((n for n in NEGOTIATIONS if n["negotiation_id"] == req.get("negotiation_id")), None)
    if not rec or rec["state"] != "FINALIZED":
        raise HTTPException(400, "pas d'accord finalise pour cette negociation")
    r = requests.get(f"{peer_url(rec['provider'])}/dsp/data/{rec['agreement_id']}",
                     headers={"Authorization": rec["token"]}, timeout=30)
    log("transfer_" + ("received" if r.status_code == 200 else "failed"), provider=rec["provider"].replace("_", "-"),
        asset=rec["asset"], http_status=r.status_code, bytes=len(r.content))
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text[:200])
    rows = list(csv.reader(io.StringIO(r.text)))
    return {"asset": rec["asset"], "http_status": 200, "columns": rows[0] if rows else [], "rows": max(len(rows) - 1, 0)}

if __name__ == "__main__":
    log("startup", usine=USINE_ID, mode="edc-facade" if EDC_MGMT else "builtin")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
