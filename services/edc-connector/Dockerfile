# Connecteur EDC — Module 2 (Data Space, à livrer par l'équipe EDC).
# Un déploiement par usine : edc-connector-usine-{1,2,3}.
# Contexte de build = racine du dépôt :
#   docker build -f services/edc-connector/Dockerfile -t dataspace/edc-connector .
FROM python:3.12-slim

WORKDIR /app

COPY services/edc-connector/requirements*.txt ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

COPY services/edc-connector/ ./

ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

EXPOSE 8000

CMD ["python", "main.py"]
