"""CVaR als Zielfunktion der zweistufigen Kapazitätsplanung (Rockafellar/Uryasev) und Auswertung eines Plans.

Einheiten (je eine Regel, DEMO-PLAYBOOK §1b):
  stage2_costs   Stufe-2-Kosten je Szenario bei festem Plan (ein Block-LP)
  cvar_of        CVaR_alpha einer Kostenliste: Mittel der teuersten (1 - alpha)-Anteile, mit Bruchteil am Rand
  solve_risk     min  c.x + (1 - lam) E[Q] + lam CVaR_alpha[Q]   als ein LP über alle Szenarien
  evaluate_plan  Erwartungswert, CVaR und Verteilung der Gesamtkosten eines festen Plans auf einer Szenarienmenge"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import block_diag, coo_matrix, csr_matrix, hstack, vstack

import rbo_algorithm as A
from rbo_scenario import Instance


def stage2_costs(inst: Instance, demand: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Stufe-2-Kosten Q(x, xi_s) je Szenario (S,)."""
    s_count = demand.shape[0]
    cost, a_cap, a_dem, upper = A.stage2_block(inst)
    nb = cost.size
    bounds = [(0.0, None if np.isinf(u) else float(u)) for u in upper] * s_count
    res = linprog(np.tile(cost, s_count), A_ub=block_diag([csr_matrix(a_cap)] * s_count),
                  b_ub=np.tile(np.asarray(x, dtype=float), s_count), A_eq=block_diag([csr_matrix(a_dem)] * s_count),
                  b_eq=demand.reshape(-1), bounds=bounds, method="highs")
    if res.status != 0:
        raise RuntimeError(f"Teilproblem nicht lösbar: {res.message}")
    return res.x.reshape(s_count, nb) @ cost


def cvar_of(values, alpha: float) -> float:
    """CVaR_alpha: Mittel der teuersten (1 - alpha) * n Werte; ein nicht ganzzahliger Rand zählt anteilig (Rockafellar/Uryasev)."""
    v = np.sort(np.asarray(values, dtype=float))[::-1]
    k = (1.0 - alpha) * len(v)
    whole = int(np.floor(k + 1e-9))
    frac = k - whole
    total = float(v[:whole].sum())
    if frac > 1e-9 and whole < len(v):
        total += frac * float(v[whole])
    return total / k


def solve_risk(inst: Instance, demand: np.ndarray, alpha: float, lam: float):
    """Rückgabe (x, Zielwert). Zielwert = c.x + (1 - lam) mean(Q) + lam CVaR_alpha(Q).

    Variablen: x (J), eta (1, frei), z_s >= 0 (S), dann je Szenario ein Stufe-2-Block (nb); Schnitt z_s >= Q_s - eta."""
    s_count, j = demand.shape
    cost, a_cap, a_dem, upper = A.stage2_block(inst)
    nb = cost.size
    w = 1.0 / s_count
    n_x, n_eta = j, 1
    n_pre = n_x + n_eta + s_count
    c_vec = np.concatenate([
        np.full(j, inst.cap_cost), [lam], np.full(s_count, lam * w / (1.0 - alpha)), np.tile((1.0 - lam) * w * cost, s_count),
    ])
    # Kapazität: sum_k y[j,k] - x_j <= 0 je (Szenario, Standort)
    rows = np.arange(s_count * j)
    cap_x = coo_matrix((-np.ones(s_count * j), (rows, np.tile(np.arange(j), s_count))), shape=(s_count * j, n_pre)).tocsr()
    a_cap_all = hstack([cap_x, block_diag([csr_matrix(a_cap)] * s_count)])
    # Risiko: Q_s - eta - z_s <= 0
    risk_pre = coo_matrix(
        (np.concatenate([-np.ones(s_count), -np.ones(s_count)]),
         (np.concatenate([np.arange(s_count), np.arange(s_count)]),
          np.concatenate([np.full(s_count, n_x), n_x + n_eta + np.arange(s_count)]))),
        shape=(s_count, n_pre)).tocsr()
    risk_blocks = block_diag([csr_matrix(cost.reshape(1, -1))] * s_count)
    a_risk = hstack([risk_pre, risk_blocks])
    budget_row = coo_matrix((np.ones(j), (np.zeros(j, dtype=int), np.arange(j))), shape=(1, n_pre + s_count * nb)).tocsr()
    a_ub = vstack([a_cap_all, a_risk, budget_row])
    b_ub = np.concatenate([np.zeros(s_count * j), np.zeros(s_count), [inst.budget]])
    a_eq = hstack([csr_matrix((s_count * j, n_pre)), block_diag([csr_matrix(a_dem)] * s_count)])
    bounds = [(0.0, None)] * n_x + [(None, None)] + [(0.0, None)] * s_count
    bounds += [(0.0, None if np.isinf(u) else float(u)) for u in upper] * s_count
    res = linprog(c_vec, A_ub=a_ub, b_ub=b_ub, A_eq=a_eq, b_eq=demand.reshape(-1), bounds=bounds, method="highs")
    if res.status != 0:
        raise RuntimeError(f"Risiko-LP nicht lösbar: {res.message}")
    return res.x[:j], float(res.fun)


@dataclass(frozen=True)
class PlanValue:
    mean: float            # Erwartungswert der Gesamtkosten
    cvar: float            # CVaR_alpha der Gesamtkosten
    costs: tuple[float, ...]   # Gesamtkosten je Szenario


def evaluate_plan(inst: Instance, x: np.ndarray, demand: np.ndarray, alpha: float) -> PlanValue:
    totals = inst.cap_cost * float(np.sum(x)) + stage2_costs(inst, demand, x)
    return PlanValue(float(totals.mean()), cvar_of(totals, alpha), tuple(float(v) for v in totals))
