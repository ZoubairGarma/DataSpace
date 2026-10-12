# Client ML fédéré — Module 3 (à livrer par l'équipe ML).
# Un déploiement par usine : ml-client-usine-{1,2,3}.
# Contexte de build = racine du dépôt :
#   docker build -f services/ml-client/Dockerfile -t dataspace/ml-client .
FROM python:3.12-slim

WORKDIR /app

COPY services/ml-client/requirements*.txt ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

COPY services/ml-client/ ./

ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

CMD ["python", "main.py"]
