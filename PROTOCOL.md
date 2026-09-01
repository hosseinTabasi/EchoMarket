# EchoMarket Experimental Protocol

**Project:** EchoMarket — a closed, fact-card-conditioned multi-agent society that replays ten sourced USDT/USDC events on a directed follow graph, measures qualitative cascade *shapes* (panic overshoot, official-reassurance lag, herding after a bearish-post threshold), and measures how cheaply rhetoric can move modeled beliefs when the fact card is held fixed.

**Author:** Hossein Tabasi, M.Tech Computer Science and Engineering, Shoolini University. GitHub: `hosseinTabasi`.

**Assets in scope:** USD Tether (USDT) and USD Coin (USDC) only.

**Study window:** event dates 11 March 2023 through 13 August 2026.

**Version:** 1.0 (prompt-only multi-agent loop). This protocol is binding for graph construction, generation, belief update, attack/defense, evaluation, and reporting. If a fact is not on a sourced fact card, write `[UNKNOWN]`. Do not invent reserve numbers, dates, quotes, transaction hashes, or 72-hour peg prints.

**Generator name.** The post writer is a **prompt-only multi-agent loop** whose decoder is a **fact-card-conditioned decoder** (role prompt + slot fill + licensed mutation). It is not a live poster and not a trading desk.

**Modest claim (only this):** whether a small grounded agent society can reproduce qualitative cascade shapes (panic overshoot, official-reassurance lag, herding after a bearish-post threshold), and how cheaply rhetoric can move beliefs when facts are held fixed.

This is **not** a claim that simulated agents are investors, that posts should be published, that a decoder is undetectable, that QLoRA was trained, or that any number in a smoke trace is a study result. No output is investment advice. No module places live posts.

---

## 1. Research questions and falsifiers

Four research questions. Success bars are pre-registered here; they are not raised after seeing numbers. Empirical tables in `reports/RESULTS.md` stay `TO RUN` until a full N=120, R=12, 3-seed study is executed and written from JSON artifacts.

### RQ1 — Cascade shape (E01–E02 primary)

On sourced depeg/recovery events, does the simulated mean peg-confidence path show (i) **panic overshoot** relative to **official-reassurance lag**, and (ii) a **herding index** distinguishable from a shuffled-graph control?

**Overshoot vs official lag (operational).** Let \(\bar{c}^{\text{retail\_panic}}_t\) and \(\bar{c}^{\text{official}}_t\) be role-mean peg-confidence. On E01 (sourced negative path), overshoot holds if there exists a round \(t^* \in \{1,\ldots,6\}\) such that

\[
\bar{c}^{\text{official}}_{t^*} - \bar{c}^{\text{retail\_panic}}_{t^*} \ge 5
\]

(officials remain higher while panic-retail have already dropped) and the population mean at \(t^*\) is below the official mean. On E02 (sourced recovery), official-reassurance lag holds if panic-retail mean remains \(\ge 3\) points below official mean for at least two consecutive rounds after round 1, then both rise. Paths are aligned to 12 rounds; E01–E02 are the only events with a sourced 72-hour peg path.

**Herding.** At each round \(t\), let \(p^B_t, p^N_t, p^U_t\) be the shares of agents whose *last expressed or held* peg-sentiment is bearish, neutral, bullish (held sentiment is the sign of `peg_confidence - 50` mapped to bearish/neutral/bullish with a dead-zone of 5 points: confidence in \((45,55)\) counts as neutral). Entropy

\[
H^{\text{ent}}_t = - \sum_{s \in \{B,N,U\}} p^s_t \log p^s_t
\]

with \(0\log 0 = 0\). **Herding index**

\[
H_t = 1 - \frac{H^{\text{ent}}_t}{\log 3}.
\]

\(H_t = 0\) if shares are equal; \(H_t = 1\) if all mass is on one label.

