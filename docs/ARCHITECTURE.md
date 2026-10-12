# Architecture Module 4 — Industrial Data Space sur Kubernetes

## Vue d'ensemble

```mermaid
flowchart TB
    subgraph cluster["Cluster Minikube — namespace : dataspace"]
        subgraph u1["Pod simulateur-usine-1 (données 100% locales)"]
            i1["initContainer<br/>historique 30 j"] --> v1[("emptyDir<br/>/app/data")]
            v1 --> s1["live-stream<br/>(Module 1)"]
            v1 --> d1["data-server :8001<br/>(CSV en HTTP)"]
        end
        subgraph u2["Pod simulateur-usine-2"]
            i2["initContainer"] --> v2[("emptyDir")] --> s2["live-stream"]; v2 --> d2["data-server :8001"]
        end
        subgraph u3["Pod simulateur-usine-3"]
            i3["initContainer"] --> v3[("emptyDir")] --> s3["live-stream"]; v3 --> d3["data-server :8001"]
        end

        subgraph mlpods["Clients ML (Module 3) — un par usine"]
            mc1["ml-client-usine-1<br/>entraîne sur données locales"]
            mc2["ml-client-usine-2"]
            mc3["ml-client-usine-3"]
        end

        fs["flower-server<br/>FedAvg :9090 / status :8080"]

        subgraph edcpods["Connecteurs EDC (Module 2) — un par usine"]
            e1["edc-connector-usine-1 :8000"]
            e2["edc-connector-usine-2 :8000"]
            e3["edc-connector-usine-3 :8000"]
        end

        dash["dashboard (Module 5)<br/>:8500 → NodePort 30080"]
    end

    d1 -. "poids uniquement (FedAvg)" .- mc1
    mc1 -->|"poids du modèle"| fs
    mc2 --> fs
    mc3 --> fs
    fs -.->|"modèle global"| mc1

    dash -->|"CSV temps réel"| d1 & d2 & d3
    dash -->|"status fédération"| fs
    dash -->|"/catalog /contracts /logs"| e1 & e2 & e3

    navigateur["Navigateur (démo)"] -->|"http://ip:30080"| dash
    navigateur -->|"http://ip:30001..3/...csv"| d1 & d2 & d3
```

## Souveraineté des données — principe directeur

Chaque usine est un pod autonome dont les données vivent dans un volume
`emptyDir` **local au pod** :

- Aucune base centrale, aucun partage de fichiers entre usines.
- Les clients ML ne transmettent au serveur de fédération que les **poids**
  du modèle (apprentissage fédéré FedAvg) — jamais les relevés capteurs.
- Les connecteurs EDC négocient l'accès aux données selon des politiques
  (contrats) — c'est le Data Space.
- Le dashboard lit les flux par HTTP mais ne stocke rien.

## Composants et responsabilités

| Composant | Image | Rôle | Module |
|---|---|---|---|
| `simulateur-usine-{1,2,3}` | `dataspace/simulateur` | historique + live + serveur CSV | 1 (existant) + 4 |
| `flower-server` | `dataspace/flower-server` | agrégation FedAvg, status HTTP | 3 |
| `ml-client-usine-{1,2,3}` | `dataspace/ml-client` | entraînement local | 3 |
| `edc-connector-usine-{1,2,3}` | `dataspace/edc-connector` | publication/contrats/politiques/journal | 2 |
| `dashboard` | `dataspace/dashboard` | supervision + alertes | 5 |

## Ports et exposition

| Service | Port interne | exposition |
|---|---|---|
| data-server (par usine) | 8001 | NodePort **30001 / 30002 / 30003** |
| flower-server gRPC | 9090 | ClusterIP |
| flower-server HTTP | 8080 | ClusterIP |
| edc-connector (par usine) | 8000 | ClusterIP |
| dashboard | 8500 | NodePort **30080** |

> **Accès depuis Windows (driver docker)** : les NodePorts ne sont pas
> routables depuis l'hôte. Utiliser `minikube service <svc> -n dataspace`
> ou `kubectl port-forward` (voir `scripts/04-status.sh`).

## Chaîne d'intégration (build → deploy)

```
services/<svc>/main.py  ──(02-build-images.sh, build dans le daemon minikube)──▶  image dataspace/<svc>
k8s/*.yaml              ──(03-deploy.sh, kubectl apply)──▶  namespace dataspace
imagePullPolicy: Never  ⇒  aucun registre externe requis
```

Les images sont construites **dans le daemon Docker de Minikube**
(`eval $(minikube docker-env)`), donc pas de push vers Docker Hub :
`imagePullPolicy: Never` force Kubernetes à utiliser l'image locale.

## Cycle de vie des pods simulateur

```
Pod démarre
  └─ initContainer generate_one.py   → 30 j d'historique dans /app/data (8 640 relevés)
  └─ live-stream (live_stream.py)    → append live_data.csv toutes les 5 s
  └─ data-server (serve_data.py)     → GET /usine_N/{live,historical}_data.csv + /healthz
```

Si le pod redémarre, l'emptyDir est réinitialisé et l'historique est régénéré :
le système est auto-suffisant, aucune donnée à monter de l'extérieur.
