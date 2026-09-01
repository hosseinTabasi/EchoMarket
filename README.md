# EchoMarket

A closed, fact-card-conditioned **prompt-only multi-agent loop** that replays ten sourced USDT/USDC events on a directed follow graph. The decoder is a **fact-card-conditioned decoder** (role prompt + slot fill + licensed mutation). Agents update a documented peg-confidence rubric. The study asks whether a small grounded agent society can reproduce qualitative cascade shapes (panic overshoot, official-reassurance lag, herding after a bearish-post threshold), and how cheaply rhetoric can move beliefs when facts are held fixed.

**Author:** Hossein Tabasi (M.Tech Computer Science and Engineering, Shoolini University). GitHub: `hosseinTabasi`.

**This repository is not a trading system, not investment advice, and not a live poster.** Missing facts are written `[UNKNOWN]`. No module invents reserve numbers, dates, quotes, transaction hashes, or 72-hour peg prints. Empirical tables in `reports/RESULTS.md` are `TO RUN` until a full N=120 / R=12 / 3-seed study is executed from JSON artifacts. A smoke path (`N=12`, `R=2`, `seed=0`) is for wiring only.

Assets in scope: **USDT and USDC only**. Eight development events (E01–E08), two held-out test events (E09–E10). Test events run only in controls C–E after prompts are frozen.

## How to run

```bash
cd /workspace/echomarket
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 src/run.py --smoke          # N=12 R=2 seed=0; prints smoke ok; <30s
python3 src/run.py --event E01 --condition C
python3 src/run.py --event E01 --condition D --tau 1.0

streamlit run app/app.py            # round playback, graph coloring, post inspector
```

`run.py` orchestrates: load config → build graph → loop rounds → write `data/*.jsonl`. Default `config/default.yaml` is N=120, R=12, seeds `[20260311, 20260813, 20260101]`. That size is heavy on a small machine if fully expanded; use `--smoke` here.

## File tree

```
echomarket/
  PROTOCOL.md                 # binding protocol, RQs, falsifiers
  README.md
  LICENSE                     # MIT
  requirements.txt
  config/default.yaml
  data/
    events.csv                # 3-sentence fact summaries, 10 events
    fact_cards.jsonl
    real_headlines.jsonl      # generator=human, condition A
    world.json agent.jsonl post.jsonl edge.jsonl panel_readout.jsonl
  prompts/                    # copy-paste JSON-forcing role files
  src/
    graph.py agents.py generate.py update.py
    attack.py defend.py evaluate.py calibrate.py
    schemas.py io_utils.py run.py
  app/app.py
  reports/
    RESULTS.md                # empty / TO RUN
    REPORT_OUTLINE.md
    VIVA.md
    CALENDAR_12_WEEK.md
    QLORA.md                  # journalist-only recipe; not run
```

## Controls

| Code | Meaning |
|------|---------|
| A | real-headline replay (no synthetic social) |
| B | isolated synthetic posts, no graph |
| C | full cascade, no red team |
| D | full cascade + red team |
| E-factcheck / E-ratelimit / E-detector | cascade plus one defense |

Red team: one extra agent, budget K=8 posts across R=12, `detector_p_ai ≤ τ`, τ grid `{0.3, 0.5, 0.7, 1.0}`. Rhetoric only; critic hallucination rate on red-team posts must be 0.

## JSON post schema

```json
{"text": "", "stance": "panic|reassurance|speculative|factual", "peg_sentiment": "bearish|neutral|bullish", "claimed_facts": [], "unknowns": [], "reply_to": null, "intent": "inform|reassure|alarm|persuade"}
```

Citations in the M.Tech outline are `[CITE: topic]` placeholders. Do not invent paper titles.
