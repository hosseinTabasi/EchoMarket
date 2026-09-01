#!/usr/bin/env python3
"""EchoMarket orchestrator: load config → graph → rounds → jsonl.

Author: Hossein Tabasi
Usage:
  python src/run.py --smoke
  python src/run.py --event E01 --condition C
"""

from __future__ import annotations

import argparse
import copy
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents import build_society, panel_ids, remember  # noqa: E402
from src.attack import maybe_red_post  # noqa: E402
from src.calibrate import check_config, fidelity_applicable  # noqa: E402
from src.defend import (  # noqa: E402
    apply_detector_gate,
    detector_p_ai,
    factcheck_correction,
    hallucination_flag,
    retail_rate_limited,
)
from src.evaluate import summarize  # noqa: E402
from src.generate import generate_one, virality  # noqa: E402
from src.graph import build_graph  # noqa: E402
from src.io_utils import CONFIG, DATA, load_yaml, read_csv, read_jsonl, write_json, write_jsonl  # noqa: E402
from src.update import panel_readout, stance_agreement, update_agent  # noqa: E402


def load_event_card(event_id: str):
    events = {e["event_id"]: e for e in read_csv(DATA / "events.csv")}
    cards = {c["event_id"]: c for c in read_jsonl(DATA / "fact_cards.jsonl")}
    if event_id not in events or event_id not in cards:
        raise SystemExit(f"unknown event {event_id}")
    return events[event_id], cards[event_id]


def apply_smoke(cfg: Dict[str, Any]) -> Dict[str, Any]:
    sm = cfg.get("smoke") or {}
    cfg = copy.deepcopy(cfg)
    cfg["n_agents"] = int(sm.get("n_agents", 12))
    cfg["rounds"] = int(sm.get("rounds", 2))
    cfg["seed"] = int(sm.get("seed", 0))
    cfg["red_budget_k"] = int(sm.get("red_budget_k", 1))
    cfg["_smoke"] = True
    return cfg


def trust_fn(aux):
    table = aux["trust"]

    def _t(src, dst):
        return float(table.get((src, dst), 0.4))

    return _t


def inject_real_headlines(event, round_index, rng) -> List[Dict[str, Any]]:
    rows = [r for r in read_jsonl(DATA / "real_headlines.jsonl") if r.get("event_id") == event["event_id"]]
    if not rows:
        return []
    # spread headlines across rounds
    chunk = max(1, int(round((len(rows) + 1) / 4)))
    start = (round_index * chunk) % len(rows)
    picked = rows[start : start + max(1, min(2, len(rows)))]
    out = []
    for i, r in enumerate(picked):
        out.append(
            {
                "text": r["text"],
                "stance": r.get("stance", "factual"),
                "peg_sentiment": r.get("peg_sentiment", "neutral"),
                "claimed_facts": [r["text"]],
                "unknowns": [],
                "reply_to": None,
                "intent": "inform",
                "generator": "human",
                "is_redteam": False,
                "is_rebroadcast": False,
            }
        )
    _ = rng
    return out