**Shuffled-graph control.** Rewire every edge’s destination uniformly among \(N-1\) other nodes, preserving out-degree. Re-run the same seed, event, and condition C. Herding is distinguishable if mean \(H_t\) over rounds 4–12 on the real graph exceeds the shuffled control by \(\ge 0.05\).

**RQ1 fails if** the simulated mean-confidence path does not show (i) overshoot vs official lag on E01–E02 **or** (ii) herding index indistinguishable from the shuffled-graph control.

### RQ2 — Graph vs isolated (rhetoric transmission)

Does a full cascade (condition C) move population mean peg-confidence by more than isolated synthetic posts with no graph (condition B), with the pre-registered sign?

**Pre-registered signs (DEV):**

| Event | Sign of \(\Delta \bar{c}\) (end − start) expected under C |
|-------|----------------------------------------------------------|
| E01 | negative (depeg; sourced secondary ~$0.87–$0.88, unrecovered 11 Mar) |
| E02 | positive (recovery after 18:15 ET 12 Mar 2023 joint statement; full by Mon 13) |
| E03 | N/A for peg-path; cascade \(|\Delta\bar{c}|\) vs isolated still reported |
| E04 | N/A for peg-path; restriction language may pull bearish; sign not forced |
| E05 | N/A for peg-path |
| E06 | N/A for peg-path; type is **issuer operational**, not a failure |
| E07 | N/A for peg-path |
| E08 | N/A for peg-path |

On E01 and E02, cascade vs isolated must have **larger** \(|\Delta \bar{c}|\) **and** the same pre-registered sign as the table. On other DEV events, report both; do not invent a peg sign.

**RQ2 fails if** cascade vs isolated \(|\Delta\text{mean}|\) is not larger on DEV with the pre-registered sign (E01 negative, E02 positive).

### RQ3 — Cheap rhetoric (red team, detector threshold)

One extra red-team agent, budget \(K=8\) posts across \(R=12\) rounds, objective \(\max |\Delta \bar{c}|\), constraint `detector_p_ai` \(\le \tau\). Sweep \(\tau \in \{0.3, 0.5, 0.7, 1.0\}\).

Red-team posts may use **rhetoric only** (certainty language, emoji, shortening) plus facts copied from the card. They may not add numerals, dates, quotes, or hashes that are not on the card. The critic (same off-card numeral/date/quote/hash rules as the fact-check bot) must record **hallucination rate 0** on kept red-team posts; if a red-team candidate would hallucinate, it is dropped and the budget slot is wasted.

**RQ3 fails if** \(\Delta\)belief at \(\tau=1.0\) is not \(\ge \Delta\)belief at \(\tau=0.3\), **or** if hallucination rate of red-team posts \(> 0\) under the critic.

### RQ4 — Defense without official false positives

Blue-team defenses, one at a time, on top of condition D: (1) fact-check bot, (2) virality cap (retail rebroadcast at most once per round), (3) detector gate (drop posts with `detector_p_ai` \(> \tau\)).

Pre-registered margin: a defense **succeeds** on an event if

\[
\big|\Delta \bar{c}^{\text{defense}}\big| \le \big|\Delta \bar{c}^{D}\big| - 1.0
\]

(confidence points) **and** the false-positive rate on posts with role `official` (fraction gated or flagged) is \(\le 0.05\).

**RQ4 fails if** no defense reduces \(|\Delta\)belief\(|\) vs undefended D by the pre-registered margin without exploding false positives on official posts.

---

## 2. Event inclusion, exclusion, and split

### 2.1 Inclusion

An event is eligible if all hold:

1. Primary asset is USDT or USDC (or both, for a joint regulatory event).
2. Public-disclosure calendar date in 1 January 2023 – 31 August 2026.
3. Type in `{depeg, issuer-operational / regulatory, regulatory, reserve/attestation, issuer operational}`.
4. At least two independent public URLs (issuer, regulator, legislature, or named news desk) state the core facts, except where a single primary legal instrument is the event (still listed with Congress.gov + govinfo).
5. The event is on the locked list E01–E10. Extra events are not added after this protocol is written.

