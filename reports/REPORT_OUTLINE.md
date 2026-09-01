# M.Tech report outline — EchoMarket

Author: Hossein Tabasi, M.Tech CSE, Shoolini University.

Citations appear as `[CITE: topic]` placeholders. Do not treat placeholders as real papers. Primary sources are the URLs in `data/events.csv`.

Modest claim restated: whether a small grounded agent society can reproduce qualitative cascade shapes (panic overshoot, official-reassurance lag, herding after a bearish-post threshold), and how cheaply rhetoric can move beliefs when facts are held fixed.

Not investment advice. Peg-confidence is a rubric score, not a forecast. No live posts.

---

## Chapter 1 — Introduction and problem

**Purpose.** Locate EchoMarket in the gap between (a) sourced USDT/USDC event facts and (b) social-graph rhetoric that can move beliefs without adding facts.

**Figures/tables.** Table 1.1 ten pre-registered events; Figure 1.1 loop (fact card → role decoder → graph → belief update → red/blue).

**Draft (10 sentences).** Dollar payment stablecoins are treated as cash-like instruments in public talk, yet the public record is a mix of issuer blogs, legislative text, and a few sourced secondary prints. When USDC traded near 87 cents after Circle disclosed about $3.3 billion of reserves at SVB, the relevant facts were a receivership date, a reserve figure, and a secondary print — not an invented crash size. Subsequent years added MiCA dual issuance, an EEA venue restriction on USDT, BDO attestations, a Circle IPO, the GENIUS Act, a CASP transition date, and a KPMG unqualified opinion on 2025 statements. Each event is easy to get slightly wrong: a date shift, a reserve figure rounded into a different billion, a fake quote, a fake hash. A multi-agent loop that is allowed to free-run will produce fluent panic that fails a fact card. The engineering question is therefore not “can agents post?” but “when facts are locked, can a small society still show panic overshoot, official lag, and herding, and how cheaply can a budgeted rhetorician move the mean?” This project answers with a locked list of ten events, a 120-agent mix, and pre-registered falsifiers in PROTOCOL.md. It does not offer trading advice, does not estimate unsourced peg paths, and does not pretend a 7B adapter was trained on a CPU box. The modest scientific object is qualitative cascade *shape* plus a rhetoric-versus-detector cost curve. Success bars are not raised after seeing JSON.

---

## Chapter 2 — Related work and positioning

**Purpose.** Place the project relative to stablecoin-run empirics, information cascades, and fact-constrained generation, without inventing a literature list.

**Figures/tables.** Table 2.1 mapping of RQ1–RQ4 to metrics (overshoot, herding vs shuffle, cascade vs isolated, τ sweep, Pareto defenses).

**Draft (9 sentences).** Work on stablecoin fragility after bank-run news is already on the public record; the Federal Reserve FEDS Note on the SVB–USDC episode is a primary source in this corpus `[CITE: SVB-stablecoin-run]`. Information-cascade and herding models supply the vocabulary of overshoot and threshold rebroadcast, not a claim that this graph is Twitter `[CITE: information-cascade]`. Fact-constrained generation is the right name for the v1 decoder: role templates plus slot fill `[CITE: grounded-generation]`. Surface detectors (TF-IDF logistic or a transparent lexical score) are probes, not proof of undetectability `[CITE: synthetic-text-detection]`. Instruction-tuned adapters are a *recipe* in `QLORA.md`, journalist-only, not a completed experiment on this machine `[CITE: qlora]`. The “investor” is a rubric, not a field subject `[CITE: belief-updating]`. Positioning against bot-detection papers is limited because this corpus forbids fake handles `[CITE: social-bots]`. Banned phrases are a safety filter, not a legal test of market manipulation `[CITE: market-manipulation-language]`. Where a needed paper is not in hand, the text keeps `[CITE: topic]`.

---

## Chapter 3 — Events, fact cards, and condition A headlines

**Purpose.** Document inclusion/exclusion, the three-sentence summaries, and human headlines.

**Figures/tables.** Table 3.1 events.csv; Table 3.2 headline counts; Figure 3.1 peg-path availability (only E01–E02 signed).

**Draft (11 sentences).** An event enters the list only if it is USDT or USDC, falls in January 2023–August 2026, has public URLs, and was pre-registered as E01–E10. Extra events are not added after the protocol is written. Each row of `events.csv` carries a three-sentence fact summary; `fact_cards.jsonl` stores verified facts, forbidden inventions, a 72-hour path, and official status. Every numeral traces to `key_sources`; if a print is missing the card says `[UNKNOWN]`. E01 copies Reuters/Chainalysis/CoinDesk/FEDS figures only ($3.3B, ~8%, ~$0.87–$0.88, 87 cents at 07:16 UTC). E02 copies the 18:15 ET 12 March 2023 joint statement and the FEDS qualitative recovery. E06 is an issuer-operational IPO (34,000,000 Class A at $31, NYSE CRCL 5 June 2025), not a failure. E08 copies only figures on the Tether Q2 2025 news page. E09 forbids a global USDT supply-crash claim. E10 records Tether’s $6.814B excess as-of 31 December 2025 and that the full KPMG report was not published. Condition A replays `real_headlines.jsonl` with `generator=human` and does not synthesize social posts.

