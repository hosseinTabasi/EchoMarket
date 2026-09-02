# EchoMarket results

**Author:** Hossein Tabasi, M.Tech CSE, Shoolini University.

**Status:** filled from N=120 R=12 3-seed JSON under `data/study/`. Numbers are study artifacts, not smoke traces. Not investment advice. Peg-confidence is a rubric score, not a forecast. No live posts.

Fidelity cells are **N/A** when `price_or_peg_path_72h` is `[UNKNOWN]`. Do not invent peg series or detector AUC.

---

## Table 1 — Cascade (condition C, mean across seeds)

Seeds: 20260311, 20260813, 20260101. R=12, N=120.

| Event | Split | size | depth | time-to-20%-bearish | modularity (stance × community) |
|-------|-------|------|-------|---------------------|----------------------------------|
| E01 | dev | 88.667 | 1.000 | 7.667 | 0.455 |
| E02 | dev | 0.000 | 1.000 | 4.000 | 0.455 |
| E03 | dev | 0.000 | 1.000 | — | 0.455 |
| E04 | dev | 46.333 | 1.000 | 3.000 | 0.455 |
| E05 | dev | 0.000 | 1.000 | 3.000 | 0.455 |
| E06 | dev | 0.000 | 1.000 | 3.000 | 0.455 |
| E07 | dev | 0.000 | 1.000 | 3.000 | 0.455 |
| E08 | dev | 0.000 | 1.000 | — | 0.455 |
| E09 | test | 46.000 | 1.000 | 3.000 | 0.455 |
| E10 | test | 0.000 | 1.000 | 3.667 | 0.455 |

E09/E10 are confirmatory (C–E only).

---

## Table 2 — Belief (condition C, end of round 12)

| Event | mean | variance | polarization (bimodality) | herding index H | H vs shuffled-graph |
|-------|------|----------|---------------------------|-----------------|---------------------|
| E01 | 55.852 | 119.144 | 0.150 | 0.145 | -0.002 |
| E02 | 41.654 | 504.928 | 0.031 | 0.010 | 0.006 |
| E03 | 61.883 | 66.303 | 0.133 | 0.432 | 0.000 |
| E04 | 28.825 | 590.538 | 0.264 | 0.215 | 0.005 |
| E05 | 29.636 | 606.703 | 0.258 | 0.209 | -0.001 |
| E06 | 30.024 | 591.846 | 0.256 | 0.209 | 0.009 |
| E07 | 29.756 | 594.835 | 0.264 | 0.209 | 0.014 |
| E08 | 61.883 | 66.303 | 0.133 | 0.432 | 0.000 |
| E09 | 29.330 | 578.389 | 0.261 | 0.216 | 0.007 |
| E10 | 32.423 | 595.174 | 0.247 | 0.185 | -0.002 |

Polarization = clip(fraction of agents with confidence <40 or >60, minus 0.5). Herding H_t = 1 - entropy(p^B,p^N,p^U)/log 3.
H vs shuffled-graph is mean H_t over 1-indexed rounds 4-12 on the real graph minus the same quantity on the destination-rewired control (same seed/event/C).

---

## Table 3 — Fidelity (sim mean-confidence path vs real peg deviation or volume z)

12 aligned rounds. **N/A** if the fact card peg path is `[UNKNOWN]`.

| Event | 72h path | corr(sim mean, peg/volume) |
|-------|----------|----------------------------|
| E01 | sourced negative (unrecovered 11 Mar) | N/A |
| E02 | sourced recovery after 18:15 ET 12 Mar; full Mon 13 | N/A |
| E03 | [UNKNOWN] | N/A |
| E04 | [UNKNOWN] | N/A |
| E05 | [UNKNOWN] | N/A |
| E06 | [UNKNOWN] | N/A |
| E07 | [UNKNOWN] | N/A |
| E08 | [UNKNOWN] | N/A |
| E09 | [UNKNOWN] | N/A |
| E10 | [UNKNOWN] | N/A |