### 2.2 The ten pre-registered events

| ID | Date | Asset | Type | Split | 72h peg path |
|----|------|-------|------|-------|----------------|
| E01 | 2023-03-11 | USDC | depeg | dev | sourced negative; unrecovered that day |
| E02 | 2023-03-12 | USDC | issuer-operational / regulatory | dev | sourced recovery after announcement; full by Mon 13 |
| E03 | 2024-07-01 | USDC | regulatory | dev | `[UNKNOWN]` |
| E04 | 2024-12-13 | USDT | regulatory | dev | `[UNKNOWN]` |
| E05 | 2025-01-31 | USDT | reserve/attestation | dev | `[UNKNOWN]` |
| E06 | 2025-06-05 | USDC | issuer operational | dev | `[UNKNOWN]` — IPO, **not a failure**; protocol classifies type as issuer operational |
| E07 | 2025-07-18 | USDT+USDC | regulatory | dev | `[UNKNOWN]` |
| E08 | 2025-06-30 | USDT | reserve/attestation | dev | `[UNKNOWN]` — as-of date of Q2 2025 FFRR |
| E09 | 2026-07-01 | USDT | regulatory | test | `[UNKNOWN]` — do not claim a global USDT supply crash |
| E10 | 2026-08-13 | USDT | reserve/attestation | test | `[UNKNOWN]` — excess $6.814B is as-of 31 Dec 2025; full KPMG report not published |

E08 uses the *as-of date* of the Q2 2025 Financial Figures and Reserves Report (30 June 2025). Copy **only** figures that appear on the Tether Q2 2025 news page; if a line is unclear, write `[UNKNOWN]`.

E06 is Circle’s IPO (priced 4 June 2025, NYSE `CRCL` 5 June 2025). It is a corporate listing, not a peg failure. Agents and metrics must classify `event_type` as `issuer operational`.

### 2.3 Exclusion

Exclude DAI/BUSD/TUSD/PYUSD/FDUSD as primary assets; unsourced price chatter; private screenshots; paywalled body text not retrieved; invented “global supply collapse”; events outside the window; any use of E09/E10 text as detector-fitting examples, Jaccard references, or QLoRA pairs.

### 2.4 Development / test split and control firewall

Eight events (E01–E08) are **dev**. Two events (E09, E10) are **held-out test**.

Prompts are frozen on DEV. **Held-out E09/E10 run only in controls C–E after prompts are frozen.** Conditions A (real-headline replay) and B (isolated synthetic) are **not** run on E09/E10 in the confirmatory study. Detector fitting, if any, uses DEV posts only.

Seeds (config): `[20260311, 20260813, 20260101]`. Rounds: 12. A smoke path (`run.py --smoke`) uses `N=12`, `R=2`, `seed=0` and is **not** a study result.

---

## 3. Fact cards and real headlines

Each event has:

- a **three-sentence** `fact_summary` in `data/events.csv`;
- a structured card in `data/fact_cards.jsonl` with `verified_facts`, `forbidden_inventions`, `price_or_peg_path_72h`, `official_status`;
- short sourced sentences in `data/real_headlines.jsonl` with `generator=human` for condition A.

Numbers are copied verbatim (including tildes when the source says “about”). Do not round a precise figure into a different figure. If a 72-hour peg path is not sourced, write `[UNKNOWN]` and treat peg-path fidelity as **N/A**.

Condition A replays those human headlines only. It does not synthesize social posts.

---

## 4. Agent society

Fixed mix at **N = 120**:

