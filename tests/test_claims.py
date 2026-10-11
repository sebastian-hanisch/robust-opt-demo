"""Jede Aussage aus README und App-Text wird hier nachgerechnet (Bänder statt exakter Werte: CI installiert die neuesten numpy/scipy)."""

import numpy as np
import pytest

import rbo_constants as C
import rbo_evaluation as ev


@pytest.fixture(scope="module")
def presets():
    return {name: ev.analyse(ev.Settings(**p)) for name, p in C.PRESETS.items()}


def test_default_robust_plan_pays_a_little_and_gains_in_the_tail(presets):
    a = presets["Standardfall (Voreinstellung)"]
    assert a.verdict == "lohnt"
    assert 3.0 <= a.robust.mean_change_pct <= 9.0
    assert -14.0 <= a.robust.cvar_change_pct <= -6.0


def test_price_and_benefit_rise_with_gamma_and_the_price_rises_faster(presets):
    curve = presets["Standardfall (Voreinstellung)"].curve
    means = [r.mean_change_pct for r in curve]
    cvars = [-r.cvar_change_pct for r in curve]
    assert means == sorted(means) and cvars == sorted(cvars)
    assert means[-1] > cvars[-1] * 0.9           # am Ende kostet die Absicherung im Mittel so viel, wie der Schwanz gewinnt
    assert 0.0 < cvars[2] / cvars[-1] < 0.6      # Γ = 2 holt weniger als 60 % des Nutzens


def test_the_knee_sits_at_two_or_three(presets):
    assert ev.knee(presets["Standardfall (Voreinstellung)"].curve) in (2, 3)


def test_the_robust_plan_is_a_capacity_buffer(presets):
    ratios = [r.capacity_ratio for r in presets["Standardfall (Voreinstellung)"].curve]
    assert ratios[0] == pytest.approx(1.0, abs=0.02)
    assert ratios == sorted(ratios)
    assert 1.3 <= ratios[-1] <= 1.45              # höchstens 1 + δ


def test_the_guarantee_covers_only_a_small_part_of_the_lognormal_scenarios(presets):
    curve = presets["Standardfall (Voreinstellung)"].curve
    assert curve[2].coverage < 0.12
    assert 0.2 <= curve[-1].coverage <= 0.4      # selbst die volle Box deckt nur etwa ein Drittel


def test_tight_budget_removes_the_effect(presets):
    a = presets["Knappes Budget: Robust schadet"]
    assert abs(a.robust.mean_change_pct) < 1.0 and abs(a.robust.cvar_change_pct) < 1.0
    assert a.verdict in ("kaum", "schadet")


def test_without_transfer_the_robust_plan_jumps_to_the_box_plan(presets):
    curve = presets["Ohne Umlagerung"].curve
    assert np.allclose(curve[4].x, curve[6].x, rtol=1e-6)      # ab Γ = 4 derselbe Plan wie die volle Box
    assert curve[3].capacity_ratio < curve[4].capacity_ratio - 0.1
    assert curve[1].mean_change_pct < 1.0                      # kleine Γ ändern ohne Umlagerung kaum etwas


def test_robust_and_cvar_plan_are_related_buffers(presets):
    a = presets["Standardfall (Voreinstellung)"]
    assert a.cvar_plan.capacity_ratio > 1.3 and a.curve[-1].capacity_ratio > 1.3
    assert abs(a.cvar_plan.cvar_change_pct - a.curve[-1].cvar_change_pct) < 8.0
    assert not np.allclose(a.cvar_plan.x, a.curve[-1].x, rtol=0.02)   # verwandt, nicht gleich


def test_the_guarantee_inside_the_set_is_what_the_robust_plan_buys(presets):
    a = presets["Standardfall (Voreinstellung)"]
    assert a.robust.worst < a.mean_worst_in_set          # im schlimmsten Fall der Menge ist der robuste Plan besser
    assert a.robust.worst <= a.mean_worst_in_set * 0.95
    assert a.mean_worst_in_set > a.mean_plan.worst       # die Menge mit Γ = 2 ist für den Mittelwertplan viel teurer als sein Mittelwert-Szenario
