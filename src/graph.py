"""Directed follow / influence graph and PageRank. Author: Hossein Tabasi."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Sequence, Tuple

RETAIL_ROLES = {"retail_panic", "retail_skeptical", "retail_apathetic"}


def scaled_degree(base: int, n: int, n_full: int = 120) -> int:
    if n <= 1:
        return 0
    d = int(round(base * n / float(n_full)))
    return max(1, min(n - 1, d))


def pagerank(
    node_ids: Sequence[str],
    follower_to_followee: Sequence[Tuple[str, str]],
    damping: float = 0.85,
    iters: int = 40,
) -> Dict[str, float]:
    """PageRank on follower -> followee edges (widely followed nodes rank higher)."""
    n = len(node_ids)
    if n == 0:
        return {}
    idx = {nid: i for i, nid in enumerate(node_ids)}
    out: List[List[int]] = [[] for _ in range(n)]
    outdeg = [0] * n
    for src, dst in follower_to_followee:
        if src not in idx or dst not in idx or src == dst:
            continue
        i, j = idx[src], idx[dst]
        out[i].append(j)
        outdeg[i] += 1
    pr = [1.0 / n] * n
    teleport = (1.0 - damping) / n
    for _ in range(iters):
        new = [teleport] * n
        dangling = 0.0
        for i in range(n):
            if outdeg[i] == 0:
                dangling += pr[i]
            else:
                share = damping * pr[i] / outdeg[i]
                for j in out[i]:
                    new[j] += share
        extra = damping * dangling / n
        for i in range(n):
            new[i] += extra
        pr = new
    return {node_ids[i]: float(pr[i]) for i in range(n)}


def build_graph(
    agents: List[Dict[str, Any]],
    cfg: Dict[str, Any],
    rng,
) -> Tuple[List[Dict[str, Any]], Dict[str, float], Dict[str, List[str]]]:
    """Return edges (src broadcasts to dst), PR(author), and visibility lists (who dst sees)."""
    n = len(agents)
    ids = [a["agent_id"] for a in agents]
    by_id = {a["agent_id"]: a for a in agents}
    gcfg = cfg.get("graph") or {}
    trust_om = float(gcfg.get("official_media_trust", 0.8))
    trust_peer = float(gcfg.get("peer_trust", 0.4))
    intra = float(gcfg.get("intra_prob", 0.18))
    inter = float(gcfg.get("inter_prob", 0.02))
    deg_map = cfg.get("expected_out_degree") or {}

    edges: List[Dict[str, Any]] = []
    seen = set()

    def add_edge(src: str, dst: str, relation: str, weight: float) -> None:
        if src == dst:
            return
        key = (src, dst)
        if key in seen:
            return
        seen.add(key)
        edges.append({"src": src, "dst": dst, "relation": relation, "weight": weight})

    # Broadcasters: sample audience (dst follows src).
    for a in agents:
        role = a["role"]
        if role in RETAIL_ROLES:
            continue
        if role == "redteam":
            base = int(deg_map.get("redteam", 8))
            relation = "follow"
            weight = trust_peer
        elif role == "official":
            base = int(deg_map.get("official", 40))
            relation = "official"
            weight = trust_om
        elif role == "journalist":
            base = int(deg_map.get("journalist", 25))
            relation = "media"
            weight = trust_om
        else:
            base = int(deg_map.get(role, 8))
            relation = "follow"
            weight = trust_peer
        k = scaled_degree(base, n)
        others = [x for x in ids if x != a["agent_id"]]
        rng.shuffle(others)
        for dst in others[:k]:
            add_edge(a["agent_id"], dst, relation, weight)

    # Retail stochastic block: directed influence among retail.
    retail = [a for a in agents if a["role"] in RETAIL_ROLES]
    for src_a in retail:
        for dst_a in retail:
            if src_a["agent_id"] == dst_a["agent_id"]:
                continue
            p = intra if src_a.get("community", -1) == dst_a.get("community", -2) else inter
            if rng.random() < p:
                add_edge(src_a["agent_id"], dst_a["agent_id"], "follow", trust_peer)

    # Shuffled-graph control: rewire every destination, preserve out-degree.
    if cfg.get("shuffle_graph"):
        edges = shuffle_destinations(edges, ids, rng)

    # Visibility: dst sees posts from src.
    visible_from: Dict[str, List[str]] = {i: [] for i in ids}
    follow_pairs: List[Tuple[str, str]] = []
    for e in edges:
        visible_from[e["dst"]].append(e["src"])
        follow_pairs.append((e["dst"], e["src"]))  # follower -> followee for PR

    pr = pagerank(ids, follow_pairs, damping=float(cfg.get("pagerank_damping", 0.85)))
    # attach trust lookup
    trust: Dict[Tuple[str, str], float] = {}
    rel: Dict[Tuple[str, str], str] = {}
    for e in edges:
        trust[(e["src"], e["dst"])] = float(e["weight"])
        rel[(e["src"], e["dst"])] = e["relation"]

    graph_aux = {
        "visible_from": visible_from,
        "trust": trust,
        "relation": rel,
        "pagerank": pr,
        "by_id": by_id,
    }
    # stash on function attribute-free return: pack aux into a dict alongside
    return edges, pr, graph_aux


def shuffle_destinations(
    edges: List[Dict[str, Any]],
    agent_ids: Sequence[str],
    rng,
) -> List[Dict[str, Any]]:
    """Degree-preserving destination rewire (shuffled-graph control)."""
    others = list(agent_ids)
    out = []
    seen = set()
    for e in edges:
        dests = [x for x in others if x != e["src"]]
        rng.shuffle(dests)
        dst = dests[0] if dests else e["dst"]
        # try to avoid duplicate
        for cand in dests:
            if (e["src"], cand) not in seen:
                dst = cand
                break
        seen.add((e["src"], dst))
        ne = dict(e)
        ne["dst"] = dst
        out.append(ne)
    return out


def log1p_pr(pr: float) -> float:
    return math.log(1.0 + max(0.0, pr))