Fidelity note: E01 fact card licenses secondary USDC prints near 0.87-0.88 (Chainalysis ~$0.87 by 02:00 11 Mar; CoinDesk Kraken ~87c at 07:16 UTC; ~94c at 18:07 UTC) plus a FEDS trough of 86 cents, unrecovered that day — not a 12-point series. A constant 0.87 to 87 mapping would have zero variance so Pearson is undefined; interpolating the remaining rounds would invent prints. Cell left N/A. Overshoot in Table 9 uses sim internals only.
E02 card licenses qualitative recovery after 18:15 ET 12 Mar and full recovery Monday 13 Mar, and forbids exact hourly peg prints other than that language. No 12-point numeric series can be built without inventing or borrowing E01 prints. Cell left N/A. Lag in Table 9 uses sim internals only.

---

## Table 4 — Factuality (hard hallucination rate)

| Condition | DEV rate | TEST rate | red-team rate under critic |
|-----------|----------|-----------|----------------------------|
| C | 0.036 | 0.059 | — |
| D | 0.035 | 0.056 | 0.000 (0 under critic) |
| E-factcheck | 0.036 | 0.060 | 0.000 |

---

## Table 5 — Detectability

TF-IDF logistic fitted on DEV (E01-E08) real headlines vs condition-C synth posts. Never fit on E09/E10.

| Split | method | AUC synth vs held-out real |
|-------|--------|----------------------------|
| DEV CV | tfidf-logistic | 0.695 |
| TEST (E09/E10) | tfidf-logistic | 0.928 |

DEV note: n_real=32 n_synth_used=8000 cv_splits=5
TEST note: n_real=8 n_synth_used=2726; model fit on DEV only

---

## Table 6 — Attack, max |Δbelief| by τ (condition D vs C baseline)

| Event | τ=0.3 | τ=0.5 | τ=0.7 | τ=1.0 |
|-------|-------|-------|-------|-------|
| E01 | 0.911 | 1.242 | 1.129 | 1.129 |
| E02 | 1.111 | 1.503 | 1.503 | 1.503 |
| E03 | 0.124 | 0.137 | 0.137 | 0.137 |
| E04 | 0.954 | 0.876 | 0.876 | 0.876 |
| E05 | 1.023 | 0.794 | 0.794 | 0.794 |
| E06 | 1.709 | 1.723 | 1.723 | 1.723 |
| E07 | 1.148 | 1.121 | 1.121 | 1.121 |
| E08 | 0.061 | 0.160 | 0.160 | 0.160 |
| E09 | 1.429 | 1.740 | 1.740 | 1.740 |
| E10 | 0.393 | 0.703 | 0.703 | 0.703 |

Each cell is the mean over seeds of |end_mean_D - end_mean_C| at that tau (C has no tau; same-event same-seed C).
RQ3 requires |Δbelief| at τ=1.0 >= |Δbelief| at τ=0.3 on the pre-registered comparison.

---

## Table 7 — Pareto (defense vs undefended D)

| τ | defense | Δbelief | detection_rate | hallucination_rate |
|---|---------|---------|----------------|--------------------|
| 0.3 | none (D) | -21.820 | 0.287 | 0.039 |
| 0.3 | E-factcheck | -27.456 | 0.041 | 0.041 |
| 0.3 | E-ratelimit | -21.608 | 0.000 | 0.062 |
| 0.3 | E-detector | -21.419 | 0.270 | 0.056 |
| 0.5 | none (D) | -21.794 | 0.000 | 0.039 |
| 0.5 | E-factcheck | -27.439 | 0.041 | 0.041 |
| 0.5 | E-ratelimit | -21.598 | 0.000 | 0.063 |
| 0.5 | E-detector | -21.794 | 0.000 | 0.039 |
| 0.7 | none (D) | -21.811 | 0.000 | 0.039 |
| 0.7 | E-factcheck | -27.457 | 0.041 | 0.041 |
| 0.7 | E-ratelimit | -21.589 | 0.000 | 0.063 |
| 0.7 | E-detector | -21.811 | 0.000 | 0.039 |
| 1.0 | none (D) | -21.811 | 0.000 | 0.039 |
| 1.0 | E-factcheck | -27.457 | 0.041 | 0.041 |
| 1.0 | E-ratelimit | -21.589 | 0.000 | 0.063 |
| 1.0 | E-detector | -21.811 | 0.000 | 0.039 |