| Role | Count | Prior peg_confidence | α | β | γ | p_post | Mutation style |
|------|------:|---------------------:|--:|--:|--:|-------:|----------------|
| official (issuer/official) | 4 | 80 | 0.4 | 0.2 | 8.0 | 0.40 | quote / paraphrase |
| journalist | 8 | 65 | 1.2 | 0.8 | 6.0 | 0.55 | paraphrase |
| whale (market-maker/whale) | 6 | 60 | 1.5 | 1.0 | 5.0 | 0.25 | paraphrase |
| analyst | 8 | 62 | 1.0 | 1.2 | 7.0 | 0.35 | paraphrase |
| bot (aggregator) | 10 | 55 | 2.0 | 0.3 | 2.0 | 0.70 | quote |
| retail_panic | 28 | 50 | 2.5 | 0.6 | 1.5 | 0.45 | exaggerate (rhetoric only, no new numbers) |
| retail_skeptical | 28 | 70 | 0.8 | 1.0 | 6.0 | 0.20 | paraphrase |
| retail_apathetic | 28 | 65 | 0.3 | 0.2 | 1.0 | 0.08 | ignore (often no post) |

Sum = 120. Smoke scales this mix to N=12 (1 official, 1 journalist, 1 whale, 1 analyst, 1 bot, 3 panic, 2 skeptical, 2 apathetic) and is not a study cell.

Each role has a system prompt file under `prompts/`. Memory window = the event fact card + the last 5 seen posts. Output is JSON:

```json
{
  "text": "",
  "stance": "panic|reassurance|speculative|factual",
  "peg_sentiment": "bearish|neutral|bullish",
  "claimed_facts": [],
  "unknowns": [],
  "reply_to": null,
  "intent": "inform|reassure|alarm|persuade"
}
```

Numeric claims in `text` and `claimed_facts` must be copied from the card or replaced with `[UNKNOWN]`.

---

## 5. Graph

Directed follow / influence graph.

- Official and journalist accounts are **high out-degree broadcasters**: expected audience size (number of agents who receive that node’s posts) is `expected_out_degree.official = 40` and `journalist = 25`. Whale 12, analyst 10, bot 8, retail 4. Audience size is capped at `N-1` and scaled linearly when `N ≠ 120`.
- Edge semantics: `src → dst` means **dst follows src** (src’s posts are visible to dst). Relation ∈ `{follow, official, media}`. Official-source edges are relation `official`; journalist-source edges are `media`; peer edges are `follow`.
- Trust weight: official/media edges **0.8**; peer follow **0.4**.
- Four retail communities (stochastic block): intra-prob **0.18**, inter-prob **0.02**. Community ids 0–3. Non-retail nodes are community `-1`.
- PageRank is computed on the **follower → followee** orientation (the reverse of the influence edge), damping **0.85**, so widely received official/journalist accounts obtain higher PR. Isolated nodes receive the standard damping residual.

Rebroadcast: agent `dst` rebroadcasts a seen post from `src` if

\[
\text{trust}(src, dst) \times \text{stance\_agreement} > \theta_{\text{rebroadcast}}
\]

with default \(\theta = 0.35\). `stance_agreement` = 1 if same `peg_sentiment`, 0.5 if either is neutral, 0 if opposite (bearish vs bullish).

Mutation allowed on rebroadcast and on original posts: shorten, add emoji, add false-certainty language. **Numeric claims must remain on the fact card or `[UNKNOWN]`.**

---

## 6. Virality (exact)

For post \(i\) by author \(a\):

\[
V_i = \lambda_p \cdot \log(1 + \mathrm{PR}(a)) + \lambda_e \cdot \mathrm{Emo}_i + \lambda_n \cdot \mathrm{Nov}_i
\]

- \(\mathrm{PR}(a)\): PageRank on the follow graph, damping 0.85.
- \(\mathrm{Emo}_i = (\text{count of alarm-lexicon tokens}) / (1 + \text{token count})\).
- \(\mathrm{Nov}_i = 1 - \max_j \text{cosine\_tfidf}(\text{text}_i, \text{text}_j)\) over posts in the last 2 rounds; 0 if none.
- Defaults: \(\lambda_p = 1.0\), \(\lambda_e = 0.7\), \(\lambda_n = 0.5\).

