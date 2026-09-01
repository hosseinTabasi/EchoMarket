"""Society construction and memory windows. Author: Hossein Tabasi."""

from __future__ import annotations

from typing import Any, Dict, List

from src.schemas import MUTATION_STYLE, SMOKE_ROLE_COUNTS


def role_counts_for(cfg: Dict[str, Any], n: int) -> Dict[str, int]:
    if n <= 12 or cfg.get("_smoke"):
        counts = dict(SMOKE_ROLE_COUNTS)
        total = sum(counts.values())
        if total != n:
            # pad/trim apathetic
            counts["retail_apathetic"] = max(0, counts["retail_apathetic"] + (n - total))
        return counts
    counts = dict(cfg.get("role_counts") or {})
    if sum(counts.values()) != n:
        # do not silently invent a 120-mix for other N; scale smoke-style if small
        if n < 120:
            return role_counts_for({**cfg, "_smoke": True}, min(n, 12))
    return counts


def build_society(cfg: Dict[str, Any], rng) -> List[Dict[str, Any]]:
    n = int(cfg.get("n_agents", 120))
    counts = role_counts_for(cfg, n)
    n_comm = int((cfg.get("graph") or {}).get("n_retail_communities", 4))
    priors = cfg.get("priors") or {}
    alpha = cfg.get("alpha") or {}
    beta = cfg.get("beta") or {}
    gamma = cfg.get("gamma") or {}
    p_post = cfg.get("p_post") or {}

    agents: List[Dict[str, Any]] = []
    retail_idx = 0
    seq = 0
    for role, k in counts.items():
        for _ in range(int(k)):
            community = -1
            if role.startswith("retail_"):
                community = retail_idx % max(1, n_comm)
                retail_idx += 1
            aid = f"A{seq:03d}-{role}"
            agents.append(
                {
                    "agent_id": aid,
                    "role": role,
                    "community": community,
                    "peg_confidence": float(priors.get(role, 60)),
                    "alpha": float(alpha.get(role, 1.0)),
                    "beta": float(beta.get(role, 0.5)),
                    "gamma": float(gamma.get(role, 1.0)),
                    "p_post": float(p_post.get(role, 0.2)),
                    "mutation": MUTATION_STYLE.get(role, "paraphrase"),
                    "memory": [],
                    "last_sentiment": "neutral",
                    "rebroadcasts_this_round": 0,
                }
            )
            seq += 1
    # freeze order; rng reserved for later shuffles
    _ = rng
    return agents


def remember(agent: Dict[str, Any], post: Dict[str, Any], window: int = 5) -> None:
    mem = agent.setdefault("memory", [])
    mem.append(
        {
            "post_id": post.get("post_id"),
            "author_id": post.get("author_id"),
            "text": post.get("text", ""),
            "peg_sentiment": post.get("peg_sentiment"),
            "stance": post.get("stance"),
        }
    )
    if len(mem) > window:
        del mem[: len(mem) - window]


def panel_ids(agents: List[Dict[str, Any]]) -> List[str]:
    from src.schemas import PANEL_SPEC

    out: List[str] = []
    by_role: Dict[str, List[Dict[str, Any]]] = {}
    for a in agents:
        by_role.setdefault(a["role"], []).append(a)
    for role, k in PANEL_SPEC:
        pool = sorted(by_role.get(role, []), key=lambda x: x["agent_id"])
        for a in pool[:k]:
            out.append(a["agent_id"])
    return out
