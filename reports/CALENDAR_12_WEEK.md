# 12-week calendar — EchoMarket M.Tech

Author: Hossein Tabasi, M.Tech CSE, Shoolini University.

Not investment advice. No live posts. Do not invent prints to stay “on schedule.”

| Week | Dates (indicative) | Deliverable | Gate |
|------|--------------------|-------------|------|
| 1 | protocol lock | PROTOCOL.md, event list E01–E10, fact-card schema, modest claim + falsifiers | No extra events after Friday of week 1 |
| 2 | cards and headlines | `data/events.csv` three-sentence summaries; `fact_cards.jsonl`; `real_headlines.jsonl` (human) | Every numeral traces to a URL; `[UNKNOWN]` where silent |
| 3 | society + graph | `src/agents.py`, `src/graph.py`, `config/default.yaml` (N=120 mix, SBM, PR 0.85) | Smoke society N=12 builds without degree overflow |
| 4 | decoder | `src/generate.py` slot-fill + prompts; JSON schema forced | Off-card numeral tests fail closed |
| 5 | belief + panel | `src/update.py` exact equation; risk-officer rubric; `panel_readout.jsonl` | Priors and αβγ match PROTOCOL table |
| 6 | red / blue | `src/attack.py`, `src/defend.py` (critic, lexical detector, three defenses) | Red-team hallucination rate 0 on a fixture pack |
| 7 | orchestrator | `src/run.py` conditions A–E; `--smoke` <30s prints `smoke ok` | Streamlit playback on smoke traces |
| 8 | DEV C runs | E01–E08 condition C, 1 seed first, then 3 seeds if machine allows | Do not copy partial numbers into RESULTS.md as final |
| 9 | RQ1–RQ2 | Overshoot/lag on E01–E02; shuffle control; cascade vs isolated | If RQ1/RQ2 already fail, write the miss, do not retune θ after seeing H |
| 10 | RQ3–RQ4 | τ grid on D; Pareto E-* defenses; official FP column | τ=1.0 vs 0.3 comparison pre-registered |
| 11 | TEST freeze | Prompts frozen; E09/E10 conditions C–E only; detector not refit | Leakage checklist signed |
| 12 | write-up | RESULTS.md from JSON only; REPORT_OUTLINE filled; VIVA rehearsal; QLORA.md still “not run” unless a GPU log exists | Empty cell > invented cell |

Buffer: if N=120 × 12 × 10 × 3 × 7 conditions does not finish, pre-register a **reduced compute appendix** (1 seed, DEV-only C/D/E) rather than shrinking the society mix. Never drop E01–E02, which carry the only sourced peg paths.

Milestones that must exist before week 8: PROTOCOL.md, prompts frozen on DEV, smoke ok, Streamlit disclaimer visible.
