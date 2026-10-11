"""Konstanten: Vehikel (wie in der Wurzel der Linie), Regler-Grenzen, Experiment, Farben und Presets."""

# --- Vehikel: Kapazitätsvorhaltung mit Zukauf, Umlagerung und Fehlmenge (identisch zur Wurzel der Linie) --------------------------------------
J = 6
MU_LOW, MU_HIGH = 60, 140
CAP_COST = 1.0
SPOT_JITTER = 0.1
UNMET_MULT = 3.0
SPOT_LIMIT = 0.5
TRANSFER_BASE, TRANSFER_SCALE = 0.3, 0.35
Z0_BINS = 5                     # nur für die Kopie des Kerns
SCENARIOS = 200                 # Vorgabe von `demand_scenarios`, hier unbenutzt
RHO = 0.4
SPOT_MULT = 1.9
SCENARIO_SEED_OFFSET = 7_000_003
BUDGET_TIGHT = 0.95             # „knapp“: Summe der Kapazitäten höchstens 95 % der mittleren Gesamtnachfrage
BUDGET_FREE = 10.0              # „frei“: so weit, dass es nie bindet

# --- Die „wahre“ Verteilung zum Prüfen: eine große Referenzmenge --------------------------------------------------------------------------
REF_SCENARIOS = 600
REF_SEED = 900_001
TAIL_ALPHA = 0.95               # CVaR-Niveau der Prüfung (die teuersten 5 %: 30 von 600 Szenarien)

# --- Regler --------------------------------------------------------------------------------------------------------------------------------
GAMMA_MIN, GAMMA_MAX, DEFAULT_GAMMA = 0, 6, 2
DELTA_MIN, DELTA_MAX, DELTA_STEP, DEFAULT_DELTA = 0.1, 0.6, 0.1, 0.4
SIGMA_MIN, SIGMA_MAX, SIGMA_STEP, DEFAULT_SIGMA = 0.10, 0.60, 0.05, 0.35
BUDGET_CHOICES = ("frei", "knapp")
DEFAULT_BUDGET = "frei"
TRANSFER_CHOICES = ("an", "aus")
DEFAULT_TRANSFER = "an"
SEED_MAX, DEFAULT_SEED = 999999, 7

# --- Vergleich mit dem CVaR-Plan ----------------------------------------------------------------------------------------------------------
CVAR_S = 100                    # Stichprobengröße des Vergleichsplans
CVAR_ALPHA = 0.9
CVAR_DRAW_SEED = 4242

# --- Farben --------------------------------------------------------------------------------------------------------------------------------
COLOR_MEAN_PLAN = "#B5651D"
COLOR_ROBUST = "#2F6B65"
COLOR_CVAR = "#4c78a8"
COLOR_GRID = "rgba(150,150,150,0.75)"

PRESETS = {
    "Standardfall (Voreinstellung)": {
        "gamma": DEFAULT_GAMMA, "delta": DEFAULT_DELTA, "sigma": DEFAULT_SIGMA,
        "budget": DEFAULT_BUDGET, "transfer": DEFAULT_TRANSFER, "seed": DEFAULT_SEED,
    },
    "Alles gleichzeitig schlecht (Γ = 6)": {
        "gamma": 6, "delta": DEFAULT_DELTA, "sigma": DEFAULT_SIGMA,
        "budget": DEFAULT_BUDGET, "transfer": DEFAULT_TRANSFER, "seed": DEFAULT_SEED,
    },
    "Knappes Budget: Robust schadet": {
        "gamma": DEFAULT_GAMMA, "delta": DEFAULT_DELTA, "sigma": DEFAULT_SIGMA,
        "budget": "knapp", "transfer": DEFAULT_TRANSFER, "seed": DEFAULT_SEED,
    },
    "Ohne Umlagerung": {
        "gamma": DEFAULT_GAMMA, "delta": DEFAULT_DELTA, "sigma": DEFAULT_SIGMA,
        "budget": DEFAULT_BUDGET, "transfer": "aus", "seed": DEFAULT_SEED,
    },
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Höchstens zwei Standorte weichen gleichzeitig um 40 % ab, Kapazität frei, Umlagerung an.",
    "Alles gleichzeitig schlecht (Γ = 6)": "Alle sechs Standorte weichen zugleich um 40 % ab: der klassische Worst Case, teuer.",
    "Knappes Budget: Robust schadet": "Das Budget bindet: Robust verteilt nur um und ist im Mittel nicht besser als der Mittelwertplan.",
    "Ohne Umlagerung": "Keine Umlagerung: weniger Möglichkeiten nach der Realisierung, der robuste Plan verändert mehr.",
}