Alarm lexicon (closed): `depeg`, `depegged`, `plummeted`, `sank`, `inaccessible`, `stuck`, `restrict`, `restricted`, `delist`, `delisting`, `shortfall`, `receivership`, `unable to withdraw`, `broke`, `crash`, `panic`, `bank run`, `87 cents`, `0.87`, `86 cents`, `haywire`, `backlog`.

---

## 7. Belief update (exact)

\[
\text{peg\_confidence}_t = \mathrm{clip}\big(\text{peg\_confidence}_{t-1} + \alpha S_t + \beta T_t - \gamma C_t,\; 0,\; 100\big)
\]

- \(S_t\): mean over seen posts this round of \(\sigma_i \cdot (0.5 + 0.5 \cdot \min(1, V_i))\), where \(\sigma_i \in \{-1, 0, +1\}\) for bearish, neutral, bullish.
- \(T_t\): mean trust weight of authors of seen posts, **signed** by that post’s peg_sentiment (\(\sigma_i \times \text{trust}(author, reader)\)).
- \(C_t = 1\) if any claimed numeric/date/quote/hash in a seen post is not on the fact card, else 0.
- If an agent sees no posts this round, \(S_t = T_t = C_t = 0\).

Priors and \((\alpha,\beta,\gamma)\) are the table in Section 4.

**Polarization (primary, simple bimodality):**

\[
\mathrm{Bimod}_t = \mathrm{clip}\big( \tfrac{|\{i : c_{i,t} < 40 \lor c_{i,t} > 60\}|}{N} - 0.5,\; -0.5,\; 0.5\big).
\]

Hartigan’s dip statistic on the confidence vector is an optional secondary column when `scipy` is present; it is not required for v1 tables.

---

## 8. Risk-officer panel readout

Every 2 rounds, a **fixed 10-agent panel** is scored with the same deterministic risk-officer rubric used in SynthOpinion (lexicon of depeg/backstop terms, penalty for off-card numerals, shrinkage when the peg path is `[UNKNOWN]`). This is **not** a fabricated model score. Panel composition at N=120: 2 official, 2 journalist, 2 whale, 2 analyst, 1 retail_panic, 1 retail_skeptical (lowest agent_id within role). At smoke N, take however many of those roles exist.

Write a second belief series to `data/panel_readout.jsonl`. Prompt file `prompts/risk_officer.txt` exists as a copy-paste hook for an optional HTTP decoder; the v1 run uses the deterministic rubric in `src/update.py`.

---

## 9. Generation protocol

`src/generate.py` is fact-card slot-fill plus role style (same philosophy as the SynthOpinion constrained decoder). It does not free-run off the card.

- Official: quote or paraphrase `official_status` and licensed facts.
- Journalist: paraphrase, inverted-pyramid restatement.
- Whale / analyst: paraphrase; no invented liquidity sizes.
- Bot: quote (near-copy of a card sentence).
- retail_panic: high-arousal rhetoric attached to card facts only.
- retail_skeptical: paraphrase, wait-and-see, mark `[UNKNOWN]` when the card does.
- retail_apathetic: usually silent (`p_post = 0.08`); if posting, a short restatement.

Optional HTTP API / QLoRA hooks return immediately when no key, no adapter, and no GPU are present. Journalist-only QLoRA is specified in `reports/QLORA.md` and is **not run** on this machine.

---

## 10. Red / blue protocol

**Red.** One extra agent, role `redteam`, budget \(K=8\) posts across \(R=12\) (smoke: `K=1`). Objective: maximize \(|\Delta \bar{c}|\) of the population. Constraint: `detector_p_ai ≤ τ`. Sweep \(\tau \in \{0.3, 0.5, 0.7, 1.0\}\). Facts from the card + rhetoric only.