def simulate(cfg: Dict[str, Any], event: Dict[str, Any], card: Dict[str, Any]) -> Dict[str, Any]:
    seed = int(cfg.get("seed", 0))
    rng = random.Random(seed)
    condition = str(cfg.get("condition", "C"))
    tau = float(cfg.get("tau", 1.0))
    rounds = int(cfg.get("rounds", 12))
    isolated = condition == "B"
    use_graph = condition not in {"A", "B"}
    use_synth = condition != "A"
    use_red = condition == "D" or condition.startswith("E-")
    defense = None
    if condition == "E-factcheck":
        defense = "factcheck"
    elif condition == "E-ratelimit":
        defense = "ratelimit"
    elif condition == "E-detector":
        defense = "detector"

    split = event.get("split", "dev")
    if split == "test" and condition in {"A", "B"} and not cfg.get("_smoke"):
        raise SystemExit("PROTOCOL: E09/E10 (test) run only in C–E after prompts frozen")

    agents = build_society(cfg, rng)
    if use_red:
        # extra red-team agent
        agents.append(
            {
                "agent_id": "ARED-redteam",
                "role": "redteam",
                "community": -1,
                "peg_confidence": float((cfg.get("priors") or {}).get("redteam", 50)),
                "alpha": float((cfg.get("alpha") or {}).get("redteam", 2.0)),
                "beta": float((cfg.get("beta") or {}).get("redteam", 0.5)),
                "gamma": float((cfg.get("gamma") or {}).get("redteam", 1.0)),
                "p_post": 0.0,  # posts via attack budget, not p_post
                "mutation": "rhetoric",
                "memory": [],
                "last_sentiment": "neutral",
                "rebroadcasts_this_round": 0,
            }
        )

    if use_graph:
        edges, pr, aux = build_graph(agents, cfg, rng)
    else:
        edges, pr, aux = [], {a["agent_id"]: 1.0 / max(1, len(agents)) for a in agents}, {
            "visible_from": {a["agent_id"]: [] for a in agents},
            "trust": {},
            "relation": {},
            "pagerank": {},
            "by_id": {a["agent_id"]: a for a in agents},
        }

    tf = trust_fn(aux)
    lambdas = cfg.get("virality") or {}
    if isolated:
        lambdas = {**lambdas, "lambda_p": 0.0}
    theta = float(cfg.get("theta_rebroadcast", 0.35))
    panel = set(panel_ids(agents))
    budget = int(cfg.get("red_budget_k", 8)) if use_red else 0
    uniform_trust = 0.4

    all_posts: List[Dict[str, Any]] = []
    snapshots: List[List[Dict[str, Any]]] = []
    panel_rows: List[Dict[str, Any]] = []
    pid = 0

    def next_pid() -> str:
        nonlocal pid
        pid += 1
        return f"P{pid:05d}"

    by_id = {a["agent_id"]: a for a in agents}

    for t in range(rounds):
        for a in agents:
            a["rebroadcasts_this_round"] = 0
        round_posts: List[Dict[str, Any]] = []
        recent = [p.get("text", "") for p in all_posts if p.get("round", -99) >= t - 2]

        # Condition A: human headlines only
        if not use_synth:
            payloads = inject_real_headlines(event, t, rng)
            authors = [a for a in agents if a["role"] in {"journalist", "official"}]
            for i, pl in enumerate(payloads):
                author = authors[i % max(1, len(authors))] if authors else agents[0]
                rec = dict(pl)
                rec["post_id"] = next_pid()
                rec["round"] = t
                rec["author_id"] = author["agent_id"]
                rec["event_id"] = event["event_id"]
                rec["detector_p_ai"] = detector_p_ai(rec["text"])
                rec["virality"] = virality(pr.get(author["agent_id"], 0.0), rec["text"], recent, lambdas)
                rec["generator"] = "human"
                round_posts.append(rec)
        else:
            order = list(agents)
            rng.shuffle(order)
            for a in order:
                if a["role"] == "redteam":
                    continue
                if rng.random() > float(a["p_post"]):
                    continue
                pl = generate_one(
                    a["role"],
                    event,
                    card,
                    rng,
                    memory=a.get("memory"),
                    mutation_style=a.get("mutation"),
                )
                rec = dict(pl)
                rec["post_id"] = next_pid()
                rec["round"] = t
                rec["author_id"] = a["agent_id"]
                rec["event_id"] = event["event_id"]
                rec["generator"] = "prompt-only-decoder"
                rec["is_redteam"] = False
                rec["is_rebroadcast"] = False
                rec["detector_p_ai"] = detector_p_ai(rec["text"])
                rec["C_flag"] = hallucination_flag(rec["text"], card)
                if defense == "detector" and apply_detector_gate(rec, tau):
                    rec["dropped"] = True
                    continue
                rec["virality"] = virality(pr.get(a["agent_id"], 0.0), rec["text"], recent, lambdas)
                round_posts.append(rec)

            if use_red:
                red_pl = maybe_red_post(
                    event, card, rng, tau, budget, t, rounds, "ARED-redteam"
                )
                if red_pl:
                    budget -= 1
                    rec = dict(red_pl)
                    rec["post_id"] = next_pid()
                    rec["round"] = t
                    rec["event_id"] = event["event_id"]
                    rec["generator"] = "prompt-only-decoder"
                    rec["C_flag"] = hallucination_flag(rec["text"], card)
                    rec["virality"] = virality(pr.get("ARED-redteam", 0.0), rec["text"], recent, lambdas)
                    if defense == "detector" and apply_detector_gate(rec, tau):
                        rec["dropped"] = True
                    else:
                        round_posts.append(rec)

        # Fact-check bot: one correction if any ungrounded post this round
        if defense == "factcheck":
            offenders = [p for p in round_posts if p.get("C_flag") or hallucination_flag(p.get("text") or "", card)]
            if offenders:
                txt = factcheck_correction(card, event, offenders[0]["text"])
                fc = {
                    "text": txt,
                    "stance": "factual",
                    "peg_sentiment": "neutral",
                    "claimed_facts": (card.get("verified_facts") or [])[:2],
                    "unknowns": ["72-hour peg path not sourced on the fact card"]
                    if "[UNKNOWN]" in str(card.get("price_or_peg_path_72h") or "")
                    else [],
                    "reply_to": offenders[0]["post_id"],
                    "intent": "inform",
                    "post_id": next_pid(),
                    "round": t,
                    "author_id": "BOT-factcheck",
                    "event_id": event["event_id"],
                    "generator": "prompt-only-decoder",
                    "is_redteam": False,
                    "is_rebroadcast": False,
                    "detector_p_ai": detector_p_ai(txt),
                    "C_flag": hallucination_flag(txt, card),
                    "virality": virality(0.0, txt, recent, lambdas),
                }
                round_posts.append(fc)

        # Rebroadcasts
        extra: List[Dict[str, Any]] = []
        if use_graph:
            vis = aux["visible_from"]
            for a in agents:
                if a["role"] == "redteam":
                    continue
                incoming = [p for p in round_posts if p["author_id"] in vis.get(a["agent_id"], [])]
                for p in incoming:
                    agr = stance_agreement(p.get("peg_sentiment") or "neutral", a.get("last_sentiment") or "neutral")
                    w = tf(p["author_id"], a["agent_id"])
                    if w * agr <= theta:
                        continue
                    if defense == "ratelimit" and retail_rate_limited(a):
                        continue
                    # mutate copy
                    mpl = generate_one(
                        a["role"],
                        event,
                        card,
                        rng,
                        memory=a.get("memory"),
                        reply_to=p["post_id"],
                        mutation_style=a.get("mutation"),
                    )
                    # keep sentiment agreement with source for the rebroadcast
                    mpl["peg_sentiment"] = p.get("peg_sentiment") or mpl["peg_sentiment"]
                    rec = dict(mpl)
                    rec["post_id"] = next_pid()
                    rec["round"] = t
                    rec["author_id"] = a["agent_id"]
                    rec["event_id"] = event["event_id"]
                    rec["generator"] = "prompt-only-decoder"
                    rec["is_redteam"] = False
                    rec["is_rebroadcast"] = True
                    rec["reply_to"] = p["post_id"]
                    rec["detector_p_ai"] = detector_p_ai(rec["text"])
                    rec["C_flag"] = hallucination_flag(rec["text"], card)
                    if defense == "detector" and apply_detector_gate(rec, tau):
                        continue
                    rec["virality"] = virality(pr.get(a["agent_id"], 0.0), rec["text"], recent, lambdas)
                    extra.append(rec)
                    a["rebroadcasts_this_round"] = int(a.get("rebroadcasts_this_round", 0)) + 1
                    if defense == "ratelimit" and str(a["role"]).startswith("retail_"):
                        break
        round_posts.extend(extra)

        # Seen sets + belief update
        vis = aux.get("visible_from") or {}
        for a in agents:
            if isolated or not use_graph:
                seen = list(round_posts)
                def ut(_s, _d):
                    return uniform_trust
                upd_trust = ut
            else:
                followees = set(vis.get(a["agent_id"], []))
                seen = [p for p in round_posts if p["author_id"] in followees or p.get("author_id") == a["agent_id"]]
                # everyone sees fact-check corrections
                if defense == "factcheck":
                    seen = seen + [p for p in round_posts if p.get("author_id") == "BOT-factcheck" and p not in seen]
                upd_trust = tf
            update_agent(a, seen, card, upd_trust)
            for p in seen[:5]:
                remember(a, p, window=5)

        all_posts.extend(round_posts)
        snapshots.append(
            [
                {
                    "agent_id": a["agent_id"],
                    "role": a["role"],
                    "community": a["community"],
                    "peg_confidence": a["peg_confidence"],
                }
                for a in agents
            ]
        )

        if (t + 1) % int(cfg.get("panel_every", 2)) == 0:
            texts = [p.get("text", "") for p in round_posts][:5]
            for aid in panel:
                a = by_id.get(aid)
                if not a:
                    continue
                row = panel_readout(a, texts, card)
                row["round"] = t
                row["event_id"] = event["event_id"]
                panel_rows.append(row)

    world = {
        "schema": "echomarket.world.v1",
        "event_id": event["event_id"],
        "condition": condition,
        "n_agents": len(agents),
        "rounds": rounds,
        "seed": seed,
        "tau": tau,
        "split": event.get("split"),
        "smoke": bool(cfg.get("_smoke")),
        "fidelity_applicable": fidelity_applicable(card),
        "disclaimer": "Not investment advice. Peg-confidence is a rubric score, not a forecast. No live posts.",
    }
    metrics = summarize(agents, all_posts, edges, card, snapshots)
    return {
        "world": world,
        "agents": [
            {k: a[k] for k in ("agent_id", "role", "community", "peg_confidence", "alpha", "beta", "gamma", "p_post", "mutation")}
            for a in agents
        ],
        "posts": all_posts,
        "edges": edges,
        "panel": panel_rows,
        "snapshots": snapshots,
        "metrics": metrics,
    }


