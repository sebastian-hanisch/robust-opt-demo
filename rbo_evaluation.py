"""Kennzahlen: Mittelwertplan, robuster Plan und CVaR-Plan, ausgewertet auf einer Referenzverteilung; Preis der Robustheit über Γ.

Die Referenzverteilung besteht aus REF_SCENARIOS gleich wahrscheinlichen lognormalen Szenarien (Streuung sigma). Die robuste Unsicherheitsmenge
U(gamma, delta) ist eine Box um die mittlere Nachfrage mit höchstens gamma Standorten am Rand; wie viele Referenzszenarien in ihr liegen, ist die Bedeckung."""

from dataclasses import dataclass

import numpy as np

import rbo_algorithm as A
import rbo_constants as C
from rbo_cvar import PlanValue, cvar_of, evaluate_plan, solve_risk
from rbo_rng import uniform_block
from rbo_robust import in_set, solve_robust, vertices
from rbo_scenario import Instance, demand_scenarios, make_instance


@dataclass(frozen=True)
class Settings:
    gamma: int = C.DEFAULT_GAMMA
    delta: float = C.DEFAULT_DELTA
    sigma: float = C.DEFAULT_SIGMA
    budget: str = C.DEFAULT_BUDGET
    transfer: str = C.DEFAULT_TRANSFER
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class PlanRow:
    gamma: int
    x: tuple[float, ...]
    capacity_ratio: float   # Summe x / Summe mu
    mean: float             # Erwartungswert der Kosten auf der Referenz
    cvar: float             # CVaR_0,95 der Kosten auf der Referenz
    worst: float            # schlimmster Fall in der Unsicherheitsmenge U(gamma, delta)
    coverage: float         # Anteil der Referenzszenarien in U(gamma, delta)
    mean_change_pct: float  # gegen den Mittelwertplan
    cvar_change_pct: float


@dataclass(frozen=True)
class Analysis:
    inst: Instance
    mean_plan: PlanRow       # gamma = 0
    robust: PlanRow          # gamma = Einstellung
    cvar_plan: PlanRow       # Plan, der den CVaR einer Stichprobe minimiert (zum Vergleich)
    curve: tuple             # PlanRow je gamma = 0..J
    box_coverage: float      # Bedeckung der vollen Box (gamma = J)
    mean_worst_in_set: float # schlimmster Fall des Mittelwertplans in derselben Menge U(gamma, delta) wie der robuste Plan
    verdict: str             # 'lohnt' | 'kaum' | 'schadet'


def build_instance(settings: Settings) -> Instance:
    ratio = C.BUDGET_TIGHT if settings.budget == "knapp" else C.BUDGET_FREE
    return make_instance(
        settings.seed, sigma=settings.sigma, rho=C.RHO, budget_ratio=ratio,
        spot_mult=C.SPOT_MULT, transfer=settings.transfer == "an",
    )


def reference_demand(inst: Instance) -> np.ndarray:
    demand, _ = demand_scenarios(inst, C.REF_SEED, count=C.REF_SCENARIOS)
    return demand


def sample_scenarios(demand: np.ndarray, seed: int, s: int) -> np.ndarray:
    """S Ziehungen MIT Zurücklegen aus den gleich wahrscheinlichen Szenarien der Referenzverteilung (Form (s, J))."""
    idx = np.minimum((uniform_block(seed, s) * len(demand)).astype(int), len(demand) - 1)
    return demand[idx]


def _row(inst, x, gamma, delta, ref, mean_ref, cvar_ref) -> PlanRow:
    pv: PlanValue = evaluate_plan(inst, np.asarray(x), ref, C.TAIL_ALPHA)
    verts = vertices(inst.mu, delta, gamma)
    totals = evaluate_plan(inst, np.asarray(x), verts, 0.5).costs
    cov = float(in_set(ref, inst.mu, delta, gamma).mean())
    return PlanRow(
        gamma=gamma, x=tuple(float(v) for v in x), capacity_ratio=float(np.sum(x) / np.sum(inst.mu)),
        mean=pv.mean, cvar=pv.cvar, worst=float(max(totals)), coverage=cov,
        mean_change_pct=100.0 * (pv.mean / mean_ref - 1.0) if mean_ref else 0.0,
        cvar_change_pct=100.0 * (pv.cvar / cvar_ref - 1.0) if cvar_ref else 0.0,
    )


def verdict_of(mean_change: float, cvar_change: float) -> str:
    if cvar_change <= -3.0 and mean_change < 30.0:
        return "lohnt"
    if mean_change >= 1.0 and cvar_change > -1.0:
        return "schadet"
    return "kaum"


def analyse(settings: Settings) -> Analysis:
    inst = build_instance(settings)
    ref = reference_demand(inst)
    mu = np.asarray(inst.mu)
    x0, _ = solve_robust(inst, mu[None, :])           # Plan für die mittlere Nachfrage
    base = evaluate_plan(inst, x0, ref, C.TAIL_ALPHA)
    curve = []
    for g in range(0, C.GAMMA_MAX + 1):
        x = x0 if g == 0 else solve_robust(inst, vertices(mu, settings.delta, g))[0]
        curve.append(_row(inst, x, g, settings.delta, ref, base.mean, base.cvar))
    sample = sample_scenarios(ref, C.CVAR_DRAW_SEED, C.CVAR_S)
    x_cvar, _ = solve_risk(inst, sample, C.CVAR_ALPHA, 1.0)
    cvar_row = _row(inst, x_cvar, settings.gamma, settings.delta, ref, base.mean, base.cvar)
    rob = curve[settings.gamma]
    verts = vertices(mu, settings.delta, settings.gamma)
    mean_worst = float(max(evaluate_plan(inst, x0, verts, 0.5).costs))
    return Analysis(inst, curve[0], rob, cvar_row, tuple(curve), curve[C.GAMMA_MAX].coverage, mean_worst,
                    verdict_of(rob.mean_change_pct, rob.cvar_change_pct))


def knee(curve) -> int | None:
    """Kleinstes gamma, das mindestens die Hälfte des Schwanznutzens (CVaR-Absenkung bis gamma = J) holt; None ohne Nutzen."""
    total = -curve[-1].cvar_change_pct
    if total < 1.0:
        return None
    for row in curve:
        if -row.cvar_change_pct >= 0.5 * total:
            return row.gamma
    return None
