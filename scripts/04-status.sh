#!/usr/bin/env bash
# =============================================================================
# 04 — État du déploiement + accès (dashboard, données live).
# Usage :  bash scripts/04-status.sh
# =============================================================================
set -euo pipefail

NS=dataspace

echo "================= Pods ($NS) ================="
kubectl get pods -n "$NS" -o wide
echo
echo "================= Services ($NS) ============="
kubectl get svc -n "$NS"
echo
echo "================= Accès (Windows/docker driver) ==="
echo "NodePort direct (http://$(minikube ip):30001..30003) n'est PAS routable depuis Windows."
echo "Utiliser le tunnel minikube (laisse le terminal ouvert, imprime une URL localhost) :"
echo
echo "  Données live usine 1 :  minikube service sim-data-usine-1 -n $NS"
echo "  Données live usine 2 :  minikube service sim-data-usine-2 -n $NS"
echo "  Données live usine 3 :  minikube service sim-data-usine-3 -n $NS"
echo "  Dashboard (Module 5) :  minikube service dashboard -n $NS"
echo
echo "Alternative (URL fixe, en arrière-plan) :"
echo "  kubectl -n $NS port-forward svc/sim-data-usine-1 30001:8001"
echo "  kubectl -n $NS port-forward svc/dashboard 30080:8500"
echo "  -> http://127.0.0.1:30001/usine_1/live_data.csv   http://127.0.0.1:30080"
echo
echo "================= Commandes utiles ============"
echo "  Logs streaming live :  kubectl logs -n $NS deploy/simulateur-usine-1 -c live-stream -f"
echo "  Vérifier historique :  kubectl exec -n $NS deploy/simulateur-usine-1 -c data-server -- wc -l /app/data/usine_1/historical_data.csv"
echo "  Supprimer tout     :  kubectl delete namespace $NS"
