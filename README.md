# Robust planen: Preis der Robustheit – Streamlit-Demo

Viertes Stück der **Optimierung-unter-Unsicherheit-Linie** der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“.
Anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt sie **ein** Verfahren, die **robuste Optimierung mit Budget der Unsicherheit**, an einem wachsenden Beispiel.
**Kante in der Linie:** Sie ist ein zweiter Weg zum selben Ziel wie die [CVaR-Demo](https://github.com/sebastian-hanisch/cvar-demo): den schlimmen Fall abfedern, aber ohne Wahrscheinlichkeiten,
mit einer **Menge** möglicher Nachfragen. Das Vehikel ist dasselbe wie in der [Wurzel](https://github.com/sebastian-hanisch/newsvendor-evpi-demo): Kapazitätsvorhaltung mit Zukauf,
Umlagerung und Fehlmenge, sechs Standorte, als lineares Programm.

## Warum dieses Problem

Wer keine Verteilung kennt oder keiner trauen will, plant auf den schlimmsten Fall einer Menge: Jeder Standort darf um höchstens δ vom Mittel abweichen, und höchstens **Γ** Standorte tun das
zugleich. Γ = 0 ist der Mittelwertplan, Γ = 6 der klassische Worst Case. Die Demo misst, **was die Absicherung im Mittel kostet, was sie im Tail bringt, und für wie viele wirkliche
Szenarien die Garantie überhaupt gilt**.

## Modell

Dasselbe Modell wie in der Wurzel; Kapazitätsbudget **frei** oder **knapp**. Die Unsicherheitsmenge U(Γ, δ) ist eine Box um die mittlere Nachfrage mit Budget Γ auf der Summe der relativen Abweichungen.
Geprüft wird auf 600 gleich wahrscheinlichen **lognormalen** Referenzszenarien (Streuung einstellbar), die nicht in der Menge liegen müssen. Formeln im 📐-Expander der App.

## Methodik

- **Robuster Plan:** minimiert Vorhaltung plus die Kosten der teuersten Ecke von U (die Kosten sind konvex in der Nachfrage, das Maximum liegt an einer Ecke): ein LP mit Hilfsvariable t und je Ecke
  einem Stufe-2-Block (Γ = 2: 73 Ecken, Γ = 6: 729).
- **Mittelwertplan:** Γ = 0, ein Szenario in Höhe des Mittels.
- **Prüfen:** beide auf den 600 Referenzszenarien: Mittel, CVaR 95 %, schlimmster Fall in U, Anteil der Referenzszenarien in U.
- **Preis-Nutzen-Kurve:** Γ = 0 bis 6 mit demselben δ; **der Knick** ist das kleinste Γ, das die Hälfte des Tail-Nutzens der vollen Box holt.
- **Vergleich:** der Plan, der den CVaR (90 %) einer Stichprobe von 100 Szenarien minimiert.

## Befunde (gemessen, keine Behauptungen)

Voreinstellung (Seed 7, δ = 40 %, Streuung 35 %, Kapazität frei, Umlagerung an); jede Aussage in `tests/test_claims.py` als Band belegt.

| Frage | Befund |
|---|---|
| **Was kostet die Absicherung, was bringt sie?** | Γ = 2: Mittel +5,6 %, CVaR 95 % −9,1 %. Γ = 3: +9,3 % / −12,8 %. Γ = 6 (volle Box): +20,7 % / −20,2 %. Der Preis wächst schneller als der Nutzen. |
| **Wo ist der Knick?** | Γ = 3 holt 63 % des Tail-Nutzens der vollen Box für 45 % der Mehrkosten. Größere Γ schützen vor Fällen, die kaum noch vorkommen. |
| **Was ist der robuste Plan?** | Ein Kapazitätspuffer: Gesamtkapazität / mittlere Nachfrage steigt von 1,00 (Γ = 0) auf 1,16 (Γ = 2) und 1,40 (Γ = 6 = 1 + δ). |
| **Was kauft man in der Menge?** | Im schlimmsten Fall von U(2, 40 %) kostet der robuste Plan 671, der Mittelwertplan 740: 9,3 % weniger. Das ist die eigentliche Garantie; für die lognormalen Referenzszenarien zählt Mittel und CVaR (oben). |
| **Für wie viele wirkliche Szenarien gilt die Garantie?** | Bei Γ = 2 liegen 6 % der lognormalen Referenzszenarien in der Menge, bei der vollen Box 30 %. Außerhalb gibt es keine Zusage. |
| **Wann schadet oder nützt es nichts?** | Bei knappem Budget (bindet immer): Mittel und CVaR ändern sich um höchstens 0,4 %. Der Plan verteilt nur um. |
| **Was bewirkt der Wegfall der Umlagerung?** | Ohne Umlagerung ändert Γ ≤ 2 kaum etwas (Γ = 2: +0,8 % / −2,2 %), ab Γ = 4 springt der Plan auf den der vollen Box (Kapazität 1,40, +16,3 % / −13,9 %). |
| **Robust gegen CVaR?** | Verwandte Puffer, nicht derselbe Plan: Der CVaR-Plan der Stichprobe hat Kapazität 1,47, +26,3 % im Mittel und −22,7 % im CVaR; der volle robuste Plan 1,40, +20,7 % und −20,2 %. |

## Ehrliche Grenzen

- **Die Menge ist gesetzt.** δ und Γ sind Setzungen des Planers, nicht aus Daten abgeleitet. Eine falsch gewählte Menge verschenkt Kosten oder Schutz.
- **Die Garantie gilt nur in der Menge.** Die lognormalen Referenzszenarien liegen überwiegend außerhalb; für sie ist der robuste Plan nur durch seinen Puffer besser, nicht durch eine Zusage.
- **Nur ganzzahliges Γ.** Die Ecken sind für ganzzahliges Γ aufgezählt; das fraktionale Budget von Bertsimas und Sim ist nicht abgebildet.
- **Nur CVaR 95 % als Tail-Maß in der Prüfung.** Eine Aussage über „den“ Tail hängt am Maß.
- **Eine Instanz, feste Preise.** Die Prozentzahlen hängen an Zukaufpreis, Strafe und Umlagerung.

## Verifikation

- **Kern:** Eckenzahlen (1, 13, 73, 729), Ecken liegen in der Menge und nutzen das Budget, Zugehörigkeit an Handwerten, Γ = 0 gleich Erwartungswertplan (160 an der Mini-Instanz), Zielwert gleich schlimmster Ecke des eigenen Plans,
  Gittersuche über alle Pläne der Mini-Instanz schlägt das LP nicht, schlimmster Fall wächst mit Γ, Budget bindet bei „knapp“.
- **Orakel (`tests/test_oracle_robust.py`):** dasselbe Problem als eigenes LP in OR-Tools (GLOP) mit und ohne Umlagerung (1e-7); 150 zufällige Punkte der Menge überschreiten das Eckenmaximum nie;
  Bedeckung gegen eine Schleife ohne Vektorisierung.
- **Claims (`tests/test_claims.py`):** Preis und Nutzen, Knick bei 2 oder 3, Puffer, Bedeckung, knappes Budget, Sprung ohne Umlagerung, Vergleich mit dem CVaR-Plan.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Footer.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App |
| `rbo_rng.py`, `rbo_scenario.py`, `rbo_algorithm.py` | Zufall, Instanz und Szenarien, Stufe-2-Block (wie in der Wurzel) |
| `rbo_cvar.py` | CVaR, Stufe-2-Kosten, Auswertung eines Plans (wie in der CVaR-Demo) |
| `rbo_robust.py` | Ecken, Zugehörigkeit, robustes LP |
| `rbo_evaluation.py` | Analyse, Preis-Nutzen-Kurve, Knick, Verdikt |
| `rbo_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `rbo_presets.py` | Permalink (Begrenzen, Einrasten), Presets, Zufalls-Seed-Button |
| `rbo_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Mini-Instanz, Orakel, Claims, Presets, AppTest-Smoke-Test, Footer |

## Bewusst nicht umgesetzt

- **Wahrscheinlichkeitsschranke von Bertsimas und Sim** (Γ als Anzahl, Verletzung höchstens exp(−Γ²/2n)): würde zeigen, wie viel das Budget Γ bei unabhängigen Abweichungen schützt; hier wird die Menge selbst ausgewertet.
- **Verteilungsrobuste Varianten** (Wasserstein-Ball): nach Messung kein eigenes Stück, bei unbeschränktem Support ändert der Radius den Plan nicht.
- **Fraktionales Γ und ellipsoide Mengen:** andere Mengenformen, andere Ecken oder konische Programme.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Unsicherheit: von EVPI bis rollierend](https://sebastianhanisch.net/konzepte-optimierung-unsicherheit.html).
