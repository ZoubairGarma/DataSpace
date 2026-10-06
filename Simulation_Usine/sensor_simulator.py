"""
Simulateur de capteurs IoT pour une machine industrielle.

Logique : une machine passe par des états NORMAL -> DEGRADATION -> PANNE -> REPARATION -> NORMAL.
Pendant la dégradation, les capteurs dérivent progressivement (température et vibrations montent,
pression baisse) AVANT la panne réelle -- c'est ce signal précoce que le modèle de Machine Learning
du Module 3 devra apprendre à détecter.

L'état affiché ("etat_fonctionnement") reste binaire : "normal" ou "panne", conformément au cahier
des charges, mais les valeurs de capteurs, elles, dérivent en continu.
"""

import random
from datetime import datetime
from enum import Enum

import config


class EtatMachine(Enum):
    NORMAL = "normal"
    DEGRADATION = "degradation"   # interne seulement, invisible dans l'export
    PANNE = "panne"
    REPARATION = "reparation"     # interne seulement


class Machine:
    def __init__(self, usine_id: str, machine_id: str):
        self.usine_id = usine_id
        self.machine_id = machine_id
        self.etat = EtatMachine.NORMAL
        self.compteur_etat = 0
        self.duree_degradation_cible = 0

    def _bruit(self, plage):
        lo, hi = plage
        return random.uniform(lo, hi)

    def _valeurs_normales(self):
        p = config.PLAGES_NORMALES
        return {
            "temperature": round(self._bruit(p["temperature"]), 2),
            "vibrations": round(self._bruit(p["vibrations"]), 3),
            "pression": round(self._bruit(p["pression"]), 2),
            "humidite": round(self._bruit(p["humidite"]), 2),
            "consommation_electrique": round(self._bruit(p["consommation_electrique"]), 2),
        }

    def _valeurs_degradees(self, progression: float):
        """progression va de 0.0 (début dégradation) à 1.0 (juste avant panne)."""
        p = config.PLAGES_NORMALES
        temp_max = p["temperature"][1]
        vib_max = p["vibrations"][1]
        press_min = p["pression"][0]

        return {
            "temperature": round(temp_max + progression * 25 + random.uniform(-1, 1), 2),
            "vibrations": round(vib_max + progression * 2.5 + random.uniform(-0.05, 0.05), 3),
            "pression": round(press_min - progression * 1.5 + random.uniform(-0.1, 0.1), 2),
            "humidite": round(self._bruit(p["humidite"]), 2),  # peu impactée
            "consommation_electrique": round(
                self._bruit(p["consommation_electrique"]) * (1 + progression * 0.4), 2
            ),
        }

    def _valeurs_panne(self):
        p = config.PLAGES_NORMALES
        return {
            "temperature": round(p["temperature"][1] + random.uniform(20, 30), 2),
            "vibrations": round(p["vibrations"][1] + random.uniform(2, 3), 3),
            "pression": round(max(0.5, p["pression"][0] - random.uniform(1.5, 2)), 2),
            "humidite": round(self._bruit(p["humidite"]), 2),
            "consommation_electrique": round(self._bruit(p["consommation_electrique"]) * 0.3, 2),
        }

    def step(self) -> dict:
        """Avance la machine d'un pas de temps et retourne un relevé capteur."""
        if self.etat == EtatMachine.NORMAL:
            valeurs = self._valeurs_normales()
            etat_export = "normal"
            if random.random() < config.PROBA_DEBUT_DEGRADATION:
                self.etat = EtatMachine.DEGRADATION
                self.compteur_etat = 0
                self.duree_degradation_cible = random.randint(
                    config.DUREE_DEGRADATION_MIN, config.DUREE_DEGRADATION_MAX
                )

        elif self.etat == EtatMachine.DEGRADATION:
            progression = min(1.0, self.compteur_etat / self.duree_degradation_cible)
            valeurs = self._valeurs_degradees(progression)
            etat_export = "normal"  # toujours "normal" du point de vue métier, tant que pas en panne
            self.compteur_etat += 1
            if self.compteur_etat >= self.duree_degradation_cible:
                self.etat = EtatMachine.PANNE
                self.compteur_etat = 0

        elif self.etat == EtatMachine.PANNE:
            valeurs = self._valeurs_panne()
            etat_export = "panne"
            self.compteur_etat += 1
            if self.compteur_etat >= 1:  # la panne est détectée/traitée immédiatement
                self.etat = EtatMachine.REPARATION
                self.compteur_etat = 0

        else:  # REPARATION
            valeurs = self._valeurs_normales()
            etat_export = "panne"  # encore hors service pendant la réparation
            self.compteur_etat += 1
            if self.compteur_etat >= config.DUREE_REPARATION:
                self.etat = EtatMachine.NORMAL
                self.compteur_etat = 0

        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "usine_id": self.usine_id,
            "machine_id": self.machine_id,
            **valeurs,
            "etat_fonctionnement": etat_export,
        }
