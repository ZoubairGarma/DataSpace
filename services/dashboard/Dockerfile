# Dashboard + API — Module 5 (à livrer par l'équipe dashboard).
# Exposé en NodePort 30080 (http://<minikube-ip>:30080).
# Contexte de build = racine du dépôt :
#   docker build -f services/dashboard/Dockerfile -t dataspace/dashboard .
FROM python:3.12-slim

WORKDIR /app

COPY services/dashboard/requirements*.txt ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

COPY services/dashboard/ ./

ENV PYTHONUNBUFFERED=1

EXPOSE 8500

CMD ["python", "main.py"]