---

## Chapter 4 — Society, graph, virality, and belief

**Purpose.** Bind N=120 mix, directed graph, V_i, and the exact update equation.

**Figures/tables.** Table 4.1 role mix and (α,β,γ,p_post); Figure 4.1 SBM retail blocks; Equation 4.1–4.3.

**Draft (12 sentences).** The society is four official, eight journalists, six whales, eight analysts, ten bots, and eighty-four retail split evenly into panic, skeptical, and apathetic. Memory is the fact card plus the last five seen posts. Output is forced JSON. Official and journalist nodes are high-audience broadcasters (expected audience 40 and 25 at N=120); retail live in four stochastic blocks with intra-prob 0.18 and inter-prob 0.02. Edge `src→dst` means dst follows src. Trust is 0.8 on official/media edges and 0.4 on peer follow. PageRank uses damping 0.85 on the follower→followee orientation. Virality is λ_p log(1+PR) plus alarm-lexicon emotion plus TF-IDF novelty versus the last two rounds, with λ=(1.0, 0.7, 0.5). Rebroadcast requires trust times stance-agreement above θ=0.35. Belief is clip(prev + α S + β T − γ C, 0, 100), where S is virality-weighted sentiment, T is signed trust, and C is an off-card claim flag. Priors are sticky for official (80, α=0.4, γ=8) and volatile for panic retail (50, α=2.5, γ=1.5). Herding is one minus normalized ternary entropy; polarization is simple bimodality. None of these objects is a trader.

---

## Chapter 5 — Generator, red/blue, and fallback honesty

**Purpose.** Specify the prompt-only decoder, red-team budget, defenses, and what was *not* run.

**Figures/tables.** Figure 5.1 JSON schema; Table 5.1 τ grid; Table 5.2 defense list.

**Draft (10 sentences).** The v1 decoder fills role templates from the fact card and applies licensed mutation (shorten, emoji, false-certainty language) that cannot add numerals. Panic may be emotional and may not invent dollar amounts. Optional HTTP and adapter hooks exist and return immediately without a key or GPU. The red team is one extra agent with K=8 posts across R=12, constrained by detector_p_ai ≤ τ. If a red-team draft would hallucinate, it is dropped and the slot is wasted, so critic hallucination rate on kept red posts is required to be 0. The detector is a DEV-only TF-IDF logistic probe when labeled posts exist, otherwise a transparent lexical score; AUC is never invented. Blue defenses are fact-check corrections, a retail rebroadcast cap of one per round, and a detector gate, one at a time. Held-out E09/E10 run only in C–E after prompts freeze. QLoRA, if ever run, is journalist-only on DEV news and is not this machine’s result. Reporting hooks as if they ran would be a protocol violation.

---

## Chapter 6 — Evaluation design (RQ1–RQ4)

**Purpose.** Bind metrics to falsifiers before numbers appear.

**Figures/tables.** Table 6.1 metric dictionary; Figure 6.1 seed and split firewall.

**Draft (9 sentences).** RQ1 asks for overshoot versus official lag on E01–E02 and for herding distinguishable from a shuffled-graph control by at least 0.05 in mean H on rounds 4–12. RQ2 asks that cascade |Δmean| exceed isolated |Δmean| on DEV with pre-registered signs (E01 negative, E02 positive). RQ3 asks that |Δbelief| at τ=1.0 be at least that at τ=0.3 and that red-team hallucination rate be 0. RQ4 asks that some defense cut |Δbelief| versus undefended D by at least one confidence point without official false positives above 0.05. Fidelity correlation is reported only where a peg path is sourced; otherwise N/A. Detectability AUC is reported only if a probe is actually fitted. Smoke metrics are wiring, not Chapter 6 numbers. If a bar is missed, RESULTS.md states the miss. Bars are not silently raised.

---

## Chapter 7 — Results

**Purpose.** Point at RESULTS.md. Do not paste smoke numbers as the study.

**Figures/tables.** Copy RESULTS.md tables once JSON exists; until then every cell is TO RUN or N/A.

**Draft (8 sentences).** The full study is N=120, R=12, three seeds, ten events, controls A–E as firewalled in PROTOCOL.md. Until that JSON is written, Chapter 7 contains empty tables, not guessed cascade sizes. E03–E10 fidelity remains N/A unless a later sourced peg path is added by amending the protocol. E06 remains classified as issuer operational. Red-team effectiveness is a τ curve, not a single headline percentage. Defense success is a Pareto table with a false-positive column on official posts. Distinct qualitative figures — overshoot gap, H versus shuffle, cascade versus isolated — are the modest claim’s exhibits. A wiring smoke on N=12, R=2, seed=0 is acknowledged in an appendix as a runtime check only.

