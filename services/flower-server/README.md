# flower-server — Module 3 (serveur de fédération FedAvg)

## À faire (équipe ML)

Dépose ton code **directement dans ce dossier**, avec un point d'entrée :

```
services/flower-server/main.py     ← requis, lancé par le conteneur
services/flower-server/requirements.txt   ← si tu as des dépendances (flwr, etc.)
```

Le Dockerfile et le manifeste `k8s/20-flower-server.yaml` sont déjà prêts :
dès que `main.py` existe, `scripts/02-build-images.sh` construit l'image et
`scripts/03-deploy.sh` la déploie. **Rien à modifier côté Module 4.**

## Contrat à respecter

| Élément       | Valeur                                                 |
|---------------|--------------------------------------------------------|
| Entrypoint    | `python main.py` (doit tourner en continu)             |
| Port gRPC     | `9090` — serveur Flower (stratégie FedAvg)             |
| Port HTTP     | `8080` — status/métriques pour le dashboard (Module 5) |

Détail complet : `docs/INTEGRATION_CONTRAT.md`.
