"""Plotly-Figuren: Preis der Robustheit über Γ, Bedeckung, Kostenverteilung, Pläne je Standort. Alle Achsen fest (fixedrange)."""

import plotly.graph_objects as go

import rbo_constants as C


def _fixed(fig, height=340):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.24))
    return fig


def build_curve(curve, selected_gamma) -> go.Figure:
    """Preis (Mehrkosten im Mittel) und Nutzen (CVaR-Absenkung) je Γ, in Prozent gegen den Mittelwertplan."""
    g = [r.gamma for r in curve]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g, y=[r.mean_change_pct for r in curve], mode="lines+markers", name="Preis: Mehrkosten im Mittel",
                             line=dict(color=C.COLOR_MEAN_PLAN)))
    fig.add_trace(go.Scatter(x=g, y=[-r.cvar_change_pct for r in curve], mode="lines+markers", name="Nutzen: CVaR 95 % gesenkt",
                             line=dict(color=C.COLOR_ROBUST)))
    fig.add_vline(x=selected_gamma, line_dash="dot", line_color="rgba(120,120,120,0.8)")
    fig.update_xaxes(title="Γ: so viele Standorte weichen gleichzeitig ab", tickvals=g, ticktext=[str(v) for v in g])
    fig.update_yaxes(title="in % gegen den Mittelwertplan")
    return _fixed(fig, 340)


def build_coverage(curve, selected_gamma) -> go.Figure:
    g = [r.gamma for r in curve]
    colors = [C.COLOR_ROBUST if r.gamma == selected_gamma else C.COLOR_GRID for r in curve]
    fig = go.Figure(go.Bar(x=g, y=[100 * r.coverage for r in curve], marker_color=colors,
                           text=[f"{100 * r.coverage:.0f} %" for r in curve], textposition="outside"))
    fig.update_xaxes(title="Γ", tickvals=g, ticktext=[str(v) for v in g])
    fig.update_yaxes(title="% der Referenzszenarien in der Menge", range=[0, 100])
    return _fixed(fig, 300)


def build_distribution(mean_plan, robust, alpha_label="95 %") -> go.Figure:
    """Gesamtkosten beider Pläne über die Referenzszenarien."""
    lo = min(min(mean_plan.costs), min(robust.costs))
    hi = max(max(mean_plan.costs), max(robust.costs))
    bins = dict(start=lo, end=hi, size=(hi - lo) / 40.0)
    fig = go.Figure()
    for name, pv, color in (("Mittelwertplan", mean_plan, C.COLOR_MEAN_PLAN), ("Robuster Plan", robust, C.COLOR_ROBUST)):
        fig.add_trace(go.Histogram(x=list(pv.costs), xbins=bins, name=name, marker_color=color, opacity=0.6, histnorm="percent"))
        fig.add_vline(x=pv.mean, line_color=color, line_dash="dot")
        fig.add_vline(x=pv.cvar, line_color=color, line_dash="dash")
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title=f"Gesamtkosten je Szenario (gepunktet: Mittel, gestrichelt: CVaR {alpha_label})")
    fig.update_yaxes(title="% der Szenarien")
    return _fixed(fig, 340)


def build_plans(mu, x_mean, x_robust, x_cvar) -> go.Figure:
    names = [f"Standort {i + 1}" for i in range(len(mu))]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=list(mu), name="mittlere Nachfrage", marker_color=C.COLOR_GRID))
    fig.add_trace(go.Bar(x=names, y=list(x_mean), name="Mittelwertplan", marker_color=C.COLOR_MEAN_PLAN))
    fig.add_trace(go.Bar(x=names, y=list(x_robust), name="Robuster Plan", marker_color=C.COLOR_ROBUST))
    fig.add_trace(go.Bar(x=names, y=list(x_cvar), name="CVaR-Plan (Stichprobe)", marker_color=C.COLOR_CVAR))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Kapazität")
    return _fixed(fig, 340)
