# Image du simulateur : code réel du Module 1 (inchangé) + utilitaires Module 4.
# Contexte de build = racine du dépôt :
#   docker build -f services/simulateur/Dockerfile -t dataspace/simulateur .
FROM python:3.12-slim

WORKDIR /app

# Code du Module 1 — aucune dépendance externe (stdlib uniquement)
COPY Simulation_Usine/config.py \
     Simulation_Usine/sensor_simulator.py \
     Simulation_Usine/generate_historical_data.py \
     Simulation_Usine/live_stream.py \
     ./

# Utilitaires Module 4 : génération mono-usine + serveur HTTP des CSV
COPY services/simulateur/generate_one.py \
     services/simulateur/serve_data.py \
     ./

ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    PORT=8001

# Par défaut : streaming live de toutes les usines (les manifests surchargent)
CMD ["python", "live_stream.py"]
