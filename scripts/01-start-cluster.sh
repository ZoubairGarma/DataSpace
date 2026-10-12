#!/usr/bin/env bash
# =============================================================================
# 01 — Démarrer l'environnement : Docker Desktop (Windows) + cluster Minikube.
# Usage :  bash scripts/01-start-cluster.sh
# Ressources paramétrables :  MINIKUBE_CPUS=4 MINIKUBE_MEMORY=6g bash scripts/01-start-cluster.sh
# =============================================================================
set -euo pipefail

CPUS="${MINIKUBE_CPUS:-4}"
# Par défaut : 2833 MB — la limite WSL2/Docker de la plupart des machines
# (cette valeur a été validée sur le poste de développement).
# Ajustable :  MINIKUBE_MEMORY=8g bash scripts/01-start-cluster.sh
MEMORY="${MINIKUBE_MEMORY:-2833mb}"

# --- 1) Daemon Docker (Docker Desktop sous Windows) -------------------------
if docker info >/dev/null 2>&1; then
    echo "[1/3] Docker déjà actif ($(docker --version | cut -d, -f1))"
else
    # Docker Desktop : installation machine (Program Files) ou utilisateur (%LOCALAPPDATA%)
    DD_CANDIDATS=(
        "/c/Program Files/Docker/Docker/Docker Desktop.exe"
        "$LOCALAPPDATA/Programs/DockerDesktop/Docker Desktop.exe"
    )
    DD=""
    for c in "${DD_CANDIDATS[@]}"; do
        [ -f "$c" ] && DD="$c" && break
    done
    if [ -n "$DD" ]; then
        echo "[1/3] Démarrage de Docker Desktop (peut prendre 1-2 min)..."
        # Sorties détachées pour ne pas bloquer le terminal (processus GUI)
        ("$DD" >/dev/null 2>&1 &)
    else
        echo "[1/3] Docker daemon absent — lance Docker Desktop manuellement."
        exit 1
    fi
    for _ in $(seq 1 60); do
        docker info >/dev/null 2>&1 && break
        sleep 5
    done
    docker info >/dev/null 2>&1 || { echo "ERREUR : daemon Docker inaccessible après 5 min."; exit 1; }
    echo "[1/3] Docker actif."
fi

# --- 2) Cluster Minikube (créé au premier appel, redémarré ensuite) ---------
echo "[2/3] Démarrage de Minikube (driver docker, ${CPUS} CPU, ${MEMORY} RAM)..."
minikube start --driver=docker --cpus "$CPUS" --memory "$MEMORY"

# --- 3) Vérification --------------------------------------------------------
kubectl config use-context minikube >/dev/null
echo "[3/3] Cluster prêt :"
kubectl get nodes
echo
echo "Étape suivante :  bash scripts/02-build-images.sh"
