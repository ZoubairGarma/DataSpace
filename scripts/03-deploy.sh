#!/usr/bin/env bash
# =============================================================================
# 03 — Déployer sur le cluster.
# Usage :
#   bash scripts/03-deploy.sh          # tout (nécessite les images buildées)
#   bash scripts/03-deploy.sh core     # socle uniquement : namespace + config + simulateurs
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

# Sécurité : ne jamais déployer sur autre chose que le cluster local
if [ "$(kubectl config current-context)" != "minikube" ]; then
    if kubectl config get-contexts -o name | grep -q '^minikube$'; then
        kubectl config use-context minikube
    else
        echo "ERREUR : aucun contexte 'minikube'. Lance d'abord scripts/01-start-cluster.sh"
        exit 1
    fi
fi

if [ "${1:-tout}" = "core" ]; then
    FILES=(k8s/00-namespace.yaml k8s/01-configmap.yaml k8s/10-simulateurs.yaml)
else
    FILES=(k8s/*.yaml)
fi

for f in "${FILES[@]}"; do
    echo "==> kubectl apply -f $f"
    kubectl apply -f "$f"
done

echo
echo "Pods :"
kubectl get pods -n dataspace
echo
echo "Suivi :  bash scripts/04-status.sh   |   logs :  kubectl logs -n dataspace <pod> -c live-stream -f"