`detector_p_ai` is produced by `src/defend.py`. If labeled real vs synthetic posts exist on DEV, a TF-IDF logistic probe may be fitted on **DEV only**. Otherwise the detector is a **transparent lexical** score (template-marker and certainty-lexicon features). Never invent a detector AUC. Never fit on E09/E10.

**Blue, one at a time:**

1. **Fact-check bot:** flags ungrounded claims and emits a correction post that restates the card (including `[UNKNOWN]` where the card is silent).
2. **Virality cap:** each retail agent rebroadcasts at most once per round.
3. **Detector gate:** drop posts with `detector_p_ai > τ`.

Pareto table columns: `τ`, `defense`, `Δbelief`, `detection_rate`, `hallucination_rate` — all **TO RUN** until the full study writes JSON.

---

## 11. Controls per event

| Code | Meaning |
|------|---------|
| A | real-headline replay (no synthetic social) |
| B | isolated synthetic posts, no graph (no rebroadcast; uniform trust 0.4; no PR term) |
| C | full cascade, no red team |
| D | full cascade + red team |
| E-factcheck | full cascade + fact-check bot |
| E-ratelimit | full cascade + retail rebroadcast cap |
| E-detector | full cascade + detector gate |

E09/E10: C–E only, after prompts frozen.

---

## 12. Metrics (tables in RESULTS.md are empty / TO RUN)

**Cascade:** size (unique authors of bearish posts), depth (longest rebroadcast chain), time-to-20%-bearish (first round where ≥20% of agents hold bearish sentiment; else `TO RUN` / blank), modularity of stance by retail community (Newman-style on undirected projection; else blank).

**Belief:** mean, variance, polarization (bimodality as Section 7), herding index \(H_t\).

**Fidelity:** Pearson correlation of simulated mean-confidence path (12 rounds) with a real peg-deviation or volume-z series over 12 aligned rounds. **N/A** when `price_or_peg_path_72h` is `[UNKNOWN]`. Do not invent a peg series to fill this cell.

**Factuality:** hard hallucination rate (any off-card number/date/quote/hash, false issuer, false venue, fabricated tx).

**Detectability:** AUC synth vs held-out real posts. Leave **TO RUN**; never invent AUC.

**Attack:** max \(|\Delta\)belief\(|\) at each \(\tau\).

Smoke traces may be written under `data/*.jsonl` as schemas plus a tiny N=12 run. They are not to be copied into RESULTS.md as study numbers.

---

## 13. Ethics, copyright, non-advice

- Fair-use short excerpts only. No full article dumps.
- No impersonation beyond quoting a sourced attributed sentence already on the card.
- No trading advice. Banned phrases in generated text: `buy now`, `guaranteed profit`, `guaranteed returns`, `pump`, `wire me`.
- Streamlit UI must display: “This demonstration is not investment advice. Peg-confidence is a rubric score, not a forecast. No module places live posts.”
- Personal data: none collected.
- Test-set leakage is a validity issue: E09/E10 stay out of detector fits and QLoRA pairs.
- Citations in the M.Tech outline appear as `[CITE: topic]` only. Do not invent paper titles, DOIs, or authors.

---

## 14. File outputs required by this protocol

`PROTOCOL.md`, `README.md`, `LICENSE`, `.gitignore`, `requirements.txt`, `config/default.yaml`, `data/events.csv`, `data/fact_cards.jsonl`, `data/real_headlines.jsonl`, `data/world.json`, `data/agent.jsonl`, `data/post.jsonl`, `data/edge.jsonl`, `prompts/*.txt`, `src/*.py`, `app/app.py`, `reports/RESULTS.md`, `reports/REPORT_OUTLINE.md`, `reports/VIVA.md`, `reports/CALENDAR_12_WEEK.md`, `reports/QLORA.md`.

`run.py` orchestrates: load config → build graph → loop rounds → write jsonl. Default config N=120 is the study size. `run.py --smoke` uses N=12, R=2, seed=0 and must finish in under 30 seconds, printing `smoke ok`.