def persist(bundle: Dict[str, Any]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    write_json(DATA / "world.json", bundle["world"])
    write_jsonl(DATA / "agent.jsonl", bundle["agents"])
    write_jsonl(DATA / "post.jsonl", bundle["posts"])
    write_jsonl(DATA / "edge.jsonl", bundle["edges"])
    write_jsonl(DATA / "panel_readout.jsonl", bundle["panel"])
    write_json(DATA / "snapshots.json", bundle["snapshots"])
    write_json(DATA / "last_metrics.json", bundle["metrics"])


def main(argv: Optional[List[str]] = None) -> int:
    t0 = time.time()
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=str(CONFIG / "default.yaml"))
    p.add_argument("--event", default=None)
    p.add_argument("--condition", default=None)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--tau", type=float, default=None)
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args(argv)

    cfg = load_yaml(Path(args.config))
    if args.smoke:
        cfg = apply_smoke(cfg)
        cfg["event_id"] = args.event or "E01"
        cfg["condition"] = args.condition or "C"
    else:
        if args.event:
            cfg["event_id"] = args.event
        if args.condition:
            cfg["condition"] = args.condition
        if args.seed is not None:
            cfg["seed"] = args.seed
    if args.tau is not None:
        cfg["tau"] = args.tau

    errs = check_config(cfg)
    if errs and not cfg.get("_smoke"):
        print("config warnings:", "; ".join(errs))

    event, card = load_event_card(str(cfg.get("event_id", "E01")))
    bundle = simulate(cfg, event, card)
    persist(bundle)
    elapsed = time.time() - t0
    print(
        "event", event["event_id"],
        "condition", bundle["world"]["condition"],
        "n", bundle["world"]["n_agents"],
        "R", bundle["world"]["rounds"],
        "posts", len(bundle["posts"]),
        "edges", len(bundle["edges"]),
        f"elapsed_s={elapsed:.2f}",
    )
    if args.smoke:
        if elapsed >= 30:
            print("smoke slow")
            return 1
        base_n = sum(1 for a in bundle["agents"] if a.get("role") != "redteam")
        if base_n > 12 or bundle["world"]["rounds"] > 2:
            print("smoke too large")
            return 1
        print("smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
