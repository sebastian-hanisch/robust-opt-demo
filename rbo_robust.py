"""Robuste Kapazitätsplanung mit Budget-Unsicherheit (Bertsimas/Sim) als ein LP über die Ecken der Unsicherheitsmenge.

Unsicherheitsmenge U(gamma, delta) = { D : |D_j - mu_j| <= delta mu_j,  sum_j |D_j - mu_j| / (delta mu_j) <= gamma }.
Die Stufe-2-Kosten sind in D konvex, ihr Maximum über U liegt also an einer Ecke; für ganzzahliges gamma haben die Ecken höchstens gamma
Standorte auf dem Rand (mu_j (1 +- delta)), alle übrigen bei mu_j. Das robuste Problem  min_x  c.x + max_{D in U} Q(x, D)  ist damit
ein LP mit einer Epigraph-Variablen t und je Ecke einem Stufe-2-Block.

Einheiten (je eine Regel, DEMO-PLAYBOOK §1b):
  vertices         alle Ecken von U (Form (V, J))
  solve_robust     min c.x + t  u. d. N.  t >= Q(x, D_v) für alle Ecken v
  in_set           liegt eine Nachfrage in U? (Bedeckung der Referenzszenarien)"""

import itertools

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import block_diag, coo_matrix, csr_matrix, hstack, vstack

import rbo_algorithm as A
from rbo_scenario import Instance


def vertices(mu, delta: float, gamma: int) -> np.ndarray:
    """Alle Ecken von U(gamma, delta): für jede Teilmenge von höchstens `gamma` Standorten jede Vorzeichenwahl, übrige bei mu."""
    mu = np.asarray(mu, dtype=float)
    j = len(mu)
    out = [mu.copy()]
    for k in range(1, min(int(gamma), j) + 1):
        for subset in itertools.combinations(range(j), k):
            for signs in itertools.product((-1.0, 1.0), repeat=k):
                d = mu.copy()
                for idx, sg in zip(subset, signs):
                    d[idx] = mu[idx] * (1.0 + sg * delta)
                out.append(d)
    return np.array(out)


def in_set(demand: np.ndarray, mu, delta: float, gamma: int, tol: float = 1e-9) -> np.ndarray:
    """Für jedes Szenario: liegt es in U(gamma, delta)? (Form (S,) bool)."""
    mu = np.asarray(mu, dtype=float)
    dev = np.abs(demand - mu) / (delta * mu)
    return (dev.max(axis=1) <= 1.0 + tol) & (dev.sum(axis=1) <= gamma + tol)


def solve_robust(inst: Instance, demand_vertices: np.ndarray):
    """Rückgabe (x, Zielwert = c.x + max_v Q(x, D_v))."""
    v_count, j = demand_vertices.shape
    cost, a_cap, a_dem, upper = A.stage2_block(inst)
    nb = cost.size
    n_pre = j + 1                       # x (J) und t
    c_vec = np.concatenate([np.full(j, inst.cap_cost), [1.0], np.zeros(v_count * nb)])
    rows = np.arange(v_count * j)
    cap_x = coo_matrix((-np.ones(v_count * j), (rows, np.tile(np.arange(j), v_count))), shape=(v_count * j, n_pre)).tocsr()
    a_cap_all = hstack([cap_x, block_diag([csr_matrix(a_cap)] * v_count)])
    risk_pre = coo_matrix((-np.ones(v_count), (np.arange(v_count), np.full(v_count, j))), shape=(v_count, n_pre)).tocsr()
    a_risk = hstack([risk_pre, block_diag([csr_matrix(cost.reshape(1, -1))] * v_count)])
    budget_row = coo_matrix((np.ones(j), (np.zeros(j, dtype=int), np.arange(j))), shape=(1, n_pre + v_count * nb)).tocsr()
    a_ub = vstack([a_cap_all, a_risk, budget_row])
    b_ub = np.concatenate([np.zeros(v_count * j), np.zeros(v_count), [inst.budget]])
    a_eq = hstack([csr_matrix((v_count * j, n_pre)), block_diag([csr_matrix(a_dem)] * v_count)])
    bounds = [(0.0, None)] * j + [(0.0, None)] + [(0.0, None if np.isinf(u) else float(u)) for u in upper] * v_count
    res = linprog(c_vec, A_ub=a_ub, b_ub=b_ub, A_eq=a_eq, b_eq=demand_vertices.reshape(-1), bounds=bounds, method="highs")
    if res.status != 0:
        raise RuntimeError(f"Robustes LP nicht lösbar: {res.message}")
    return res.x[:j], float(res.fun)
