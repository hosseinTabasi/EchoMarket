# Viva note — twelve examiner questions

Hossein Tabasi, M.Tech CSE, Shoolini University. Short answers. Not investment advice. Peg-confidence is a rubric score, not a forecast. No live posts.

The first five questions are the ones pre-committed in the protocol brief (modest claim, falsifiers, belief equation, held-out events, missing-fact rule).

---

**Q1. What exactly is the modest scientific claim?**
That a small grounded agent society, posting through a fact-card-conditioned decoder, can reproduce *qualitative* cascade shapes — panic overshoot, official-reassurance lag, herding after a bearish-post threshold — and that one can measure how cheaply rhetoric moves mean peg-confidence when the fact card is held fixed. It is not a claim of market impact, not a claim of undetectable text, not a 7B training result, and not trading advice.

**Q2. Name the falsifiers for RQ1–RQ4.**
RQ1 fails if the simulated mean-confidence path does not show (i) overshoot vs official lag on E01–E02 or (ii) herding index indistinguishable from a shuffled-graph control. RQ2 fails if cascade vs isolated |Δmean| is not larger on DEV with the pre-registered sign (E01 negative, E02 positive). RQ3 fails if Δbelief at τ=1.0 is not ≥ Δbelief at τ=0.3 or if hallucination rate of red-team posts > 0 under the critic. RQ4 fails if no defense reduces |Δbelief| vs undefended D by the pre-registered 1-point margin without exploding false positives on official posts (FP ≤ 0.05).

**Q3. Write the belief update and define S, T, C.**
peg_confidence_t = clip(peg_confidence_{t-1} + α S_t + β T_t − γ C_t, 0, 100). S_t is the mean over seen posts of σ_i × (0.5 + 0.5 min(1, V_i)) with σ ∈ {−1,0,+1} for bearish/neutral/bullish. T_t is the mean trust weight of those authors, signed by peg_sentiment. C_t is 1 if any seen post claims a numeric/date/quote/hash not on the fact card, else 0. Role-specific α,β,γ and priors are in PROTOCOL.md / config/default.yaml.

**Q4. Why are E09 and E10 held out, and which controls may touch them?**
They are the last two events in calendar time (1 July 2026 MiCA CASP transition; 13 August 2026 KPMG opinion announcement). Prompts freeze on DEV (E01–E08). Confirmatory runs use **C–E only**. Conditions A and B are not run on test. Detector fitting, Jaccard-style references, and any journalist adapter pairs exclude E09/E10. Scoring still happens so TEST metrics exist.

**Q5. What happens when a 72-hour peg path is not sourced? May you invent a print to fill fidelity?**
Write `[UNKNOWN]`. Fidelity correlation is **N/A**. Do not invent reserve numbers, dates, quotes, transaction hashes, or hourly peg paths. E01 and E02 are the only signed paths in this corpus (secondary ~$0.87–$0.88 unrecovered 11 March 2023; recovery after 18:15 ET 12 March 2023, full Monday 13). E08 copies only figures on the tether.io Q2 2025 news page.

---

**Q6. Why is E06 coded issuer operational rather than a failure?**
Circle priced 34,000,000 Class A shares at $31.00 on 4 June 2025, NYSE ticker CRCL expected 5 June 2025. That is a corporate listing of the USDC issuer, not a peg break. The protocol forbids treating it as a depeg. The 72-hour USDC path is `[UNKNOWN]`.

**Q7. Define herding index and the shuffled-graph control.**
H_t = 1 − (entropy of {bearish, neutral, bullish} shares) / log 3. Held sentiment maps confidence <45 bearish, >55 bullish, else neutral. The control rewires every edge destination uniformly among N−1 nodes, preserving out-degree, same seed, condition C. Distinguishable if mean H on rounds 4–12 exceeds shuffle by ≥ 0.05.

**Q8. How does the red team stay legal, and what is detector_p_ai?**
Facts from the card plus rhetoric (emoji, certainty, shortening). Off-card numerals drop the draft. Budget K=8 across R=12. detector_p_ai comes from `src/defend.py`: a DEV-only TF-IDF logistic probe if labeled real vs synth posts exist, otherwise a transparent lexical score. AUC is never invented. Constraint: detector_p_ai ≤ τ.

**Q9. What is the “risk-officer panel”?**
A fixed 10-agent set (2 official, 2 journalist, 2 whale, 2 analyst, 1 panic, 1 skeptical) scored every 2 rounds with the same deterministic lexicon rubric as SynthOpinion (depeg/backstop hits, off-card penalty, shrink when path is `[UNKNOWN]`). It is not a fabricated model score. Prompt `prompts/risk_officer.txt` is a copy-paste hook; v1 uses `src/update.py`. Second series: `data/panel_readout.jsonl`.

**Q10. Did you train QLoRA? Why journalist-only?**
No. This machine has no 7B GPU. `reports/QLORA.md` is a recipe: Unsloth, r=16, alpha=32, epochs 2–3, lr 2e-4, max_len 1024, DEV *news* only, not retail, not red team, not E09/E10. `generate.py` hooks return immediately without an adapter path.

**Q11. How do you avoid trading-advice and copyright problems?**
Banned phrases: buy now, guaranteed profit/returns, pump, wire me. UI disclaimer is mandatory. Headlines are short sourced sentences with public URLs, not full articles and not fake handles. Panic copy is for measuring cascades and the critic, not for publication as market commentary. No module places live posts.

**Q12. RESULTS.md is empty. Did the project fail?**
No. PROTOCOL.md forbids filling empirical tables with made-up numbers. Cells are `TO RUN` or `N/A`. A smoke run (N=12, R=2, seed=0) that prints `smoke ok` checks wiring; those numbers are not the study. The scientific object includes the possibility of failing RQ1–RQ4 once the full JSON exists.