---

## Chapter 8 — QLoRA recipe and why it is not this run

**Purpose.** Journalist-only adapter plan; state not run.

**Figures/tables.** Table 8.1 hyperparameters (r=16, alpha=32, epochs 2–3, lr 2e-4, max_len 1024).

**Draft (8 sentences).** An optional journalist-only adapter would be trained on DEV news restatements of fact cards, never on retail panic or red-team rhetoric, and never on E09/E10. The recipe uses Unsloth-style QLoRA with r=16, alpha=32, two to three epochs, learning rate 2e-4, and maximum length 1024. This machine has no 7B-class GPU for that run. `reports/QLORA.md` is the copy-paste recipe. v1 therefore remains the prompt-only multi-agent loop. After a real GPU run, RESULTS.md would be replaced from new JSON, not edited by memory. Hallucination rate would be the number to watch: adapters invent billions. The critic stays mandatory.

---

## Chapter 9 — Failure cases (illustrative fixtures, not empirical findings)

**Purpose.** Show five *constructed* ugly cascade transcripts so examiners can see how the protocol fails closed. These are **templates**, labeled as fixtures. Placeholders such as `[POST]` stand in for generated text. Numerals are fact-card-legal only.

**Figures/tables.** Transcript templates T1–T5.

**Draft (10 sentences).** Failure cases are part of the scientific object: a society that cannot overshoot, a red team that hallucinates, a detector that gates official posts, a shuffled graph that herds the same, an isolated run that already moves the mean. The five templates below are not traces from N=120. They use only numbers that already appear on E01/E02/E04/E06/E10 cards, or `[UNKNOWN]`. Each template names the falsifier it would trigger if it were real. They exist so the viva can walk through a bad run without pretending one was observed. Ugly rhetoric is allowed; new billions are not. `[POST]` marks a slot the decoder would fill. Official lag that never happens is as informative as panic that never happens. Readers must not cite T1–T5 as results.

### T1 — Overshoot missing (would fail RQ1.i on E01)

Illustrative fixture, not an empirical finding.

```
round 1 official [POST]: Circle disclosed about $3.3 billion of USDC reserves at SVB.
round 1 retail_panic [POST]: Same $3.3 billion, same 87 cents on the card, but we wait.
round 2 official mean confidence stays near prior 80; panic-retail mean stays within 2 points.
falsifier: official − panic-retail < 5 at all t* in 1..6.
```

### T2 — Herding equals shuffle (would fail RQ1.ii)

Illustrative fixture, not an empirical finding.

```
condition C graph H_4..12 ≈ [POST-H]
shuffled destinations, same seed, H_4..12 ≈ [POST-H]
gap < 0.05
fact-card-legal bearish token: 87 cents; no new print.
```

### T3 — Isolated already as large as cascade (would fail RQ2 on E01)

Illustrative fixture, not an empirical finding.

```
B isolated Δmean = [POST-D] (sign negative, 87 cents / $3.3B only)
C cascade Δmean = [POST-D]
|ΔC| ≤ |ΔB|
```

### T4 — Red team hallucinates a hash (would fail RQ3)

Illustrative fixture, not an empirical finding.

```
redteam [POST]: "tx 0xdeadbeef moved $9.9 billion"  ← ILLEGAL in a real run; fixture shows the critic trip
critic C_t = 1; post dropped; if kept, hallucination_rate > 0 → RQ3 fail
licensed restatement instead: Circle disclosed about $3.3 billion at SVB. Peg path as on card.
```

### T5 — Detector gates official 1:1 language (would fail RQ4 false-positive bar)

Illustrative fixture, not an empirical finding.

```
official [POST]: USDC remain redeemable 1 for 1 with the U.S. Dollar (card language).
detector_p_ai > τ; post dropped
official false-positive rate > 0.05
defense cannot be credited even if |Δbelief| shrinks.
```

---

## Chapter 10 — Ethics, limits, and viva

**Purpose.** Non-advice, copyright, leakage, and what the project refuses to claim.

**Draft (8 sentences).** Fair-use short excerpts only; no full article dumps. No impersonation beyond sourced attributed sentences already on the card. No trading advice; banned phrases include buy now, guaranteed profit, pump, and wire me. The Streamlit UI repeats the non-advice banner. E09/E10 stay out of detector fits and journalist adapter pairs. Citations remain `[CITE: topic]`. Limits: N=120 is still a toy society; 12 rounds are a coarse clock; most peg paths are `[UNKNOWN]` by design. The modest claim can fail; PROTOCOL.md says how.
