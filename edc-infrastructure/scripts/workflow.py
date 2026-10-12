"""Workflow EDC : publier, decouvrir, negocier, transferer.

Usage (depuis edc-infrastructure/) :
    python -m pip install requests
    python scripts/workflow.py setup                        # publie assets+policies+contractdefs des 3 usines
    python scripts/workflow.py catalog 2 1                  # usine 2 consulte le catalogue de l'usine 1
    python scripts/workflow.py exchange 2 1 iot-usine-1-historical [fichier_sortie.csv]
    python scripts/workflow.py demo                         # scenarios de test + tableau de resultats
"""
import json, os, re, sys, time, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
PAYLOADS = os.path.join(HERE, "payloads")
LOG_FILE = os.path.join(HERE, "..", "exchange_log.jsonl")
CTX = {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"}
PROTO = "dataspace-protocol-http:2025-1"


# Usine N -> ports (hote) et adresses (reseau Docker)
def mgmt(n): return f"http://localhost:{n}9193/management/v3"
def dsp(n):  return f"http://connector-{n}:{n}9194/protocol/2025-1"
def pid(n):  return f"usine-{n}"

def public_localhost(url):
    """L'EDR renvoie http://connector-N:PORT/... : on le traduit pour l'hote."""
    return re.sub(r"http://connector-\d", "http://localhost", url)


def log_event(event, **kw):
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rec = {"ts": ts, "event": event, **kw}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[{ts}] {event} {kw}")


def load(name, **repl):
    txt = open(os.path.join(PAYLOADS, name), encoding="utf-8").read()
    for k, v in repl.items():
        txt = txt.replace(f"__{k}__", str(v))
    left = re.findall(r"__[A-Z]+__", txt)
    if left:
        raise ValueError(f"Placeholder non substitue dans {name} : {left[0]}")
    return json.loads(txt)


# ---------- HTTP helpers ----------
def post(url, body):
    """POST JSON strict : leve une erreur si le connecteur refuse."""
    r = requests.post(url, json=body, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"POST {url} -> {r.status_code} {r.text[:300]}")
    return r


def post_soft(url, body):
    """POST JSON tolerant : 409 (deja existant) ignore, refus du connecteur signale sans planter.
    Retourne True si la ressource existe (creee ou deja presente)."""
    r = requests.post(url, json=body, timeout=30)
    if r.status_code == 409:
        return True
    if r.status_code >= 400:
        print(f"  [refuse par le connecteur] {url} -> {r.status_code} {r.text[:160]}")
        return False
    return True


# ---------- 1. Publication ----------
def setup():
    for n in (1, 2, 3):
        m = mgmt(n)
        print(f"--- usine {n} ---")
        post_soft(f"{m}/policydefinitions", load("policy_ok.json"))
        expired_ok = post_soft(f"{m}/policydefinitions", load("policy_expired.json"))
        published = []
        for tpl, suffix, policy in [("asset_historical.json", "historical", "policy-ok"),
                                    ("asset_live.json", "live", "policy-ok"),
                                    ("asset_expired.json", "expired", "policy-expired"),
                                    ("asset_hidden.json", "hidden", None)]:
            if policy == "policy-expired" and not expired_ok:
                print("  [ignore] asset_expired : policy-expired non creee")
                continue
            post_soft(f"{m}/assets", load(tpl, N=n))
            asset = f"iot-usine-{n}-{suffix}"
            published.append(suffix)
            if policy:  # 'hidden' n'a volontairement pas de contract definition
                post_soft(f"{m}/contractdefinitions",
                          load("contractdef.json", ASSET=asset, POLICY=policy, N=n))
        log_event("publish", participant=pid(n), assets=published)
    print("OK : 3 usines configurees (409 = deja existant, ignore).")


# ---------- 2. Decouverte ----------
def as_list(x):
    return x if isinstance(x, list) else ([] if x is None else [x])

def catalog(consumer, provider):
    body = {"@context": CTX, "counterPartyAddress": dsp(provider),
            "counterPartyId": pid(provider), "protocol": PROTO}
    r = post(f"{mgmt(consumer)}/catalog/request", body).json()
    datasets = as_list(r.get("dataset") or r.get("dcat:dataset"))
    out = []
    for d in datasets:
        pol = d.get("hasPolicy") or d.get("odrl:hasPolicy")
        pol = as_list(pol)[0] if pol else {}
        out.append({"asset": d.get("@id"), "offer": pol.get("@id"), "policy": pol})
    log_event("catalog", consumer=pid(consumer), provider=pid(provider),
              assets=[o["asset"] for o in out])
    return out


# ---------- 3. Negociation ----------
def negotiate(consumer, provider, offer, asset_id, timeout=60):
    pol = {k: v for k, v in offer["policy"].items() if k != "@context"}
    pol.update({"@context": "http://www.w3.org/ns/odrl.jsonld", "@id": offer["offer"],
                "@type": "Offer", "assigner": pid(provider), "target": asset_id})
    body = {"@context": CTX, "@type": "ContractRequest",
            "counterPartyAddress": dsp(provider), "counterPartyId": pid(provider),
            "protocol": PROTO, "policy": pol}
    nid = post(f"{mgmt(consumer)}/contractnegotiations", body).json()["@id"]
    log_event("negotiation_started", consumer=pid(consumer), provider=pid(provider),
              asset=asset_id, negotiation=nid)
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = requests.get(f"{mgmt(consumer)}/contractnegotiations/{nid}", timeout=30).json()
        state = r.get("state")
        if state in ("FINALIZED", "TERMINATED"):
            log_event("negotiation_" + state.lower(), consumer=pid(consumer),
                      provider=pid(provider), asset=asset_id, negotiation=nid,
                      agreement=r.get("contractAgreementId"), error=r.get("errorDetail"))
            return r
        time.sleep(1)
    raise TimeoutError("negociation trop longue")


# ---------- 4. Transfert ----------
def transfer(consumer, provider, agreement_id, asset_id, timeout=60):
    body = {"@context": CTX, "@type": "TransferRequest", "assetId": asset_id,
            "contractId": agreement_id, "counterPartyAddress": dsp(provider),
            "counterPartyId": pid(provider), "protocol": PROTO,
            "transferType": "HttpData-PULL"}
    tid = post(f"{mgmt(consumer)}/transferprocesses", body).json()["@id"]
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = requests.get(f"{mgmt(consumer)}/transferprocesses/{tid}", timeout=30).json()
        if r.get("state") in ("STARTED", "COMPLETED", "TERMINATED"):
            log_event("transfer_" + r["state"].lower(), consumer=pid(consumer),
                      provider=pid(provider), asset=asset_id, transfer=tid)
            return tid, r
        time.sleep(1)
    raise TimeoutError("transfert trop long")


def fetch_data(consumer, transfer_id):
    """Recupere l'EDR (endpoint + token) puis telecharge les donnees via le data plane du provider."""
    edr = None
    for _ in range(15):
        edr = requests.get(f"{mgmt(consumer)}/edrs/{transfer_id}/dataaddress", timeout=30)
        if edr.status_code == 200:
            break
        time.sleep(1)
    if edr is None or edr.status_code != 200:
        raise RuntimeError(f"EDR indisponible ({edr.status_code}) : {edr.text[:200]}")
    e = edr.json()
    endpoint = e.get("endpoint") or e.get("edc:endpoint")
    token = e.get("authorization") or e.get("edc:authorization")
    return requests.get(public_localhost(endpoint), headers={"Authorization": token}, timeout=60)


def exchange(consumer, provider, asset_id, out_file=None):
    offers = {o["asset"]: o for o in catalog(consumer, provider)}
    if asset_id not in offers:
        log_event("asset_not_offered", consumer=pid(consumer), provider=pid(provider), asset=asset_id)
        return {"status": "NOT_OFFERED"}
    neg = negotiate(consumer, provider, offers[asset_id], asset_id)
    if neg["state"] != "FINALIZED":
        return {"status": "NEGOTIATION_" + neg["state"], "detail": neg.get("errorDetail")}
    tid, tr = transfer(consumer, provider, neg["contractAgreementId"], asset_id)
    if tr.get("state") == "TERMINATED":
        return {"status": "TRANSFER_TERMINATED", "detail": tr.get("errorDetail")}
    resp = fetch_data(consumer, tid)
    log_event("data_fetched", consumer=pid(consumer), provider=pid(provider), asset=asset_id,
              http_status=resp.status_code, bytes=len(resp.content))
    if resp.status_code == 200 and out_file:
        open(out_file, "wb").write(resp.content)
    return {"status": "OK" if resp.status_code == 200 else f"DATA_HTTP_{resp.status_code}",
            "bytes": len(resp.content)}


# ---------- Demo / tests ----------
def demo():
    results = []
    def run(name, expected, fn):
        try: got = fn()
        except Exception as ex: got = {"status": "ERROR", "detail": str(ex)[:150]}
        ok = got["status"] == expected or (expected == "REFUSED" and got["status"] != "OK")
        results.append((name, expected, got["status"], "OK" if ok else "A VERIFIER"))
    run("S1 usine-2 -> usine-1, politique valide", "OK",
        lambda: exchange(2, 1, "iot-usine-1-historical"))
    run("S2 usine-3 -> usine-1, flux live", "OK",
        lambda: exchange(3, 1, "iot-usine-1-live"))
    run("S3 politique expiree", "REFUSED",
        lambda: exchange(2, 1, "iot-usine-1-expired"))
    run("S4 asset sans contract definition", "NOT_OFFERED",
        lambda: exchange(2, 1, "iot-usine-1-hidden"))
    print("\n| Scenario | Attendu | Obtenu | Verdict |\n|---|---|---|---|")
    for r in results: print("| " + " | ".join(r) + " |")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "demo"
    a = sys.argv[2:]
    if cmd == "setup": setup()
    elif cmd == "catalog":
        for o in catalog(int(a[0]), int(a[1])): print(o["asset"], "-> offre", o["offer"])
    elif cmd == "exchange": print(exchange(int(a[0]), int(a[1]), a[2], a[3] if len(a) > 3 else None))
    elif cmd == "demo": demo()
    else: print(__doc__)