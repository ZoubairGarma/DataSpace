# ml-client — Module 3 (client ML fédéré, un par usine)

## À faire (équipe ML)

Dépose ton code **directement dans ce dossier**, avec un point d'entrée :

```
services/ml-client/main.py             ← requis, lancé par le conteneur
services/ml-client/requirements.txt    ← si tu as des dépendances (flwr, scikit-learn...)
```

Le manifeste `k8s/21-ml-clients.yaml` déploie **3 instances** de cette image
(usine_1, usine_2, usine_3) — une par usine, avec ses données locales.

## Contrat à respecter

| Élément        | Valeur                                                        |
|----------------|---------------------------------------------------------------|
| Entrypoint     | `python main.py`                                              |
| Données locales| `$DATA_DIR/$USINE_ID/historical_data.csv` — pré-rempli par un initContainer (30 jours, 8 640 relevés) |

Variables d'environnement injectées par le manifeste :

| Variable         | Exemple                | Rôle                                   |
|------------------|------------------------|----------------------------------------|
| `USINE_ID`       | `usine_1`              | identité de l'usine locale             |
| `DATA_DIR`       | `/data`                | volume local de l'usine                |
| `FLOWER_SERVER`  | `flower-server:9090`   | adresse du serveur de fédération       |

⚠️ Les données ne sortent jamais de l'usine : seul le **modèle** (poids)
transite vers `FLOWER_SERVER` (FedAvg).

Détail complet : `docs/INTEGRATION_CONTRAT.md`.
