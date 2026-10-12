# Serveur de fédération FedAvg — Module 3 (à livrer par l'équipe ML).
# PRÊT POUR INTÉGRATION : dépose ton code dans services/flower-server/
# avec un main.py — voir docs/INTEGRATION_CONTRAT.md.
# Contexte de build = racine du dépôt :
#   docker build -f services/flower-server/Dockerfile -t dataspace/flower-server .
FROM python:3.12-slim

WORKDIR /app

# requirements.txt optionnel tant que le module n'est pas livré
COPY services/flower-server/requirements*.txt ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

COPY services/flower-server/ ./

ENV PYTHONUNBUFFERED=1

# 9090 : gRPC Flower (clients)  |  8080 : HTTP status/métriques (dashboard)
EXPOSE 9090 8080

CMD ["python", "main.py"]
