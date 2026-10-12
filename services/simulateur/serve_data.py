"""
Sidecar Module 4 — expose les CSV d'une usine en HTTP (lecture seule).

Sert le dossier DATA_DIR (défaut : /app/data) :
    GET /usine_1/live_data.csv
    GET /usine_1/historical_data.csv
    GET /healthz                       -> {"status": "ok"}

Les réponses incluent un en-tête CORS afin que le dashboard (Module 5)
puisse interroger ce service directement depuis le navigateur.
"""

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

DATA_DIR = os.environ.get("DATA_DIR", "data")
PORT = int(os.environ.get("PORT", "8001"))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DATA_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self):
        if self.path == "/healthz":
            body = json.dumps({"status": "ok"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        # Journalisation discrète : uniquement les erreurs
        if any(code in (fmt % args) for code in ("404", "500")):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    print(f"Serveur de données sur http://0.0.0.0:{PORT} — dossier : {DATA_DIR}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
