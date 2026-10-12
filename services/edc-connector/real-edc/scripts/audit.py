"""Journal d'audit : interroge la Management API de chaque usine (negociations + transferts)
et ajoute les nouveaux evenements a exchange_log.jsonl (sans doublon).
Usage : python scripts/audit.py"""
import json, os, datetime, requests

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exchange_log.jsonl")
BODY = {"@context": {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"}, "@type": "QuerySpec", "limit": 500}

def seen():
    s = set()
    if os.path.exists(LOG_FILE):
        for line in open(LOG_FILE, encoding="utf-8"):
            try:
                r = json.loads(line); s.add((r.get("source"), r.get("id"), r.get("state")))
            except json.JSONDecodeError: pass
    return s

def main():
    done, new = seen(), 0
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        for n in (1, 2, 3):
            base = f"http://localhost:{n}9193/management/v3"
            for kind, path in (("negotiation", "contractnegotiations"), ("transfer", "transferprocesses")):
                try:
                    items = requests.post(f"{base}/{path}/request", json=BODY, timeout=30).json()
                except Exception as ex:
                    print(f"usine-{n}: {path} injoignable ({ex})"); continue
                for it in items if isinstance(items, list) else []:
                    key = (f"usine-{n}", it.get("@id"), it.get("state"))
                    if key in done: continue
                    rec = {"ts": datetime.datetime.utcnow().isoformat() + "Z", "event": "audit_" + kind,
                           "source": key[0], "id": key[1], "state": key[2], "type": it.get("type"),
                           "counterParty": it.get("counterPartyId") or it.get("counterPartyAddress"),
                           "asset": it.get("assetId"), "agreement": it.get("contractAgreementId") or it.get("contractId"),
                           "error": it.get("errorDetail")}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); new += 1
    print(f"{new} nouvel(s) evenement(s) ajoute(s) a {os.path.normpath(LOG_FILE)}")

if __name__ == "__main__":
    main()