# dashboard — Module 5 (tableau de bord + API)

## À faire (équipe dashboard)

Dépose ton code **directement dans ce dossier**, avec un point d'entrée :

```
services/dashboard/main.py             ← requis, lancé par le conteneur
services/dashboard/requirements.txt    ← si tu as des dépendances (streamlit, fastapi...)
```

## Contrat à respecter

| Élément    | Valeur                                              |
|------------|-----------------------------------------------------|
| Entrypoint | `python main.py`                                    |
| Port HTTP  | `8500` — exposé en NodePort **30080** par le manifeste |

Variables d'environnement injectées (depuis le ConfigMap `dataspace-config`) :

| Variable           | Valeur                                                                    | Rôle                          |
|--------------------|---------------------------------------------------------------------------|-------------------------------|
| `SIM_DATA_URLS`    | `http://sim-data-usine-1:8001,...`                                        | données temps réel (CSV)      |
| `FLOWER_STATUS_URL`| `http://flower-server:8080`                                               | état/métriques de la fédération |
| `EDC_URLS`         | `http://edc-connector-usine-1:8000,...`                                   | état des connecteurs EDC      |

Le dashboard consomme, il ne stocke rien : les données restent dans les usines.

Détail complet : `docs/INTEGRATION_CONTRAT.md`.
