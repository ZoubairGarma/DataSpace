# Module 4 — Déploiement Docker + Kubernetes (Minikube)

Industrial Data Space for Predictive Maintenance — couche déploiement :
dockerisation des services et orchestration Kubernetes (Minikube), prête à
accueillir les Modules 2 (EDC), 3 (ML fédéré) et 5 (dashboard).

## Prérequis

- Docker Desktop (Windows) — installé et exécutable
- Minikube, kubectl
- Un shell bash (Git Bash sur Windows)

## Démarrage rapide (démo)

```bash
bash scripts/01-start-cluster.sh     # Docker Desktop + cluster Minikube
bash scripts/02-build-images.sh      # build des images (dans le daemon minikube)
bash scripts/03-deploy.sh core       # socle : namespace + config + simulateurs
bash scripts/04-status.sh            # état + URLs d'accès
```

Test immédiat des données temps réel (Windows + driver docker : passer par
un tunnel minikube — les NodePorts ne sont pas routables depuis l'hôte) :

```bash
minikube service sim-data-usine-1 -n dataspace      # ouvre le flux live usine 1
# ou URL fixe en arrière-plan :
kubectl -n dataspace port-forward svc/sim-data-usine-1 30001:8001 &
curl http://127.0.0.1:30001/usine_1/live_data.csv
```

Le dashboard arrivera sur `http://$IP:30080` dès que le Module 5 est livré.

## Contenu

```
services/            un dossier par service (Dockerfile prêt + README d'intégration)
  simulateur/        code Module 1 réel + utilitaires Module 4   ← buildable aujourd'hui
  flower-server/     Module 3 (serveur FedAvg)                   ← ajouter main.py
  ml-client/         Module 3 (client fédéré par usine)          ← ajouter main.py
  edc-connector/     Module 2 (connecteur Data Space)            ← ajouter main.py
  dashboard/         Module 5 (tableau de bord)                  ← ajouter main.py
k8s/                 manifests Kubernetes (namespace dataspace)
scripts/             01-start-cluster / 02-build-images / 03-deploy / 04-status
docs/                INTEGRATION_CONTRAT.md (pour les coéquipiers), ARCHITECTURE.md
```

## Quand un coéquipier livre son module

Aucune modification côté Module 4 — son code respecte
[`docs/INTEGRATION_CONTRAT.md`](docs/INTEGRATION_CONTRAT.md) :

```bash
bash scripts/02-build-images.sh     # détecte et build les nouveaux services
bash scripts/03-deploy.sh           # déploie tout (images manquantes = pods en attente)
```

Tant qu'une image n'existe pas, son pod reste en `ErrImageNeverPull` :
c'est le comportement attendu, le reste du cluster fonctionne normalement.

## Scénario de démo complet (jour J)

1. `bash scripts/01-start-cluster.sh` — le cluster démarre
2. `bash scripts/02-build-images.sh` — toutes les images livrées sont buildées
3. `bash scripts/03-deploy.sh` — déploiement complet
4. `bash scripts/04-status.sh` — tous les pods `Running`
5. Ouvrir le dashboard (tunnel minikube, garde le terminal ouvert) :
   `minikube service dashboard -n dataspace` — usines connectées, état EDC,
   données temps réel, métriques du modèle, alertes de panne
6. En direct : `kubectl -n dataspace port-forward svc/sim-data-usine-1 30001:8001`
   puis `curl http://127.0.0.1:30001/usine_1/live_data.csv` — les relevés
   s'ajoutent toutes les 5 secondes

## Nettoyage

```bash
kubectl delete namespace dataspace    # supprime le déploiement
minikube stop                         # arrête le cluster (conservé pour la prochaine fois)
minikube delete                       # supprime le cluster entièrement
```

## Choix techniques

- **Images construites dans le daemon Minikube** (`imagePullPolicy: Never`) :
  pas de registre externe, pas de push Docker Hub.
- **emptyDir par pod** : les données restent locales à chaque usine
  (cahier des charges) ; l'initContainer régénère l'historique au redémarrage.
- **Socle testable dès aujourd'hui** : les pods simulateur utilisent le vrai
  code du Module 1 ; les services des Modules 2/3/5 ont leurs manifests et
  Dockerfiles prêts, activés dès livraison de leur `main.py`.
