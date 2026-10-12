#!/usr/bin/env bash
# =============================================================================
# 02 — Construire les images et les charger DANS le cluster Minikube.
# Pas besoin de registre : les images vivent dans le cluster, les manifests
# utilisent imagePullPolicy: Never.
#
# Usage :  bash scripts/02-build-images.sh
#
# Stratégie (automatique) :
#   1. build directement dans le daemon Docker de Minikube (minikube docker-env)
#   2. sinon (Windows/containerd) : build avec Docker Desktop puis
#      `minikube image load` pour importer l'image dans le cluster
#
# - dataspace/simulateur   : toujours buildable (code Module 1 déjà livré)
# - les autres services    : buildables dès que services/<svc>/main.py existe
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

MODE=""
if eval "$(minikube docker-env)" 2>/dev/null && docker info >/dev/null 2>&1; then
    MODE="direct"   # build dans le daemon minikube
else
    # Fallback : daemon local (Docker Desktop) + import dans le cluster
    docker info >/dev/null 2>&1 || {
        echo "ERREUR : ni daemon minikube ni Docker accessible. Lance scripts/01-start-cluster.sh"; exit 1;
    }
    MODE="load"
fi

build() { # build <chemin Dockerfile> <tag>
    local dockerfile="$1" tag="$2"
    docker build -f "$dockerfile" -t "$tag" .
    if [ "$MODE" = "load" ]; then
        minikube image load "$tag"
    fi
}

if [ "$MODE" = "direct" ]; then
    echo "==> Mode : build direct dans le daemon Docker de Minikube"
else
    echo "==> Mode : build Docker Desktop + 'minikube image load' (docker-env indisponible)"
fi
echo

echo "==> Image du simulateur (Module 1, code réel)"
build services/simulateur/Dockerfile dataspace/simulateur:latest
echo "    ✓ dataspace/simulateur"
echo

echo "==> Services des Modules 2/3/5 (build dès que main.py est livré)"
for svc in flower-server ml-client edc-connector dashboard; do
    if [ -f "services/$svc/main.py" ]; then
        build "services/$svc/Dockerfile" "dataspace/$svc:latest"
        echo "    ✓ dataspace/$svc"
    else
        echo "    – dataspace/$svc : ignoré (services/$svc/main.py absent — module non encore livré)"
    fi
done
echo
echo "Images présentes dans le cluster :"
minikube image list --format json 2>/dev/null | grep -o '"Name": *"[^"]*"' | grep dataspace || \
    kubectl get nodes -o jsonpath='{.items[0].status.images[*].names}' | tr ' ' '\n' | grep dataspace || true
echo
echo "Étape suivante :  bash scripts/03-deploy.sh"
