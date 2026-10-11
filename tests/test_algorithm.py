"""Einheiten: Ecken der Unsicherheitsmenge, Zugehörigkeit, robustes LP an der Mini-Instanz; Ergebnisse von Hand gerechnet."""

import itertools

import numpy as np
import pytest

import rbo_constants as C
import rbo_evaluation as ev
from rbo_cvar import evaluate_plan, stage2_costs
from rbo_robust import in_set, solve_robust, vertices


def test_vertex_counts():
    mu = np.arange(1, 7) * 10.0
    assert len(vertices(mu, 0.4, 0)) == 1
    assert len(vertices(mu, 0.4, 1)) == 1 + 12
    assert len(vertices(mu, 0.4, 2)) == 1 + 12 + 60
    assert len(vertices(mu, 0.4, 6)) == 3 ** 6


def test_vertices_stay_in_the_set_and_use_the_budget():
    mu = np.array([100.0, 60.0, 80.0])
    v = vertices(mu, 0.5, 2)
    assert in_set(v, mu, 0.5, 2).all()
    dev = np.abs(v - mu) / (0.5 * mu)
    assert (dev.sum(axis=1) <= 2 + 1e-9).all()
    assert set(np.round(dev.sum(axis=1)).astype(int)) == {0, 1, 2}


def test_in_set_hand_values():
    mu = np.array([100.0, 60.0])
    d = np.array([[100.0, 60.0], [150.0, 60.0], [150.0, 90.0], [160.0, 60.0]])
    # delta 0,5: (150, 60) liegt auf dem Rand (Abweichung 1), (150, 90) braucht Budget 2, (160, 60) überschreitet die Box
    assert list(in_set(d, mu, 0.5, 1)) == [True, True, False, False]
    assert list(in_set(d, mu, 0.5, 2)) == [True, True, True, False]


def test_robust_with_gamma_zero_is_the_expected_value_plan(mini):
    mu = np.asarray(mini.mu)
    x, obj = solve_robust(mini, vertices(mu, 0.5, 0))
    # bei bekannter Nachfrage kauft man genau sie: 160 Einheiten Vorhaltung, Kosten 160
    assert obj == pytest.approx(160.0)
    assert x == pytest.approx(mu)


def test_robust_objective_equals_worst_vertex_of_its_own_plan(mini):
    mu = np.asarray(mini.mu)
    v = vertices(mu, 0.5, 1)
    x, obj = solve_robust(mini, v)
    totals = mini.cap_cost * x.sum() + stage2_costs(mini, v, x)
    assert obj == pytest.approx(totals.max(), rel=1e-7)


def test_robust_beats_every_grid_plan_in_the_worst_case(mini):
    mu = np.asarray(mini.mu)
    v = vertices(mu, 0.5, 1)
    _, obj = solve_robust(mini, v)
    best_grid = min(
        a + b + stage2_costs(mini, v, np.array([a, b])).max()
        for a, b in itertools.product(np.arange(0.0, 201.0, 10.0), repeat=2)
    )
    assert obj <= best_grid + 1e-6
    assert best_grid <= obj + 5.0     # Raster 10: das Optimum liegt höchstens wenige Einheiten darüber


def test_worst_case_never_decreases_with_gamma():
    inst = ev.build_instance(ev.Settings())
    mu = np.asarray(inst.mu)
    objs = [solve_robust(inst, vertices(mu, 0.4, g))[1] for g in range(0, 4)]
    assert objs == sorted(objs)


def test_tight_budget_binds_for_every_gamma():
    inst = ev.build_instance(ev.Settings(budget="knapp"))
    mu = np.asarray(inst.mu)
    for g in (1, 3):
        x, _ = solve_robust(inst, vertices(mu, 0.4, g))
        assert x.sum() == pytest.approx(inst.budget, rel=1e-6)


def test_reference_tail_is_integral_and_cvar_exceeds_mean():
    assert (1 - C.TAIL_ALPHA) * C.REF_SCENARIOS == pytest.approx(30.0)
    inst = ev.build_instance(ev.Settings())
    pv = evaluate_plan(inst, np.asarray(inst.mu), ev.reference_demand(inst), C.TAIL_ALPHA)
    assert pv.cvar >= pv.mean
