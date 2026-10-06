"""
Génère des relevés IoT en continu, un peu comme le feraient de vrais capteurs.
Utile pour le Module 5 (tableau de bord "temps réel") et pour tester l'API FastAPI.

Usage :
    python live_stream.py                # toutes les usines
    python live_stream.py --usine usine_1  # une seule usine

Chaque relevé est à la fois :
  - affiché dans la console (pour debug/démo)
  - ajouté (append) au CSV local de l'usine, data/<usine>/live_data.csv
"""

import argparse
import csv
import os
import time

import config
from sensor_simulator import Machine

CHAMPS = [
    "timestamp", "usine_id", "machine_id",
    "temperature", "vibrations", "pression", "humidite", "consommation_electrique",
    "etat_fonctionnement",
]


def init_csv(usine_id: str) -> str:
    dossier = os.path.join(config.DATA_DIR, usine_id)
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, "live_data.csv")
    if not os.path.exists(chemin):
        with open(chemin, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CHAMPS).writeheader()
    return chemin


def run(usines):
    machines_par_usine = {
        usine_id: [
            Machine(usine_id, f"machine_{i+1}")
            for i in range(config.MACHINES_PAR_USINE)
        ]
        for usine_id in usines
    }
    chemins_csv = {usine_id: init_csv(usine_id) for usine_id in usines}

    print(f"Simulation en direct démarrée pour : {', '.join(usines)}")
    print(f"(Ctrl+C pour arrêter)\n")

    try:
        while True:
            for usine_id, machines in machines_par_usine.items():
                with open(chemins_csv[usine_id], "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=CHAMPS)
                    for machine in machines:
                        ligne = machine.step()
                        writer.writerow(ligne)
                        alerte = " ⚠️  PANNE" if ligne["etat_fonctionnement"] == "panne" else ""
                        print(
                            f"[{usine_id}] {ligne['machine_id']} | "
                            f"T={ligne['temperature']}°C  "
                            f"Vib={ligne['vibrations']}mm/s  "
                            f"P={ligne['pression']}bar{alerte}"
                        )
            time.sleep(config.INTERVALLE_SECONDES)
    except KeyboardInterrupt:
        print("\nSimulation arrêtée.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--usine", help="Simuler une seule usine (ex: usine_1)")
    args = parser.parse_args()

    usines = [args.usine] if args.usine else config.USINES
    run(usines)
