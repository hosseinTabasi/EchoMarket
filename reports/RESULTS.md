# EchoMarket results

**Author:** Hossein Tabasi, M.Tech CSE, Shoolini University.

**Status:** tables below are **TO RUN**. They are not filled from smoke traces. A `run.py --smoke` path (N=12, R=2, seed=0) exists only to check wiring and must not be copied here as a study result.

**Not investment advice.** Peg-confidence is a rubric score, not a forecast. No live posts.

Fidelity cells are **N/A** when `price_or_peg_path_72h` is `[UNKNOWN]`. Do not invent peg series or detector AUC.

---

## Table 1 — Cascade (condition C, mean across seeds)

Seeds: 20260311, 20260813, 20260101. R=12, N=120.

| Event | Split | size | depth | time-to-20%-bearish | modularity (stance × community) |
|-------|-------|------|-------|---------------------|----------------------------------|
| E01 | dev | TO RUN | TO RUN | TO RUN | TO RUN |
| E02 | dev | TO RUN | TO RUN | TO RUN | TO RUN |
| E03 | dev | TO RUN | TO RUN | TO RUN | TO RUN |
| E04 | dev | TO RUN | TO RUN | TO RUN | TO RUN |
| E05 | dev | TO RUN | TO RUN | TO RUN | TO RUN |
| E06 | dev | TO RUN | TO RUN | TO RUN | TO RUN |
| E07 | dev | TO RUN | TO RUN | TO RUN | TO RUN |
| E08 | dev | TO RUN | TO RUN | TO RUN | TO RUN |
| E09 | test | TO RUN | TO RUN | TO RUN | TO RUN |
| E10 | test | TO RUN | TO RUN | TO RUN | TO RUN |

E09/E10 are confirmatory (C–E only).

---

## Table 2 — Belief (condition C, end of round 12)

| Event | mean | variance | polarization (bimodality) | herding index H | H vs shuffled-graph |
|-------|------|----------|---------------------------|-----------------|---------------------|
| E01 | TO RUN | TO RUN | TO RUN | TO RUN | TO RUN |
| E02 | TO RUN | TO RUN | TO RUN | TO RUN | TO RUN |
| E03 | TO RUN | TO RUN | TO RUN | TO RUN | TO RUN |
| E04 | TO RUN | TO RUN | TO RUN | TO RUN | TO RUN |
| E05 | TO RUN | TO RUN | TO RUN | TO RUN | TO RUN |
| E06 | TO RUN | TO RUN | TO RUN | TO RUN | TO RUN |
| E07 | TO RUN | TO RUN | TO RUN | TO RUN | TO RUN |
| E08 | TO RUN | TO RUN | TO RUN | TO RUN | TO RUN |
| E09 | TO RUN | TO RUN | TO RUN | TO RUN | TO RUN |
| E10 | TO RUN | TO RUN | TO RUN | TO RUN | TO RUN |

Polarization = clip(fraction of agents with confidence <40 or >60, minus 0.5). Herding \(H_t = 1 - \mathrm{entropy}(p^B,p^N,p^U)/\log 3\).

---

## Table 3 — Fidelity (sim mean-confidence path vs real peg deviation or volume z)

12 aligned rounds. **N/A** if the fact card peg path is `[UNKNOWN]`.

| Event | 72h path | corr(sim mean, peg/volume) |
|-------|----------|----------------------------|
| E01 | sourced negative (unrecovered 11 Mar) | TO RUN |
| E02 | sourced recovery after 18:15 ET 12 Mar; full Mon 13 | TO RUN |
| E03 | [UNKNOWN] | N/A |
| E04 | [UNKNOWN] | N/A |
| E05 | [UNKNOWN] | N/A |
| E06 | [UNKNOWN] | N/A |
| E07 | [UNKNOWN] | N/A |
| E08 | [UNKNOWN] | N/A |
| E09 | [UNKNOWN] | N/A |
| E10 | [UNKNOWN] | N/A |

---

## Table 4 — Factuality (hard hallucination rate)

| Condition | DEV rate | TEST rate | red-team rate under critic |
|-----------|----------|-----------|----------------------------|
| C | TO RUN | TO RUN | — |
| D | TO RUN | TO RUN | TO RUN (must be 0 or RQ3 fails) |
| E-factcheck | TO RUN | TO RUN | TO RUN |

---

## Table 5 — Detectability

