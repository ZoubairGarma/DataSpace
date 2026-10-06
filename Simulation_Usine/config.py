"""
Configuration du simulateur IoT — Industrial Data Space for Predictive Maintenance
"""

# Les 3 usines du projet (chacune stocke ses données localement, séparément)
USINES = ["usine_1", "usine_2", "usine_3"]

# Nombre de machines simulées par usine (chaque machine = une ligne de production)
MACHINES_PAR_USINE = 3

# Plages "normales" de fonctionnement (utilisées comme point de départ + bruit)
PLAGES_NORMALES = {
    "temperature": (55.0, 70.0),        # °C
    "vibrations": (0.2, 0.8),           # mm/s (amplitude RMS)
    "pression": (4.0, 6.0),             # bar
    "humidite": (30.0, 50.0),           # %
    "consommation_electrique": (10.0, 25.0),  # kW
}

# Dossier de stockage local (chaque usine garde ses données séparées, pas de partage direct)
DATA_DIR = "data"

# Fréquence des relevés
INTERVALLE_SECONDES = 5          # pour le mode live (simulation temps réel)
FREQUENCE_HISTORIQUE_MIN = 15    # un relevé toutes les 15 min pour l'historique
JOURS_HISTORIQUE = 30            # 30 jours de données simulées

# Paramètres du cycle de dégradation (pour générer des signaux prédictifs réalistes)
PROBA_DEBUT_DEGRADATION = 0.002   # probabilité, à chaque pas, qu'une machine saine commence à se dégrader
DUREE_DEGRADATION_MIN = 20        # nombre de pas avant panne une fois la dégradation commencée
DUREE_DEGRADATION_MAX = 80
DUREE_REPARATION = 5              # nombre de pas pour revenir à "normal" après une panne
