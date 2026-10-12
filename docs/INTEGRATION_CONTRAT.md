# Contrat d'intégration — Modules 2, 3, 5 → déploiement Module 4

Ce document définit **ce que le Module 4 attend de votre code** pour qu'il soit
dockerisé et déployé dans le cluster Minikube **sans aucune modification du
Module 4**. Si vous respectez ce contrat, l'intégration est automatique :

```
ton code dans services/<ton-service>/  →  bash scripts/02-build-images.sh  →  bash scripts/03-deploy.sh
```

## Règle universelle (les 3 modules)

1. **Point d'entrée unique** : `services/<ton-service>/main.py`, lancé par
   `python main.py`. Il doit tourner en continu (pas un script qui finit).
2. **Dépendances** : liste-les dans `services/<ton-service>/requirements.txt`
   (le Dockerfile les installe automatiquement).
3. **Ne touche à rien en dehors de ton dossier** `services/<ton-service>/` :
   ni `k8s/`, ni `scripts/`, ni `Simulation_Usine/`, ni les Dockerfiles.
4. **Configuration par variables d'environnement** (jamais de valeurs en dur) :
   le cluster injecte tout ce qui est listé ci-dessous.

Conventions : identifiants d'usines au format `usine_1`, `usine_2`, `usine_3`
(underscores, comme dans les données). Le préfixe `USINE_ID` identifie toujours
l'usine locale du pod.

---

## Module 3 — Équipe ML

### `services/flower-server/` — serveur de fédération (1 instance dans le cluster)

| Élément     | Contrat                                                        |
|-------------|----------------------------------------------------------------|
| Entrypoint  | `python main.py`, écoute **en continu**                        |
| Port gRPC   | `9090` — serveur Flower (stratégie FedAvg)                     |
| Port HTTP   | `8080` — status/métriques JSON pour le dashboard               |

Le dashboard (Module 5) interrogera `http://flower-server:8080` — expose au
minimum un endpoint racine ou `/status` renvoyant l'état de la fédération
(round en cours, nombre de clients connectés, métriques du modèle global :
Accuracy / Precision / Recall / F1).

### `services/ml-client/` — client fédéré (3 instances : une par usine)

Variables d'environnement injectées :

| Variable        | Exemple              | Signification                              |
|-----------------|----------------------|--------------------------------------------|
| `USINE_ID`      | `usine_1`            | identité de l'usine locale du pod          |
| `DATA_DIR`      | `/data`              | volume local **de l'usine uniquement**     |
| `FLOWER_SERVER` | `flower-server:9090` | adresse du serveur de fédération           |

**Données d'entraînement** — un initContainer a déjà généré l'historique :

```
$DATA_DIR/$USINE_ID/historical_data.csv    # 30 jours, 8 640 relevés (3 machines)
```

Colonnes : `timestamp, usine_id, machine_id, temperature, vibrations,
pression, humidite, consommation_electrique, etat_fonctionnement`.
La cible à prédire est `etat_fonctionnement` (`normal`/`panne`) ; les signes
précurseurs sont la dérive de `temperature`, `vibrations`, `pression`
(voir `Simulation_Usine/sensor_simulator.py`).

**Règle du Data Space** : les lignes de données ne sortent JAMAIS du pod.
Seuls les **poids du modèle** sont envoyés à `FLOWER_SERVER` (FedAvg).

---

## Module 2 — Équipe EDC (connecteurs)

### `services/edc-connector/` — 3 instances : une par usine

| Élément    | Contrat                              |
|------------|--------------------------------------|
| Entrypoint | `python main.py`, écoute en continu  |
| Port HTTP  | `8000`                               |

Variables d'environnement injectées : `USINE_ID` (`usine_1`...) et `DATA_DIR`
(`/data`, contient déjà `$DATA_DIR/$USINE_ID/historical_data.csv`).

Endpoints attendus par le dashboard (réponses JSON) :

| Endpoint          | Rôle                                        |
|-------------------|---------------------------------------------|
| `GET /catalog`    | jeux de données publiés par l'usine         |
| `GET /contracts`  | négociations / contrats en cours            |
| `GET /policies`   | politiques d'accès appliquées               |
| `GET /logs`       | journal des échanges (traçabilité)          |

Adresses des autres connecteurs depuis un pod (si le Data Space doit
fédérer la découverte) : `edc-connector-usine-1:8000`,
`edc-connector-usine-2:8000`, `edc-connector-usine-3:8000`.

---

## Module 5 — Équipe dashboard

### `services/dashboard/` — 1 instance

| Élément    | Contrat                                                     |
|------------|-------------------------------------------------------------|
| Entrypoint | `python main.py`, écoute en continu                         |
| Port HTTP  | `8500` — exposé en NodePort **30080** (accès : `minikube service dashboard -n dataspace`) |

Variables d'environnement injectées (listes séparées par des virgules) :

| Variable            | Valeur                                                                  |
|---------------------|-------------------------------------------------------------------------|
| `SIM_DATA_URLS`     | `http://sim-data-usine-1:8001,http://sim-data-usine-2:8001,http://sim-data-usine-3:8001` |
| `FLOWER_STATUS_URL` | `http://flower-server:8080`                                             |
| `EDC_URLS`          | `http://edc-connector-usine-1:8000,http://edc-connector-usine-2:8000,http://edc-connector-usine-3:8000` |

**Données temps réel disponibles dès maintenant** sur chaque `SIM_DATA_URLS`
(serveur HTTP fourni par le Module 4, réponses CORS `*`) :

```
GET /usine_1/live_data.csv          # flux live (append toutes les 5 s)
GET /usine_1/historical_data.csv    # historique 30 jours
GET /healthz                        # {"status": "ok"}
```

Le dashboard consomme, il ne stocke rien — les données restent dans les usines.

---

## Checklist avant de pousser ton code

- [ ] `services/<ton-service>/main.py` existe et tourne en boucle
- [ ] écoute sur le bon port (voir tableau ci-dessus)
- [ ] lit sa config depuis les variables d'environnement du contrat
- [ ] `requirements.txt` à jour
- [ ] test local : `python main.py` avec les variables exportées à la main
- [ ] puis : `bash scripts/02-build-images.sh && bash scripts/03-deploy.sh`