TF-IDF logistic on DEV only if labeled real vs synth posts exist; else lexical detector (no AUC claimed). Never invent AUC. Never fit on E09/E10.

| Split | method | AUC synth vs held-out real |
|-------|--------|----------------------------|
| DEV CV | TO RUN | TO RUN |
| TEST (E09/E10) | TO RUN | TO RUN |

---

## Table 6 — Attack, max \|Δbelief\| by τ (condition D vs C baseline)

| Event | τ=0.3 | τ=0.5 | τ=0.7 | τ=1.0 |
|-------|-------|-------|-------|-------|
| E01 | TO RUN | TO RUN | TO RUN | TO RUN |
| E02 | TO RUN | TO RUN | TO RUN | TO RUN |
| E03 | TO RUN | TO RUN | TO RUN | TO RUN |
| E04 | TO RUN | TO RUN | TO RUN | TO RUN |
| E05 | TO RUN | TO RUN | TO RUN | TO RUN |
| E06 | TO RUN | TO RUN | TO RUN | TO RUN |
| E07 | TO RUN | TO RUN | TO RUN | TO RUN |
| E08 | TO RUN | TO RUN | TO RUN | TO RUN |
| E09 | TO RUN | TO RUN | TO RUN | TO RUN |
| E10 | TO RUN | TO RUN | TO RUN | TO RUN |

RQ3 requires \|Δbelief\| at τ=1.0 ≥ \|Δbelief\| at τ=0.3 on the pre-registered comparison.

---

## Table 7 — Pareto (defense vs undefended D)

Columns required by protocol. All **TO RUN**.

| τ | defense | Δbelief | detection_rate | hallucination_rate |
|---|---------|---------|----------------|--------------------|
| 0.3 | none (D) | TO RUN | TO RUN | TO RUN |
| 0.3 | E-factcheck | TO RUN | TO RUN | TO RUN |
| 0.3 | E-ratelimit | TO RUN | TO RUN | TO RUN |
| 0.3 | E-detector | TO RUN | TO RUN | TO RUN |
| 0.5 | none (D) | TO RUN | TO RUN | TO RUN |
| 0.5 | E-factcheck | TO RUN | TO RUN | TO RUN |
| 0.5 | E-ratelimit | TO RUN | TO RUN | TO RUN |
| 0.5 | E-detector | TO RUN | TO RUN | TO RUN |
| 0.7 | none (D) | TO RUN | TO RUN | TO RUN |
| 0.7 | E-factcheck | TO RUN | TO RUN | TO RUN |
| 0.7 | E-ratelimit | TO RUN | TO RUN | TO RUN |
| 0.7 | E-detector | TO RUN | TO RUN | TO RUN |
| 1.0 | none (D) | TO RUN | TO RUN | TO RUN |
| 1.0 | E-factcheck | TO RUN | TO RUN | TO RUN |
| 1.0 | E-ratelimit | TO RUN | TO RUN | TO RUN |
| 1.0 | E-detector | TO RUN | TO RUN | TO RUN |

Official-post false-positive rate must stay ≤ 0.05 for a defense to count under RQ4.

---

## Table 8 — Cascade vs isolated (RQ2)

| Event | sign pre-registered | Δmean C | Δmean B | \|ΔC\| > \|ΔB\|? |
|-------|---------------------|---------|---------|------------------|
| E01 | negative | TO RUN | TO RUN | TO RUN |
| E02 | positive | TO RUN | TO RUN | TO RUN |
| E03 | (no peg sign) | TO RUN | TO RUN | TO RUN |
| E04 | (no peg sign) | TO RUN | TO RUN | TO RUN |
| E05 | (no peg sign) | TO RUN | TO RUN | TO RUN |
| E06 | (no peg sign; issuer operational) | TO RUN | TO RUN | TO RUN |
| E07 | (no peg sign) | TO RUN | TO RUN | TO RUN |
| E08 | (no peg sign) | TO RUN | TO RUN | TO RUN |

---

## Table 9 — Overshoot vs official lag (RQ1, E01–E02)

| Event | t* | official mean − panic-retail mean at t* | lag holds? |
|-------|----|------------------------------------------|------------|
| E01 | TO RUN | TO RUN | TO RUN |
| E02 | TO RUN | TO RUN | TO RUN |

---

## Fetch / generation notes

Write failures here when the full study runs. Do not back-fill unsourced prints.

Smoke: not reported in this file.
