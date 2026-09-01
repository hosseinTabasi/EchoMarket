"""Belief update and deterministic risk-officer panel. Author: Hossein Tabasi."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Sequence, Tuple

from src.defend import hallucination_flag, number_not_on_card
from src.schemas import RISK_NEG, RISK_NEU_REG, RISK_POS


def clip01_100(x: float) -> float:
    return max(0.0, min(100.0, x))


def sigma(peg_sentiment: str) -> float:
    if peg_sentiment == "bearish":
        return -1.0
    if peg_sentiment == "bullish":
        return 1.0
    return 0.0


def stance_agreement(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if a == "neutral" or b == "neutral":
        return 0.5
    if {a, b} == {"bearish", "bullish"}:
        return 0.0
    return 0.5


def held_sentiment(confidence: float) -> str:
    if confidence < 45:
        return "bearish"
    if confidence > 55:
        return "bullish"
    return "neutral"


def herding_index(sentiments: Sequence[str]) -> float:
    if not sentiments:
        return 0.0
    n = float(len(sentiments))
    shares = []
    for lab in ("bearish", "neutral", "bullish"):
        shares.append(sum(1 for s in sentiments if s == lab) / n)
    ent = 0.0
    for p in shares:
        if p > 0:
            ent -= p * math.log(p)
    return 1.0 - (ent / math.log(3.0))


def bimodality(confidences: Sequence[float]) -> float:
    if not confidences:
        return 0.0
    n = float(len(confidences))
    frac = sum(1 for c in confidences if c < 40 or c > 60) / n
    return max(-0.5, min(0.5, frac - 0.5))


def update_agent(
    agent: Dict[str, Any],
    seen: List[Dict[str, Any]],
    card: Dict[str, Any],
    trust_lookup,
) -> Dict[str, float]:
    """Apply the exact PROTOCOL belief update. seen posts include virality V_i."""
    if not seen:
        return {"S": 0.0, "T": 0.0, "C": 0.0, "peg_confidence": float(agent["peg_confidence"])}
    s_terms = []
    t_terms = []
    c_any = 0
    for p in seen:
        v = float(p.get("virality", 0.0))
        sig = sigma(p.get("peg_sentiment") or "neutral")
        s_terms.append(sig * (0.5 + 0.5 * min(1.0, v)))
        src = p.get("author_id")
        dst = agent["agent_id"]
        w = 0.4
        if callable(trust_lookup):
            w = float(trust_lookup(src, dst))
        elif isinstance(trust_lookup, dict):
            w = float(trust_lookup.get((src, dst), 0.4))
        t_terms.append(sig * w)
        txt = p.get("text") or ""
        if hallucination_flag(txt, card) or p.get("C_flag"):
            c_any = 1
        elif number_not_on_card(txt, card):
            c_any = 1
    S = sum(s_terms) / len(s_terms)
    T = sum(t_terms) / len(t_terms)
    C = float(c_any)
    new = agent["peg_confidence"] + agent["alpha"] * S + agent["beta"] * T - agent["gamma"] * C
    new = clip01_100(new)
    agent["peg_confidence"] = new
    agent["last_sentiment"] = held_sentiment(new)
    return {"S": S, "T": T, "C": C, "peg_confidence": new}


def score_text_risk_officer(text: str, card: Dict[str, Any]) -> Tuple[float, List[str]]:
    """Deterministic SynthOpinion-style rubric. Not a fabricated model score."""
    tl = (text or "").lower()
    delta = 0.0
    reasons: List[str] = []
    n_neg = sum(1 for k in RISK_NEG if k in tl)
    n_pos = sum(1 for k in RISK_POS if k in tl)
    if n_neg:
        delta -= min(18.0, 4.0 * n_neg)
        reasons.append(f"depeg/restriction lexicon hits={n_neg}")
    if n_pos:
        delta += min(16.0, 3.5 * n_pos)
        reasons.append(f"backstop/excess/1:1 lexicon hits={n_pos}")
    if any(k in tl for k in RISK_NEU_REG) and n_neg == 0:
        delta += 1.5
        reasons.append("regulatory/attestation framing with no depeg lexicon")
    off = number_not_on_card(text, card)
    if off:
        delta -= min(25.0, 8.0 * len(off))
        reasons.append(f"off-card numerals penalized n={len(off)}")
    path = (card.get("price_or_peg_path_72h") or "").lower()
    if "negative" in path and n_neg:
        delta -= 4.0
        reasons.append("text aligned with sourced negative peg path")
    if "positive" in path and n_pos:
        delta += 4.0
        reasons.append("text aligned with sourced recovery path")
    if "[unknown]" in path:
        delta *= 0.45
        reasons.append("peg path [UNKNOWN]: magnitude shrunk")
    if not reasons:
        reasons.append("no lexicon hit; near-prior")
    return delta, reasons[:3]


def panel_readout(
    agent: Dict[str, Any],
    seen_texts: List[str],
    card: Dict[str, Any],
) -> Dict[str, Any]:
    prior = float(agent.get("peg_confidence", 70.0))
    deltas = []
    all_r: List[str] = []
    for t in seen_texts:
        d, r = score_text_risk_officer(t, card)
        deltas.append(d)
        all_r.extend(r)
    if deltas:
        mean_d = sum(deltas) / len(deltas)
        post = clip01_100(prior + mean_d)
    else:
        post = prior
        all_r = ["prior only"]
    uniq = []
    for x in all_r:
        if x not in uniq:
            uniq.append(x)
    return {
        "agent_id": agent["agent_id"],
        "role": agent["role"],
        "rubric_score": post,
        "reasons": uniq[:3],
        "peg_confidence": float(agent.get("peg_confidence", post)),
    }
