"""Orakel-Tests (DEMO-PLAYBOOK §12): anderer Rechenweg als der Kern.

1. Dasselbe robuste Problem als eigenes LP in OR-Tools (GLOP, Schleifen statt Blockmatrizen).
2. Zufallsprobe: kein Punkt der Unsicherheitsmenge (zufällig, nicht nur Ecken) überschreitet das berechnete Maximum (Konvexität: Ecken genügen).
3. Bedeckung: Anteil der Referenzszenarien in der Menge gegen eine Schleife ohne Vektorisierung."""

import dataclasses

import numpy as np
import pytest

import rbo_evaluation as ev
import rbo_scenario as S
from rbo_cvar import stage2_costs
from rbo_robust import in_set, solve_robust, vertices

pywraplp = pytest.importorskip("ortools.linear_solver.pywraplp")


def _glop_robust_value(inst, verts) -> float:
    j_count, v_count = inst.n, verts.shape[0]
    solver = pywraplp.Solver.CreateSolver("GLOP")
    inf = solver.infinity()
    x = [solver.NumVar(0, inf, f"x{j}") for j in range(j_count)]
    t = solver.NumVar(0, inf, "t")
    solver.Add(sum(x) <= inst.budget)
    for v in range(v_count):
        q_terms = []
        y = {}
        for j in range(j_count):
            for k in range(j_count):
                y[j, k] = solver.NumVar(0, inf if (inst.transfer or j == k) else 0.0, f"y{v}_{j}_{k}")
                q_terms.append((y[j, k], inst.transfer_cost[j][k]))
        for k in range(j_count):
            u = solver.NumVar(0, inst.spot_limit[k], f"u{v}_{k}")
            w = solver.NumVar(0, inf, f"w{v}_{k}")
            q_terms.append((u, inst.spot[k]))
            q_terms.append((w, inst.unmet))
            solver.Add(sum(y[j, k] for j in range(j_count)) + u + w == float(verts[v, k]))
        for j in range(j_count):
            solver.Add(sum(y[j, k] for k in range(j_count)) <= x[j])
        solver.Add(sum(c * var for var, c in q_terms) <= t)
    obj = solver.Objective()
    for j in range(j_count):
        obj.SetCoefficient(x[j], inst.cap_cost)
    obj.SetCoefficient(t, 1.0)
    obj.SetMinimization()
    assert solver.Solve() == pywraplp.Solver.OPTIMAL
    return obj.Value()


@pytest.mark.parametrize("transfer", [True, False])
@pytest.mark.parametrize("gamma", [1, 2])
def test_robust_lp_matches_independent_glop_model(transfer, gamma):
    inst = dataclasses.replace(
        S.make_instance(51, sigma=0.4, rho=0.4, budget_ratio=0.9, spot_mult=1.6, transfer=transfer),
        mu=(80.0, 120.0, 100.0), spot=(1.7, 1.5, 1.9), spot_limit=(40.0, 60.0, 50.0),
        transfer_cost=((0.0, 0.3, 0.5), (0.3, 0.0, 0.4), (0.5, 0.4, 0.0)), budget=1e9,
    )
    verts = vertices(inst.mu, 0.4, gamma)
    assert solve_robust(inst, verts)[1] == pytest.approx(_glop_robust_value(inst, verts), rel=1e-7)


def test_no_random_point_of_the_set_exceeds_the_vertex_maximum():
    inst = ev.build_instance(ev.Settings())
    mu = np.asarray(inst.mu)
    gamma, delta = 2, 0.4
    x, obj = solve_robust(inst, vertices(mu, delta, gamma))
    rng = np.random.default_rng(5)
    pts = []
    while len(pts) < 150:
        d = mu * (1 + delta * rng.uniform(-1, 1, len(mu)))
        if in_set(d[None, :], mu, delta, gamma)[0]:
            pts.append(d)
    totals = inst.cap_cost * x.sum() + stage2_costs(inst, np.array(pts), x)
    assert totals.max() <= obj + 1e-6


def test_coverage_matches_a_plain_loop():
    inst = ev.build_instance(ev.Settings())
    mu = np.asarray(inst.mu)
    ref = ev.reference_demand(inst)
    delta, gamma = 0.4, 2
    loop = 0
    for d in ref:
        dev = [abs(d[j] - mu[j]) / (delta * mu[j]) for j in range(len(mu))]
        if max(dev) <= 1.0 + 1e-9 and sum(dev) <= gamma + 1e-9:
            loop += 1
    assert in_set(ref, mu, delta, gamma).sum() == loop