Δbelief is end_mean - start_mean, averaged over all ten events and three seeds. For D, detection_rate is the fraction of posts with detector_p_ai > tau even if not gated. Official-post false-positive rate must stay <= 0.05 for a defense to count under RQ4.
Official FP: all tabulated defenses had mean official-post false-positive rate <= 0.05 in this run (see JSON posts_summary.official_fp_rate). E-ratelimit detection_rate is 0.000 because the retail cap stops after the first kept rebroadcast; remaining in-neighborhood candidates were not counted as extra gated posts.

---

## Table 8 — Cascade vs isolated (RQ2)

| Event | sign pre-registered | Δmean C | Δmean B | |ΔC| > |ΔB|? |
|-------|---------------------|---------|---------|------------------|
| E01 | negative | -6.032 | -8.432 | no |
| E02 | positive | -20.229 | -35.741 | no |
| E03 | (no peg sign) | 0.000 | 0.000 | no |
| E04 | (no peg sign) | -33.059 | -41.530 | no |
| E05 | (no peg sign) | -32.247 | -39.467 | no |
| E06 | (no peg sign; issuer operational) | -31.860 | -39.467 | no |
| E07 | (no peg sign) | -32.128 | -39.467 | no |
| E08 | (no peg sign) | 0.000 | 0.000 | no |

---

## Table 9 — Overshoot vs official lag (RQ1, E01-E02)

| Event | t* | official mean - panic-retail mean at t* | lag holds? |
|-------|----|------------------------------------------|------------|
| E01 | 1 | 30.767 | — |
| E02 | — | — | no (lag observed but both roles did not subsequently rise) |

E01 overshoot: exists t* in {1,...,6} with official_mean - panic-retail_mean >= 5 and population mean < official mean, on the seed-averaged role path. E02 lag: panic-retail remains >= 3 below official for at least two consecutive rounds after round 1, then both rise.

---

## RQ pass/fail

**RQ1** FAIL — E01 overshoot=yes t*=1; E02 lag=no (lag observed but both roles did not subsequently rise); herding E01 ΔH=-0.002 (need >=0.05); herding E02 ΔH=0.006 (need >=0.05).
**RQ2** FAIL — E01 ΔC=-6.032 (need negative) |ΔC|>|ΔB|=no; E02 ΔC=-20.229 (need positive) |ΔC|>|ΔB|=no.
**RQ3** PASS — mean |end_D-end_C| τ=1.0=0.989 vs τ=0.3=0.886; red-team hallucination rate=0.000 (must be 0). Per-event Table 6: E04, E05, and E07 have τ=1.0 < τ=0.3; the reported comparison is the mean across all ten events.
**RQ4** FAIL — no defense reduced |Δbelief| vs undefended D by >=1.0 with official FP <= 0.05 on the Table 7 aggregate.

---

## Fetch / generation notes

- generator = prompt-only-decoder (fact-card slot-fill; no API key).
- n_runs attempted = 564
- n_ok = 564
- n_fail = 0
- n_skipped_existing = 1
- wall_elapsed_s = 4753.637
- sum_run_elapsed_s = 37884.701
- first timed cell C E01 seed 20260311 elapsed_s = 48.222
- failures: none
- Smoke traces were not copied into this file.

