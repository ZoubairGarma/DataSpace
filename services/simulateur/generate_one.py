"""
Wrapper Module 4 — génère l'historique d'UNE seule usine dans le pod.

Réutilise le code du Module 1 sans le modifier : on surcharge config.USINES
avec la variable d'environnement USINE_ID avant d'appeler le générateur.

Variables d'environnement :
    USINE_ID   usine à simuler (ex: usine_1)   — requis
    DATA_DIR   dossier racine des données (défaut: config.DATA_DIR)
"""

import os
import sys

import config

usine_id = os.environ.get("USINE_ID", "").strip()
if not usine_id:
    sys.exit("ERREUR : variable d'environnement USINE_ID requise (ex: usine_1)")
if usine_id not in config.USINES:
    sys.exit(f"ERREUR : USINE_ID inconnu '{usine_id}' (attendus : {config.USINES})")

config.USINES = [usine_id]
if os.environ.get("DATA_DIR"):
    config.DATA_DIR = os.environ["DATA_DIR"]

import generate_historical_data

generate_historical_data.main()
