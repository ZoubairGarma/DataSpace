"""
Génère des jeux de données historiques pour les 3 usines.
Chaque usine a son propre fichier CSV, stocké localement (data/<usine>/historical_data.csv) --
conformément au cahier des charges : "Les données restent stockées localement".

Usage :
    python generate_historical_data.py
"""

import csv
import os
from datetime import datetime, timedelta

import config
from sensor_simulator import Machine

CHAMPS = [
    "timestamp", "usine_id", "machine_id",
    "temperature", "vibrations", "pression", "humidite", "consommation_electrique",
    "etat_fonctionnement",
]


def generer_pour_usine(usine_id: str):
    dossier = os.path.join(config.DATA_DIR, usine_id)
    os.makedirs(dossier, exist_ok=True)
    chemin_csv = os.path.join(dossier, "historical_data.csv")

    machines = [
        Machine(usine_id, f"machine_{i+1}")
        for i in range(config.MACHINES_PAR_USINE)
    ]

    nb_points = int(
        (config.JOURS_HISTORIQUE * 24 * 60) / config.FREQUENCE_HISTORIQUE_MIN
    )
    t0 = datetime.now() - timedelta(days=config.JOURS_HISTORIQUE)

    with open(chemin_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHAMPS)
        writer.writeheader()

        for point in range(nb_points):
            timestamp_simule = t0 + timedelta(
                minutes=point * config.FREQUENCE_HISTORIQUE_MIN
            )
            for machine in machines:
                ligne = machine.step()
                ligne["timestamp"] = timestamp_simule.isoformat(timespec="seconds")
                writer.writerow(ligne)

    print(f"[{usine_id}] {nb_points * len(machines)} relevés écrits dans {chemin_csv}")


def main():
    print(f"Génération de {config.JOURS_HISTORIQUE} jours d'historique "
          f"({config.MACHINES_PAR_USINE} machines/usine, "
          f"1 relevé/{config.FREQUENCE_HISTORIQUE_MIN} min)...\n")
    for usine_id in config.USINES:
        generer_pour_usine(usine_id)
    print("\nTerminé. Les données de chaque usine sont isolées dans data/<usine_id>/")


if __name__ == "__main__":
    main()
