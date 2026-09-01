"""Metrics from traces. Does not fill RESULTS.md. Author: Hossein Tabasi."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.defend import hallucination_flag
from src.update import bimodality, held_sentiment, herding_index


def time_to_20pct_bearish(agents_by_round: List[List[Dict[str, Any]]]) -> Optional[int]:
    for t, agents in enumerate(agents_by_round):
        if not agents:
            continue
        n_b = sum(1 for a in agents if held_sentiment(a["peg_confidence"]) == "bearish")
        if n_b / float(len(agents)) >= 0.20:
            return t
    return None


def cascade_size_depth(posts: List[Dict[str, Any]]) -> Tuple[int, int]:
    bearish_authors = {p["author_id"] for p in posts if p.get("peg_sentiment") == "bearish"}
    by_id = {p["post_id"]: p for p in posts if p.get("post_id")}

    def depth(pid: str, seen=None) -> int:
        seen = seen or set()
        if pid in seen or pid not in by_id:
            return 0
        seen.add(pid)
        parent = by_id[pid].get("reply_to")
        if not parent:
            return 1 if by_id[pid].get("is_rebroadcast") else 0
        return 1 + depth(parent, seen)

    dmax = 0
    for p in posts:
        if p.get("is_rebroadcast"):
            dmax = max(dmax, depth(p.get("post_id") or ""))
    return len(bearish_authors), dmax


def modularity_stance(agents: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Optional[float]:
    """Newman modularity on undirected retail projection partitioned by community."""
    retail = [a for a in agents if str(a.get("role", "")).startswith("retail_")]
    if len(retail) < 4:
        return None
    ids = {a["agent_id"]: a for a in retail}
    und = set()
    for e in edges:
        a, b = e["src"], e["dst"]
        if a in ids and b in ids and a != b:
            und.add(tuple(sorted((a, b))))
    m = len(und)
    if m == 0:
        return None
    comm = {a["agent_id"]: a.get("community", -1) for a in retail}
    deg = defaultdict(int)
    for a, b in und:
        deg[a] += 1
        deg[b] += 1
    q_std = 0.0
    nodes = list(ids)
    two_m = 2.0 * m
    for i in nodes:
        for j in nodes:
            if comm.get(i) != comm.get(j):
                continue
            aij = 1.0 if (tuple(sorted((i, j))) in und and i != j) else 0.0
            q_std += aij - (deg[i] * deg[j]) / two_m
    return q_std / two_m


def belief_snapshot(agents: List[Dict[str, Any]]) -> Dict[str, float]:
    cs = [float(a["peg_confidence"]) for a in agents]
    if not cs:
        return {"mean": 0.0, "variance": 0.0, "polarization": 0.0, "herding_index": 0.0}
    mean = sum(cs) / len(cs)
    var = sum((x - mean) ** 2 for x in cs) / len(cs)
    sents = [held_sentiment(c) for c in cs]
    return {
        "mean": mean,
        "variance": var,
        "polarization": bimodality(cs),
        "herding_index": herding_index(sents),
    }


def factuality_rate(posts: List[Dict[str, Any]], card: Dict[str, Any]) -> float:
    if not posts:
        return 0.0
    hits = sum(1 for p in posts if hallucination_flag(p.get("text") or "", card))
    return hits / float(len(posts))


def summarize(
    agents: List[Dict[str, Any]],
    posts: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    card: Dict[str, Any],
    agents_by_round: Optional[List[List[Dict[str, Any]]]] = None,
) -> Dict[str, Any]:
    size, depth = cascade_size_depth(posts)
    t20 = time_to_20pct_bearish(agents_by_round or [agents])
    snap = belief_snapshot(agents)
    red = [p for p in posts if p.get("is_redteam")]
    unk = "[UNKNOWN]" in str(card.get("price_or_peg_path_72h") or "")
    return {
        "cascade_size": size,
        "cascade_depth": depth,
        "time_to_20pct_bearish": t20 if t20 is not None else "TO RUN",
        "modularity": modularity_stance(agents, edges),
        "belief": snap,
        "factuality_hard_hallucination_rate": factuality_rate(posts, card),
        "redteam_hallucination_rate": factuality_rate(red, card) if red else 0.0,
        "n_posts": len(posts),
        "n_agents": len(agents),
        "fidelity_corr": "N/A" if unk else "TO RUN",
        "detectability_auc": "TO RUN",
    }


def pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)
