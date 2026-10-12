# edc-connector — Module 2 (connecteur Eclipse Dataspace Components)

## À faire (équipe EDC)

Dépose ton code **directement dans ce dossier**, avec un point d'entrée :

```
services/edc-connector/main.py             ← requis, lancé par le conteneur
services/edc-connector/requirements.txt    ← si tu as des dépendances (fastapi, uvicorn...)
```

Le manifeste `k8s/30-edc-connectors.yaml` déploie **3 instances** de cette
image (une par usine), chacune avec ses données locales.

## Contrat à respecter

| Élément     | Valeur                                     |
|-------------|--------------------------------------------|
| Entrypoint  | `python main.py`                           |
| Port HTTP   | `8000` (le Service K8s expose ce port)     |

Endpoints attendus par le dashboard (Module 5) :

| Endpoint          | Rôle                                              |
|-------------------|---------------------------------------------------|
| `GET /catalog`    | jeux de données publiés par l'usine               |
| `GET /contracts`  | négociations / contrats en cours                  |
| `GET /policies`   | politiques d'accès appliquées                     |
| `GET /logs`       | journal des échanges (traçabilité)                |

Variables d'environnement injectées :

| Variable   | Exemple   | Rôle                     |
|------------|-----------|--------------------------|
| `USINE_ID` | `usine_1` | identité de l'usine      |
| `DATA_DIR` | `/data`   | données locales (30 j d'historique pré-généré par initContainer) |

Détail complet : `docs/INTEGRATION_CONTRAT.md`.
