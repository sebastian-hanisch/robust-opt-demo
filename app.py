"""Robust planen: Preis der Robustheit - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Lauffähig mit: streamlit run app.py
"""

import numpy as np
import streamlit as st

import rbo_constants as C
from rbo_cvar import evaluate_plan
from rbo_evaluation import Settings, analyse, knee, reference_demand
from rbo_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from rbo_visualization import build_coverage, build_curve, build_distribution, build_plans

st.set_page_config(page_title="Robust planen – Sebastian Hanisch", layout="wide")


def _de(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def _pct(value: float, digits: int = 1) -> str:
    return f"{value:+.{digits}f} %".replace(".", ",").replace("-", "−")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


st.title("🧱 Robust planen: Preis der Robustheit")
st.markdown(
    """
Die **robuste Optimierung** plant nicht auf Wahrscheinlichkeiten, sondern auf eine **Menge** möglicher Nachfragen: Jeder Standort darf um höchstens δ vom Mittel abweichen,
und höchstens **Γ Standorte** tun das gleichzeitig. Der Plan ist dann für den schlimmsten Fall in dieser Menge optimal. Diese Demo fragt: **Was kostet diese Absicherung im Mittel,
was bringt sie im Tail, und wofür gilt die Garantie überhaupt?**

Anders als die Fall-Demos zeigt sie **ein** Verfahren an einem wachsenden Beispiel, mit demselben Kapazitäts-Vehikel wie die
[Wurzel der Linie](https://github.com/sebastian-hanisch/newsvendor-evpi-demo). Weiter unten: der Vergleich mit dem CVaR-Plan, **🚧 Wo die Annahmen enden** und **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die robuste Planung", expanded=True):
    st.markdown(
        """
1. **Menge statt Verteilung:** Die Nachfrage jedes Standorts liegt in [(1 − δ) · Mittel, (1 + δ) · Mittel]. Höchstens **Γ** Standorte sind gleichzeitig am Rand (Budget der Unsicherheit).
2. **Schlimmster Fall an den Ecken:** Die Kosten nach der Nachfrage sind in der Nachfrage konvex, ihr Maximum über die Menge liegt also an einer Ecke: Standorte am Rand oder im Mittel.
3. **Als LP:** Eine Hilfsvariable t trägt die Kosten der teuersten Ecke; der Plan minimiert Vorhaltung plus t.
4. **Prüfen:** der Plan auf 600 lognormalen Referenzszenarien, die **nicht** in der Menge sein müssen: Mittel, CVaR 95 % und wie viele Szenarien überhaupt in der Menge liegen.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    cols = st.columns(len(C.PRESETS))
    for col, name in zip(cols, C.PRESETS):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Unsicherheitsmenge**")
    gamma = st.slider("Γ: gleichzeitig abweichende Standorte", *bounds("gamma_slider"), step=1, key="gamma_slider",
                      help="0: nur der Mittelwert (Mittelwertplan). 6: alle Standorte zugleich am Rand (klassischer Worst Case).")
    delta = st.slider("δ: größte Abweichung je Standort", *bounds("delta_slider"), step=C.DELTA_STEP, key="delta_slider",
                      help="Wie weit ein Standort vom Mittel abweichen darf, als Anteil des Mittels.")
    st.markdown("**Wahre Nachfrage (zum Prüfen)**")
    sigma = st.slider("Streuung (Log-Streuung σ)", *bounds("sigma_slider"), step=C.SIGMA_STEP, key="sigma_slider",
                      help="Wie stark die lognormale Nachfrage der Referenz um den Mittelwert schwankt. Sie ist nicht dieselbe Menge wie die Unsicherheitsmenge.")
    st.markdown("**Möglichkeiten**")
    budget = st.radio("Kapazitätsbudget", C.BUDGET_CHOICES, key="budget_radio", horizontal=True,
                      help="Frei: so viel Kapazität wie gewünscht. Knapp: höchstens 95 % der mittleren Gesamtnachfrage, das Budget bindet immer.")
    transfer = st.radio("Umlagerung zwischen Standorten", C.TRANSFER_CHOICES, key="transfer_radio", horizontal=True,
                        help="An: ungenutzte Kapazität eines Standorts kann den Bedarf eines anderen decken (mit Transportkosten).")
    st.markdown("**Instanz**")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({
    "gamma_slider": int(gamma), "delta_slider": delta, "sigma_slider": sigma, "budget_radio": budget,
    "transfer_radio": transfer, "seed_input": int(seed),
})

settings = Settings(gamma=int(gamma), delta=float(delta), sigma=float(sigma), budget=str(budget), transfer=str(transfer), seed=int(seed))

# --- Ergebnis ----------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Mittelwertplan gegen robusten Plan")
if settings.gamma == 0:
    st.info("Bei Γ = 0 ist der robuste Plan der Mittelwertplan. Stellen Sie Γ höher, um den Preis der Robustheit zu sehen.")
with st.spinner("Löse die robusten Probleme für Γ = 0 bis 6 und werte sie auf 600 Referenzszenarien aus …"):
    a = _analysis(settings)
rob, base = a.robust, a.mean_plan

m1, m2, m3, m4 = st.columns(4)
m1.metric("Mittel der Kosten, robuster Plan", f"{rob.mean:,.0f}".replace(",", "."), delta=f"{_pct(rob.mean_change_pct)} gegen Mittelwertplan", delta_color="inverse")
m2.metric("CVaR 95 %, robuster Plan", f"{rob.cvar:,.0f}".replace(",", "."), delta=f"{_pct(rob.cvar_change_pct)} gegen Mittelwertplan", delta_color="inverse")
m3.metric("Schlimmster Fall in der Menge", f"{rob.worst:,.0f}".replace(",", "."),
          delta=f"{_pct(100.0 * (rob.worst / a.mean_worst_in_set - 1.0))} gegen Mittelwertplan ({a.mean_worst_in_set:,.0f})".replace(",", "."), delta_color="inverse")
m4.metric("Referenzszenarien in der Menge", f"{100 * rob.coverage:.0f} %", delta=f"volle Box (Γ = 6): {100 * a.box_coverage:.0f} %", delta_color="off")

inst = a.inst
ref = reference_demand(inst)
pv_mean = evaluate_plan(inst, np.asarray(base.x), ref, C.TAIL_ALPHA)
pv_rob = evaluate_plan(inst, np.asarray(rob.x), ref, C.TAIL_ALPHA)
st.plotly_chart(build_distribution(pv_mean, pv_rob), width="stretch", key="distribution_chart")
st.caption("Verteilung der Gesamtkosten über die 600 lognormalen Referenzszenarien. Der robuste Plan verschiebt Kosten aus dem rechten Tail in die Mitte und bezahlt dafür im Mittel.")

left, right = st.columns(2)
with left:
    st.plotly_chart(build_curve(a.curve, settings.gamma), width="stretch", key="curve_chart")
    st.caption("Preis und Nutzen je Γ gegen den Mittelwertplan, auf der Referenz. Der Nutzen wächst langsamer, als der Preis steigt.")
with right:
    st.plotly_chart(build_coverage(a.curve, settings.gamma), width="stretch", key="coverage_chart")
    st.caption("Wie viele der lognormalen Referenzszenarien in der Unsicherheitsmenge liegen: nur dafür gilt die Garantie des robusten Plans.")

# --- Kernfrage ---------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Lohnt sich die Absicherung?")
if settings.gamma == 0:
    st.info("Mit Γ = 0 gibt es keine Absicherung.")
elif a.verdict == "lohnt":
    st.success(
        f"**Ja, hier lohnt sie:** Γ = {settings.gamma} senkt den CVaR 95 % um {_de(-rob.cvar_change_pct)} %, die mittleren Kosten steigen um {_de(rob.mean_change_pct)} %. "
        f"Je gewonnenem Prozent Tail kostet das {_de(rob.mean_change_pct / -rob.cvar_change_pct, 2)} Prozent im Mittel."
    )
elif a.verdict == "schadet":
    st.warning(
        f"**Hier schadet sie:** mittlere Kosten {_pct(rob.mean_change_pct)}, CVaR 95 % {_pct(rob.cvar_change_pct)}. "
        "Ohne Spielraum bei der Kapazität (knappes Budget) verteilt der robuste Plan nur um und gewinnt nichts."
    )
else:
    st.info(f"**Kaum ein Unterschied:** mittlere Kosten {_pct(rob.mean_change_pct)}, CVaR 95 % {_pct(rob.cvar_change_pct)}.")
k = knee(a.curve)
if k is not None:
    row_k, row_all = a.curve[k], a.curve[-1]
    st.caption(
        f"**Der Knick:** Γ = {k} holt {_de(100 * row_k.cvar_change_pct / row_all.cvar_change_pct, 0)} % des Tail-Nutzens von Γ = {C.GAMMA_MAX} "
        f"für {_de(100 * row_k.mean_change_pct / row_all.mean_change_pct, 0)} % der Mehrkosten. Größere Γ schützen vor Fällen, die kaum noch vorkommen."
    )
st.caption(
    f"Garantiert ist der schlimmste Fall **in der Menge**: Nur {_de(100 * rob.coverage, 0)} % der Referenzszenarien liegen darin. "
    "Die Garantie ist deshalb keine Aussage über die lognormale Nachfrage."
)

st.markdown("---")

# --- Vergleich mit dem CVaR-Plan ----------------------------------------------------------------------------------------------------------

st.subheader("⚖️ Robust und CVaR: derselbe Gedanke?")
st.markdown(
    f"Zum Vergleich der Plan, der den **CVaR** ({round(C.CVAR_ALPHA * 100)} %, Gewicht 1) einer Stichprobe von {C.CVAR_S} Szenarien minimiert, "
    "wie in der [CVaR-Demo](https://github.com/sebastian-hanisch/cvar-demo) der Linie."
)
table = [
    {"Plan": "Mittelwertplan (Γ = 0)", "Kapazität gesamt / mittlere Nachfrage": round(base.capacity_ratio, 2),
     "Mittel (%)": 0.0, "CVaR 95 % (%)": 0.0},
    {"Plan": f"Robust (Γ = {settings.gamma}, δ = {_de(settings.delta)})".replace(".", ","), "Kapazität gesamt / mittlere Nachfrage": round(rob.capacity_ratio, 2),
     "Mittel (%)": round(rob.mean_change_pct, 1), "CVaR 95 % (%)": round(rob.cvar_change_pct, 1)},
    {"Plan": f"Robust, volle Box (Γ = {C.GAMMA_MAX})", "Kapazität gesamt / mittlere Nachfrage": round(a.curve[-1].capacity_ratio, 2),
     "Mittel (%)": round(a.curve[-1].mean_change_pct, 1), "CVaR 95 % (%)": round(a.curve[-1].cvar_change_pct, 1)},
    {"Plan": "CVaR-Plan (Stichprobe)", "Kapazität gesamt / mittlere Nachfrage": round(a.cvar_plan.capacity_ratio, 2),
     "Mittel (%)": round(a.cvar_plan.mean_change_pct, 1), "CVaR 95 % (%)": round(a.cvar_plan.cvar_change_pct, 1)},
]
st.dataframe(table, hide_index=True, width="stretch")
st.plotly_chart(build_plans(inst.mu, base.x, rob.x, a.cvar_plan.x), width="stretch", key="plans_chart")
st.caption(
    "Beide Wege kaufen Kapazität als Puffer: Auf diesem Vehikel sind robuster Plan und CVaR-Plan **verwandt**, nicht gleich. "
    "Der robuste Plan braucht keine Wahrscheinlichkeiten, der CVaR-Plan keine Menge; dafür hängt der CVaR-Plan an der Stichprobe."
)

st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Menge beschreibt die Nachfrage** | Die Garantie gilt nur in der Menge. Von den lognormalen Referenzszenarien liegt nur ein kleiner Teil darin (die volle Box etwa ein Drittel): Außerhalb gibt es keine Zusage. | – |
| **Kapazität ist frei wählbar** | Bei knappem Budget wird nur verteilt: Der robuste Plan unterscheidet sich kaum vom Mittelwertplan und gewinnt im Tail nichts. | – |
| **Der schlimmste Fall ist das Ziel** | Er kann sehr unwahrscheinlich sein; ein Plan für Γ = 6 bezahlt für Fälle, die in der Referenz nie vorkommen. Wer Wahrscheinlichkeiten kennt, kann den Tail direkt gewichten. | [CVaR-Demo](https://github.com/sebastian-hanisch/cvar-demo): Risiko als gewichtetes Ziel statt Garantie |
| **δ und Γ sind bekannt** | Beide sind Setzungen des Planers; eine falsch gewählte Menge verschenkt Kosten oder Schutz. Hier nicht aus Daten abgeleitet. | [Stichproben-Demo (SAA)](https://github.com/sebastian-hanisch/saa-demo): was eine Stichprobe über die Verteilung sagt |
| **Eine Instanz, feste Preise** | Wie viel Robustheit kostet, hängt an Zukaufpreis, Fehlmenge-Strafe und Umlagerung. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Wie in der Wurzel der Linie: Kapazität $x\ge 0$ mit Kosten $c\,\mathbf 1^\top x$ und Budget, nach der Nachfrage $D$ die Stufe-2-Kosten $Q(x,D)$ (Umlagerung, Zukauf, Fehlmenge).

**Unsicherheitsmenge (Budget der Unsicherheit).** Mit Mittel $\mu$, Abweichung $\delta$ und Budget $\Gamma$:

$$U(\Gamma,\delta)=\Big\{D:\; |D_j-\mu_j|\le \delta\mu_j\;\;\forall j,\;\; \sum_j \frac{|D_j-\mu_j|}{\delta\mu_j}\le \Gamma\Big\}$$

**Robustes Problem.**

$$\min_{x\ge 0}\;\; c\,\mathbf 1^\top x+\max_{D\in U(\Gamma,\delta)} Q(x,D)$$

**Lösung als LP.** $Q(x,\cdot)$ ist konvex, das Maximum über das Polytop $U$ liegt an einer Ecke. Für ganzzahliges $\Gamma$ haben die Ecken höchstens $\Gamma$ Koordinaten bei
$\mu_j(1\pm\delta)$, die übrigen bei $\mu_j$. Mit der Menge $V$ dieser Ecken und einer Hilfsvariablen $t$:

$$\min_{x,t}\;\; c\,\mathbf 1^\top x+t\qquad\text{u. d. N.}\qquad t\ge Q(x,D_v)\;\;\forall v\in V$$

Jede Nebenbedingung enthält ein Stufe-2-LP mit eigenen Flüssen. Für $J=6$ Standorte hat $\Gamma=6$ genau $3^6=729$ Ecken, $\Gamma=2$ genau $1+12+60=73$.

**Literatur.** Bertsimas & Sim, *The Price of Robustness*, Operations Research 52(1), 2004, S. 35–53 (Budget der Unsicherheit, Wahrscheinlichkeitsgarantie je Nebenbedingung bei
unabhängigen, symmetrischen Koeffizienten; hier nicht verwendet: Es wird die Menge selbst ausgewertet, nicht eine Wahrscheinlichkeitsschranke).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
